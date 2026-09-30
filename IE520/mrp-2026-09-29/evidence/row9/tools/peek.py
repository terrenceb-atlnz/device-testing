#!/usr/bin/env python3
"""peek.py tty baud transcript -- open with console.py, send one bare CR, print the tail."""
import sys, time
sys.path.insert(0, "/tmp/ck9")
import console
c = console.Console(sys.argv[1], sys.argv[3], baud=int(sys.argv[2]))
try:
    c.s.read(4096)
    c.s.write(b"\r"); time.sleep(2.0)
    out = b""
    while True:
        b = c.s.read(4096)
        if not b: break
        out += b
    c._t.write(out.decode(errors="replace"))
    print("%s %s: %r" % (time.strftime("%H:%M:%S"), sys.argv[1], out.decode(errors="replace")[-120:]))
finally:
    c.close()
