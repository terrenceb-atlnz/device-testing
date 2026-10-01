"""Shared AW+ login/expect for the console drivers (same prompt-waiting login as ckcon.py).

Library, not a command: `import console, awlogin as L` from a sibling script, then
    c = console.Console(tty, transcript, baud=baud); ok = L.login(c)
Credentials default to console.USERNAME / console.PASSWORD (manager/friend unless the
env vars CK_USER / CK_PASSWORD are set), or pass login(c, username=..., password=...)."""
import os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import console

LOGIN, PASSWD, PRIV, USER, NEWPW, BAD = (r"login:\s*$", r"Password:\s*$", r"#\s*$", r">\s*$",
                                         r"new password", r"Login incorrect")
YN = r"\(y/n\)\s*:?\s*$"


def expect(c, pats, timeout):
    buf = ""; t0 = time.time()
    while time.time() - t0 < timeout:
        b = c.s.read(4096)
        if b:
            s = b.decode(errors="replace"); c._t.write(s); buf += s
            for p in pats:
                if re.search(p, buf[-400:]):
                    return p, buf
        else:
            time.sleep(0.05)
    return None, buf


def login(c, tries=5, username=None, password=None):
    user = (console.USERNAME if username is None else username).encode()
    pw = (console.PASSWORD if password is None else password).encode()
    expect(c, [r"$^"], 0.5)
    c.s.write(b"\r")
    for _ in range(tries):
        p, out = expect(c, [LOGIN, PASSWD, PRIV, USER, NEWPW], 15)
        if p is None:
            c.s.write(b"\r"); continue
        if p == NEWPW:
            raise SystemExit("forced password-change dialog; refusing")
        if p == LOGIN:
            c.s.write(user + b"\r")
            if expect(c, [PASSWD], 10)[0] is None: continue
            c.s.write(pw + b"\r")
            p3, _ = expect(c, [PRIV, USER, BAD, NEWPW], 25)
            if p3 in (None, BAD): continue
            if p3 == NEWPW: raise SystemExit("forced password-change dialog")
            if p3 == USER: c.s.write(b"enable\r"); expect(c, [PRIV], 15)
            break
        if p == PASSWD:
            c.s.write(pw + b"\r"); expect(c, [PRIV, USER, BAD, LOGIN], 25); c.s.write(b"\r"); continue
        if p == USER:
            c.s.write(b"enable\r"); expect(c, [PRIV], 15)
        break
    c.s.write(b"\r")
    if expect(c, [PRIV], 8)[0] is None:
        return False
    if not c.to_exec():             # a parked host(config)# prompt -> end first
        return False
    c.cmd("terminal length 0", timeout=15.0)
    return c.monitor_off()          # exec-only; console.py set_monitor()


def stamp():
    t = time.time()
    return "%.3f %s" % (t, time.strftime("%H:%M:%S", time.localtime(t)))


if __name__ == "__main__":
    # A library: running it directly only explains how to use it.
    print("usage: import console, awlogin as L  (library; run a driver such as cfg.py instead)")
    sys.exit(0 if sys.argv[1:2] in (["-h"], ["--help"]) else 2)
