#!/usr/bin/env python3
"""Run commands on a DUT console with the async-tolerant driver.

    ./rc.py /dev/u4 "show stack" "show boot"

Every byte read is appended to <port-basename>-console.log beside this script.
"""
import os
import sys

from console import Console, ConsoleError

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    args = sys.argv[1:]
    if not args or not args[0].startswith('/dev/'):
        print('usage: rc.py /dev/uN "cmd" ["cmd" ...]')
        return 2
    port = args.pop(0)
    transcript = os.path.join(HERE, '{}-console.log'.format(os.path.basename(port)))

    c = Console(port, transcript)
    try:
        c.login()
    except ConsoleError as exc:
        print('ABORT: {}'.format(exc))
        c.close()
        return 1

    rc = 0
    try:
        for cmd in args:
            print('\n########## {} ##########'.format(cmd))
            out = c.cmd(cmd, timeout=120.0)
            if not out.strip():
                print('!! EMPTY RESPONSE -- treat as no result, not as success')
                rc = 1
            print(out)
    finally:
        c.close()
    return rc


if __name__ == '__main__':
    sys.exit(main())
