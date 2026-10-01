#!/usr/bin/env python3
"""Get an AW+ unit's console out of the bootloader menu and back to a booted CLI.

    bootmenu_escape.py <console-tty> [--baud 115200]      e.g. /dev/uN on a testbox

Persists nothing: only '0' (return/cancel) and '9' (quit and continue booting).
Menu wording and option numbers ('Boot Menu', 'Select device', 'to cancel', 0 = back
in a submenu, 9 = quit and continue booting) are those of the IE520 Boot Menu; on
another product read a bootloader transcript first and confirm they match.
Each key is sent with a trailing CR, as it always has been."""
import argparse, serial, time, sys

def drain(s, secs, quiet=1.2):
    buf, start, last = '', time.time(), time.time()
    while time.time() - start < secs:
        n = s.in_waiting
        if n:
            buf += s.read(n).decode('utf-8', 'replace'); last = time.time()
        else:
            time.sleep(0.1)
            if buf and time.time() - last > quiet:
                break
    return buf

ap = argparse.ArgumentParser(description=__doc__,
                             formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('tty', help='console device of the unit, e.g. /dev/uN')
ap.add_argument('--baud', type=int, default=115200, help='console baud rate (default 115200)')
a = ap.parse_args()

s = serial.Serial(a.tty, a.baud, timeout=1)
s.write(b'\r')
out = drain(s, 6)
print('=== CURRENT STATE ===');  print(out[-1200:])

# Walk out of any submenu with '0' (Return to previous menu / cancel), then quit with '9'.
for i in range(4):
    if 'login:' in out or out.rstrip().endswith('#') or out.rstrip().endswith('>'):
        break
    if 'Enter selection' in out or 'Boot Menu' in out or 'Select device' in out or 'to cancel' in out:
        if 'Boot Menu' in out and 'Select device' not in out and 'to cancel' not in out:
            break
        print('--- sending 0 (step %d) ---' % i)
        s.write(b'0\r'); out = drain(s, 20)
        print(out[-800:])
    else:
        break

print('=== sending 9 (quit and continue booting) ===')
s.write(b'9\r')
out = drain(s, 300, quiet=8)
print(out[-2500:])
s.close()
