#!/usr/bin/env python3
"""reloadc.py <tty> <baud> <transcript> <listen_s> <donefile> <command...>
Log in, send <command> (e.g. `reload`), answer the (y/n) with y+CR, print the EVENT epoch,
then passively record the console (stamped lines) for <listen_s> s. Sends nothing else,
except one bare CR per 20 s once a login: banner has appeared. Touches <donefile>."""
import sys, time
sys.path.insert(0, "/tmp/ck9")
import console, ck15lib as L
tty, baud, tr, listen, done = sys.argv[1], int(sys.argv[2]), sys.argv[3], float(sys.argv[4]), sys.argv[5]
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
