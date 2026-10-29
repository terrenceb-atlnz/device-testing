#!/usr/bin/env python3
"""Read-only CLI help for `flowcontrol` in interface mode, sent WITHOUT a CR.
usage: fchelp.py /dev/uN <transcript> <interface>"""
import sys, time
sys.path.insert(0, '/tmp/ckorient/triage')
from console import Console

port, tr, ifc = sys.argv[1:4]
c = Console(port, tr, baud=115200)
try:
    c.login(monitor=False)
    c.cmd('configure terminal')
    c.cmd('interface ' + ifc)
    for q in ('flowcontrol ?', 'flowcontrol receive ?', 'flowcontrol send ?'):
        c._t.write('\n>>> {} (no CR)\n'.format(q))
        c.s.write(q.encode())
        out = c.read_until_quiet(quiet=1.2, timeout=10.0, need_prompt=False)
        print('### ' + q + '\n' + out)
        c.s.write(b'\x15')          # Ctrl-U: erase the re-printed line, never execute it
        c.read_until_quiet(quiet=0.8, timeout=5.0, need_prompt=False)
finally:
    try:
        c.s.write(b'\x15')
        c.send('end', quiet=0.6, timeout=10.0)
        c.send('terminal no monitor', quiet=0.6, timeout=10.0)
    finally:
        c.close()
