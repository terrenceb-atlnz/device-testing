#!/usr/bin/env python3
"""Reboot one IE520 and capture the whole boot on its console.

    ./reboot_unit.py /dev/u4 [minutes_to_watch]

The AW+ CLI confirmation ('Are you sure you want to reboot...? (y/n)') needs
'y' AND a carriage return.  A bare 'y' -- which is what the BOOTLOADER Boot Menu
wants -- leaves the confirmation unanswered, and the result is silent: no
reboot, no output, uptime unchanged, looking exactly like a hung box.
"""
import re
import sys
import time

from console import Console, ConsoleError

CONFIRM_RE = re.compile(r'\((?:y|Y)/(?:n|N)\)[^\n]{0,20}$')


def log(m):
    print('{}  {}'.format(time.strftime('%H:%M:%S'), m), flush=True)


def main():
    port = sys.argv[1]
    watch_min = float(sys.argv[2]) if len(sys.argv) > 2 else 12.0
    tag = port.rsplit('/', 1)[-1]

    c = Console(port, 'reboot-{}.log'.format(tag))
    try:
        c.login()
    except ConsoleError as exc:
        log('ABORT: {}'.format(exc))
        c.close()
        return 1

    up = c.cmd('show system | include Uptime', timeout=60)
    log('uptime before: {}'.format(up.strip()))

    log('sending: reboot')
    c.s.write(b'reboot\r')
    out = c.read_until_quiet(quiet=2.0, timeout=30.0, need_prompt=False)
    if CONFIRM_RE.search(out.rstrip()):
        log('confirmation pending -> "y" + CR')
        c.s.write(b'y\r')
    else:
        log('!! no confirmation prompt seen; tail={!r}'.format(out[-160:]))

    log('watching boot for up to {:.0f} min...'.format(watch_min))
    deadline = time.time() + watch_min * 60
    seen_banner = False
    while time.time() < deadline:
        text = c._read_some()
        if not text:
            time.sleep(0.2)
            continue
        if 'Loading' in text or 'Starting' in text:
            seen_banner = True
        if re.search(r'login:\s*$', text) or re.search(r'awplus[^\n]*[#>]\s*$', text):
            log('reached a prompt/login -- boot looks complete')
            break
    log('watch ended (banner seen: {})'.format(seen_banner))
    c.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
