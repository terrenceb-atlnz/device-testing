#!/usr/bin/env python3
"""TEST 38378 -- shut down stack ports 300 times; the stack must stay stable.

2026-08-26: switched to cmd_fast (prompt-based completion) and monitor=True.
The first 300-cycle run averaged ~200 s/cycle with times clustered at
110 / 199 / 288 s -- differences of ~89 s, which is the 90 s command timeout,
not device convergence.  Cause: the old prompt regex required newline-or-end
after the '#', so it never matched the spliced form the platform emits
    awplus(config-if)#switch: port 1(port1.0.27) entered disabled state
and those commands ran to full timeout.  Fixed in console.py.

    ./test_38378.py --master /dev/u5 --iterations 300 \
        --pair port1.0.28,port2.0.27 --pair port1.0.27,port2.0.28

Topology (Terrence's call, 2026-08-25): TWO stacking pairs, so shutting one pair
at a time leaves the stack up on the other.  That is what makes the case's
expected result -- "stack should remain stable" -- testable.  With a single pair
a shutdown splits the stack instead, which measures something else entirely.

MEASURED ON THE BENCH FIRST (2026-08-25), because guessing these would have
graded all 300 cycles wrongly:

  * 'shutdown' IS accepted on a stackport, and warns
    '% Warning: "shutdown" command is not saved to configuration for stackports'
    -- it is a RUNTIME-only change.  Nothing is persisted and a reboot restores.
  * With one pair shut the stack stays formed but Operational Status becomes
    'Not all stack ports are up', NOT 'Normal operation'.  Requiring
    'Normal operation' during the shut phase would fail every single cycle.
  * A healthy stack port reads 'Learnt neighbor N, connected portX.0.Y'.
    A shut one reads exactly 'Down'.  Neither contains the word 'up', so a
    naive substring test for 'up' is wrong in both directions.
  * Shutting ONE end of a pair downs BOTH ends.

Evidence discipline: every cycle needs positive evidence.  "No error appeared"
is not a pass -- a console read that times out and returns nothing would satisfy
it.  A cycle that cannot be read is UNMEASURED, never PASS.
"""
import argparse
import os
import re
import sys
import time

from console import Console, ConsoleError

ERROR_PATTERNS = [
    'coredump', 'core dump', 'exception', 'segmentation', 'panic',
    'watchdog', 'i2c bus locked', 'fatal', 'assertion',
]
# Operational Status values that still mean "the stack is one stack".
OK_STATUS = ('Normal operation', 'Not all stack ports are up')
# ...and ones that mean it is not.
BAD_STATUS = ('failover', 'Standalone', 'Disabled Master')

HEALTHY_PORT = re.compile(r'Learnt neighbor', re.I)

# The device prefixes BOTH warnings and errors with '%', and interleaves async
# console text mid-line, so "any % line is a refusal" and "any % line that is
# not a known warning is a refusal" are both wrong.  Match refusals positively.
REFUSAL_RE = re.compile(
    r'%\s*(Invalid|Unrecognized|Unknown|Cannot|Incomplete|Ambiguous|Command'
    r'|Failed|Error|Bad|Not )', re.I)


def ts():
    return time.strftime('%Y-%m-%d %H:%M:%S')


