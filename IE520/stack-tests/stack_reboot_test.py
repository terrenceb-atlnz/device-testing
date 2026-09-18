#!/usr/bin/env python3
"""Repeated VCStack member / master reboot test, driven by the AT framework and bound
from a .setup file.  Platform-agnostic: nothing here names a port, a console, a member
ID or a product string -- all of that is read from the .setup and from the stack itself.

    # backup-member reboots, rotating through the current backups (TEST 38377 shape)
    cd <dated run dir> && PYTHONPATH=/home/st-art python3 /abs/path/stack_reboot_test.py \
        --mode member --cycles 300 --case-id 38377 --setup /home/st-art/st-art/configs/tb470.setup

    # master reboots -- each cycle reboots whoever is Active Master NOW (TEST 38376 shape)
    cd <dated run dir> && PYTHONPATH=/home/st-art python3 /abs/path/stack_reboot_test.py \
        --mode master --cycles 300 --case-id 38376

Run it from a DATED RUN DIRECTORY: the framework writes one console transcript per member
(<swi_name>.log), the stack log (<stk_name>.log) and setup.log into the current directory,
and this script adds <case>.log (the campaign log), <case>-progress.txt (one line, for
polling) and <case>-summary.json (per-cycle verdicts and timings).

What a cycle proves (positive evidence only -- "no error appeared" is never a pass):
  1. the stack was FULL before the reboot (Normal operation, every member Ready);
  2. the target's OWN console printed a boot and came back to a login prompt (its
     transcript is the boot capture);
  3. [master mode] a surviving console announced the promotion, and `show stack` read
     from a survivor shows a DIFFERENT Active Master -- the failover time is measured from
     the confirmed reboot to that reading;
  4. every member is Ready again and every stack port reads a learnt neighbour;
  5. `show reboot history` gained exactly one entry for the target, typed Expected;
  6. the exception log did not grow, and a `show log` tail carries none of the fatal
     signatures.  A new exception-log entry is recorded as a FINDING (the cycle FAILs, the
     run continues, the baseline is re-taken) -- provoking one is the point of the loop.
A cycle whose evidence could not be read is UNMEASURED, never PASS and never FAIL.

Policy (Terrence, 2026-09-18): record-and-continue.  Nothing here stops the run on a
failure; the exit code and the summary carry the counts.

Framework traps this script works around (see orient-dt SKILL.md S3/S4):
  * init_stk() does not establish the console session -> mode('#') first, on each member;
  * Stack.members is an unordered set -> members are sorted by their .setup name;
  * powerOn defaults True and switches the PDU outlet on -> powerOn=False;
  * library sys.exit() on a timeout kills the run silently -> exception_on_exit() on
    every member, and every framework call is wrapped so a timeout grades UNMEASURED;
  * a console with a live read() thread must not be written to ("EXISTING READ THREAD
    DETECTED") -> read threads are stopped before any send/mode on that console;
  * the framework has no --More-- handling worth trusting on a busy console -> `terminal
    length 0` is (re)issued after every login, session-scoped, never written to config.
"""
import argparse
import json
import os
import re
import sys
import time
import traceback

try:
    from framework.Setup import LoadSetup
except ImportError:
    sys.exit('cannot import framework.Setup -- run with PYTHONPATH=/home/st-art on the testbox')

# ----------------------------------------------------------------------------------
# constants -- all AW+ generic, none product-specific
# ----------------------------------------------------------------------------------
PROMOTED_STRINGS = ['has become the Active Master']

