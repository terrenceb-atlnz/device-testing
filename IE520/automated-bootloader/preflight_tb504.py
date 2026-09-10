#!/usr/bin/python3
"""Read-only pre-flight on tb504's IE520. Waits for boot, logs in, reads state.
Sends nothing but a login and 'show' commands. Never touches the boot menu."""
import serial, time, sys

PORT, BAUD = '/dev/ttyUSB0', 9600

def read_until(s, pats, timeout, quiet=2.0):
    buf, start, last = '', time.time(), time.time()
    while time.time() - start < timeout:
        n = s.in_waiting
        if n:
            buf += s.read(n).decode('utf-8', 'replace'); last = time.time()
        else:
            time.sleep(0.2)
        if any(p in buf for p in pats) and time.time() - last > quiet:
            break
    return buf

s = serial.Serial(PORT, BAUD, timeout=1)
try:
    s.write(b'\r')
    out = read_until(s, ['login:', '>', '#'], 420, quiet=3.0)
    tail = out[-600:]
    print('=== console state ==='); print(tail)

    if 'login:' in out:
        s.write(b'manager\r'); time.sleep(1.5); read_until(s, ['assword'], 15)
        s.write(b'friend\r');  print(read_until(s, ['>', '#'], 60)[-300:])
    elif not (out.rstrip().endswith('#') or out.rstrip().endswith('>')):
        print('!! not at a prompt or login - device may still be booting'); sys.exit(2)

    s.write(b'enable\r');            read_until(s, ['#'], 20)
    s.write(b'terminal length 0\r'); read_until(s, ['#'], 20)
    for cmd in ['show boot', 'dir *.rel', 'show system serialnumber']:
        s.write((cmd + '\r').encode())
        print(f'\n===== {cmd} =====')
        print(read_until(s, ['#'], 90, quiet=3.0))
finally:
    s.close()
    print('\n[console released]')
