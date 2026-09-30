#!/usr/bin/env python3
"""ckcon.py <tty> <baud> <transcript> [--stop-on-error] CMD [CMD ...]
Drive one AW+ console with the maintained console.py (quiet mode), print each
command and its output, and (with --stop-on-error) stop at the first "% " line.
Login waits on PROMPTS, never on quiet (orient-dt §3, 2026-09-28): the username is
sent only when a login prompt is showing, nothing else is sent until a prompt is seen,
and the exit preamble is sent only after a successful login."""
import sys, time, re, os
sys.path.insert(0, "/tmp/ckorient")
import console
tty, baud, transcript = sys.argv[1], int(sys.argv[2]), sys.argv[3]
args = sys.argv[4:]
stop = False
if args and args[0] == "--stop-on-error":
    stop = True; args = args[1:]
c = console.Console(tty, transcript, baud=baud)

def expect(pats, timeout):
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

LOGIN, PASSWD, PRIV, USER, NEWPW, BAD = (r"login:\s*$", r"Password:\s*$", r"#\s*$", r">\s*$", r"new password", r"Login incorrect")

def login():
    expect([r"$^"], 0.5)          # drain
    c.s.write(b"\r")
    for _ in range(5):
        p, out = expect([LOGIN, PASSWD, PRIV, USER, NEWPW], 15)
        if p is None:
            c.s.write(b"\r"); continue
        if p == NEWPW:
            raise SystemExit("forced password-change dialog on %s; refusing" % tty)
        if p == LOGIN:
            c.s.write(b"manager\r")
            if expect([PASSWD], 10)[0] is None: continue
            c.s.write(b"friend\r")
            p3, _ = expect([PRIV, USER, BAD, NEWPW], 25)
            if p3 in (None, BAD): continue
            if p3 == NEWPW: raise SystemExit("forced password-change dialog on %s" % tty)
            if p3 == USER:
                c.s.write(b"enable\r"); expect([PRIV], 15)
            break
        if p == PASSWD:            # stale dialog from a stray line: answer, then re-evaluate
            c.s.write(b"friend\r"); expect([PRIV, USER, BAD, LOGIN], 25); c.s.write(b"\r"); continue
        if p == USER:
            c.s.write(b"enable\r"); expect([PRIV], 15)
        break
    c.s.write(b"\r")
    if expect([PRIV], 8)[0] is None:
        raise SystemExit("no privileged prompt on %s" % tty)
    c.cmd("terminal length 0", timeout=15.0)
    c.cmd("terminal no monitor", timeout=15.0)
    c.monitor = False

rc = 0
ok = False
try:
    login(); ok = True
    for line in args:
        out = c.cmd(line, timeout=float(os.environ.get("CKTO", "90")))
        print("{} >>> {}".format(time.strftime("%H:%M:%S"), line))
        if out:
            print(out)
        if stop and any(l.lstrip().startswith("%") for l in out.splitlines()):
            print("!!! CLI error on {!r} -- stopping".format(line))
            rc = 2
            break
finally:
    if ok:
        try:
            raw = c.send("", timeout=5.0)
            if "(config" in raw:
                c.cmd("end", timeout=15.0)
            c.cmd("terminal no monitor", timeout=15.0)
        except Exception as e:
            print("cleanup: {}".format(e))
    c.close()
sys.exit(rc)
