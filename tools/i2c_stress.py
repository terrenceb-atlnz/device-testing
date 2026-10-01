#!/usr/bin/env python3
"""IE520 i2c stress -- interleave the two bus-taxing show commands N times each.

    setsid nohup ./i2c_stress.py /dev/uN [-n 300] [--baud 115200] \
        > i2c-stress.stdout 2>&1 < /dev/null &

STANDALONE variant: no framework, no .setup file. Needs python3 + pyserial on
the testbox, and read access to the console device. Run it from a FRESH dated
directory -- the evidence log and raw transcript are written to the CWD.

WHAT IT DOES
  Interleaves, N times each (default 300):
      show platform port                  <- the proven single-command
                                             reproducer: locked a unit hosting
                                             faulty AT-SPTXc A10217F213300006
                                             at iteration 1, +2.6 s (twice)
      show system pluggable diagnostics   <- DDM A2-page read of every
                                             DDM-capable module
  Alternating them maximises mux-channel switching on the IE520's shared
  mv64xxx controller + 28-port sfp-i2c-mux, on top of the kernel's own
  background DDM poller. Provenance: ~/i2c_evidence.log sections 1, 14, 15
  (2026-08-19/20 campaign, bench tb470).

DETECTION (IE520-specific, all three checked in every read):
  * the kernel printk 'i2c i2c-0: mv64xxx: I2C bus locked' -- in-band only on
    the unit's OWN console, which is why this drives the DUT console directly
  * a command that never returns a prompt (silent wedge -- backup-role events
    in the campaign printed nothing before resetting)
  * a boot banner (BootROM / U-Boot / 'Bootloader ... loaded') = watchdog reset

ON A LOCK: stop sending immediately (stop-on-first-lock), record the event,
watch passively through the ~42 s watchdog reset and the reboot (up to 15 min
-- NEVER power-cycle: a netbooting unit or one mid-SPIFlash-write looks dead
and is not), re-login, capture 'show reboot history' as the anchor, exit 1.

Read-only 'show' commands only. Nothing is written to the DUT.
"""
import argparse
import os
import re
import subprocess
import sys
import time

import serial

CMD_A = 'show platform port'
CMD_B = 'show system pluggable diagnostics'
CMD_TIMEOUT = 90.0          # ceiling, not a delay: send() returns on prompt

# 'awplus#', 'awplus(config)#', etc.
PROMPT_RE = re.compile(r'[\w.-]+(?:\([\w -]+\))?#[ \t]*$')
PROMPT_ANYWHERE_RE = re.compile(r'[\w.-]+(?:\([\w -]+\))?#[ \t]*(?:\r?\n|$)')

# The smoking gun. Full line: 'i2c i2c-0: mv64xxx: I2C bus locked, block: 1,
# time_left: 0'. Matched loosely in case the controller instance differs.
LOCK_RE = re.compile(r'I2C bus locked', re.I)
# Watchdog reset -> bootloader banner. 9.1.0 leaks raw U-Boot; the pauld dev
# build prints the AT form; BootROM precedes both.
RESET_RE = re.compile(r'BootROM \d|U-Boot 20|Bootloader \S+ loaded')
LOGIN_RE = re.compile(r'login:\s*$')


class ConsoleError(Exception):
    pass


