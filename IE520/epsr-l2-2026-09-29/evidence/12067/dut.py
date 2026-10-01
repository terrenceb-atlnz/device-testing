#!/usr/bin/env python3
"""Run a list of CLI lines on one console; print each output; flag '% ' lines.
usage: dut.py /dev/uN <transcript> <line> [<line> ...]
Exit 3 if any line returned a '% ' error (caller gates on it)."""
import sys
sys.path.insert(0, '/tmp/ckorient/triage')
from console import Console

port, tr, lines = sys.argv[1], sys.argv[2], sys.argv[3:]
c = Console(port, tr, baud=115200)
bad = []
try:
    c.s.write(b'\r')
    st = c.read_until_quiet(quiet=1.0, timeout=8.0, need_prompt=False)
    print('### state on open:', repr(st.strip()[-80:]))
    c.login(monitor=False)
    for ln in lines:
        out = c.cmd(ln, quiet=1.0, timeout=90.0)
        print('\n### ' + ln + '\n' + out)
        for o in out.splitlines():
            if o.lstrip().startswith('% '):
                bad.append((ln, o.strip()))
finally:
    try:
        c.send('end', quiet=0.6, timeout=10.0)
        c.send('terminal no monitor', quiet=0.6, timeout=10.0)
    finally:
        c.close()
if bad:
    print('\n!!! CLI ERRORS:')
    for ln, o in bad:
        print('   ', ln, '->', o)
    sys.exit(3)
