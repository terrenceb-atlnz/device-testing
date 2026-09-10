#!/usr/bin/env python3
"""rc.py variant that opens the console at a caller-supplied baud (x230 = 9600)."""
import os
import sys

from console import Console, ConsoleError

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    args = sys.argv[1:]
    if len(args) < 2 or not args[0].startswith('/dev/'):
        print('usage: rc9600.py /dev/uN <baud> "cmd" ["cmd" ...]')
        return 2
    port = args.pop(0)
    baud = int(args.pop(0))
    transcript = os.path.join(HERE, '{}-console.log'.format(os.path.basename(port)))

    c = Console(port, transcript, baud=baud)
    try:
        c.login()
    except ConsoleError as exc:
        print('ABORT: {}'.format(exc))
        c.close()
        return 1
    try:
        for cmd in args:
            print('\n########## {} ##########'.format(cmd))
            out = c.cmd(cmd, timeout=120.0)
            if not out.strip():
                print('!! EMPTY RESPONSE -- treat as no result, not as success')
            print(out)
    finally:
        c.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
