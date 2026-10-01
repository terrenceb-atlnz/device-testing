#!/usr/bin/env python3
"""listen.py <tty> <baud> <transcript> <listen_s> <donefile> -- passive: record every line
the console prints, stamped, for <listen_s> s. Sends nothing (no login: it records whatever
the console already prints). <tty> is the unit's console device on the testbox you run it
on; <transcript> and <donefile> are paths you choose."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
USAGE = "usage: listen.py <tty> <baud> <transcript> <listen_s> <donefile>"
if len(sys.argv) != 6 or sys.argv[1] in ("-h", "--help"):
    print(USAGE); sys.exit(0 if sys.argv[1:2] in (["-h"], ["--help"]) else 2)
try:
    tty, baud, tr, listen, done = sys.argv[1], int(sys.argv[2]), sys.argv[3], float(sys.argv[4]), sys.argv[5]
except ValueError as e:
    print(USAGE); print("bad argument: %s" % e); sys.exit(2)
import console
c = console.Console(tty, tr, baud=baud)
try:
    t0 = time.time()
    while time.time() - t0 < listen:
        b = c.s.read(4096)
        if b:
            s = b.decode(errors="replace"); c._t.write(s)
            for line in s.replace("\r", "").splitlines():
                if line.strip():
                    print("%.3f %s" % (time.time(), line))
            sys.stdout.flush()
        else:
            time.sleep(0.05)
finally:
    c.close()
    open(done, "w").write("%.3f\n" % time.time())
