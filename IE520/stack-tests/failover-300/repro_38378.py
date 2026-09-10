#!/usr/bin/env python3
"""TEST 38378 cycle-293 reproducer: repeated REDUNDANT shutdown of a stackport.

    ./repro_38378.py --master /dev/u4 --carrier port1.0.28,port2.0.27 \
        --shut-first port2.0.28 --target port1.0.27 --iterations 5000

WHAT THIS ISOLATES
  In the 300-cycle run the harness shut BOTH ends of a pair each cycle.  The
  first shutdown downed both ends; the second therefore landed on a port that
  was ALREADY `disabled`.  Measured over the run: that redundant shutdown was
  issued 293 times (293 shutdowns produced 3 "entered disabled state" lines,
  293 produced 1) and the master wedged on exactly one of them -- ~0.34%.

  So it is NOT deterministic, and a reproducer has to be built for volume.
  This script strips away everything else: the carrier pair stays up the whole
  time, the target port is shut ONCE at the start, and then the same redundant
  `shutdown` is issued against it over and over.  No port-state transitions, no
  stack re-form waits -- roughly 2-3 s per attempt instead of ~200 s per cycle.

WHAT IT CANNOT SHOW
  If the real cause is cumulative (a leak or drift over ~17 h) rather than the
  command itself, this loop will stay clean indefinitely from a fresh boot.  A
  dry result weakens the command hypothesis but does not clear it.

FAITHFULNESS TO THE ORIGINAL
  Original: master was member 1; it shut its OWN port1.0.27, then issued the
  redundant shutdown against member 2's port2.0.28 -- i.e. a REMOTE member's
  already-down stackport.  Roles have since swapped, so the mirror is: master
  (member 2) shuts its own port2.0.28, then hammers member 1's port1.0.27.

SAFETY
  * Refuses to start unless the stack is FULL and all four stackports read
    "Learnt neighbor".
  * Only ever shuts ONE pair.  The carrier pair is re-verified every
    --check-every iterations; if it degrades the run stops immediately, because
    shutting a pair while the survivor is down would SPLIT the stack.
  * A finally: block restores every stackport, so an exception or Ctrl-C cannot
    leave the stack on one link.
"""
import argparse
import os
import re
import sys
import time

from console import Console, ConsoleError

HEALTHY_PORT = re.compile(r'Learnt neighbor', re.I)
# Positive matching: the device prefixes warnings AND errors with '%', and
# splices async console text mid-line, so "any % line is bad" and "any % line
# that isn't a known warning is bad" are both wrong.  This bit me once already.
REFUSAL_RE = re.compile(
    r'%\s*(Invalid|Unrecognized|Unknown|Cannot|Incomplete|Ambiguous|Command'
    r'|Failed|Error|Bad|Not )', re.I)


def ts():
    return time.strftime('%Y-%m-%d %H:%M:%S')