# MEASURED 2026-09-18 against two healthy IE520 boots AND the 2026-08-26 wedge captures.
# Every pattern below is CASE-SENSITIVE and anchored on punctuation the kernel actually
# prints, because the obvious loose forms are all false positives here:
#   'core'      -> usbcore, pps_core, l2tp_core, pinctrl core, "Core: 22 devices"
#   'oops'      -> ramoops, mtdoops  (the pstore driver; this alone produced 2 hits in
#                  the real wedge capture, i.e. the loose pattern "detected" the wedge
#                  for entirely the wrong reason)
#   'watchdog'  -> f1020300.watchdog driver registration, printed on every boot
#   'exception' -> our own `show exception log` echoed back in `show log`
# A healthy boot scores ZERO on all of these.
FATAL_RE = re.compile(r'Kernel panic|Oops:|Unable to handle kernel|BUG:|segfault'
                      r'|core dumped|coredump|Internal error|i2c bus locked'
                      r'|watchdog: BUG|Disabled Master|Standalone unit')
# `show log` echoes every command we type (IMISH[pid]: [manager@ttyS0]<cmd>), so scanning
# raw log text matches our own command names.  These lines are dropped before matching.
LOG_ECHO_RE = re.compile(r'IMISH\[\d+\]')
# ONE boot prints ONE of these.  (It also prints 'BootROM: Image checksum verification
# PASSED' and a 'U-Boot <ver>' banner -- matching those too counted a normal boot as 3
# boots.)  Two in a capture that should hold one boot = the unit reset itself mid-boot.
BOOT_BANNER_RE = re.compile(r'BootROM \d+\.\d+')
STACK_ROW_RE = re.compile(r'^\s*(\d+)\s+(\S+)\s+([0-9a-fA-F.]{14})\s+(\d+)\s+(\S+)\s+(.+?)\s*$', re.M)
OPER_RE = re.compile(r'^\s*Operational Status\s{2,}(.+?)\s*$', re.M)
STACKPORT_RE = re.compile(r'Stack (port[\d.]+) status\s+(.+)')
REBOOT_HDR_RE = re.compile(r'^Stack member (\d+):\s*$', re.M)
REBOOT_ROW_RE = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+(Expected|Unexpected)\s+(.*)$', re.M)
LOGIN_RE = re.compile(r'^(\S+?)(?:-(\d+))?\s+login:', re.M)


def ts():
    return time.strftime('%Y-%m-%d %H:%M:%S')


class Unreadable(Exception):
    """A console read that did not yield evidence.  Grades the cycle UNMEASURED."""


