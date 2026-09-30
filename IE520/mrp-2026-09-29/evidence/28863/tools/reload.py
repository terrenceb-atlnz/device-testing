#!/usr/bin/env python3
"""reload.py <tty> <baud> <transcript> <member> <listen_s> <donefile>
Log in, send `reload stack-member <member>`, answer the (y/n) with y+CR, print the epoch
at which `y` was sent (EVENT line), then keep the console open and passively record what
it prints for <listen_s> s (stamped per chunk) -- this is the reloading member's own
console, so it shows the reboot. Sends nothing after `y` except a bare CR once a login:
banner appears, to read it. Touches <donefile> at the end."""
import sys, time
sys.path.insert(0, "/tmp/ck15")
import console, ck15lib as L
tty, baud, tr, member, listen, done = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], float(sys.argv[5]), sys.argv[6]
c = console.Console(tty, tr, baud=baud)
try:
    if not L.login(c):
        print("no privileged prompt; not reloading"); sys.exit(3)
    print(L.stamp(), "stack before:"); print(c.cmd("show stack", timeout=20))
    L.expect(c, [r"$^"], 0.2)
    c.s.write(("reload stack-member %s\r" % member).encode())
    p, out = L.expect(c, [L.YN, L.PRIV], 30)
    print(out)
    if p != L.YN:
        print("!!! no (y/n) prompt -- not reloading"); sys.exit(4)
    t = time.time()
    c.s.write(b"y\r")
    print("EVENT reload-y-sent %.3f %s" % (t, time.strftime("%H:%M:%S", time.localtime(t))))
    t0 = time.time(); seen_login = False
    while time.time() - t0 < listen:
        b = c.s.read(4096)
        if b:
            s = b.decode(errors="replace"); c._t.write(s)
            for line in s.replace("\r", "").splitlines():
                if line.strip():
                    print("%.3f %s" % (time.time(), line))
            if "login:" in s:
                seen_login = True
                print("EVENT login-banner %.3f" % time.time())
                break
        else:
            time.sleep(0.05)
    print("listen ended, login banner seen:", seen_login)
finally:
    c.close()
    open(done, "w").write("%.3f\n" % time.time())
