#!/usr/bin/python3
"""
Reproduce, on real IE520 hardware (tb470 /dev/u5), the console text that
ATBootLoader.__set_swi_boot_from_media_via_bootrom() parses.

Navigates: reboot -> Ctrl+B -> [2] Change default boot source -> [1] Flash,
captures the file listing, then CANCELS (0 / 0) and quits with [9] so that
NOTHING is persisted and the unit boots normally again.
"""
import re, serial, sys, time

LOG = open('/home/terrenceb/copilot/bootloader-rca/bootmenu_capture.log', 'w')

def say(*a):
    m = ' '.join(str(x) for x in a)
    print(m); LOG.write(m + '\n'); LOG.flush()

def read_until(s, pats, timeout, quiet=1.5, tick=None):
    """Read until any pattern seen, or timeout. Optionally send `tick` bytes while waiting."""
    buf, start, last = '', time.time(), time.time()
    while time.time() - start < timeout:
        n = s.in_waiting
        if n:
            buf += s.read(n).decode('utf-8', 'replace'); last = time.time()
        else:
            if tick:
                s.write(tick)
            time.sleep(0.05)
        if any(p in buf for p in pats) and time.time() - last > quiet:
            break
    return buf

s = serial.Serial('/dev/u5', 115200, timeout=1)

# ---- 1. baseline: get to enable and record boot config -------------------
s.write(b'\r'); time.sleep(1); s.read(s.in_waiting or 0)
s.write(b'\r'); out = read_until(s, ['login:', '>', '#'], 8)
if 'login:' in out:
    s.write(b'manager\r'); time.sleep(1); s.read(s.in_waiting or 0)
    s.write(b'friend\r');  read_until(s, ['>', '#'], 10)
s.write(b'enable\r');            read_until(s, ['#'], 8)
s.write(b'terminal length 0\r'); read_until(s, ['#'], 8)
s.write(b'show boot\r');   say('===== show boot (BEFORE) =====\n' + read_until(s, ['#'], 15))
s.write(b'dir *.rel\r');   say('===== dir *.rel =====\n'          + read_until(s, ['#'], 20))

# ---- 2. reboot and break into the bootloader -----------------------------
say('\n===== rebooting, will send Ctrl+B =====')
s.write(b'reboot\r'); time.sleep(2)
s.write(b'y\r')
boot = read_until(s, ['Boot Menu', 'Enter selection'], 240, quiet=2.0, tick=b'\x02')
say(boot[-1500:])
if 'Enter selection' not in boot:
    say('!! never reached the Boot Menu - sending 9 to continue booting'); s.write(b'9\r')
    sys.exit(1)

# ---- 3. option 2 -> option 1 (Flash): the output the framework parses ----
s.write(b'2\r'); menu = read_until(s, ['Select device'], 60, quiet=2.0)
say('\n===== after [2] Change the default boot source =====\n' + menu)

s.write(b'1\r'); listing = read_until(s, ['and press enter', 'Enter selection'], 120, quiet=3.0)
say('\n===== after [1] Flash - THIS is the string the parser sees =====\n' + listing)

# ---- 4. run BOTH parsers over the captured text --------------------------
m = re.search(r'^\s*1\.\s*\S*?:?(\S+\.rel)\s*$', listing, re.M)
filename = m.group(1) if m else 'unknown.rel'
say('\n\n########## PARSER COMPARISON (filename = %r) ##########' % filename)

sent = None
for line in listing.splitlines():                       # framework's current code
    if filename in line:
        try:
            sent = line.split()[0][:-1]
        except (ValueError, IndexError):
            continue
        say('CURRENT  matched line : %r' % line)
        say('CURRENT  would SEND   : %r' % sent)
        break
else:
    say('CURRENT  matched nothing')

cand = [x.strip() for x in listing.splitlines() if x.strip().endswith(':%s' % filename)]
if cand:
    say('FIXED    matched line : %r' % cand[0])
    say('FIXED    would SEND   : %r' % cand[0].split()[0].replace('.', ''))
else:
    say('FIXED    matched nothing')
say('#######################################################\n')

# ---- 5. cancel out, persist NOTHING, continue booting -------------------
say('===== cancelling: 0 (cancel file) =====')
s.write(b'0\r'); say(read_until(s, ['Enter selection'], 60, quiet=2.0))
say('===== 0 (return to previous menu) =====')
s.write(b'0\r'); say(read_until(s, ['Enter selection'], 60, quiet=2.0))
say('===== 9 (quit and continue booting) =====')
s.write(b'9\r')
say(read_until(s, ['login:'], 300, quiet=3.0)[-1200:])
s.close(); say('DONE')