class Repro:
    def __init__(self, con, args, logf):
        self.c = con
        self.a = args
        self.logf = logf
        self.carrier = tuple(args.carrier.split(','))

    def log(self, msg):
        line = '{}  {}'.format(ts(), msg)
        print(line, flush=True)
        self.logf.write(line + '\n')
        self.logf.flush()

    def read_all(self):
        """(state, ports) -- two SHORT commands; measured faster than one big one."""
        out = self.c.cmd_fast('show stack', timeout=90)
        m = re.search(r'^\s*Operational Status\s{2,}(.+?)\s*$', out, re.M)
        if not out.strip() or not m:
            return None, None
        status = m.group(1)
        pout = self.c.cmd_fast('show stack detail | include Stack port',
                               timeout=90)
        ports = {k: v.strip() for k, v in
                 re.findall(r'Stack (port[\d.]+) status\s+(.+)', pout)}
        low = out.lower()
        # NB: check the SUMMARY, not 'show stack detail' -- the detail output
        # contains "Disabled Master Monitoring", which substring-matches
        # "Disabled Master" on a perfectly healthy stack.
        if 'disabled master' in low or 'failover' in low or 'standalone' in low:
            return 'BROKEN', ports
        if len(re.findall(r'\bReady\b', out)) < 2:
            return 'BROKEN', ports
        if status == 'Normal operation':
            return 'FULL', ports
        if status == 'Not all stack ports are up':
            return 'DEGRADED', ports
        return 'BROKEN', ports

    def carrier_ok(self, ports):
        return ports is not None and all(
            HEALTHY_PORT.search(ports.get(p, '')) for p in self.carrier)

    def _check_refusal(self, out, port):
        for line in out.splitlines():
            if REFUSAL_RE.search(line):
                raise RuntimeError('refused on {}: {}'.format(port, line.strip()))

    def set_port(self, port, shut, timeout=60.0):
        """Full-cycle version: enter config, set, leave.  Used for setup/restore."""
        self.c.cmd_fast('configure terminal', timeout=30)
        try:
            self.c.cmd_fast('interface {}'.format(port), timeout=30)
            out = self.c.cmd_fast('shutdown' if shut else 'no shutdown',
                                  timeout=timeout)
            self._check_refusal(out, port)
            return out
        finally:
            self.c.cmd_fast('end', timeout=30)

    # ---- the hot loop ----------------------------------------------------
    #
    # Entering config mode and the interface context ONCE, then repeating just
    # `shutdown`, cuts the per-iteration command count from 4 to 1.  Fidelity
    # note: the original issued its redundant shutdown in a freshly-entered
    # interface context, so this is slightly less faithful -- it is a purer test
    # of "shutdown against an already-down stackport" and a weaker test of
    # "re-entering the interface context each time".  enter_ctx()/leave_ctx()
    # are called around health checks so the context is rebuilt periodically.

    def enter_ctx(self, port):
        self.c.cmd_fast('configure terminal', timeout=30)
        out = self.c.cmd_fast('interface {}'.format(port), timeout=30)
        self._check_refusal(out, port)

    def leave_ctx(self):
        self.c.cmd_fast('end', timeout=30)

    def hammer(self, port, timeout):
        """One redundant shutdown.  Raises if the prompt never came back.

        This is THE detection point for the thing we are hunting: a wedge shows
        up as the CLI simply ceasing to respond -- no error, no echo, nothing.
        An earlier version relied on cmd_fast raising, which it never does on
        timeout, so a wedge would have been recorded as a normal iteration.
        """
        out = self.c.cmd_fast('shutdown', timeout=timeout)
        if not getattr(self.c, 'last_prompt_seen', True):
            raise RuntimeError(
                'NO PROMPT after `shutdown` on {} within {:.0f}s -- console '
                'stopped responding (tail={!r})'.format(port, timeout, out[-200:]))
        self._check_refusal(out, port)
        return out

    def restore_all(self):
        self.log('RESTORING every stackport (no shutdown)')
        for p in list(self.carrier) + [self.a.shut_first, self.a.target]:
            try:
                self.set_port(p, shut=False)
            except Exception as exc:
                self.log('!! restore of {} raised: {}'.format(p, exc))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--master', default='/dev/u4')
    ap.add_argument('--carrier', required=True,
                    help='comma-separated pair that must stay UP the whole run')
    ap.add_argument('--shut-first', required=True,
                    help='master-side port of the victim pair, shut ONCE')
    ap.add_argument('--target', required=True,
                    help='remote-member port to hammer with redundant shutdowns')
    ap.add_argument('--iterations', type=int, default=5000)
    ap.add_argument('--check-every', type=int, default=50,
                    help='full stack health check every N iterations')
    ap.add_argument('--wedge-timeout', type=float, default=25.0,
                    help='seconds with no prompt before declaring a wedge')
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    logf = open(os.path.join(here, 'repro-38378.log'), 'a', buffering=1)
    prog = os.path.join(here, 'repro-progress.txt')
    con = Console(args.master, os.path.join(here, 'repro-38378-console.log'))
    r = Repro(con, args, logf)

    r.log('=' * 72)
    r.log('REPRO: redundant shutdown of {} (carrier {}, first-shut {})'.format(
        args.target, args.carrier, args.shut_first))
    r.log('master console {} -- iterations {}'.format(args.master, args.iterations))
    r.log('=' * 72)

    try:
        # monitor=True: the console capture was the ONLY artefact covering the
        # original wedge, so we want the device talking as much as possible.
        # Declared here, not re-enabled later, so reordering cannot silently
        # leave logging off.
        con.login(monitor=True)
    except ConsoleError as exc:
        r.log('ABORT: {}'.format(exc))
        return 1
    r.log('terminal monitor ENABLED (via login(monitor=True))')

    state, ports = r.read_all()
    if state != 'FULL' or not r.carrier_ok(ports):
        r.log('ABORT: stack not FULL with all stackports healthy at start: '
              '{} {}'.format(state, ports))
        con.close()
        return 1
    r.log('baseline OK: {} {}'.format(state, ports))

    wedged = False
    n = 0
    started = time.time()
    try:
        r.log('shutting {} ONCE (this downs both ends of the victim pair)'
              .format(args.shut_first))
        r.set_port(args.shut_first, shut=True)
        time.sleep(5)
        state, ports = r.read_all()
        if not r.carrier_ok(ports):
            r.log('ABORT: carrier {} not healthy after initial shut: {}'
                  .format(r.carrier, ports))
            return 1
        r.log('victim pair down, carrier {} still up -- starting loop'
              .format(r.carrier))

        r.enter_ctx(args.target)
        r.log('entered config context on {} -- looping `shutdown` only'
              .format(args.target))

        for n in range(1, args.iterations + 1):
            t0 = time.time()
            try:
                r.hammer(args.target, timeout=args.wedge_timeout)
            except Exception as exc:
                # A wedge presents as no prompt coming back at all.
                r.log('*** POSSIBLE WEDGE at iteration {} after {:.1f}s: {!r}'
                      .format(n, time.time() - t0, exc))
                r.log('*** leaving the console UNTOUCHED and watching for a reset')
                wedged = True
                break

            if n % args.check_every == 0:
                r.leave_ctx()
                state, ports = r.read_all()
                el = time.time() - started
                r.log('iter {:5d}/{}  {:.2f}s/iter  state={} carrier_ok={}'.format(
                    n, args.iterations, el / n, state, r.carrier_ok(ports)))
                with open(prog, 'w') as fh:
                    fh.write('iter {}/{} elapsed={:.0f}s rate={:.2f}s/iter '
                             'state={}\n'.format(n, args.iterations, el,
                                                 el / n, state))
                if state == 'BROKEN' or not r.carrier_ok(ports):
                    r.log('*** STACK DEGRADED at iteration {}: {} {}'.format(
                        n, state, ports))
                    wedged = True
                    break
                r.enter_ctx(args.target)   # rebuild the context and carry on
    except KeyboardInterrupt:
        r.log('interrupted by user at iteration {}'.format(n))
    finally:
        if wedged:
            # Do not type into a wedged box.  Just listen -- the original reset
            # ~2 min after the wedge and the console was the only witness.
            r.log('watching the console for up to 300 s for a reset/recovery...')
            deadline = time.time() + 300
            while time.time() < deadline:
                txt = con._read_some()
                if txt and ('BootROM' in txt or 'U-Boot' in txt):
                    r.log('*** RESET OBSERVED -- BootROM/U-Boot banner seen')
                    break
                if not txt:
                    time.sleep(0.3)
            r.log('watch ended')
        else:
            try:
                try:
                    r.leave_ctx()
                except Exception:
                    pass
                r.restore_all()
                # Poll rather than sample once: the stack needs a few seconds
                # after a stackport is restored before Operational Status reads
                # 'Normal operation' again, and a single immediate read logged
                # a self-contradictory "DEGRADED" alongside four healthy ports.
                deadline = time.time() + 120
                state, ports = r.read_all()
                while time.time() < deadline and state != 'FULL':
                    time.sleep(3)
                    state, ports = r.read_all()
                r.log('final state: {} {}'.format(state, ports))
                if state != 'FULL':
                    r.log('!! stack did NOT return to FULL within 120s '
                          '-- CHECK THE BENCH before the next run')
            except Exception as exc:
                r.log('!! restore raised: {}'.format(exc))
        con.close()

    r.log('RESULT: {} after {} iterations in {:.0f}s'.format(
        'WEDGE REPRODUCED' if wedged else 'no wedge', n, time.time() - started))
    logf.close()
    return 2 if wedged else 0


if __name__ == '__main__':
    sys.exit(main())