class Console:
    """AW+ console driver tolerating async output. Derived from the proven
    failover-300/console.py (same rules): a command is finished when a prompt
    has appeared AFTER the echoed command and the port has gone quiet; async
    chatter in between is captured, not fatal. Every byte read is written to
    the transcript as it arrives -- a timeout must not discard the bytes
    needed to diagnose it."""

    def __init__(self, port, transcript, baud, user, password):
        self.port = port
        self.user, self.password = user, password
        self._t = open(transcript, 'a', buffering=1, errors='replace')
        self._t.write('\n===== opened {} at {} =====\n'.format(
            port, time.strftime('%Y-%m-%d %H:%M:%S')))
        # Opening the port drops DTR, which the IE520 sees as a BREAK; the
        # next character would be eaten as a sysrq key. -hupcl stops the drop.
        os.system('stty -F {} -hupcl 2>/dev/null'.format(os.path.realpath(port)))
        self.s = serial.Serial(port, baud, timeout=0.2)

    def _read_some(self):
        chunk = self.s.read(4096)
        if not chunk:
            return ''
        text = chunk.decode(errors='replace')
        self._t.write(text)
        return text

    def read_until_quiet(self, quiet=0.8, timeout=30.0, need_prompt=True):
        buf = ''
        deadline = time.time() + timeout
        last = time.time()
        while time.time() < deadline:
            text = self._read_some()
            if text:
                buf += text
                last = time.time()
                if '--More--' in text:
                    self.s.write(b' ')
                continue
            if time.time() - last >= quiet:
                if not need_prompt or PROMPT_ANYWHERE_RE.search(buf):
                    return buf
                # No prompt yet: silence is not an outcome. Only the prompt
                # or the timeout ends the read.
            time.sleep(0.05)
        return buf

    def send(self, line, quiet=0.8, timeout=60.0, need_prompt=True):
        self._t.write('\n>>> {}\n'.format(line))
        self.s.write((line + '\r').encode())
        return self.read_until_quiet(quiet=quiet, timeout=timeout,
                                     need_prompt=need_prompt)

    def wait_for(self, regexes, timeout):
        """Passive watch: read (logging everything) until any regex matches.
        Returns (name_of_match, buffer) or (None, buffer). Sends NOTHING."""
        buf = ''
        deadline = time.time() + timeout
        while time.time() < deadline:
            text = self._read_some()
            if text:
                buf += text
                for name, rx in regexes:
                    if rx.search(buf):
                        return name, buf
            else:
                time.sleep(0.2)
        return None, buf

    def login(self, timeout=60.0):
        self.s.write(b'\r')
        out = self.read_until_quiet(quiet=1.0, timeout=10.0, need_prompt=False)
        if 'login:' in out[-200:].lower():
            self.s.write((self.user + '\r').encode())
            self.read_until_quiet(quiet=1.0, timeout=15.0, need_prompt=False)
            self.s.write((self.password + '\r').encode())
            out = self.read_until_quiet(quiet=1.2, timeout=timeout,
                                        need_prompt=False)
        if 'new password' in out.lower():
            raise ConsoleError(
                'console is in the forced password-change dialog; refusing '
                'to commit a value. Tail: {!r}'.format(out[-300:]))
        if not PROMPT_RE.search(out.rstrip()[-120:]):
            self.s.write(b'enable\r')
            out = self.read_until_quiet(quiet=1.0, timeout=20.0,
                                        need_prompt=False)
        if not PROMPT_ANYWHERE_RE.search(out):
            raise ConsoleError('no privileged prompt on {}. Tail: {!r}'.format(
                self.port, out[-300:]))
        # Both commands below are exec-only: a console parked at host(config)#
        # answers them "% Invalid input" (console.py set_monitor(), 2026-10-02).
        if '(' in (re.findall(r'[\w.-]+(?:\([\w -]+\))?#', out) or [''])[-1]:
            self.send('end', quiet=0.6, timeout=15.0)
        self.send('terminal length 0', quiet=0.6, timeout=15.0)
        self.send('terminal no monitor', quiet=0.6, timeout=15.0)
        # NB: kernel printk (the i2c lock line) is printed BELOW the AW+ log
        # layer and survives 'terminal no monitor' -- that is what we rely on.
        return True

    def cmd(self, line, quiet=0.8, timeout=60.0):
        raw = self.send(line, quiet=quiet, timeout=timeout)
        lines = raw.splitlines()
        if lines and line.strip() and line.strip() in lines[0]:
            lines = lines[1:]
        while lines and PROMPT_RE.search(lines[-1].rstrip()):
            lines.pop()
        return '\n'.join(lines).strip()

    def close(self):
        try:
            self.s.close()
        finally:
            self._t.write('\n===== closed {} at {} =====\n'.format(
                self.port, time.strftime('%Y-%m-%d %H:%M:%S')))
            self._t.close()


class Evidence:
    def __init__(self, path):
        self.f = open(path, 'a', buffering=1, errors='replace')

    def log(self, msg):
        line = '{}  {}'.format(time.strftime('%Y-%m-%d %H:%M:%S'), msg)
        print(line, flush=True)
        self.f.write(line + '\n')

    def block(self, title, body):
        self.log('----- {} -----'.format(title))
        self.f.write(body.rstrip() + '\n')
        self.log('----- end {} -----'.format(title))


