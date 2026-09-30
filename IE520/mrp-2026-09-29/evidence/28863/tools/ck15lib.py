"""Shared login/expect for the T28863 drivers (same prompt-waiting login as ckcon.py)."""
import re, sys, time
sys.path.insert(0, "/tmp/ck15")
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


def login(c, tries=5):
    expect(c, [r"$^"], 0.5)
    c.s.write(b"\r")
    for _ in range(tries):
        p, out = expect(c, [LOGIN, PASSWD, PRIV, USER, NEWPW], 15)
        if p is None:
            c.s.write(b"\r"); continue
        if p == NEWPW:
            raise SystemExit("forced password-change dialog; refusing")
        if p == LOGIN:
            c.s.write(b"manager\r")
            if expect(c, [PASSWD], 10)[0] is None: continue
            c.s.write(b"friend\r")
            p3, _ = expect(c, [PRIV, USER, BAD, NEWPW], 25)
            if p3 in (None, BAD): continue
            if p3 == NEWPW: raise SystemExit("forced password-change dialog")
            if p3 == USER: c.s.write(b"enable\r"); expect(c, [PRIV], 15)
            break
        if p == PASSWD:
            c.s.write(b"friend\r"); expect(c, [PRIV, USER, BAD, LOGIN], 25); c.s.write(b"\r"); continue
        if p == USER:
            c.s.write(b"enable\r"); expect(c, [PRIV], 15)
        break
    c.s.write(b"\r")
    if expect(c, [PRIV], 8)[0] is None:
        return False
    c.cmd("terminal length 0", timeout=15.0)
    c.cmd("terminal no monitor", timeout=15.0)
    c.monitor = False
    return True


def stamp():
    t = time.time()
    return "%.3f %s" % (t, time.strftime("%H:%M:%S", time.localtime(t)))
