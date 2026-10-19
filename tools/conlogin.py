#!/usr/bin/env python3
"""conlogin.py <tty> <baud> <transcript> --user U --password P [options]

Log a console OUT and back IN as a named user, and report what the login did.  This is the
instrument an AAA case needs: `aaa authentication login` only runs when somebody actually
logs in, so a case that configures RADIUS, TACACS+ or local authentication has to produce a
real login attempt and grade it.  A `show` command cannot do that.

It reports the outcome as one machine-readable line and as an exit code, so a FAILED login is
a first-class result rather than an error:

    LOGIN RESULT: PRIV|USER|FAIL|TIMEOUT  user=<u>  seconds=<s>  prompt=<the last line seen>

Afterwards it can log back in as a known-good fallback user, so a case that deliberately
breaks authentication always hands the console back usable.

Options:
  --user U --password P     the credentials to test (P may be empty)
  --logout                  log out again after a successful test login (default: stay in)
  --restore-user U          log in as this user at the end (default: CK_USER, `manager`)
  --restore-password P      its password (default: CK_PASSWORD, `friend`)
  --no-restore              do not log back in at the end
  --settle S                seconds to wait for the login verdict (default 25)
  --expect fail|priv|user   what the case expects; sets exit 0 when it matches and 5 when it
                            does not, instead of the code-per-outcome below

Exit (without --expect): 0 reached a privileged `#` prompt, 1 reached an unprivileged `>`
prompt, 2 the login was refused, 3 nothing recognisable within --settle, 4 the RESTORE login
failed (the serious one -- the console may need a human), 6 usage error.
"""
import argparse
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import console

LOGIN = r"login:\s*$"
PASSWD = r"[Pp]assword:\s*$"
PRIV = r"[\w.-]+(?:\([\w -]+\))?#[ \t]*$"
USER = r"[\w.-]+>[ \t]*$"
BAD = r"Login incorrect|Authentication failed|% Login invalid|Access denied"
NEWPW = r"new password"


def expect(c, pats, timeout):
    buf, t0 = "", time.time()
    while time.time() - t0 < timeout:
        b = c.s.read(4096)
        if b:
            s = b.decode(errors="replace")
            c._t.write(s)
            buf += s
            for p in pats:
                if re.search(p, buf[-600:], re.M):
                    return p, buf
        else:
            time.sleep(0.05)
    return None, buf


def last_line(buf):
    for ln in reversed(buf.replace("\r", "\n").split("\n")):
        if ln.strip():
            return ln.strip()[:120]
    return ""


def to_login(c, timeout=30.0):
    """Get the console to a `login:` banner, whatever state it is in."""
    for _ in range(6):
        c.s.write(b"\r")
        p, buf = expect(c, [LOGIN, PRIV, USER, PASSWD], 8)
        if p == LOGIN:
            return True
        if p == PRIV:
            c.s.write(b"end\r")
            expect(c, [PRIV], 5)
            c.s.write(b"exit\r")
            if expect(c, [LOGIN], 12)[0] == LOGIN:
                return True
        elif p == USER:
            c.s.write(b"exit\r")
            if expect(c, [LOGIN], 12)[0] == LOGIN:
                return True
        elif p == PASSWD:
            c.s.write(b"\r")          # abandon a half-finished login
    return False


def do_login(c, user, password, settle):
    """Return (outcome, prompt_line, seconds)."""
    t0 = time.time()
    c.s.write((user + "\r").encode())
    p, buf = expect(c, [PASSWD, BAD, LOGIN], 15)
    if p != PASSWD:
        return ("FAIL" if p else "TIMEOUT"), last_line(buf), time.time() - t0
    c.s.write((password + "\r").encode())
    p, buf = expect(c, [PRIV, USER, BAD, LOGIN, NEWPW], settle)
    took = time.time() - t0
    if p == NEWPW:
        return "FAIL", "forced password change dialog", took
    if p == PRIV:
        return "PRIV", last_line(buf), took
    if p == USER:
        return "USER", last_line(buf), took
    if p in (BAD, LOGIN):
        # a refusal usually prints the message and then re-offers `login:`
        expect(c, [LOGIN], 8)
        return "FAIL", last_line(buf), took
    return "TIMEOUT", last_line(buf), took


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("tty")
    ap.add_argument("baud", type=int)
    ap.add_argument("transcript")
    ap.add_argument("--user", required=True)
    ap.add_argument("--password", default="")
    ap.add_argument("--logout", action="store_true")
    ap.add_argument("--restore-user", default=console.USERNAME)
    ap.add_argument("--restore-password", default=console.PASSWORD)
    ap.add_argument("--no-restore", action="store_true")
    ap.add_argument("--settle", type=float, default=25.0)
    ap.add_argument("--expect", choices=["fail", "priv", "user"])
    ap.add_argument("-h", "--help", action="store_true")
    a = ap.parse_args()
    if a.help:
        print(__doc__)
        return 0

    c = console.Console(a.tty, a.transcript, baud=a.baud)
    rc = 6
    try:
        if not to_login(c):
            print("conlogin: could not reach a `login:` banner -- console not touched further")
            return 3
        outcome, prompt, took = do_login(c, a.user, a.password, a.settle)
        print("LOGIN RESULT: %s  user=%s  seconds=%.1f  prompt=%r"
              % (outcome, a.user, took, prompt))
        rc = {"PRIV": 0, "USER": 1, "FAIL": 2, "TIMEOUT": 3}[outcome]
        if outcome in ("PRIV", "USER") and a.logout:
            c.s.write(b"exit\r")
            expect(c, [LOGIN], 12)
            print("conlogin: logged out again")
        if a.expect:
            want = {"fail": "FAIL", "priv": "PRIV", "user": "USER"}[a.expect]
            ok = (outcome == want)
            print("conlogin: expected %s, got %s -- %s" % (want, outcome, "MATCH" if ok else "MISMATCH"))
            rc = 0 if ok else 5
    finally:
        if not a.no_restore:
            try:
                if to_login(c):
                    o, pr, _ = do_login(c, a.restore_user, a.restore_password, 25.0)
                    print("conlogin: restore login as %s -> %s (%r)" % (a.restore_user, o, pr))
                    if o not in ("PRIV", "USER"):
                        print("!!! conlogin: RESTORE LOGIN FAILED -- the console is at a "
                              "login prompt and may need a human")
                        rc = 4
                    elif o == "USER":
                        c.s.write(b"enable\r")
                        expect(c, [PRIV, PASSWD], 10)
                else:
                    print("!!! conlogin: could not reach `login:` to restore")
                    rc = 4
                try:
                    c.to_exec()
                    c.monitor_off()
                except Exception as e:
                    print("conlogin: cleanup:", e)
            except Exception as e:
                print("conlogin: restore raised:", e)
                rc = 4
        c.close()
    return rc


if __name__ == "__main__":
    sys.exit(main())
