#!/usr/bin/env python3
"""Break (or restore) the tb470 IE520 L2 ring by shutting port1.0.1.

WHY port1.0.1 AND NOT port2.0.9
    The ring is  IE520 port1.0.1 -> x230 -> x230 sa1 -> AR4050S -> AR4050S
    port1.0.3 -> IE520 port2.0.9.  The x230 has SPANNING TREE DISABLED, so it
    neither participates nor propagates BPDUs and the AR4050S never learns that
    the root is reachable through it -- which is why STP cannot see this ring.

    Shutting port2.0.9 would NOT fix it.  The AR4050S blocks port1.0.4 only
    because port1.0.3 is its root port; remove port1.0.3's link and it promotes
    port1.0.4, bringing IE520 port2.0.1 into forwarding and rebuilding the same
    loop over a different cable.

    Shutting port1.0.1 removes the x230 leg.  The remaining IE520<->AR4050S pair
    is safe because BOTH those endpoints run STP and the 4050 already blocks the
    redundant one.  Nothing is orphaned: the x230 stays reachable via the 4050's
    sa1, and tb470 eth3 via the 4050.

USAGE
    ./break_loop.py --apply            # shut port1.0.1, verify, do NOT save
    ./break_loop.py --apply --persist  # ... and `write` so it survives a reboot
    ./break_loop.py --revert           # no shutdown  (add --persist to save)
    ./break_loop.py --check            # read-only: report state, change nothing

Running with no flag does nothing but print this contract.
"""
import argparse
import re
import sys
import time

from console import Console, ConsoleError

PORT = '/dev/u4'          # stack Active Master (member 2) as at 2026-08-31
TARGET = 'port1.0.1'      # the x230 leg -- see module docstring
WITNESS = 'port2.0.9'     # the AR4050S leg; its counters prove the storm
DESC = 'LOOP-BREAK-2026-08-31 ring via STP-disabled x230'

TRANSCRIPT = 'break_loop-console.log'


def counters(c, port):
    """Return (input_pkts, output_pkts) for `port`, or (None, None)."""
    out = c.cmd('show interface {}'.format(port), timeout=60.0)
    i = re.search(r'input packets (\d+)', out)
    o = re.search(r'output packets (\d+)', out)
    return (int(i.group(1)) if i else None,
            int(o.group(1)) if o else None)


def stack_ok(c):
    out = c.cmd('show stack', timeout=60.0)
    healthy = 'Normal operation' in out
    ready = len(re.findall(r'\bReady\b', out))
    return healthy and ready >= 2, out


def admin_state(c, port):
    """'up' / 'down' from the running-config (absence of `shutdown` == up)."""
    out = c.cmd('show running-config interface {}'.format(port), timeout=60.0)
    return ('down' if re.search(r'^\s*shutdown\s*$', out, re.M) else 'up'), out


def config_lines(c, lines):
    """Send config-mode lines, aborting on any CLI rejection."""
    for line in lines:
        out = c.cmd(line, timeout=60.0)
        if '% ' in out or 'Invalid input' in out:
            raise ConsoleError('device rejected {!r}:\n{}'.format(line, out))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument('--apply', action='store_true', help='shut {}'.format(TARGET))
    g.add_argument('--revert', action='store_true', help='no shutdown on {}'.format(TARGET))
    g.add_argument('--check', action='store_true', help='read-only report')
    ap.add_argument('--persist', action='store_true',
                    help='`write` afterwards so the change survives a reboot')
    args = ap.parse_args()

    if not (args.apply or args.revert or args.check):
        print(__doc__)
        return 2

    c = Console(PORT, TRANSCRIPT)
    try:
        c.login()
    except ConsoleError as exc:
        print('ABORT: cannot get a prompt on {}: {}'.format(PORT, exc))
        c.close()
        return 1

    try:
        # ---------- preconditions ----------
        ok, out = stack_ok(c)
        print('stack: {}'.format('Normal operation, members Ready'
                                 if ok else 'NOT HEALTHY'))
        if not ok:
            print(out)
            print('ABORT: refusing to change a bench that is not healthy.')
            return 1

        state, _ = admin_state(c, TARGET)
        print('{} admin state: {}'.format(TARGET, state))

        if args.check:
            a, b = counters(c, WITNESS)
            time.sleep(20)
            a2, b2 = counters(c, WITNESS)
            print('{} over ~20 s: input +{}, output +{}'.format(
                WITNESS, a2 - a, b2 - b))
            print('VERDICT: {}'.format(
                'LOOP ACTIVE' if (a2 - a) > 100000 else 'quiet'))
            return 0

        want = 'down' if args.apply else 'up'
        if state == want:
            print('{} is already {} -- nothing to do.'.format(TARGET, want))
            return 0

        # ---------- baseline ----------
        pre_in, pre_out = counters(c, WITNESS)
        print('baseline {}: input {}, output {}'.format(WITNESS, pre_in, pre_out))

        # ---------- change ----------
        body = ([' description {}'.format(DESC), ' shutdown'] if args.apply
                else [' no shutdown'])
        print('applying: {} {}'.format(TARGET, 'shutdown' if args.apply else 'no shutdown'))
        config_lines(c, ['configure terminal',
                         'interface {}'.format(TARGET)] + body + ['end'])

        # ---------- verify ----------
        state, cfg = admin_state(c, TARGET)
        print('{} admin state now: {}'.format(TARGET, state))
        if state != want:
            print(cfg)
            print('FAIL: {} did not reach {}.'.format(TARGET, want))
            return 1

        print('settling 25 s before re-measuring...')
        time.sleep(25)
        post_in, post_out = counters(c, WITNESS)
        d_in, d_out = post_in - pre_in, post_out - pre_out
        print('{} delta over the change: input +{}, output +{}'.format(
            WITNESS, d_in, d_out))

        mid_in, mid_out = post_in, post_out
        time.sleep(20)
        end_in, end_out = counters(c, WITNESS)
        r_in, r_out = end_in - mid_in, end_out - mid_out
        print('{} over the last ~20 s: input +{}, output +{}'.format(
            WITNESS, r_in, r_out))

        ok, out = stack_ok(c)
        print('stack after change: {}'.format(
            'Normal operation, members Ready' if ok else 'NOT HEALTHY'))
        if not ok:
            print(out)

        if args.apply:
            quiet = r_in < 10000 and r_out < 10000
            print('\nRESULT: {}'.format(
                'LOOP BROKEN -- traffic has fallen to background levels.' if quiet
                else 'STILL FLOODING -- the ring is not (only) through {}. '
                     'Investigate before trusting the bench.'.format(TARGET)))
            if not quiet:
                return 1

        # ---------- persist ----------
        if args.persist:
            print('saving to startup-config...')
            out = c.cmd('write', timeout=180.0)
            print(out.strip()[-400:])
        else:
            print('\nNOT saved. This reverts on the next reboot -- re-run with '
                  '--persist if the change should survive one.')

        return 0
    except ConsoleError as exc:
        print('ABORT: {}'.format(exc))
        return 1
    finally:
        c.close()


if __name__ == '__main__':
    sys.exit(main())
