#!/usr/bin/env python3
"""Park an AW+ unit at its bootloader Boot Menu with the default boot source set to Flash + a file.

    bootmenu_park.py <tty> <flash-file> [--baud 115200] [--transcript PATH] [--reload] [--watch 600]

Catch the unit at `Press <Ctrl+B>` while it reboots, then:
  main menu: bare '2' (Change the default boot source) -> 'Select device': the Flash digit ->
  'Listing of usable files': the file's number + Enter -> wait for 'Saving settings... Complete'
and LEAVE it at the main menu. Release it later with `bootmenu_escape.py <tty>` (bare '9'), so
several units can be parked first and released together (the image update procedure, memory
ie520-image-update-procedure).

Who reboots the unit:
  * a stack member: start this first, then `reload stack-member N` on the master;
  * the master or a standalone: pass --reload. It logs in on this same port, sends `reload`,
    answers y+CR (n+CR to any save question), and only then starts watching.

Menu keys are bare keypresses; only file selection takes Enter (platforms/IE520.md §2). After the
menu first appears it stops ticking Ctrl+B and drains until the console is quiet: queued Ctrl+B
presses each re-draw the menu (AR4050S 5.2.8 drew it 9 times, 2026-10-09). If the expected menu
is not on screen it sends one bare CR, which re-draws the current menu and selects nothing.
On anything else it stops and sends nothing more.
Exit: 0 parked; 2 unexpected screen (unit left in the bootloader -- read it, then
bootmenu_escape.py); 3 no Ctrl+B prompt within --watch; 7 --reload could not log in."""
import argparse, os, re, sys, time
import serial

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('tty', help='console device of the unit, e.g. /dev/uN')
ap.add_argument('file', help='file name as the bootloader lists it after flash:, e.g. IE520-awplus_main-20261008-57.rel')
ap.add_argument('--baud', type=int, default=115200)
ap.add_argument('--transcript', default=None, help='append the raw console here (default ./park-<tty>.log)')
ap.add_argument('--reload', action='store_true', help='log in on this port and send `reload` first')
ap.add_argument('--watch', type=float, default=600, help='seconds to wait for the Ctrl+B prompt')
a = ap.parse_args()
tr = a.transcript or 'park-%s.log' % os.path.basename(a.tty)

if a.reload:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import console, awlogin as L
    c = console.Console(a.tty, tr, baud=a.baud)
    if not L.login(c):
        print('no privileged prompt'); sys.exit(7)
    c.to_exec()
    c._t.write('\n>>> reload\n'); c.s.write(b'reload\r')
    buf, t0, yes, nsave = '', time.time(), False, False
    while time.time() - t0 < 30:
        buf += c._read_some()
        if not nsave and re.search(r'(?i)save.*\(y/n\)', buf):
            c.s.write(b'n\r'); nsave = True; buf = ''; continue
        if re.search(r'(?i)(reboot|restart|reload).*\(y/n\)', buf):
            c.s.write(b'y\r'); yes = True; break
        time.sleep(0.1)
    c.close()
    if not yes:
        print('no reboot (y/n) after `reload` -- not parking:\n' + buf[-400:]); sys.exit(2)

os.system('stty -F {} -hupcl 2>/dev/null'.format(os.path.realpath(a.tty)))   # no DTR drop (BREAK)
s = serial.Serial(a.tty, a.baud, timeout=0.1)
log = open(tr, 'a', buffering=1, errors='replace')
log.write('\n===== bootmenu_park.py opened %s at %s =====\n' % (a.tty, time.strftime('%F %T')))
buf = ''

def rd():
    global buf
    b = s.read(4096)
    if b:
        t = b.decode('utf-8', 'replace'); buf += t; log.write(t)
    return bool(b)

def wait_for(pat, secs, since):
    t0 = time.time()
    while time.time() - t0 < secs:
        rd()
        m = re.search(pat, buf[since:])
        if m:
            return m
    return None

def settle(quiet=2.0, cap=60):
    t0, last = time.time(), time.time()
    while time.time() - t0 < cap:
        if rd():
            last = time.time()
        elif time.time() - last > quiet:
            return

def screen(since, want):
    """Text of the newest menu since `since`; one bare CR to re-draw it if `want` is missing."""
    settle()
    i = buf.rfind('Enter selection')
    if i >= since and want in buf[since:i]:
        return buf[since:]
    mark = len(buf); s.write(b'\r'); settle()
    return buf[mark:]

def say(m):
    print('%s %s' % (time.strftime('%H:%M:%S'), m)); log.write('\n[bootmenu_park] %s\n' % m)

def stop(m, rc=2):
    say(m + '\n' + buf[-1200:].replace('\r', '')); s.close(); sys.exit(rc)

t0 = time.time()
if not wait_for(r'Ctrl\+B', a.watch, 0):
    stop('no Ctrl+B prompt within %.0f s' % a.watch, 3)
say('Ctrl+B prompt after %.0f s; ticking' % (time.time() - t0))
mark = len(buf); t1 = time.time()
while time.time() - t1 < 30 and 'Enter selection' not in buf[mark:]:
    s.write(b'\x02'); time.sleep(0.25); rd()
txt = screen(mark, '9. Quit and continue booting')
if '9. Quit and continue booting' not in txt:
    stop('main Boot Menu not recognised')
say('main Boot Menu; sending 2')
mark = len(buf); s.write(b'2')
txt = screen(mark, 'Select device')
m = re.search(r'(\d)\.\s*Flash', txt)
if 'Select device' not in txt or not m:
    stop('no Select device / Flash entry')
say('Select device: Flash = %s' % m.group(1))
mark = len(buf); s.write(m.group(1).encode())
if not wait_for(r'to cancel\)', 120, mark):
    stop('no file list')
settle()
m = re.search(r'(\d+)\.\s+flash:/?' + re.escape(a.file) + r'\s', buf[mark:].replace('\r', ''))
if not m:
    stop('%s is not in the file list' % a.file)
say('%s is entry %s; selecting' % (a.file, m.group(1)))
mark = len(buf); s.write((m.group(1) + '\r').encode())
if not wait_for(r'Saving settings\.\.\.\s*Complete', 60, mark):
    stop('no "Saving settings... Complete"')
txt = screen(mark, '9. Quit and continue booting')
if '9. Quit and continue booting' not in txt:
    stop('saved, but not back at the main menu')
say('PARKED at the main menu: default boot source = Flash + %s (release: bootmenu_escape.py %s)' % (a.file, a.tty))
s.close()
sys.exit(0)
