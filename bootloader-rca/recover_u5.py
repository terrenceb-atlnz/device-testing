#!/usr/bin/python3
"""Get tb470 /dev/u5 out of the bootloader menu and back to a booted CLI.
Persists nothing: only '0' (return/cancel) and '9' (quit and continue booting)."""
import serial, time, sys

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

s = serial.Serial('/dev/u5', 115200, timeout=1)
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
