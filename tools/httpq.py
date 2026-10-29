#!/usr/bin/env python3
"""httpq.py -- one HTTP/HTTPS request to a device's management interface, from the testbox.

A minimal, dependency-free client for the third management access path.  `service http` is a
feature a Management case has to grade just like telnet and ssh, and the only honest way to
say what the web interface does -- or that there is nothing behind it -- is to ask it.

It prints the status line, the response headers and (optionally truncated) body, so a case can
quote what the device actually answered instead of inferring it from `show http`.

Device certificates are self-signed (`CN = AlliedwarePlusDefault`), so TLS verification is OFF
by default: this talks to lab hardware on a lab segment, never to anything that matters.

Usage:
  httpq.py <url> [--method M] [--user U --password P] [--data STR] [--header 'K: V']...
           [--timeout S] [--max-body N] [--verify] [--head-only]

Exit: 0 got a response (whatever its status), 4 the transport failed, 6 usage.
"""

import argparse
import base64
import ssl
import sys
import urllib.error
import urllib.request


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("url")
    ap.add_argument("--method", default="GET")
    ap.add_argument("--user", default=None)
    ap.add_argument("--password", default=None)
    ap.add_argument("--data", default=None,
                    help="request body; sets the method to POST unless --method says otherwise")
    ap.add_argument("--header", action="append", default=[],
                    help="extra request header 'Key: value'; repeatable")
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--max-body", type=int, default=4000)
    ap.add_argument("--verify", action="store_true",
                    help="verify TLS (off by default: device certs are self-signed)")
    ap.add_argument("--head-only", action="store_true", help="do not print the body")
    ap.add_argument("--cafile", default=None,
                    help="verify the server chain against THIS CA file (PEM); implies --verify")
    ap.add_argument("--no-hostname-check", action="store_true",
                    help="with --verify/--cafile: check the chain but not the name (an IP URL "
                         "against a CN-only cert has no SAN to match)")
    ap.add_argument("--peer-cert", action="store_true",
                    help="https only: first print the certificate the server presents "
                         "(subject, issuer, SAN, validity, SHA-256), read without verification")
    args = ap.parse_args()

    method = args.method.upper()
    body = args.data.encode() if args.data is not None else None
    if body is not None and method == "GET":
        method = "POST"

    req = urllib.request.Request(args.url, data=body, method=method)
    for h in args.header:
        if ":" not in h:
            print("httpq: bad --header %r (want 'Key: value')" % h)
            return 6
        k, v = h.split(":", 1)
        req.add_header(k.strip(), v.strip())
    if args.user is not None:
        token = base64.b64encode(
            ("%s:%s" % (args.user, args.password or "")).encode()).decode()
        req.add_header("Authorization", "Basic " + token)
    if body is not None and not any(h.lower() == "content-type"
                                    for h in req.headers):
        req.add_header("Content-Type", "application/x-www-form-urlencoded")

    # Build the context unconditionally, not just for an https:// URL: an AW+ device answers
    # plain http with a 301 to https, urllib follows it, and a context attached only to an
    # https starting URL is not in play by then -- the redirect then dies on
    # CERTIFICATE_VERIFY_FAILED against the device's self-signed cert (tb277 2026-10-20).
    if args.cafile:
        args.verify = True
    ctx = ssl.create_default_context(cafile=args.cafile) if args.cafile else ssl.create_default_context()
    if args.verify and args.no_hostname_check:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_REQUIRED
    if not args.verify:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    print("=== %s %s ===" % (method, args.url))
    print("TLS: %s" % ("chain verified against %s%s" % (args.cafile or "the system store",
                                                        ", hostname NOT checked" if args.no_hostname_check else "")
                       if args.verify else "NOT verified"))
    if args.peer_cert and args.url.lower().startswith("https://"):
        show_peer_cert(args.url, args.timeout)
    try:
        resp = urllib.request.urlopen(req, timeout=args.timeout, context=ctx)
        status, reason, headers = resp.status, resp.reason, resp.headers
        payload = resp.read(args.max_body + 1)
    except urllib.error.HTTPError as exc:
        status, reason, headers = exc.code, exc.reason, exc.headers
        payload = exc.read(args.max_body + 1)
    except (urllib.error.URLError, OSError, ssl.SSLError) as exc:
        print("TRANSPORT FAILED: %s" % exc)
        return 4

    print("HTTP %s %s" % (status, reason))
    for k, v in sorted(headers.items()):
        print("  %s: %s" % (k, v))
    if args.head_only:
        return 0
    print("--- body (%d bytes shown%s) ---"
          % (min(len(payload), args.max_body),
             ", TRUNCATED" if len(payload) > args.max_body else ""))
    sys.stdout.write(payload[:args.max_body].decode("utf-8", "replace"))
    print()
    return 0


def show_peer_cert(url, timeout):
    """Print the server's certificate as presented, without trusting it."""
    import hashlib, socket, tempfile, os
    from urllib.parse import urlsplit
    u = urlsplit(url)
    host, port = u.hostname, u.port or 443
    c = ssl.create_default_context()
    c.check_hostname = False
    c.verify_mode = ssl.CERT_NONE
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            with c.wrap_socket(s, server_hostname=host) as ss:
                der = ss.getpeercert(binary_form=True)
                ver = ss.version()
    except (OSError, ssl.SSLError) as exc:
        print("PEER CERT: connect failed: %s" % exc)
        return
    pem = ssl.DER_cert_to_PEM_cert(der)
    fd, path = tempfile.mkstemp(suffix=".pem")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(pem)
        d = ssl._ssl._test_decode_cert(path)
    except Exception as exc:                      # decoding is a convenience, never fatal
        d = {"error": str(exc)}
    finally:
        os.unlink(path)
    flat = lambda x: ", ".join("%s=%s" % kv for rdn in x for kv in rdn) if x else "-"
    print("PEER CERT (%s): subject %s" % (ver, flat(d.get("subject"))))
    print("  issuer   %s" % flat(d.get("issuer")))
    print("  SAN      %s" % (", ".join("%s:%s" % kv for kv in d.get("subjectAltName", ())) or "-"))
    print("  valid    %s -> %s   serial %s" % (d.get("notBefore"), d.get("notAfter"), d.get("serialNumber")))
    print("  sha256   %s" % hashlib.sha256(der).hexdigest())


if __name__ == "__main__":
    sys.exit(main())
