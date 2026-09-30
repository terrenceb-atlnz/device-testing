#!/usr/bin/env python3
"""ckyn.py <tty> <baud> <transcript> CMD [CMD ...]
Like ckcon.py --stop-on-error, but a CMD prefixed "YN:" is expected to prompt (y/n): the
driver waits for "(y/n)", answers "y\\r" (memories awplus-config-prompts-abort-and-logout,
awplus-cli-confirmations-need-enter), then waits for the privileged/config prompt. A (y/n)
on a command NOT marked YN:, or a missing (y/n) on a marked one, stops the run with the
line unanswered-safe ("n\\r" is sent to decline an unexpected prompt). Stops on any "% " line."""
import sys, time, re
sys.path.insert(0, "/tmp/ck5093")
tty, baud, transcript = sys.argv[1], int(sys.argv[2]), sys.argv[3]
cmds = sys.argv[4:]
sys.path.insert(0, "/tmp/ckorient")
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
LOGIN, PASSWD, PRIV, USER, NEWPW, BAD = (r"login:\s*$", r"Password:\s*$", r"#\s*$", r">\s*$", r"new password", r"Login incorrect")
YN = r"\(y/n\)(\[[yn]\])?\s*:?\s*$"
def login():
    expect([r"$^"], 0.5); c.s.write(b"\r")
    for _ in range(5):
        p, out = expect([LOGIN, PASSWD, PRIV, USER, NEWPW], 15)
        if p is None: c.s.write(b"\r"); continue
        if p == NEWPW: raise SystemExit("forced password-change dialog; refusing")
        if p == LOGIN:
            c.s.write(b"manager\r")
            if expect([PASSWD], 10)[0] is None: continue
            c.s.write(b"friend\r")
            p3, _ = expect([PRIV, USER, BAD, NEWPW], 25)
            if p3 in (None, BAD): continue
            if p3 == NEWPW: raise SystemExit("forced password-change dialog")
            if p3 == USER: c.s.write(b"enable\r"); expect([PRIV], 15)
            break
        if p == PASSWD:
            c.s.write(b"friend\r"); expect([PRIV, USER, BAD, LOGIN], 25); c.s.write(b"\r"); continue
        if p == USER: c.s.write(b"enable\r"); expect([PRIV], 15)
        break
    c.s.write(b"\r")
    if expect([PRIV], 8)[0] is None: raise SystemExit("no privileged prompt")
    c.cmd("terminal length 0", timeout=15.0); c.cmd("terminal no monitor", timeout=15.0); c.monitor = False
rc = 0; ok = False
try:
    login(); ok = True
    for line in cmds:
        yn = line.startswith("YN:"); cmd = line[3:] if yn else line
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
        elif yn:
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
