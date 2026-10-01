#!/usr/bin/env python3
"""ckyn.py <tty> <baud> <transcript> CMD [CMD ...]
(Was ckyn3.py. "YN?:" = the command MAY prompt (y/n); answered y\\r if it does, no stop if it
 does not -- e.g. T12589: `no mls qos` gave no prompt on an IE520 on 2026-09-30.)
Like ckcon.py --stop-on-error, but a CMD prefixed "YN:" is expected to prompt (y/n): the
driver waits for "(y/n)", answers "y\\r" (memories awplus-config-prompts-abort-and-logout,
awplus-cli-confirmations-need-enter), then waits for the privileged/config prompt. A (y/n)
on a command NOT marked YN:, or a missing (y/n) on a marked one, stops the run with the
line unanswered-safe ("n\\r" is sent to decline an unexpected prompt). Stops on any "% " line.
<tty> is the unit's console device on the testbox you run it on; <transcript> is a path you
choose. Env: CK_USER / CK_PASSWORD = login credentials (default manager / friend)."""
import os, sys, time, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
USAGE = "usage: ckyn.py <tty> <baud> <transcript> [YN:|YN?:]CMD [[YN:|YN?:]CMD ...]"
if len(sys.argv) < 4 or sys.argv[1] in ("-h", "--help"):
    print(USAGE); sys.exit(0 if sys.argv[1:2] in (["-h"], ["--help"]) else 2)
try:
    tty, baud, transcript = sys.argv[1], int(sys.argv[2]), sys.argv[3]
except ValueError as e:
    print(USAGE); print("bad argument: %s" % e); sys.exit(2)
cmds = sys.argv[4:]
import console
c = console.Console(tty, transcript, baud=baud)
def expect(pats, timeout):
    buf = ""; t0 = time.time()
    while time.time() - t0 < timeout:
        b = c.s.read(4096)
        if b:
            s = b.decode(errors="replace"); c._t.write(s); buf += s
            for p in pats:
                if re.search(p, buf[-400:]): return p, buf
        else: time.sleep(0.05)
    return None, buf
LOGIN, PASSWD, PRIV, USER, NEWPW, BAD = (r"login:\s*$", r"Password:\s*$", r"#[ \t]*(?:\s*[\w.]+: (?:entered|left) [a-z ]+ mode)*\s*$", r">\s*$", r"new password", r"Login incorrect")
YN = r"\(y/n\)(\[[yn]\])?\s*:?\s*$"
def login():
    expect([r"$^"], 0.5); c.s.write(b"\r")
    for _ in range(5):
        p, out = expect([LOGIN, PASSWD, PRIV, USER, NEWPW], 15)
        if p is None: c.s.write(b"\r"); continue
        if p == NEWPW: raise SystemExit("forced password-change dialog; refusing")
        if p == LOGIN:
            c.s.write((console.USERNAME + "\r").encode())
            if expect([PASSWD], 10)[0] is None: continue
            c.s.write((console.PASSWORD + "\r").encode())
            p3, _ = expect([PRIV, USER, BAD, NEWPW], 25)
            if p3 in (None, BAD): continue
            if p3 == NEWPW: raise SystemExit("forced password-change dialog")
            if p3 == USER: c.s.write(b"enable\r"); expect([PRIV], 15)
            break
        if p == PASSWD:
            c.s.write((console.PASSWORD + "\r").encode()); expect([PRIV, USER, BAD, LOGIN], 25); c.s.write(b"\r"); continue
        if p == USER: c.s.write(b"enable\r"); expect([PRIV], 15)
        break
    c.s.write(b"\r")
    if expect([PRIV], 8)[0] is None: raise SystemExit("no privileged prompt")
    c.cmd("terminal length 0", timeout=15.0); c.cmd("terminal no monitor", timeout=15.0); c.monitor = False
rc = 0; ok = False
try:
    login(); ok = True
    for line in cmds:
        opt = line.startswith("YN?:"); yn = line.startswith("YN:") or opt
        cmd = line[4:] if opt else (line[3:] if yn else line)
        expect([r"$^"], 0.2)
        c.s.write((cmd + "\r").encode())
        p, out = expect([YN, PRIV], 60)
        if p == YN:
            if not yn:
                c.s.write(b"n\r"); _, o2 = expect([PRIV], 30); out += o2
                print("{} >>> {}".format(time.strftime("%H:%M:%S"), cmd)); print(out)
                print("!!! unexpected (y/n) -- declined with n, stopping"); rc = 3; break
            c.s.write(b"y\r"); p2, o2 = expect([PRIV, LOGIN], 120); out += o2
            if p2 != PRIV:
                print(out); print("!!! no prompt after answering y (p=%r) -- stopping" % p2); rc = 4; break
        elif p is None:
            print(out); print("!!! no prompt within 60 s -- stopping"); rc = 5; break
        elif yn and not opt:
            print("{} >>> {}".format(time.strftime("%H:%M:%S"), cmd)); print(out)
            print("!!! expected (y/n) but got a prompt -- stopping"); rc = 6; break
        print("{} >>> {}".format(time.strftime("%H:%M:%S"), cmd)); print(out)
        if any(l.lstrip().startswith("%") for l in out.replace("\r", "").splitlines()):
            print("!!! CLI error on {!r} -- stopping".format(cmd)); rc = 2; break
finally:
    if ok:
        try:
            raw = c.send("", timeout=5.0)
            if "(config" in raw: c.cmd("end", timeout=15.0)
            c.cmd("terminal no monitor", timeout=15.0)
        except Exception as e: print("cleanup:", e)
    c.close()
sys.exit(rc)
