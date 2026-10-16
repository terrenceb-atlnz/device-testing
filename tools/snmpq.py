#!/usr/bin/env python3
"""Run one net-snmp query against an agent and CLASSIFY the outcome.

Why a wrapper: a bench verdict needs the difference between "the agent answered with a value",
"the agent answered that the OID is outside my MIB view", "the agent rejected my credentials"
and "nothing came back at all".  net-snmp expresses all four on stdout/stderr with exit status 1
for most of them, so a raw exit code cannot grade a step.  This classifies and sets a distinct
exit code, and can repeat a query so a packet capture started in parallel is certain to catch it.

Classes (and exit codes):
  0 VALUE      at least one `OID = TYPE: value` came back
  1 NOSUCH     noSuchObject / noSuchInstance / "No more variables left in this MIB View"
  2 DENIED     authorizationError -- the credentials are good, the view forbids the OID
  3 AUTHFAIL   unknown user / authentication failure / decryption error / unsupported sec level
  4 TIMEOUT    no response at all
  5 ERROR      anything else (usage, name resolution, unparsed)
  6 EXPECTFAIL --expect was given and the class did not match (overrides the class code)

Usage:
  snmpq.py get|getnext|walk|set <agent> <oid> [<oid>...] [options]

  v3:   --v3 --user U --level noAuthNoPriv|authNoPriv|authPriv
        [--auth-proto MD5|SHA] [--auth-pass P] [--priv-proto DES|AES] [--priv-pass P]
  v2c:  --v2c --community C          v1: --v1 --community C
  set:  --set-type i|u|s|x|a|o|t|b --set-value V      (one oid only)
  also: --timeout S (default 3) --retries N (default 1) --port N
        --repeat N --interval S     repeat the same query N times, S seconds apart
        --expect VALUE|NOSUCH|DENIED|AUTHFAIL|TIMEOUT   grade it, print GRADE PASS/FAIL
        --quiet                     print only the RESULT/GRADE lines
"""
import argparse
import hashlib
import subprocess
import sys
import time

CLASSES = ["VALUE", "NOSUCH", "DENIED", "AUTHFAIL", "TIMEOUT", "ERROR"]


def classify(out, err, rc):
    """Return (class, evidence-line) from a net-snmp invocation."""
    blob = (out or "") + (err or "")
    low = blob.lower()

    def first(*needles):
        for line in blob.splitlines():
            ll = line.lower()
            for n in needles:
                if n in ll:
                    return line.strip()
        return ""

    if "timeout: no response" in low or "no response from" in low:
        return "TIMEOUT", first("timeout", "no response")
    for n in ("unknown user name", "authentication failure", "unsupported security level",
              "decryption error", "not in time window", "wrong digest",
              "authentication error", "usmstats"):
        if n in low:
            return "AUTHFAIL", first(n)
    if "authorizationerror" in low or "authorization error" in low or "not writable" in low:
        return "DENIED", first("authorization", "not writable")
    for n in ("no such object", "no such instance",
              "no more variables left in this mib view", "nosuchobject", "nosuchinstance"):
        if n in low:
            return "NOSUCH", first("no such", "no more variables")
    for line in blob.splitlines():
        if " = " in line and not line.strip().startswith(("Error", "Reason")):
            return "VALUE", line.strip()
    if rc == 0 and blob.strip() == "":
        return "NOSUCH", "(empty response, exit 0)"
    return "ERROR", (blob.strip().splitlines() or [""])[0]


def build(a, oids):
    cmd = {"get": "snmpget", "getnext": "snmpgetnext", "walk": "snmpwalk", "set": "snmpset"}[a.op]
    argv = ["/usr/bin/" + cmd, "-On", "-t", str(a.timeout), "-r", str(a.retries)]
    if a.v3:
        argv += ["-v", "3", "-u", a.user, "-l", a.level]
        if a.auth_pass is not None:
            argv += ["-a", a.auth_proto, "-A", a.auth_pass]
        if a.priv_pass is not None:
            argv += ["-x", a.priv_proto, "-X", a.priv_pass]
        if a.context:
            argv += ["-n", a.context]
        if a.engine_id:
            argv += ["-e", a.engine_id]
    else:
        argv += ["-v", "1" if a.v1 else "2c", "-c", a.community]
    target = a.agent if not a.port else "%s:%d" % (a.agent, a.port)
    argv.append(target)
    argv += list(oids)
    if a.op == "set":
        argv += [a.set_type, a.set_value]
    return argv


def fingerprint(s):
    """A non-disclosing identity for a password: its length and a sha1 prefix.

    This is what makes a shell-quoting accident visible.  A password with `!`, `$`, a backtick,
    a backslash or `{}` in it can be mangled on its way through a local shell, ssh and a remote
    shell, and the agent then reports an authentication failure that reads exactly like the
    feature being broken.  Printing the fingerprint the CLIENT actually used lets two legs be
    compared byte-for-byte without ever writing the secret into a log.
    """
    return "<PASS len=%d sha1=%s>" % (len(s), hashlib.sha1(s.encode("utf-8")).hexdigest()[:10])


def redact(argv, a):
    """A printable command line with the USM passwords replaced by their fingerprints."""
    mask = {p: fingerprint(p) for p in (a.auth_pass, a.priv_pass) if p is not None}
    return " ".join(mask.get(tok, tok) for tok in argv)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("op", choices=["get", "getnext", "walk", "set"])
    ap.add_argument("agent")
    ap.add_argument("oids", nargs="+")
    ap.add_argument("--v3", action="store_true")
    ap.add_argument("--v2c", action="store_true")
    ap.add_argument("--v1", action="store_true")
    ap.add_argument("--community", default="public")
    ap.add_argument("--user", default="")
    ap.add_argument("--level", default="authPriv",
                    choices=["noAuthNoPriv", "authNoPriv", "authPriv"])
    ap.add_argument("--auth-proto", default="MD5")
    ap.add_argument("--auth-pass", default=None)
    ap.add_argument("--priv-proto", default="DES")
    ap.add_argument("--priv-pass", default=None)
    ap.add_argument("--context", default=None)
    ap.add_argument("--engine-id", default=None)
    ap.add_argument("--set-type", default="s")
    ap.add_argument("--set-value", default="")
    ap.add_argument("--timeout", type=float, default=3)
    ap.add_argument("--retries", type=int, default=1)
    ap.add_argument("--port", type=int, default=0)
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--interval", type=float, default=2)
    ap.add_argument("--expect", default=None, choices=CLASSES)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    if not (a.v3 or a.v2c or a.v1):
        a.v2c = True
    if a.v3 and not a.user:
        ap.error("--v3 needs --user")

    argv = build(a, a.oids)
    if not a.quiet:
        print("CMD  %s" % redact(argv, a))

    cls, ev, rc = "ERROR", "", 5
    for i in range(a.repeat):
        if i:
            time.sleep(a.interval)
        p = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             universal_newlines=True)
        out, err = p.communicate()
        cls, ev = classify(out, err, p.returncode)
        if not a.quiet:
            for line in (out or "").splitlines() + (err or "").splitlines():
                if line.strip():
                    print("  | %s" % line.rstrip())
        print("RESULT %s -- %s%s" % (cls, ev, "" if a.repeat == 1 else "   [%d/%d]" % (i + 1, a.repeat)))
        rc = CLASSES.index(cls)

    if a.expect:
        ok = (cls == a.expect)
        print("GRADE %s -- expected %s, got %s" % ("PASS" if ok else "FAIL", a.expect, cls))
        return 0 if ok else 6
    return rc


if __name__ == "__main__":
    sys.exit(main())
