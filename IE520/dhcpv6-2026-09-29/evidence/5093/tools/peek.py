#!/usr/bin/env python3
"""peek.py <tty> <baud> <transcript>: bare CR, report the prompt tail (gate item 2)."""
import sys, os, time, serial
tty, baud, tr = sys.argv[1], int(sys.argv[2]), sys.argv[3]
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
