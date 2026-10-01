#!/usr/bin/env python3
"""reloadc.py <tty> <baud> <transcript> <listen_s> <donefile> <command...>
Log in (awlogin.login), send <command> (e.g. `reload`), answer the (y/n) with y+CR, print
the EVENT epoch, then passively record the console (stamped lines) for <listen_s> s. Sends
nothing else. Touches <donefile> with the end epoch. <tty> is the console device of the AW+
unit (e.g. /dev/uN on a testbox); <transcript> and <donefile> are paths you choose.
Stops (exit 3) without a privileged prompt, (exit 4) if <command> asks no (y/n)."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
USAGE = "usage: reloadc.py <tty> <baud> <transcript> <listen_s> <donefile> <command...>"
if sys.argv[1:2] in (["-h"], ["--help"]):
    print(USAGE); print(__doc__); sys.exit(0)
if len(sys.argv) < 7:
    print(USAGE); sys.exit(2)
try:
    tty, baud, tr, listen, done = sys.argv[1], int(sys.argv[2]), sys.argv[3], float(sys.argv[4]), sys.argv[5]
except ValueError as e:
    print(USAGE); print("bad argument: %s" % e); sys.exit(2)
import console, awlogin as L
command = " ".join(sys.argv[6:])
c = console.Console(tty, tr, baud=baud)
try:
    if not L.login(c):
        print("no privileged prompt; not reloading"); sys.exit(3)
    L.expect(c, [r"$^"], 0.2)
    c.s.write((command + "\r").encode())
    p, out = L.expect(c, [L.YN, L.PRIV], 30)
    print(out)
    if p != L.YN:
        print("!!! no (y/n) prompt -- not reloading"); sys.exit(4)
    t = time.time(); c.s.write(b"y\r")
    print("EVENT y-sent %.3f %s" % (t, time.strftime("%H:%M:%S", time.localtime(t))))
    t0 = time.time(); last_login = None
    while time.time() - t0 < listen:
        b = c.s.read(4096)
        if b:
            s = b.decode(errors="replace"); c._t.write(s)
            for line in s.replace("\r", "").splitlines():
                if line.strip():
                    print("%.3f %s" % (time.time(), line))
            if "login:" in s and last_login is None:
                last_login = time.time(); print("EVENT login-banner %.3f" % last_login)
        else:
            time.sleep(0.05)
        sys.stdout.flush()
finally:
    c.close()
    open(done, "w").write("%.3f\n" % time.time())
