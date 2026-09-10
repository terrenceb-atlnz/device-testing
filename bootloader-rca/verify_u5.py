#!/usr/bin/python3
import serial, time
def drain(s, secs, quiet=3):
    buf, start, last = '', time.time(), time.time()
    while time.time() - start < secs:
        n = s.in_waiting
        if n: buf += s.read(n).decode('utf-8','replace'); last = time.time()
        else:
            time.sleep(0.2)
            if buf and time.time()-last > quiet: break
    return buf
s = serial.Serial('/dev/u5', 115200, timeout=1)
s.write(b'\r'); out = drain(s, 120, quiet=5)
print('=== state ==='); print(out[-800:])
if 'login:' in out:
    s.write(b'manager\r'); time.sleep(1); drain(s,3)
    s.write(b'friend\r');  print(drain(s, 15)[-400:])
    s.write(b'enable\r'); drain(s,5)
    s.write(b'terminal length 0\r'); drain(s,5)
    s.write(b'show boot\r'); print('=== show boot (AFTER) ==='); print(drain(s, 20))
s.close()
