#!/usr/bin/env python3
"""Passive, TIMESTAMPED console logger for a peer unit during a reproducer.

    ./witness_log.py <tty> [<outfile>] [<baud>]

    <tty>      the unit's console device on the testbox you run it on
    <outfile>  stamped log, default witness-<ttyname>.log in the CURRENT directory
               (a relative path is relative to the current directory); the raw byte
               transcript goes beside it as witness-raw-<ttyname>.log
    <baud>     default 115200 (console.BAUD)
    Env: CK_USER / CK_PASSWORD = login credentials (default manager / friend).
    Stop with Ctrl-C (or SIGINT).

Why this exists: during the cycle-293 wedge the only record covering the event
was the testbox-side console capture -- and that capture had NO timestamps, being
a raw serial byte stream.  Every correlation in the evidence pack had to be
anchored by CONTENT instead of by clock.  This logger stamps each line on
arrival (testbox wall clock), so the next event can be correlated directly.

It logs in once, turns `terminal monitor` on so the device mirrors its log
messages to the console, and then goes strictly READ-ONLY -- it never sends
another byte.  That matters: two processes on one port produces
"device disconnected or multiple access on port?", which reads exactly like a
hardware fault while dmesg shows zero USB events.

Clock note for whoever reads the output: these stamps are the testbox's LOCAL
time, while the switches log in their own clock (UTC unless configured).  The
header records the testbox's hostname, timezone and UTC offset, computed when the
logger starts.
"""
import os
import socket
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from console import BAUD, Console, ConsoleError

USAGE = 'usage: witness_log.py <tty> [<outfile>] [<baud>]'


def local_zone():
    """'<TZ name> = UTC+HH:MM' for the testbox's local time right now."""
    lt = time.localtime()
    off = lt.tm_gmtoff
    sign = '+' if off >= 0 else '-'
    off = abs(off)
    return '{} = UTC{}{:02d}:{:02d}'.format(
        time.strftime('%Z', lt), sign, off // 3600, (off % 3600) // 60)


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 4 or sys.argv[1] in ('-h', '--help'):
        print(__doc__)
        print(USAGE)
        return 0 if sys.argv[1:2] in (['-h'], ['--help']) else 2
    port = sys.argv[1]
    outpath = sys.argv[2] if len(sys.argv) > 2 else 'witness-{}.log'.format(
        port.rsplit('/', 1)[-1])
    try:
        baud = int(sys.argv[3]) if len(sys.argv) > 3 else BAUD
    except ValueError as exc:
        print(USAGE)
        print('bad argument: {}'.format(exc))
        return 2
    outdir = os.path.dirname(outpath) or '.'

    # console.py's own transcript is the raw byte stream; this is the stamped one.
    con = Console(port, os.path.join(outdir, 'witness-raw-{}.log'.format(
        port.rsplit('/', 1)[-1])), baud=baud)

    out = open(outpath, 'a', buffering=1)
    out.write('\n{} ===== witness logger attached to {} =====\n'.format(
        time.strftime('%Y-%m-%d %H:%M:%S'), port))
    out.write('{} ===== stamps are {} LOCAL time ({}); devices log their own '
              'clock (UTC unless configured) =====\n'.format(
                  time.strftime('%Y-%m-%d %H:%M:%S'), socket.gethostname(),
                  local_zone()))

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
