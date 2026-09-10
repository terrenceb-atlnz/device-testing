#!/usr/bin/python3
"""Non-destructive identity + boot-state probe of the IE520 on tb470 /dev/u5."""
import serial, sys, time

def drain(s, secs):
    buf, end = '', time.time() + secs
    while time.time() < end:
        n = s.in_waiting
        if n:
            buf += s.read(n).decode('utf-8', 'replace')
            end = time.time() + 1.0
        else:
            time.sleep(0.1)
    return buf

s = serial.Serial('/dev/u5', 115200, timeout=1)
s.write(b'\r'); out = drain(s, 4)
print('--- after CR ---'); print(repr(out[-400:]))

if 'login:' in out:
    s.write(b'manager\r'); drain(s, 2)
    s.write(b'friend\r');  print('--- login ---'); print(drain(s, 6)[-400:])

for cmd in ['terminal length 0', 'show system serialnumber', 'show boot', 'show version']:
    s.write((cmd + '\r').encode()); r = drain(s, 8)
    print('\n===== %s =====' % cmd); print(r)
s.close()
