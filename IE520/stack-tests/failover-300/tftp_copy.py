#!/usr/bin/env python3
"""TFTP a release into an IE520's flash, and verify it actually landed.

    ./tftp_copy.py /dev/u4 10.38.215.65 IE520-tb470.rel [expected_source_bytes]

Two IE520 facts shape this script:

  * Flash is SPIFlash and is extraordinarily slow -- a ~41 MB write takes about
    12 minutes, and for most of that the console answers NOTHING, not even a
    bare CR.  That is normal.  Do not interrupt it and do not power-cycle.

  * 'copy' returns as soon as it prints 'Copying...'; the prompt coming back is
    NOT evidence the file is on disk.  So this re-reads 'dir' afterwards and
    reports the on-flash byte count, and exits non-zero if the file is missing.

A CLI (y/n) confirmation needs 'y' AND a carriage return -- only the bootloader
Boot Menu takes a bare keypress.
"""
import re
import sys
import time

from console import Console, ConsoleError

COPY_TIMEOUT = 1800.0          # 30 min ceiling; returns as soon as the prompt is back

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
    if len(sys.argv) < 4:
        print(__doc__)
        return 2
    port, server, filename = sys.argv[1], sys.argv[2], sys.argv[3]
    expected = int(sys.argv[4]) if len(sys.argv) > 4 else None
    # Destination defaults to the source name but may differ -- AW+ refuses to
    # overwrite whatever 'boot system' currently points at, so a fresh name is
    # the normal case here, and it also makes verification unambiguous.
    dest = sys.argv[5] if len(sys.argv) > 5 else filename

    c = Console(port, 'tftp-copy-{}.log'.format(port.rsplit('/', 1)[-1]))
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
    if CONFIRM_RE.search(early.rstrip()):
        log('confirmation prompt pending -> sending "y" + CR')
        c.s.write(b'y\r')

    log('waiting for the write (SPIFlash: expect ~12 min of silence)...')
    start = time.time()
    out = c.read_until_quiet(quiet=5.0, timeout=COPY_TIMEOUT, need_prompt=True)
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
