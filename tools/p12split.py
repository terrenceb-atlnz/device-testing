#!/usr/bin/env python3
"""p12split.py -- split a PKCS#12 bundle into the pieces an EAP-TLS supplicant needs,
and MEASURE each piece, so a client certificate flight's size is a number and not a guess.

Why this exists
---------------
A switch that enrols a user against its own CA (AW+ `crypto pki enroll local user <u>`)
exports a PKCS#12 that carries the CA certificate ALONGSIDE the leaf.  wpa_supplicant
hands the whole bundle to OpenSSL, which then sends the whole chain in the client's
TLS Certificate message.  On tb277 that made the client flight 2141 bytes -- two EAP-TLS
fragments -- and wpa_supplicant 2.6 (which predates RFC 9190) declared the EAP method Done
with the second fragment unsent (T9032 run 1, 2026-10-23).

Splitting the bundle and passing `client_cert` + `private_key` separately keeps the CA out
of the client's chain while `ca_cert` still validates the SERVER.  This tool does the split
and prints the DER size of every certificate, so the resulting flight size can be predicted
and compared against what the wire actually shows.

It shells out to the `openssl` CLI on purpose: a testbox always has it, and the python
`cryptography` package is not installed on every bench host.

Run
---
  p12split.py <bundle.p12> --passwd P [--out-dir D] [--name N] [--no-chain]

Writes, into --out-dir (default: the bundle's directory):
  <name>-leaf.pem   the CLIENT certificate alone        -> wpa_supplicant client_cert
  <name>-key.pem    the private key, unencrypted, 0600  -> wpa_supplicant private_key
  <name>-chain.pem  every OTHER certificate in the bundle (usually the issuing CA),
                    written for the record and NOT meant to be given to client_cert

Prints one line per certificate with its DER size, subject and issuer, then the predicted
TLS Certificate message payload for a leaf-only credential and for the whole chain.
Exit 0 on success, 2 on a bad bundle or a wrong passphrase.
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile


def run(cmd, stdin=None):
    p = subprocess.run(cmd, input=stdin, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, universal_newlines=True)
    return p.returncode, p.stdout, p.stderr


def pem_blocks(text):
    return re.findall(
        r"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----\n?",
        text, re.S)


def cert_facts(pem):
    """DER length, subject and issuer of one PEM certificate."""
    with tempfile.NamedTemporaryFile("w", suffix=".pem", delete=False) as fh:
        fh.write(pem)
        path = fh.name
    try:
        p = subprocess.run(["openssl", "x509", "-in", path, "-outform", "DER"],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        der_len = len(p.stdout)
        _, txt, _ = run(["openssl", "x509", "-in", path, "-noout",
                         "-subject", "-issuer", "-dates"])
    finally:
        os.unlink(path)
    subject = issuer = notafter = "?"
    for line in txt.splitlines():
        if line.startswith("subject="):
            subject = line[len("subject="):].strip()
        elif line.startswith("issuer="):
            issuer = line[len("issuer="):].strip()
        elif line.startswith("notAfter="):
            notafter = line[len("notAfter="):].strip()
    return der_len, subject, issuer, notafter


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("p12")
    ap.add_argument("--passwd", required=True,
                    help="the bundle's export passphrase")
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--name", default=None,
                    help="basename for the written files (default: the bundle's stem)")
    ap.add_argument("--no-chain", action="store_true",
                    help="do not write the <name>-chain.pem file")
    args = ap.parse_args()

    if not os.path.isfile(args.p12):
        print("p12split: no such file: %s" % args.p12, file=sys.stderr)
        return 2
    out_dir = args.out_dir or os.path.dirname(os.path.abspath(args.p12))
    os.makedirs(out_dir, exist_ok=True)
    name = args.name or os.path.splitext(os.path.basename(args.p12))[0]

    passin = "pass:" + args.passwd

    rc, leaf_pem, err = run(["openssl", "pkcs12", "-in", args.p12, "-passin", passin,
                             "-clcerts", "-nokeys"])
    if rc != 0:
        print("p12split: could not read the client certificate -- %s"
              % err.strip().splitlines()[-1:], file=sys.stderr)
        return 2
    rc, ca_pem, err = run(["openssl", "pkcs12", "-in", args.p12, "-passin", passin,
                           "-cacerts", "-nokeys"])
    if rc != 0:
        ca_pem = ""
    rc, key_pem, err = run(["openssl", "pkcs12", "-in", args.p12, "-passin", passin,
                            "-nocerts", "-nodes"])
    if rc != 0:
        print("p12split: could not read the private key -- %s"
              % err.strip().splitlines()[-1:], file=sys.stderr)
        return 2

    leaves = pem_blocks(leaf_pem)
    cas = pem_blocks(ca_pem)
    if not leaves:
        print("p12split: the bundle holds no client certificate", file=sys.stderr)
        return 2

    leaf_path = os.path.join(out_dir, name + "-leaf.pem")
    key_path = os.path.join(out_dir, name + "-key.pem")
    chain_path = os.path.join(out_dir, name + "-chain.pem")

    with open(leaf_path, "w") as fh:
        fh.write(leaves[0])
    # keep only the key block; openssl -nodes also echoes bag attributes
    key_body = re.search(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?"
                         r"-----END [A-Z ]*PRIVATE KEY-----\n?", key_pem, re.S)
    if not key_body:
        print("p12split: no private key block in the bundle", file=sys.stderr)
        return 2
    with open(key_path, "w") as fh:
        fh.write(key_body.group(0))
    os.chmod(key_path, 0o600)
    if cas and not args.no_chain:
        with open(chain_path, "w") as fh:
            fh.write("".join(cas))

    print("bundle: %s" % os.path.abspath(args.p12))
    total = 0
    leaf_len, subj, iss, exp = cert_facts(leaves[0])
    total += leaf_len
    print("  LEAF  %5d bytes DER  subject=%s" % (leaf_len, subj))
    print("                        issuer =%s  notAfter=%s" % (iss, exp))
    for i, c in enumerate(cas):
        n, s, isr, e = cert_facts(c)
        total += n
        print("  CA[%d] %5d bytes DER  subject=%s" % (i, n, s))
        print("                        issuer =%s  notAfter=%s" % (isr, e))
    if not cas:
        print("  (no additional certificates in the bundle -- it was already leaf-only)")

    # TLS Certificate message: 3-byte msg header + 3-byte list length
    # (TLS<=1.2) and 3 bytes of length per entry; TLS 1.3 adds a 1-byte
    # context length and 2 bytes of extensions per entry.
    leaf_only_12 = leaf_len + 3 + 3 + 3
    chain_12 = total + 3 + 3 + 3 * (1 + len(cas))
    print("  predicted TLS Certificate payload: leaf-only %d bytes, whole chain %d bytes"
          % (leaf_only_12, chain_12))
    print("  (an EAP-TLS fragment on a 1500-byte wire carries about 1398 bytes, so a client")
    print("   flight above roughly 1.4 kB needs a SECOND fragment)")
    print("wrote:")
    print("  client_cert  %s" % leaf_path)
    print("  private_key  %s   (mode 0600)" % key_path)
    if cas and not args.no_chain:
        print("  chain (record only, NOT for client_cert)  %s" % chain_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
