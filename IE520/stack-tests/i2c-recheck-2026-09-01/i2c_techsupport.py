#!/usr/bin/env python3
"""Confirm the mv64xxx I2C bus-lock defect is FIXED after removal of AT-SPTXc ...006.

    ./i2c_techsupport.py --console /dev/u5 --iterations 6

WHAT THIS RE-RUNS
  The August 2026 campaign established `show tech-support` as the trigger for
  `i2c i2c-0: mv64xxx: I2C bus locked, block: 1, time_left: 0`, which wedged the
  control plane and was followed ~41 s later by a watchdog reset.  Root cause was
  isolated to ONE module -- AT-SPTXc S/N A10217F213300006 -- which locked the bus
  of whichever unit hosted it (8 locks in 8 configurations containing it; 0 in
  22+ without).  That module was removed 2026-08-20.

  This run is the positive confirmation that the bug is gone, rather than
  inferring it from the module's absence.

STANDARD OF EVIDENCE (from the campaign -- do not lower it)
  * Every lock happened on iteration <= 2, at +55..+71 s into the command.
  * A clean bundle completes in ~67-85 s and prints 9 progress dots.
  * Six clean iterations is the tightening-run standard.
  So a single clean pass proves nothing; the second iteration is the one that
  historically failed.

DETECTION -- three independent signatures, all positive
  1. 'mv64xxx' / 'I2C bus locked'  -- the driver printk.  NOTE it TRAILS the true
     wedge by ~3.05 s (the mv64xxx transfer timeout expiring), so it is a
     confirmation, not the first sign.
  2. Console silence with no prompt -- the wedge itself.
  3. 'BootROM' -- the watchdog reset that follows.
  A pass requires the PROMPT to come back.  Silence is never a pass: an earlier
  generation of this tooling returned on quiet and reported a wedged unit as
  healthy.

  Progress dots are timestamped so a lock can be placed within the battery
  without any network path -- a locked run leaves NO tech-support file on flash
  at all (the hard reset discards unsynced writes), so file archaeology is
  impossible and the dot index is the only position record.
"""
import argparse
import os
import re
import sys
import time

from console import Console, ConsoleError, PROMPT_ANYWHERE_RE

LOCK_RE = re.compile(r'mv64xxx|I2C bus locked|i2c-0:', re.I)
RESET_RE = re.compile(r'BootROM|U-Boot|Booting from SPI flash', re.I)


def ts():
    return time.strftime('%Y-%m-%d %H:%M:%S')