class Runner:
    def __init__(self, con, pairs, settle, logf):
        self.c = con
        self.pairs = pairs
        # Ceilings, not delays -- wait_for returns as soon as the state is right.
        self.settle_shut = max(settle, 45.0)
        self.settle_restore = max(settle * 4, 120.0)
        self.logf = logf

    def log(self, msg):
        line = '{}  {}'.format(ts(), msg)
        print(line, flush=True)
        self.logf.write(line + '\n')
        self.logf.flush()

    # ---- readers ---------------------------------------------------------

    def read_all(self):
        """(state, ports) using two SHORT commands.

        Measured, not assumed: replacing these with a single 'show stack detail'
        was SLOWER -- 285 s/cycle vs 199 s -- because that command prints ~40
        lines and at 115200 baud the transmission costs more than the round trip
        it saves.  Fewer commands is not the same as less time.

        'show stack' (the summary) is also the safe place to look for a bad
        role: 'show stack detail' carries the line
            Disabled Master Monitoring              Enabled
        which substring-matches 'Disabled Master' on a perfectly healthy stack.
        """
        out = self.c.cmd_fast('show stack', timeout=90)
        m = re.search(r'^\s*Operational Status\s{2,}(.+?)\s*$', out, re.M)
        if not out.strip() or not m:
            return None, None
        status = m.group(1)

        pout = self.c.cmd_fast('show stack detail | include Stack port', timeout=90)
        ports = {k: v.strip() for k, v in
                 re.findall(r'Stack (port[\d.]+) status\s+(.+)', pout)}

        low = out.lower()
        if 'disabled master' in low or 'failover' in low or 'standalone' in low:
            return 'BROKEN', ports
        if len(re.findall(r'\bReady\b', out)) < 2:
            return 'BROKEN', ports
        if status == 'Normal operation':
            return 'FULL', ports
        if status == 'Not all stack ports are up':
            return 'DEGRADED', ports
        return 'BROKEN', ports

    def stack_state(self):
        """(state, detail) where state is 'FULL' | 'DEGRADED' | 'BROKEN' | None.

        None means "could not read" -- deliberately distinct from BROKEN so an
        unreadable console is never scored as a product failure.
        """
        out = self.c.cmd_fast('show stack', timeout=90)
        if not out.strip() or 'Operational Status' not in out:
            return None, 'unreadable "show stack": {!r}'.format(out[-200:])
        for bad in BAD_STATUS:
            if bad.lower() in out.lower():
                return 'BROKEN', out.strip()
        ready = len(re.findall(r'\bReady\b', out))
        if ready < 2:
            return 'BROKEN', 'only {} member(s) Ready:\n{}'.format(ready, out.strip())
        if 'Normal operation' in out:
            return 'FULL', out.strip()
        if 'Not all stack ports are up' in out:
            return 'DEGRADED', out.strip()
        return 'BROKEN', out.strip()

    def port_states(self):
        out = self.c.cmd_fast('show stack detail | include Stack port', timeout=90)
        states = dict(re.findall(r'Stack (port[\d.]+) status\s+(.+)', out))
        return ({k: v.strip() for k, v in states.items()}, out)

    # ---- actions ---------------------------------------------------------

    def set_pair(self, pair, shut):
        verb = 'shutdown' if shut else 'no shutdown'
        self.c.cmd_fast('configure terminal', timeout=30)
        try:
            for port in pair:
                self.c.cmd_fast('interface {}'.format(port), timeout=30)
                out = self.c.cmd_fast(verb, timeout=90)
                # A real refusal is a '%' line that is not a warning.  Test the
                # PREFIX only: the console interleaves async text mid-line, and
                # an earlier version matched on the warning's tail and so read
                #   % Warning: "shutswitch: port 46(...) entered disabled state
                # (the warning spliced by a port-state message) as a refusal,
                # aborting the cycle and leaving the stackport shut.
                for line in out.splitlines():
                    if REFUSAL_RE.search(line):
                        raise RuntimeError('"{}" refused on {}: {}'.format(
                            verb, port, line.strip()))
        finally:
            self.c.cmd_fast('end', timeout=30)

    def wait_for(self, predicate, timeout, what):
        """Poll until predicate(state, ports) is true.  Returns (ok, state, ports).

        A fixed sleep was wrong here: after restoring a pair the stack needs a
        variable time to read 'Normal operation' again, and sampling once after
        8 s scored a still-converging stack as a product FAIL.  Polling also
        makes the healthy case FASTER, since it returns the moment it is ready.
        """
        deadline = time.time() + timeout
        state = ports = None
        while time.time() < deadline:
            state, ports = self.read_all()
            if state is not None and predicate(state, ports):
                return True, state, ports
            time.sleep(1.0)
        return False, state, ports

    def cycle(self, n):
        idx = n % len(self.pairs)
        pair = self.pairs[idx]
        others = [p for i, p in enumerate(self.pairs) if i != idx]

        state, states = self.read_all()
        if state is None:
            return 'UNMEASURED', 'could not read stack before cycle'
        if state != 'FULL':
            return 'FAIL', 'stack not FULL before cycle ({})'.format(state)

        # Never shut a pair while the survivor is already down: that would split
        # the stack, which is a different test and must not happen by accident.
        for op in others:
            for port in op:
                st = states.get(port, '<absent>')
                if not HEALTHY_PORT.search(st):
                    return 'FAIL', ('surviving pair {} not healthy before shutting'
                                    ' {}: {} = "{}"'.format(op, pair, port, st))

        self.set_pair(pair, shut=True)

        def is_shut(state, ports):
            return (state != 'BROKEN'
                    and all(ports.get(p, '').lower() == 'down' for p in pair))
        ok, state, ports = self.wait_for(is_shut, self.settle_shut, 'shut')
        if not ok:
            if state == 'BROKEN':
                return 'FAIL', 'STACK LOST while {} was shut'.format(pair)
            if ports is None:
                return 'UNMEASURED', 'no stack reading with {} shut'.format(pair)
            return 'FAIL', ('{} did not read "Down" within {:.0f}s: {}'.format(
                pair, self.settle_shut,
                {p: ports.get(p, '<absent>') for p in pair}))

        # The survivor must have genuinely carried the stack meanwhile.
        for op in others:
            for port in op:
                st = ports.get(port, '<absent>')
                if not HEALTHY_PORT.search(st):
                    return 'FAIL', ('survivor {} degraded while {} shut: {} = "{}"'
                                    .format(op, pair, port, st))

        self.set_pair(pair, shut=False)

        def is_full(state, ports):
            return (state == 'FULL'
                    and all(HEALTHY_PORT.search(ports.get(p, '')) for p in pair))
        ok, state, ports = self.wait_for(is_full, self.settle_restore, 'restore')
        if not ok:
            if ports is None:
                return 'UNMEASURED', 'no stack reading after restoring {}'.format(pair)
            return 'FAIL', ('stack did not return to FULL within {:.0f}s after'
                            ' restoring {} (state={}): {}'.format(
                                self.settle_restore, pair, state,
                                {p: ports.get(p, '<absent>') for p in pair}))
        return 'PASS', 'shut+restored {}'.format(','.join(pair))

    def scan_logs(self):
        out = self.c.cmd_fast('show log | tail 120', timeout=120)
        return [p for p in ERROR_PATTERNS if p in out.lower()], out

    def restore_all(self):
        self.log('restoring: no shutdown on every stack port')
        for pair in self.pairs:
            try:
                self.set_pair(pair, shut=False)
            except Exception as exc:
                self.log('!! restore of {} raised: {}'.format(pair, exc))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--master', default='/dev/u5')
    ap.add_argument('--iterations', type=int, default=300)
    ap.add_argument('--pair', action='append', required=True)
    ap.add_argument('--settle', type=float, default=8.0)
    ap.add_argument('--log-every', type=int, default=25)
    args = ap.parse_args()

    pairs = [tuple(p.split(',')) for p in args.pair]
    if len(pairs) < 2:
        print('refusing to run with fewer than 2 stacking pairs: shutting the '
              'only pair splits the stack instead of testing its stability')
        return 2

    here = os.path.dirname(os.path.abspath(__file__))
    logf = open(os.path.join(here, '38378.log'), 'a', buffering=1)
    prog = os.path.join(here, '38378-progress.txt')
    con = Console(args.master, os.path.join(here, '38378-console.log'))
    r = Runner(con, pairs, args.settle, logf)

    r.log('=' * 72)
    r.log('TEST 38378 -- shut stack ports x{}, pairs={}'.format(args.iterations, pairs))
    r.log('=' * 72)

    try:
        con.login(monitor=True)
    except ConsoleError as exc:
        r.log('ABORT: {}'.format(exc))
        return 1

    state, detail = r.stack_state()
    if state != 'FULL':
        r.log('ABORT: stack is not FULL at the start ({}):\n{}'.format(state, detail))
        con.close()
        return 1
    r.log('baseline: stack FULL, both members Ready')

    counts = {'PASS': 0, 'FAIL': 0, 'UNMEASURED': 0}
    started = time.time()
    try:
        for n in range(1, args.iterations + 1):
            t0 = time.time()
            try:
                verdict, detail = r.cycle(n)
            except Exception as exc:
                verdict, detail = 'UNMEASURED', 'cycle raised: {!r}'.format(exc)
            counts[verdict] += 1
            el = time.time() - started
            rate = el / n
            eta = rate * (args.iterations - n)
            r.log('cycle {:3d}/{}  {:10s} {:5.1f}s  pass={PASS} fail={FAIL} '
                  'unmeas={UNMEASURED}  elapsed={el:.0f}s eta={eta:.0f}s'.format(
                      n, args.iterations, verdict, time.time() - t0,
                      el=el, eta=eta, **counts))
            if verdict != 'PASS':
                r.log('    -> {}'.format(detail))
            # A one-line progress file so anything can poll without the console.
            with open(prog, 'w') as fh:
                fh.write('cycle {}/{} pass={PASS} fail={FAIL} unmeas={UNMEASURED} '
                         'elapsed={el:.0f}s eta={eta:.0f}s\n'.format(
                             n, args.iterations, el=el, eta=eta, **counts))
            if n % args.log_every == 0:
                hits, _ = r.scan_logs()
                r.log('    log scan @{}: {}'.format(
                    n, 'CLEAN' if not hits else 'HITS {}'.format(hits)))
    finally:
        try:
            r.restore_all()
            hits, _ = r.scan_logs()
            r.log('final log scan: {}'.format('CLEAN' if not hits else 'HITS {}'.format(hits)))
            state, detail = r.stack_state()
            r.log('final stack state: {} {}'.format(
                state, '' if state == 'FULL' else detail))
        finally:
            con.close()

    r.log('RESULT  pass={PASS} fail={FAIL} unmeasured={UNMEASURED}'.format(**counts))
    logf.close()
    return 0 if counts['FAIL'] == 0 and counts['UNMEASURED'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
