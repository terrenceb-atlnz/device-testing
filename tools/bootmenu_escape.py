#!/usr/bin/env python3
"""Get an AW+ unit's console out of the bootloader Boot Menu and back to a booted CLI.

    bootmenu_escape.py <console-tty> [--baud 115200] [--boot-wait 360]   e.g. /dev/uN

Persists nothing. It reads which menu is on screen and sends only the key that backs out of it:
  * a file list ('... 0 to cancel) and press Enter')         -> '0' + Enter
  * a submenu ('0. Return to previous menu')                 -> bare '0'
  * the main Boot Menu ('9. Quit and continue booting')      -> bare '9', then waits for login:
  * a CLI or login: prompt                                   -> nothing (already booted)
  * anything else                                            -> nothing; exits 3 and says so
It never sends '0' on the main menu (0 = Restart) and never '9' in a submenu: in 'Select
device', 9 = 'Boot from default' is a selection, and it SAVES the default boot source.

Menu options take a bare keypress (a trailing CR answers the next prompt); only file selection
takes Enter. The menu wording is the IE520's (2026-08 and 2026-10 transcripts); on another
product read a bootloader transcript first and confirm it matches.
Exit: 0 booted to login: (or already there), 3 unknown state, 4 no login: after '9'."""
import argparse, os, re, serial, sys, time

def drain(s, secs, quiet=1.5, until=None):
    buf, start, last = '', time.time(), time.time()
    while time.time() - start < secs:
        n = s.in_waiting
        if n:
            buf += s.read(n).decode('utf-8', 'replace'); last = time.time()
            if until and re.search(until, buf):
                break
        else:
            time.sleep(0.1)
            if until is None and buf and time.time() - last > quiet:
                break
    return buf

def state(out):
    t = out.replace('\r', '')
    lines = [l for l in t.split('\n') if l.strip()]
    tail = lines[-1].rstrip() if lines else ''
    if tail.endswith('login:') or (re.match(r'^\S+[#>]$', tail) and not tail.endswith('==>')):
        return 'cli'
    if tail.endswith('Password:'):
        return 'password'
    i = t.rfind('Enter selection')
    if i < 0:
        return 'unknown'
    if 'to cancel' in t[i:]:
        return 'filelist'
    # The newest menu printed before a prompt decides; a wake CR may re-prompt without a menu.
    for block in reversed(t[:i].split('Enter selection')):
        if '9. Quit and continue booting' in block:
            return 'main'
        if '0. Return to previous menu' in block:
            return 'submenu'
    return 'unknown'

ap = argparse.ArgumentParser(description=__doc__,
                             formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('tty', help='console device of the unit, e.g. /dev/uN')
ap.add_argument('--baud', type=int, default=115200, help='console baud rate (default 115200)')
ap.add_argument('--boot-wait', type=float, default=360,
                help='seconds to wait for login: after quitting the menu (default 360)')
a = ap.parse_args()

# Opening or closing the port drops DTR, which the IE520 reads as a BREAK -- on close,
# right after '9', that can park the unit straight back in the bootloader. Same guard
# as console.py (added 2026-10-02); harmless where stty fails.
os.system('stty -F {} -hupcl 2>/dev/null'.format(os.path.realpath(a.tty)))
s = serial.Serial(a.tty, a.baud, timeout=1)
out = drain(s, 3)
if state(out) in ('unknown',):
    s.write(b'\r')                      # a parked menu prints nothing; a CR re-prompts it
    out += drain(s, 6)
print('=== CURRENT STATE ===');  print(out[-1200:])

rc = 3
for step in range(6):
    st = state(out)
    print('--- step %d: %s ---' % (step, st))
    if st == 'cli':
        print('at a CLI / login: prompt -- nothing to escape'); rc = 0; break
    if st in ('password', 'unknown'):
        print('not at a recognised Boot Menu prompt -- sending nothing more'); break
    if st == 'filelist':
        s.write(b'0\r'); out = drain(s, 20)
    elif st == 'submenu':
        s.write(b'0'); out = drain(s, 20)
    elif st == 'main':
        s.write(b'9')
        out = drain(s, a.boot_wait, until=r'login:\s*$')
        print(out[-2500:])
        rc = 0 if re.search(r'login:\s*$', out) else 4
        print('booted to login:' if rc == 0 else 'NO login: within %.0f s' % a.boot_wait)
        break
    print(out[-800:])
s.close()
sys.exit(rc)