class Run:
    def __init__(self, con, logf):
        self.c = con
        self.logf = logf

    def log(self, msg):
        line = '{}  {}'.format(ts(), msg)
        print(line, flush=True)
        self.logf.write(line + '\n')

    def tech_support(self, n, timeout, silence_limit):
        """One `show tech-support`.  Returns (verdict, detail, dots)."""
        c = self.c
        c._t.write('\n>>> show tech-support  (iteration {})\n'.format(n))
        c.s.write(b'show tech-support\r')

        t0 = time.time()
        buf = ''
        dots = []
        last_byte = t0
        seen_lock = None
        echo_end = 0

        while True:
            now = time.time()
            chunk = c._read_some()

            if chunk:
                # Timestamp every dot as it lands -- this is the position index.
                for ch in chunk:
                    if ch == '.':
                        dots.append(round(time.time() - t0, 2))
                buf += chunk
                last_byte = now

                if seen_lock is None and LOCK_RE.search(chunk):
                    seen_lock = now - t0
                    self.log('    *** I2C LOCK SIGNATURE at +{:.1f}s: {!r}'
                             .format(seen_lock,
                                     LOCK_RE.search(chunk).group(0)))

                if RESET_RE.search(chunk):
                    return ('RESET',
                            'device reset at +{:.1f}s (lock signature {})'
                            .format(now - t0,
                                    'at +{:.1f}s'.format(seen_lock)
                                    if seen_lock else 'ABSENT'),
                            dots)

                # Completion = a prompt AFTER the command echo.  Anchored the
                # same way console.py anchors it, because with terminal monitor
                # on the device splices log lines straight onto the prompt.
                if echo_end == 0:
                    m = re.search(r'show tech-support[^\n]*\n', buf)
                    if m:
                        echo_end = m.end()
                if echo_end:
                    if PROMPT_ANYWHERE_RE.search(buf, echo_end):
                        return ('CLEAN',
                                'completed in {:.1f}s, {} dots'.format(
                                    now - t0, len(dots)),
                                dots)

            quiet_for = now - last_byte
            elapsed = now - t0

            # Silence is the wedge signature.  Report it, then KEEP LISTENING --
            # the watchdog reset is the confirmation and arrives ~41 s later.
            if quiet_for > silence_limit:
                return ('WEDGE',
                        'no output for {:.0f}s (last byte at +{:.1f}s; lock '
                        'signature {})'.format(
                            quiet_for, last_byte - t0,
                            'at +{:.1f}s'.format(seen_lock)
                            if seen_lock else 'ABSENT'),
                        dots)

            if elapsed > timeout:
                return ('TIMEOUT',
                        'no prompt within {:.0f}s'.format(timeout), dots)

            if not chunk:
                time.sleep(0.05)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--console', default='/dev/u5',
                    help='console to DRIVE (the CLI is stack-wide)')
    ap.add_argument('--iterations', type=int, default=6)
    ap.add_argument('--timeout', type=float, default=300.0,
                    help='per-iteration ceiling; a ceiling costs nothing on a '
                         'healthy run because we return on the prompt')
    ap.add_argument('--silence-limit', type=float, default=30.0,
                    help='console silence that counts as a wedge. Clean runs '
                         'print a dot every ~5-8s, so 30s is well clear.')
    ap.add_argument('--settle', type=float, default=10.0,
                    help='pause between iterations')
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    tag = args.console.rsplit('/', 1)[-1]
    logf = open(os.path.join(here, 'i2c-recheck-{}.log'.format(tag)),
                'a', buffering=1)

    con = Console(args.console,
                  os.path.join(here, 'i2c-recheck-{}-console.log'.format(tag)))
    r = Run(con, logf)

    r.log('=' * 70)
    r.log('I2C RE-CHECK: `show tech-support` x{} on {}'.format(
        args.iterations, args.console))
    r.log('confirming the mv64xxx bus lock is gone after AT-SPTXc ...006 was '
          'removed 2026-08-20')
    r.log('=' * 70)

    try:
        con.login(monitor=True)
    except ConsoleError as e:
        r.log('ABORT: {}'.format(e))
        return 2
    r.log('logged in, terminal monitor ON')

    # Record what is actually on the bus -- the whole defect was one module, so
    # the inventory IS part of the result.
    for probe in ('show system pluggable', 'show system pluggable diagnostics'):
        r.log('--- {} ---'.format(probe))
        out = con.cmd_fast(probe, timeout=90)
        logf.write(out + '\n')

    verdicts = []
    for n in range(1, args.iterations + 1):
        r.log('iteration {}/{}: show tech-support'.format(n, args.iterations))
        verdict, detail, dots = r.tech_support(n, args.timeout,
                                               args.silence_limit)
        r.log('  -> {}: {}'.format(verdict, detail))
        r.log('  -> dots: {}'.format(' '.join('{:.2f}'.format(d)
                                              for d in dots) or '(none)'))
        verdicts.append(verdict)
        if verdict != 'CLEAN':
            r.log('STOPPING on first non-clean iteration -- preserving state '
                  'for forensics.')
            break
        time.sleep(args.settle)

    r.log('=' * 70)
    if verdicts and all(v == 'CLEAN' for v in verdicts):
        r.log('RESULT: {}/{} CLEAN -- no I2C lock signature, no wedge, no '
              'reset.'.format(len(verdicts), args.iterations))
        if len(verdicts) >= 6:
            r.log('Meets the campaign standard of evidence (6 clean).')
        else:
            r.log('NOTE: {} iterations is BELOW the 6-iteration standard.'
                  .format(len(verdicts)))
    else:
        r.log('RESULT: REPRODUCED -- {}'.format(verdicts[-1]))
    r.log('=' * 70)
    con.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