def port_is_held(port):
    """True if another process holds the console. Never share a serial port:
    two holders interleave in both directions and read as a hardware fault."""
    real = os.path.realpath(port)
    try:
        rc = subprocess.call(['fuser', real], stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        return rc == 0
    except OSError:
        return False      # fuser unavailable; proceed, the lock files remain


def scan(raw):
    """Classify one read. Returns 'lock', 'reset', or None."""
    if LOCK_RE.search(raw):
        return 'lock'
    if RESET_RE.search(raw):
        return 'reset'
    return None


def lock_protocol(c, ev, iteration, command, kind):
    """Stop-on-first-lock: record, ride out the watchdog reset passively,
    re-login, anchor against reboot history. Returns the exit code."""
    ev.log('*** {} DETECTED at iteration {}, in-flight command: {!r} '
           '(epoch {:.3f}) ***'.format(kind.upper(), iteration, command,
                                       time.time()))
    ev.log('stop-on-first-lock: no further commands. Watching passively '
           'through the ~42 s watchdog reset and reboot (up to 15 min). '
           'Do NOT power-cycle.')
    watches = [('reset', RESET_RE), ('login', LOGIN_RE)]
    t0 = time.time()
    if kind != 'reset':
        name, _ = c.wait_for(watches, timeout=180)
        if name == 'reset':
            ev.log('boot banner seen +{:.1f} s after detection '
                   '(watchdog-consistent)'.format(time.time() - t0))
        elif name is None:
            ev.log('!! no boot banner within 180 s -- unit may be wedged '
                   'without self-recovery; continuing to watch for login')
    name, _ = c.wait_for([('login', LOGIN_RE)], timeout=900)
    if name != 'login':
        ev.log('!! WEDGED, NO SELF-RECOVERY: no login banner within 15 min. '
               'Leaving the unit exactly as it is for a human. Console '
               'transcript holds everything received.')
        return 2
    ev.log('login banner seen +{:.1f} s after detection; re-logging in for '
           'the post-mortem reads'.format(time.time() - t0))
    try:
        c.login()
        ev.block('post-event show reboot history',
                 c.cmd('show reboot history', timeout=60))
        ev.block('post-event ' + CMD_B, c.cmd(CMD_B, timeout=60))
    except ConsoleError as exc:
        ev.log('!! post-event login failed: {}'.format(exc))
    return 1


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('port', help='console device, e.g. /dev/u5')
    p.add_argument('-n', '--iterations', type=int, default=300,
                   help='iterations PER COMMAND (default 300)')
    p.add_argument('--baud', type=int, default=115200,
                   help='IE520 consoles run 9600 or 115200; the port is '
                        'opened once and never renegotiated (default 115200)')
    p.add_argument('--user', default='manager')
    p.add_argument('--password', default='friend')
    args = p.parse_args()

    tag = os.path.basename(args.port)
    stamp = time.strftime('%Y%m%d-%H%M%S')
    ev = Evidence('i2c-stress-{}-{}.evidence.log'.format(tag, stamp))
    ev.log('i2c_stress.py starting: port={} baud={} iterations={}x2 '
           'commands=[{!r}, {!r}]'.format(args.port, args.baud,
                                          args.iterations, CMD_A, CMD_B))

    if port_is_held(args.port):
        ev.log('ABORT: {} is held by another process (fuser). Never share a '
               'serial port.'.format(args.port))
        return 2

    c = Console(args.port, 'i2c-stress-{}-{}.console.log'.format(tag, stamp),
                args.baud, args.user, args.password)
    try:
        try:
            c.login()
        except ConsoleError as exc:
            ev.log('ABORT: {}'.format(exc))
            return 2

        # Baseline: self-contained evidence, and the DDM Vcc census doubles
        # as the known defect screen (faulty ...006 read Vcc 3.4167 V, above
        # the 3.4000 High-warning threshold).
        for title, command in (('show system', 'show system'),
                               ('show stack', 'show stack'),
                               ('pluggable inventory', 'show system pluggable'),
                               ('DDM census / Vcc screen', CMD_B),
                               ('reboot history baseline',
                                'show reboot history')):
            out = c.cmd(command, timeout=60)
            ev.block('baseline ' + title, out or '(empty)')
            if command == 'show stack' and 'Standalone unit' not in out:
                ev.log('!! WARNING: unit does not read as a standalone unit; '
                       'this run assumes no stack. Proceeding, but a relayed '
                       'session would miss the in-band kernel printk.')

        empty = 0
        locks_exit = None
        for i in range(1, args.iterations + 1):
            for command in (CMD_A, CMD_B):
                t0 = time.time()
                raw = c.send(command, timeout=CMD_TIMEOUT)
                took = time.time() - t0
                kind = scan(raw)
                prompted = bool(PROMPT_ANYWHERE_RE.search(raw))
                if kind:
                    locks_exit = lock_protocol(c, ev, i, command, kind)
                    break
                if not prompted:
                    ev.log('iter {:>3}  {!r}  NO PROMPT after {:.1f} s -- '
                           'silent-wedge suspicion, watching'.format(
                               i, command, took))
                    name, buf = c.wait_for(
                        [('lock', LOCK_RE), ('reset', RESET_RE),
                         ('prompt', PROMPT_ANYWHERE_RE)], timeout=120)
                    if name in ('lock', 'reset'):
                        locks_exit = lock_protocol(c, ev, i, command, name)
                        break
                    if name != 'prompt':
                        locks_exit = lock_protocol(c, ev, i, command, 'wedge')
                        break
                    ev.log('iter {:>3}  {!r}  prompt arrived late (+{:.1f} s '
                           'total) -- continuing'.format(
                               i, command, time.time() - t0))
                body = len(raw.strip())
                if body < 40:
                    # Evidence discipline: an empty read that produced a
                    # prompt is UNMEASURED as a stressor, not a pass.
                    empty += 1
                    ev.log('iter {:>3}  {!r}  {:.2f} s  !! EMPTY RESPONSE '
                           '({} bytes)'.format(i, command, took, body))
                else:
                    ev.log('iter {:>3}  {!r}  {:.2f} s  ok ({} bytes)'.format(
                        i, command, took, body))
            if locks_exit is not None:
                return locks_exit

        ev.block('final pluggable inventory',
                 c.cmd('show system pluggable', timeout=60) or '(empty)')
        ev.block('final reboot history',
                 c.cmd('show reboot history', timeout=60) or '(empty)')
        ev.log('COMPLETE: {} iterations of each command, 0 i2c events, '
               '{} empty responses.'.format(args.iterations, empty))
        return 0
    finally:
        c.close()


if __name__ == '__main__':
    sys.exit(main())
