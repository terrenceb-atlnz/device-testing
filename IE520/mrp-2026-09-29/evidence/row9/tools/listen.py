#!/usr/bin/env python3
"""listen.py <tty> <baud> <transcript> <listen_s> <donefile> -- passive: record every line
the console prints, stamped, for <listen_s> s. Sends nothing."""
import sys, time
sys.path.insert(0, "/tmp/ck9")
import console
tty, baud, tr, listen, done = sys.argv[1], int(sys.argv[2]), sys.argv[3], float(sys.argv[4]), sys.argv[5]
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