# ----------------------------------------------------------------------------------
class Campaign:
    def __init__(self, args):
        self.args = args
        self.case = args.case_id or {'member': '38377', 'master': '38376'}[args.mode]
        self.logf = open('%s.log' % self.case, 'a', buffering=1)
        self.prog = '%s-progress.txt' % self.case
        self.summary_path = '%s-summary.json' % self.case
        self.cycles = []
        self.counts = {'PASS': 0, 'FAIL': 0, 'UNMEASURED': 0}
        self.started = time.time()
        self.members = []          # Switch objects, sorted by .setup name
        self.by_id = {}            # stack ID (str) -> Switch
        self.ids = []              # all stack IDs as strings, from `show stack`
        self.master_id = None
        self.rotate_index = 0
        self.exception_baseline = None
        self.live_threads = {}     # Switch -> Read thread

    # ---- logging -------------------------------------------------------------
    def log(self, msg):
        for line in str(msg).splitlines() or ['']:
            out = '%s  %s' % (ts(), line)
            print(out, flush=True)
            self.logf.write(out + '\n')

    def progress(self, n, verdict):
        el = time.time() - self.started
        rate = el / n if n else 0
        with open(self.prog, 'w') as fh:
            fh.write('cycle %d/%d %s pass=%d fail=%d unmeas=%d elapsed=%.0fs eta=%.0fs master=%s\n' % (
                n, self.args.cycles, verdict, self.counts['PASS'], self.counts['FAIL'],
                self.counts['UNMEASURED'], el, rate * (self.args.cycles - n), self.master_id))
        with open(self.summary_path, 'w') as fh:
            json.dump({'case': self.case, 'mode': self.args.mode, 'setup': self.args.setup,
                       'stack': self.args.stack, 'started': time.strftime(
                           '%Y-%m-%d %H:%M:%S', time.localtime(self.started)),
                       'counts': self.counts, 'cycles': self.cycles}, fh, indent=1)

    # ---- console helpers -----------------------------------------------------
    def stop_threads(self, *swis):
        for swi in swis or list(self.live_threads):
            t = self.live_threads.pop(swi, None)
            if t is not None and not t.has_finished():
                try:
                    t.stop()
                except Exception as exc:
                    self.log('  (stopping read thread on %s raised %r)' % (swi.name, exc))

    def login(self, swi, timeout=180):
        """Reach '#' on a console and disable paging for this session."""
        self.stop_threads(swi)
        swi.mode('#', timeOut=timeout)
        swi.cmd('terminal length 0', maxWait=30)

    def cmd(self, swi, command, maxwait=120):
        out = swi.cmd(command, maxWait=maxwait)
        if not out or not out.strip():
            raise Unreadable('empty reply to %r on %s' % (command, swi.name))
        return out

    # ---- stack readers -------------------------------------------------------
    def show_stack(self, swi):
        out = self.cmd(swi, 'show stack')
        rows = {m.group(1): {'mac': m.group(3), 'prio': m.group(4), 'status': m.group(5),
                             'role': m.group(6).strip()} for m in STACK_ROW_RE.finditer(out)}
        oper = OPER_RE.search(out)
        if not rows or not oper:
            raise Unreadable('could not parse `show stack` on %s: %r' % (swi.name, out[-300:]))
        master = [i for i, r in rows.items() if 'Active' in r['role']]
        return {'rows': rows, 'oper': oper.group(1), 'master': master[0] if master else None, 'raw': out}

    def is_full(self, st):
        return (st['oper'] == 'Normal operation' and st['master'] is not None
                and set(st['rows']) == set(self.ids)
                and all(r['status'] == 'Ready' for r in st['rows'].values()))

    def stackports(self, swi):
        out = self.cmd(swi, 'show stack detail | include Stack port')
        ports = {k: v.strip() for k, v in STACKPORT_RE.findall(out)}
        if not ports:
            raise Unreadable('no stack port lines on %s' % swi.name)
        return ports

    def reboot_history(self, swi):
        """{member id: [(time, type, description), ...]} newest first, as the device prints."""
        out = self.cmd(swi, 'show reboot history', maxwait=120)
        hist = {}
        heads = list(REBOOT_HDR_RE.finditer(out))
        if not heads:                      # standalone: one unheaded block
            hist[self.master_id] = REBOOT_ROW_RE.findall(out)
            return hist
        for i, h in enumerate(heads):
            end = heads[i + 1].start() if i + 1 < len(heads) else len(out)
            hist[h.group(1)] = REBOOT_ROW_RE.findall(out[h.end():end])
        return hist

    def exception_log(self, swi):
        return self.cmd(swi, 'show exception log', maxwait=120).strip()

    def log_tail(self, swi, lines=150):
        """`show log tail N` -- NOT `show log | tail N`.

        MEASURED 2026-09-18: the pipe form is '% Invalid input detected' on this build.
        That matters beyond this script: test_38378.py's scan_logs() uses the pipe form,
        so every 'log scan: CLEAN' it has ever printed was scanning an error message --
        an absence-of-evidence pass.  Here the command is verified to have produced log
        text, and a reply that is not log output raises Unreadable (UNMEASURED), never a
        silent clean.
        """
        out = self.cmd(swi, 'show log tail %d' % lines, maxwait=180)
        if 'Invalid input' in out or '<date> <time>' not in out:
            raise Unreadable('`show log tail %d` did not return log text on %s: %r'
                             % (lines, swi.name, out[:200]))
        return '\n'.join(l for l in out.splitlines() if not LOG_ECHO_RE.search(l))

    def newest_reboots(self, swi):
        """{member id: newest (time, type, description) or None} -- for EVERY member.

        This is the load-bearing health check of the whole campaign.  The 2026-08-26
        cycle-293 wedge emitted NOTHING on the console on its way down (it goes straight
        from silence to a BootROM banner), so no console-text pattern can catch it.  What
        it DOES leave is an 'Unexpected' entry in `show reboot history`.  Watching every
        member's newest entry each cycle therefore catches a self-reset anywhere in the
        stack, including on units this cycle never touched.
        """
        return {mid: (rows[0] if rows else None)
                for mid, rows in self.reboot_history(swi).items()}

    def wait_full(self, swi, timeout, what):
        """Poll `show stack` until FULL.  Returns (ok, seconds, last_state)."""
        t0 = time.time()
        st = None
        while time.time() - t0 < timeout:
            try:
                st = self.show_stack(swi)
                if self.is_full(st):
                    return True, time.time() - t0, st
            except Unreadable:
                st = None
            time.sleep(5)
        self.log('  !! %s: stack not FULL within %ds; last: %s' % (
            what, timeout, st['raw'].strip() if st else '<unreadable>'))
        return False, time.time() - t0, st

    # ---- binding -------------------------------------------------------------
    def bind(self):
        a = self.args
        self.log('=' * 78)
        self.log('TEST %s -- %s reboot x%d  (setup=%s stack=%s)' % (
            self.case, a.mode.upper(), a.cycles, a.setup, a.stack))
        self.log('=' * 78)
        setup = LoadSetup(a.setup)
        stk = setup.init_stk(a.stack, powerOn=False)
        self.members = sorted(stk.all_members(), key=lambda s: s.name)
        self.log('members from .setup: %s' % ', '.join('%s=%s' % (m.name, m.tty) for m in self.members))
        for m in self.members:
            m.exception_on_exit()          # a framework timeout must raise, not sys.exit()
            self.login(m)
        control = self.members[0]
        st = self.show_stack(control)
        self.ids = sorted(st['rows'], key=int)
        self.master_id = st['master']
        self.log('show stack (via %s):\n%s' % (control.name, st['raw'].strip()))
        if not self.is_full(st):
            raise SystemExit('ABORT: stack is not FULL at the start (%s)' % st['oper'])
        if len(self.ids) != len(self.members):
            raise SystemExit('ABORT: .setup declares %d members but the stack has %d (%s)' % (
                len(self.members), len(self.ids), self.ids))

        # console -> stack ID, from each console's own login banner.  A backup shows
        # '<host>-<id> login:', the master shows the bare '<host> login:'.  This is the
        # only unit-level identity a relayed stack console offers (TESTBOX-ACCESS S2).
        self.log('mapping consoles to stack IDs by login banner ...')
        for m in self.members:
            out = m.send('exit\n', waitTime=30, strList=['login:'])
            banners = LOGIN_RE.findall(out)
            if not banners:
                raise SystemExit('ABORT: no login banner on %s after `exit`: %r' % (m.name, out[-200:]))
            host, sid = banners[-1]
            sid = sid or self.master_id
            if sid in self.by_id:
                raise SystemExit('ABORT: consoles %s and %s both present as member %s' % (
                    self.by_id[sid].name, m.name, sid))
            self.by_id[sid] = m
            m.stackID = sid
            self.log('  %s (%s) -> member %s  [banner %r]' % (m.name, m.tty, sid, out.strip().splitlines()[-1][:60]))
            self.login(m)
        if set(self.by_id) != set(self.ids):
            raise SystemExit('ABORT: banner map %s != show stack IDs %s' % (sorted(self.by_id), self.ids))

        master = self.by_id[self.master_id]
        self.log('device identity (via %s):' % master.name)
        self.log(self.cmd(master, 'show system | include Board|Base|Bootloader|Software version|Build date|Stack member', maxwait=120).strip())
        ports = self.stackports(master)
        self.log('stack ports: %s' % '; '.join('%s=%s' % kv for kv in sorted(ports.items())))
        bad = [p for p, s in ports.items() if 'Learnt neighbor' not in s]
        if bad:
            raise SystemExit('ABORT: stack ports not all learnt at start: %s' % bad)
        self.exception_baseline = self.exception_log(master)
        self.log('exception log baseline: %d chars' % len(self.exception_baseline))
        self.log('reboot history counts: %s' % {k: len(v) for k, v in self.reboot_history(master).items()})
        self.log('bound OK; master=%s (%s)' % (self.master_id, master.name))

    # ---- target selection ----------------------------------------------------
    def pick_target(self):
        if self.args.mode == 'master':
            return self.master_id
        if self.args.member:
            if self.args.member == self.master_id:
                raise Unreadable('pinned member %s is currently the master; refusing' % self.args.member)
            return self.args.member
        backups = [i for i in self.ids if i != self.master_id]
        t = backups[self.rotate_index % len(backups)]
        self.rotate_index += 1
        return t

    # ---- one cycle -----------------------------------------------------------
    def cycle(self, n):
        a = self.args
        rec = {'n': n, 'start': ts(), 'mode': a.mode}
        master = self.by_id[self.master_id]

        # 1. pre-state must be FULL
        st = self.show_stack(master)
        if not self.is_full(st):
            ok, _, st = self.wait_full(master, a.settle, 'pre-cycle')
            if not ok:
                return 'FAIL', 'stack not FULL before cycle: %s' % (st['oper'] if st else '?'), rec
        if st['master'] != self.master_id:          # roles moved behind our back
            self.log('  note: master moved %s -> %s outside the test' % (self.master_id, st['master']))
            self.master_id = st['master']
            master = self.by_id[self.master_id]
        target_id = self.pick_target()
        target = self.by_id[target_id]
        others = [m for m in self.members if m is not target]
        rec.update(target=target_id, target_console=target.name, master_before=self.master_id)
        # The NEWEST entry per member, not the count: `show reboot history` is a capped ring
        # (member 1 was already at 33 entries on 2026-09-18), so over 300 cycles the count
        # stops growing and a count-delta check would start reporting false failures the
        # moment it saturates.  Snapshot ALL members so a self-reset on a unit this cycle
        # never touched is caught too.
        reboots_before = self.newest_reboots(master)
        newest_before = reboots_before.get(target_id)
        self.log('  target member %s on %s (%s); master=%s; newest reboot-history entry: %s' % (
            target_id, target.name, target.tty, self.master_id, newest_before or '<none>'))

        # 2. arm witnesses BEFORE the reboot (never on the console we are about to write to)
        if a.mode == 'master':
            for m in others:
                self.live_threads[m] = m.read(a.failover_timeout, untilStrList=PROMOTED_STRINGS)

        # 3. issue the reboot from the master console.
        # The confirmation is ANSWERED BLIND rather than gated on: `reboot stack-member`
        # prompts '(y/n)' on this build, but 0009 drove it with a bare cmd() as though it
        # did not, so the prompt is not guaranteed across platforms/builds.  A stray 'y'
        # at an enable prompt is harmless ('% Invalid input'), whereas refusing to answer
        # a prompt that IS there would leave the CLI mid-dialog.  Whether the reboot
        # actually happened is proven at step 5/7 by the target's own boot capture and by
        # `show reboot history` -- never by the presence of this prompt.
        out = master.send('reboot stack-member %s\n' % target_id, waitTime=20, strList=['(y/n)'])
        rec['confirm_prompt'] = '(y/n)' in out
        if not rec['confirm_prompt']:
            self.log('  note: no "(y/n)" within 20s of the reboot command; answering anyway. Tail: %r'
                     % out[-160:])
        t_reboot = time.time()
        master.send('y\r\n', waitTime=0)
        rec['reboot_issued'] = ts()
        # boot capture on the target's own console -- for the master this is the console
        # we just wrote to, which is fine: the write is done and the unit is going down.
        self.live_threads[target] = target.read(a.boot_timeout, untilStrList=['login:'])

        # 4. master mode: find the new master from a survivor
        driver = master
        if a.mode == 'master':
            announced = None
            deadline = time.time() + a.failover_timeout
            while time.time() < deadline and announced is None:
                for m in others:
                    t = self.live_threads.get(m)
                    if t is not None and t.is_keyword_found():
                        announced = m
                        break
                time.sleep(1)
            rec['promotion_seen_on'] = announced.name if announced else None
            rec['promotion_s'] = round(time.time() - t_reboot, 1) if announced else None
            self.log('  promotion message %s' % (
                'seen on %s after %.1fs' % (announced.name, rec['promotion_s']) if announced
                else 'NOT seen on any survivor within %ds (will confirm via show stack)' % a.failover_timeout))
            self.stop_threads(*others)
            # the promotion line is printed by the winner; whoever printed it holds the CLI now
            driver = announced or others[0]
            new_master = None
            t0 = time.time()
            while time.time() - t0 < a.failover_timeout:
                try:
                    self.login(driver, timeout=60)
                    st = self.show_stack(driver)
                    if st['master'] and st['master'] != target_id and st['rows'][st['master']]['status'] == 'Ready':
                        new_master = st['master']
                        break
                except Exception as exc:              # survivor consoles drop to login: mid-failover
                    self.log('  (survivor %s not answering yet: %s)' % (driver.name, str(exc)[:80]))
                    driver = others[(others.index(driver) + 1) % len(others)]
                time.sleep(3)
            if new_master is None:
                rec['failover_s'] = None
                self.log('  !! no new Active Master readable within %ds' % a.failover_timeout)
                verdict, why = 'FAIL', 'no new Active Master within %ds of rebooting master %s' % (
                    a.failover_timeout, target_id)
                self.collect_evidence(driver, rec, why)
                self.wait_full(driver, a.boot_timeout, 'recovery')
                self.stop_threads()
                self.refresh_master(driver)
                return verdict, why, rec
            rec['failover_s'] = round(time.time() - t_reboot, 1)
            rec['master_after'] = new_master
            self.master_id = new_master
            self.log('  new Active Master = %s (%s); failover measured %.1fs' % (
                new_master, self.by_id[new_master].name, rec['failover_s']))
            driver = self.by_id[new_master]
            self.login(driver, timeout=120)

        # 5. the target must boot and present a login prompt on its own console
        t = self.live_threads[target]
        while not t.has_finished():
            time.sleep(2)
        boot_text = target.console.buffer or ''
        rec['boot_to_login_s'] = round(time.time() - t_reboot, 1) if t.is_keyword_found() else None
        banners = len(BOOT_BANNER_RE.findall(boot_text))
        rec['boot_banners'] = banners
        self.stop_threads(target)
        if not t.is_keyword_found():
            why = 'target %s console showed no login prompt within %ds of the reboot (%d bytes captured)' % (
                target_id, a.boot_timeout, len(boot_text))
            self.collect_evidence(driver, rec, why, target=target)
            self.wait_full(driver, a.ready_timeout, 'recovery')
            self.refresh_master(driver)
            return 'FAIL', why, rec
        self.log('  target %s back at login after %.1fs (boot banners seen: %d)' % (
            target_id, rec['boot_to_login_s'], banners))

        # 6. whole stack Ready again, every stack port learnt
        ok, secs, st = self.wait_full(driver, a.ready_timeout, 'rejoin')
        rec['all_ready_s'] = round(time.time() - t_reboot, 1) if ok else None
        if not ok:
            why = 'stack not FULL within %ds after rebooting %s (last: %s)' % (
                a.ready_timeout, target_id, st['oper'] if st else 'unreadable')
            self.collect_evidence(driver, rec, why, target=target)
            self.refresh_master(driver)
            return 'FAIL', why, rec
        self.master_id = st['master']
        rec['master_after'] = self.master_id
        ports = self.stackports(driver)
        rec['stackports_unlearnt'] = [p for p, s in ports.items() if 'Learnt neighbor' not in s]
        self.log('  stack FULL after %.1fs; master=%s; unlearnt stack ports: %s' % (
            rec['all_ready_s'], self.master_id, rec['stackports_unlearnt'] or 'none'))

        # 7. positive evidence the reboot happened, and nothing else did
        problems = []
        if banners > 1:
            problems.append('%d bootloader banners in one boot capture (self-reset mid-boot?)' % banners)
        reboots_after = self.newest_reboots(driver)
        newest_after = reboots_after.get(target_id)
        rec['reboot_history_newest'] = newest_after
        if newest_after is None:
            problems.append('no reboot history for member %s after rebooting it' % target_id)
        elif newest_after == newest_before:
            problems.append('reboot history for member %s gained no new entry (newest still %s)'
                            % (target_id, newest_before))
        elif newest_after[1] != 'Expected':
            problems.append('newest reboot-history entry for %s is %s: %s'
                            % (target_id, newest_after[1], newest_after[2]))
        # Any OTHER member that rebooted this cycle is a finding whatever its type: we only
        # asked one unit to go down.  This is what would catch a cycle-293-style watchdog
        # reset, which leaves no console text at all.
        collateral = {mid: new for mid, new in reboots_after.items()
                      if mid != target_id and new != reboots_before.get(mid)}
        rec['collateral_reboots'] = collateral or None
        if collateral:
            problems.append('member(s) other than the target also rebooted: %s' % collateral)
        if rec['stackports_unlearnt']:
            problems.append('stack ports without a learnt neighbour: %s' % rec['stackports_unlearnt'])
        exc_now = self.exception_log(driver)
        if exc_now != self.exception_baseline:
            problems.append('exception log CHANGED (%d -> %d chars) -- device finding' % (
                len(self.exception_baseline), len(exc_now)))
            self.log('  !! exception log now:\n%s' % exc_now)
            self.exception_baseline = exc_now       # re-baseline so each cycle reports its own delta
        # Our own reboot legitimately logs the member leaving and rejoining (user.crit
        # 'Member N ... has left/joined the stack'); only the fatal set below counts.
        hits = sorted(set(FATAL_RE.findall(self.log_tail(driver))))
        if hits:
            problems.append('fatal signatures in `show log tail`: %s' % hits)
        boot_hits = sorted(set(FATAL_RE.findall(boot_text)))
        if boot_hits:
            problems.append('fatal signatures in the target boot capture: %s' % boot_hits)
        rec['problems'] = problems
        if problems:
            self.collect_evidence(driver, rec, '; '.join(problems), target=target, light=True)
            return 'FAIL', '; '.join(problems), rec
        return 'PASS', 'member %s rebooted (Expected), back Ready in %.0fs%s' % (
            target_id, rec['all_ready_s'],
            ', failover %.1fs' % rec['failover_s'] if rec.get('failover_s') else ''), rec

    def refresh_master(self, driver):
        try:
            st = self.show_stack(driver)
            if st['master']:
                self.master_id = st['master']
        except Exception:
            pass

    def collect_evidence(self, driver, rec, why, target=None, light=False):
        """Best effort, never raises.  Everything lands in the framework transcripts plus
        an evidence-<cycle>.txt beside the campaign log."""
        self.log('  !! collecting evidence: %s' % why)
        path = 'evidence-cycle%03d.txt' % rec['n']
        cmds = ['show stack', 'show stack detail', 'show reboot history', 'show exception log',
                'show log tail 300']          # `| tail` is % Invalid input on this build
        if not light:
            cmds += ['show system', 'show version', 'show file systems', 'show cpu',
                     'show memory', 'show log permanent tail 200']
        with open(path, 'a') as fh:
            fh.write('===== %s  cycle %d  %s =====\n' % (ts(), rec['n'], why))
            for c in cmds:
                try:
                    out = driver.cmd(c, maxWait=180)
                except Exception as exc:
                    out = '<< %s raised %r >>' % (c, exc)
                fh.write('\n##### %s\n%s\n' % (c, out))
            if target is not None:
                fh.write('\n##### boot capture on %s (%s)\n%s\n' % (
                    target.name, target.tty, target.console.buffer or ''))
        rec['evidence'] = path
        self.log('  evidence -> %s' % path)

    # ---- main loop -----------------------------------------------------------
    def run(self):
        a = self.args
        for n in range(1, a.cycles + 1):
            t0 = time.time()
            self.log('-' * 78)
            self.log('cycle %d/%d  (%s mode)' % (n, a.cycles, a.mode))
            try:
                verdict, detail, rec = self.cycle(n)
            except Unreadable as exc:
                verdict, detail, rec = 'UNMEASURED', str(exc), {'n': n}
            except Exception as exc:
                verdict, detail, rec = 'UNMEASURED', 'cycle raised %r' % exc, {'n': n}
                self.log(traceback.format_exc())
            finally:
                self.stop_threads()
            self.counts[verdict] += 1
            rec.update(verdict=verdict, detail=detail, seconds=round(time.time() - t0, 1))
            self.cycles.append(rec)
            self.log('cycle %3d/%d  %-10s %6.0fs  pass=%d fail=%d unmeas=%d  master=%s' % (
                n, a.cycles, verdict, rec['seconds'], self.counts['PASS'], self.counts['FAIL'],
                self.counts['UNMEASURED'], self.master_id))
            self.log('    -> %s' % detail)
            self.progress(n, verdict)
            if verdict == 'UNMEASURED':
                # get every console back to a known state before the next cycle
                for m in self.members:
                    try:
                        self.login(m, timeout=300)
                    except Exception as exc:
                        self.log('  (re-login on %s failed: %s)' % (m.name, str(exc)[:100]))
                try:
                    self.refresh_master(self.members[0])
                except Exception:
                    pass
            if n < a.cycles:
                time.sleep(a.settle)
        self.log('=' * 78)
        self.log('RESULT  pass=%d fail=%d unmeasured=%d  (%.1f h)' % (
            self.counts['PASS'], self.counts['FAIL'], self.counts['UNMEASURED'],
            (time.time() - self.started) / 3600))
        try:
            st = self.show_stack(self.by_id[self.master_id])
            self.log('final stack state: %s\n%s' % ('FULL' if self.is_full(st) else 'NOT FULL', st['raw'].strip()))
        except Exception as exc:
            self.log('final stack state: unreadable (%s)' % exc)
        return 0 if self.counts['FAIL'] == 0 and self.counts['UNMEASURED'] == 0 else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--mode', choices=('member', 'master'), required=True)
    ap.add_argument('--setup', default='/home/st-art/st-art/configs/tb470.setup')
    ap.add_argument('--stack', default='stk_a')
    ap.add_argument('--cycles', type=int, default=300)
    ap.add_argument('--case-id', default=None, help='campaign log prefix; default 38377 (member) / 38376 (master)')
    ap.add_argument('--member', default=None, help='member mode: pin one backup ID instead of rotating')
    ap.add_argument('--settle', type=float, default=60.0, help='seconds between cycles')
    ap.add_argument('--boot-timeout', type=float, default=900.0, help='target console must show login: within')
    ap.add_argument('--ready-timeout', type=float, default=900.0, help='whole stack Ready within')
    ap.add_argument('--failover-timeout', type=float, default=180.0, help='master mode: new master readable within')
    args = ap.parse_args()
    c = Campaign(args)
    try:
        c.bind()
    except SystemExit as exc:
        c.log(str(exc))
        return 2
    except Exception:
        c.log('ABORT during bind:\n' + traceback.format_exc())
        return 2
    try:
        return c.run()
    finally:
        c.stop_threads()
        c.logf.close()


if __name__ == '__main__':
    sys.exit(main())
