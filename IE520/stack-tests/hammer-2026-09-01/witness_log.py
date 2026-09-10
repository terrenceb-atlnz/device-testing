#!/usr/bin/env python3
"""Passive, TIMESTAMPED console logger for the peer member during a reproducer.

    ./witness_log.py /dev/u5 witness-member1.log

Why this exists: during the cycle-293 wedge the only record covering the event
was the tb470-side console capture -- and that capture had NO timestamps, being
a raw serial byte stream.  Every correlation in the evidence pack had to be
anchored by CONTENT instead of by clock.  This logger stamps each line on
arrival (tb470 wall clock), so the next event can be correlated directly.

It logs in once, turns `terminal monitor` on so the device mirrors its log
messages to the console, and then goes strictly READ-ONLY -- it never sends
another byte.  That matters: two processes on one port produces
"device disconnected or multiple access on port?", which reads exactly like a
hardware fault while dmesg shows zero USB events.

Clock note for whoever reads the output: these stamps are tb470 local time
(NZST), while the switches log in UTC.  Both are recorded in the header.
"""
import os
import sys
import time

from console import Console, ConsoleError


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    port = sys.argv[1]
    here = os.path.dirname(os.path.abspath(__file__))
    outname = sys.argv[2] if len(sys.argv) > 2 else 'witness-{}.log'.format(
        port.rsplit('/', 1)[-1])
    outpath = os.path.join(here, outname)

    # console.py's own transcript is the raw byte stream; this is the stamped one.
    con = Console(port, os.path.join(here, 'witness-raw-{}.log'.format(
        port.rsplit('/', 1)[-1])))

    out = open(outpath, 'a', buffering=1)
    out.write('\n{} ===== witness logger attached to {} =====\n'.format(
        time.strftime('%Y-%m-%d %H:%M:%S'), port))
    out.write('{} ===== stamps are tb470 LOCAL time (NZST); devices log UTC '
              '(NZST = UTC+12) =====\n'.format(time.strftime('%Y-%m-%d %H:%M:%S')))

    try:
        con.login(monitor=True)
        out.write('{} ===== terminal monitor enabled; going READ-ONLY =====\n'
                  .format(time.strftime('%Y-%m-%d %H:%M:%S')))
        print('witness attached to {}, logging to {}'.format(port, outpath),
              flush=True)
    except ConsoleError as exc:
        out.write('{} ===== LOGIN FAILED: {} -- logging raw anyway =====\n'
                  .format(time.strftime('%Y-%m-%d %H:%M:%S'), exc))
        print('WARNING: login failed ({}); logging raw stream only'.format(exc),
              flush=True)

    # Strictly read-only from here.  Partial lines are held until a newline so a
    # stamp always marks the start of a real line.
    pending = ''
    try:
        while True:
            text = con._read_some()
            if not text:
                time.sleep(0.2)
                continue
            pending += text
            while '\n' in pending:
                line, pending = pending.split('\n', 1)
                line = line.rstrip('\r')
                if line:
                    out.write('{} {}\n'.format(
                        time.strftime('%Y-%m-%d %H:%M:%S'), line))
    except KeyboardInterrupt:
        pass
    finally:
        if pending.strip():
            out.write('{} {}\n'.format(
                time.strftime('%Y-%m-%d %H:%M:%S'), pending.rstrip('\r')))
        out.write('{} ===== witness detached =====\n'.format(
            time.strftime('%Y-%m-%d %H:%M:%S')))
        out.close()
        con.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
