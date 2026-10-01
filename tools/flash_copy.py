#!/usr/bin/env python3
"""Copy a file into an AW+ unit's flash from ANY source path, and verify it landed.

    ./flash_copy.py <console-tty> <source> <dest> [expected_source_bytes]
                    [--baud 115200] [--timeout 1800] [--log PATH]

    e.g.  ./flash_copy.py /dev/uN awplus-2/flash:/<release>.rel <release>.rel 41103575

<console-tty> is the unit's serial console (e.g. /dev/uN on a testbox).  The
transcript goes to --log, default flash-copy-<tty name>.log in the current
directory.  Login is console.py's (manager/friend).

This is tftp_copy.py generalised: the source is an arbitrary AW+ path rather
than a tftp:// URL, so it also covers the cross-member form
'<hostname>-<stackID>/flash:/<file>' documented for `dir`/`copy`.  That route
matters because a stack whose config has been replaced has no IP address at
all, while the peer member's flash is still reachable over the stack link.

The two facts from tftp_copy.py apply unchanged.  The first was MEASURED ON
IE520 and is why --timeout defaults to 1800 s; other products' flash may be far
faster (or slower) and may need a different value:

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
from console import Console, ConsoleError

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
    ap.add_argument('source', help='AW+ source path, e.g. awplus-2/flash:/<file>')
    ap.add_argument('dest', help='destination file name on flash:/ (must not exist)')
    ap.add_argument('expected', nargs='?', type=int, default=None,
                    help='expected source size in bytes (abort if it differs)')
    ap.add_argument('--baud', type=int, default=115200,
                    help='console baud rate (default 115200)')
    ap.add_argument('--timeout', type=float, default=COPY_TIMEOUT,
                    help='copy ceiling in s (default %(default).0f, IE520 SPIFlash)')
    ap.add_argument('--log', default=None,
                    help='transcript path (default ./flash-copy-<tty>.log)')
    a = ap.parse_args()
    port, source, dest, expected = a.port, a.source, a.dest, a.expected
    logfile = a.log or 'flash-copy-{}.log'.format(port.rsplit('/', 1)[-1])

    c = Console(port, logfile, baud=a.baud)
    try:
        c.login()
    except ConsoleError as exc:
        log('ABORT: {}'.format(exc))
        c.close()
        return 1

    before = c.cmd('show file systems', timeout=60)
    log('free space before:\n{}'.format(before.splitlines()[1] if before else '?'))

    # Prove the SOURCE exists before starting, so "it didn't land" can never be
    # confused with "it was never there".  dir on a cross-member path is a
    # documented form: `dir awplus-2/flash:/`.
    src_listing = c.cmd('dir {}'.format(source), timeout=120)
    m_src = re.search(r'^\s*(\d+)\s+-rw-', src_listing, re.M)
    if not m_src:
        log('ABORT: source {} not found:\n{}'.format(source, src_listing))
        c.close()
        return 1
    src_bytes = int(m_src.group(1))
    log('source {} = {:,} bytes'.format(source, src_bytes))
    if expected is not None and src_bytes != expected:
        log('ABORT: source is {:,} bytes but {:,} was expected -- wrong file?'
            .format(src_bytes, expected))
        c.close()
        return 1

    # A pre-existing destination would make "the file is there" meaningless as
    # proof, so refuse rather than report a stale file as a fresh transfer.
    pre = c.cmd('dir flash:/{}'.format(dest), timeout=60)
    if re.search(r'-rw-.*' + re.escape(dest), pre):
        log('ABORT: flash:/{} already exists -- pick a fresh name or delete it '
            'first, otherwise a failed copy looks like a good one:\n{}'
            .format(dest, pre))
        c.close()
        return 1

    cmd = 'copy {} flash:/{}'.format(source, dest)
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
    if CONFIRM_RE.search(early.rstrip()):
        log('confirmation prompt pending -> sending "y" + CR')
        c.s.write(b'y\r')

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
    log('source was {:,} bytes -> delta {:+,}'.format(src_bytes, landed - src_bytes))
    return 0 if landed == src_bytes else 1


if __name__ == '__main__':
    sys.exit(main())
