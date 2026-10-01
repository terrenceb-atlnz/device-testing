#!/usr/bin/env python3
"""TFTP a release into an AW+ unit's flash, and verify it actually landed.

    ./tftp_copy.py <console-tty> <tftp-server-ip> <filename> [expected_source_bytes] [dest]
                   [--baud 115200] [--timeout 1800] [--log PATH]

<console-tty> is the unit's serial console (e.g. /dev/uN on a testbox);
<tftp-server-ip> must be reachable FROM THE UNIT (the testbox's lab-side
address, typically).  [dest] defaults to <filename>.  The transcript goes to
--log, default tftp-copy-<tty name>.log in the current directory.  Login is
console.py's (manager/friend).

Two facts shape this script.  The first was MEASURED ON IE520 and is why
--timeout defaults to 1800 s; other products' flash may be far faster (or
slower) and may need a different value:

  * IE520 flash is SPIFlash and is extraordinarily slow -- a ~41 MB write takes about
    12 minutes, and for most of that the console answers NOTHING, not even a
    bare CR.  That is normal.  Do not interrupt it and do not power-cycle.

  * 'copy' returns as soon as it prints 'Copying...'; the prompt coming back is
    NOT evidence the file is on disk.  So this re-reads 'dir' afterwards and
    reports the on-flash byte count, and exits non-zero if the file is missing.

A CLI (y/n) confirmation needs 'y' AND a carriage return -- only the bootloader
Boot Menu takes a bare keypress.
"""
import argparse
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from console import Console, ConsoleError, PROMPT_ANYWHERE_RE

# 30 min ceiling (IE520 SPIFlash, measured); returns as soon as the prompt is back.
# Default for --timeout.
COPY_TIMEOUT = 1800.0

# Only a real interrogative still awaiting an answer -- it has to be the LAST
# thing on the buffer.  Matching the word 'overwrite' anywhere is not good
# enough: AW+ refuses with
#   '% Cannot overwrite flash:/X as it is configured as the current boot image'
# and answering that error with 'y' just feeds 'y' to the CLI as a command.
CONFIRM_RE = re.compile(r'(?:\((?:y|Y)/(?:n|N)\)|\[(?:y|Y)/(?:n|N)\])[^\n]{0,20}$')
# A '%' line is AW+ reporting a failure; never answer one.
ERROR_RE = re.compile(r'^%.*$', re.M)


def log(msg):
    print('{}  {}'.format(time.strftime('%H:%M:%S'), msg), flush=True)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('port', help='console tty of the unit, e.g. /dev/uN')
    ap.add_argument('server', help='TFTP server IP as reachable from the unit')
    ap.add_argument('filename', help='file name on the TFTP server')
    ap.add_argument('expected', nargs='?', type=int, default=None,
                    help='expected source size in bytes (reported as a delta only)')
    ap.add_argument('dest', nargs='?', default=None,
                    help='destination name on flash:/ (default: filename; must not exist)')
    ap.add_argument('--baud', type=int, default=115200,
                    help='console baud rate (default 115200)')
    ap.add_argument('--timeout', type=float, default=COPY_TIMEOUT,
                    help='copy ceiling in s (default %(default).0f, IE520 SPIFlash)')
    ap.add_argument('--log', default=None,
                    help='transcript path (default ./tftp-copy-<tty>.log)')
    a = ap.parse_args()
    port, server, filename, expected = a.port, a.server, a.filename, a.expected
    # Destination defaults to the source name but may differ -- AW+ refuses to
    # overwrite whatever 'boot system' currently points at, so a fresh name is
    # the normal case here, and it also makes verification unambiguous.
    dest = a.dest if a.dest is not None else filename
    logfile = a.log or 'tftp-copy-{}.log'.format(port.rsplit('/', 1)[-1])

    c = Console(port, logfile, baud=a.baud)
    try:
        c.login()
    except ConsoleError as exc:
        log('ABORT: {}'.format(exc))
        c.close()
        return 1

    before = c.cmd('show file systems', timeout=60)
    log('free space before:\n{}'.format(before.splitlines()[1] if before else '?'))

    # A pre-existing destination would make "the file is there" meaningless as
    # proof, so refuse rather than report a stale file as a fresh transfer.
    pre = c.cmd('dir flash:/{}'.format(dest), timeout=60)
    if re.search(r'-rw-.*' + re.escape(dest), pre):
        log('ABORT: flash:/{} already exists -- pick a fresh name or delete it '
            'first, otherwise a failed copy looks like a good one:\n{}'
            .format(dest, pre))
        c.close()
        return 1

    cmd = 'copy tftp://{}/{} flash:/{}'.format(server, filename, dest)
    log('sending: {}'.format(cmd))
    c.s.write((cmd + '\r').encode())

    # Answer a confirmation only if one is genuinely pending.  Bail on a '%'
    # error line instead of replying to it.
    early = c.read_until_quiet(quiet=2.0, timeout=25.0, need_prompt=False)
    err = ERROR_RE.search(early)
    if err:
        log('ABORT: device refused the copy: {}'.format(err.group(0).strip()))
        c.close()
        return 1
    pending = bool(CONFIRM_RE.search(early.rstrip()))
    if pending:
        log('confirmation prompt pending -> sending "y" + CR')
        c.s.write(b'y\r')

    if not pending and PROMPT_ANYWHERE_RE.search(early.split('Copying', 1)[-1]):
        # A small file finishes inside the first read: its prompt has already come back,
        # so waiting for another would sit out the whole timeout (seen 2026-10-02 with a
        # 1.6 KB file).  The dir check below is still the proof.
        log('copy finished within the first read')
        out = early
    else:
        log('waiting for the write (up to {:.0f} s; IE520 SPIFlash: ~12 min of silence '
            'per ~41 MB)...'.format(a.timeout))
        start = time.time()
        out = c.read_until_quiet(quiet=5.0, timeout=a.timeout, need_prompt=True)
        log('copy returned after {:.0f} s'.format(time.time() - start))
    tail = '\n'.join(out.strip().splitlines()[-6:])
    log('tail:\n{}'.format(tail))

    if re.search(r'(?i)error|fail|timed out|no such file|not found', out):
        log('!! copy output contains an error string -- see transcript')

    # 'Copying...' is not proof.  Go and look.
    log('verifying on flash...')
    listing = c.cmd('dir flash:/{}'.format(dest), timeout=120)
    log('dir:\n{}'.format(listing))
    after = c.cmd('show file systems', timeout=60)
    log('free space after:\n{}'.format(after.splitlines()[1] if after else '?'))
    c.close()

    m = re.search(r'^\s*(\d+)\s+-rw-.*' + re.escape(dest), listing, re.M)
    if not m:
        log('VERIFY FAILED: {} is not in flash'.format(dest))
        return 1
    landed = int(m.group(1))
    log('VERIFIED on flash: {} = {:,} bytes'.format(dest, landed))
    if expected is not None:
        log('source was {:,} bytes -> delta {:+,}'.format(expected, landed - expected))
    return 0


if __name__ == '__main__':
    sys.exit(main())
