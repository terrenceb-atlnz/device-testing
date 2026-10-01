#!/usr/bin/env python3
"""peek.py <tty> <baud> <transcript>: bare CR, report the prompt tail (the pre-run console
gate: is the unit at login:, '>', '#', a (config) mode, or silent?). Sends one CR and does
not log in. <tty> is the unit's console device on the testbox you run it on; <transcript>
is a path you choose (appended). The stty -hupcl is the IE520 DTR-drop/BREAK workaround
(see console.py); harmless on other AW+ products."""
import sys, os, time
USAGE = "usage: peek.py <tty> <baud> <transcript>"
if len(sys.argv) != 4 or sys.argv[1] in ("-h", "--help"):
    print(USAGE); sys.exit(0 if sys.argv[1:2] in (["-h"], ["--help"]) else 2)
try:
    tty, baud, tr = sys.argv[1], int(sys.argv[2]), sys.argv[3]
except ValueError as e:
    print(USAGE); print("bad argument: %s" % e); sys.exit(2)
import serial
os.system('stty -F {} -hupcl 2>/dev/null'.format(os.path.realpath(tty)))
s = serial.Serial(tty, baud, timeout=0.2)
t = open(tr, 'a', errors='replace'); t.write('\n===== peek {} {} =====\n'.format(tty, time.strftime('%F %T')))
time.sleep(0.3); s.read(8192)
s.write(b'\r'); buf=b''; t0=time.time()
while time.time()-t0 < 3.0:
    b = s.read(4096)
    if b: buf += b
t.write(buf.decode(errors='replace')); t.close(); s.close()
tail = buf.decode(errors='replace').replace('\r','').strip().splitlines()
print(tty, 'TAIL:', repr(tail[-1] if tail else ''))
