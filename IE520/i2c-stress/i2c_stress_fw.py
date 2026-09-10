#!/usr/bin/env python3
"""IE520 i2c stress -- FRAMEWORK variant (thin wrapper over ATSwitch.Switch).

    cd <fresh dated run dir>       # the framework writes console logs in CWD
    PYTHONPATH=/home/st-art setsid nohup python3 ./i2c_stress_fw.py /dev/uN \
        [-n 300] > i2c-stress.stdout 2>&1 < /dev/null &

Same test as i2c_stress.py (the standalone twin -- see its docstring for the
full provenance: ~/i2c_evidence.log sections 1, 14, 15): interleave
    show platform port                    (the proven +2.6 s reproducer)
    show system pluggable diagnostics     (DDM A2-page reads)
N times each against the shared mv64xxx + 28-port sfp-i2c-mux, stopping on
the first lock, riding out the watchdog reset passively, hands-off recovery.

This variant borrows only the framework's console driver (no ATTestSet
machinery, no .setup file): Switch(devicePath) is constructed directly, the
way the staged legacy scripts do it. Notes that cost hours before:
  * TBv4 testboxes (/etc/network/interfaces exists) need the FULL device path
    ('/dev/u5'), never an integer.
  * The framework opens the port at its default rate and never renegotiates.
    If this console runs at 9600, use the standalone variant's --baud.
  * ATSwitch.cmd() answers a console failure with sys.exit(2), and SystemExit
    is NOT an Exception -- every cmd here is wrapped for BaseException, and a
    SystemExit mid-run is treated as wedge evidence, not a crash.
  * Every cmd() passes an explicit maxWait: the inherited default is a flat
    1800 s wall-clock ('INFINITE LOOP DETECTED' / 'WAITED TOO LONG'
    are that timeout, never a diagnosis).
  * Per-run log names below, because the framework overwrites its logs in
    CWD -- run each campaign from its own directory anyway.

Read-only 'show' commands only. Nothing is written to the DUT.
"""
import argparse
import os
import re
import subprocess
import sys
import time

try:
    from framework.ATDrivers import ATSwitch
except ImportError:
    print('Could not import the framework. Run with PYTHONPATH=/home/st-art')
    print('(or symlink the read-only /home/st-art/framework into the CWD --')
    print(' NEVER write into /home/st-art/framework itself).')
    sys.exit(2)

CMD_A = 'show platform port'
CMD_B = 'show system pluggable diagnostics'
CMD_MAXWAIT = 90

LOCK_RE = re.compile(r'I2C bus locked', re.I)
RESET_RE = re.compile(r'BootROM \d|U-Boot 20|Bootloader \S+ loaded')

# Framework read() takes plain substrings, not regexes.
REBOOT_WATCH_STRINGS = ['login:', 'BootROM']


class Evidence:
    def __init__(self, path):
        self.f = open(path, 'a', buffering=1, errors='replace')

    def log(self, msg):
        line = '{}  {}'.format(time.strftime('%Y-%m-%d %H:%M:%S'), msg)
        print(line, flush=True)
        self.f.write(line + '\n')

    def block(self, title, body):
        self.log('----- {} -----'.format(title))
        self.f.write((body or '(empty)').rstrip() + '\n')
        self.log('----- end {} -----'.format(title))


def port_is_held(port):
    real = os.path.realpath(port)
    try:
        rc = subprocess.call(['fuser', real], stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        return rc == 0
    except OSError:
        return False


def scan(text):
    if text and LOCK_RE.search(text):
        return 'lock'
    if text and RESET_RE.search(text):
        return 'reset'
    return None


def safe_cmd(sw, ev, command, max_wait=CMD_MAXWAIT):
    """cmd() that can never kill the run. Returns (output, error_or_None).
    SystemExit from the console layer is caught and reported as an error."""
    try:
        return sw.cmd(command, maxWait=max_wait), None
    except BaseException as exc:                      # incl. SystemExit
        return '', '{}: {}'.format(type(exc).__name__, exc)


def lock_protocol(sw, ev, iteration, command, kind):
    """Stop-on-first-lock: record, watch passively through the ~42 s watchdog
    reset and reboot (up to 15 min), re-login, anchor on reboot history."""
    ev.log('*** {} DETECTED at iteration {}, in-flight command: {!r} '
           '(epoch {:.3f}) ***'.format(kind.upper(), iteration, command,
                                       time.time()))
    ev.log('stop-on-first-lock: no further commands. Watching passively; '
           'do NOT power-cycle.')
    t0 = time.time()
    reader = sw.read(900, REBOOT_WATCH_STRINGS)
    while not reader.has_finished():
        time.sleep(0.5)
    buf = sw.console.preReadBuf + sw.console.buffer
    ev.block('reboot watch transcript tail', buf[-4000:])
    if LOCK_RE.search(buf) and kind != 'lock':
        ev.log('i2c lock printk confirmed in the reboot-watch buffer')
    if 'login:' not in buf:
        ev.log('!! WEDGED, NO SELF-RECOVERY: no login banner within 15 min. '
               'Leaving the unit exactly as it is for a human.')
        return 2
    ev.log('login banner seen +{:.1f} s after detection; re-logging in for '
           'the post-mortem reads'.format(time.time() - t0))
    try:
        sw.mode('#')
        out, err = safe_cmd(sw, ev, 'show reboot history')
        ev.block('post-event show reboot history', err or out)
        out, err = safe_cmd(sw, ev, CMD_B)
        ev.block('post-event ' + CMD_B, err or out)
    except BaseException as exc:
        ev.log('!! post-event login failed: {}: {}'.format(
            type(exc).__name__, exc))
    return 1


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('port', help='console device, e.g. /dev/u5 (full path)')
    p.add_argument('-n', '--iterations', type=int, default=300,
                   help='iterations PER COMMAND (default 300)')
    p.add_argument('-v', '--verbose', action='store_true',
                   help='echo console traffic (Switch debug)')
    args = p.parse_args()

    tag = os.path.basename(args.port)
    stamp = time.strftime('%Y%m%d-%H%M%S')
    ev = Evidence('i2c-stress-{}-{}.evidence.log'.format(tag, stamp))
    ev.log('i2c_stress_fw.py starting: port={} iterations={}x2 '
           'commands=[{!r}, {!r}]'.format(args.port, args.iterations,
                                          CMD_A, CMD_B))

    if port_is_held(args.port):
        ev.log('ABORT: {} is held by another process (fuser). Never share a '
               'serial port.'.format(args.port))
        return 2

    sw = ATSwitch.Switch(args.port, debug=args.verbose)
    # Per-run console log name; the framework's default names collide and
    # overwrite across runs in one CWD.
    sw.logFileName = sw.console.logFileName = \
        'i2c-stress-{}-{}.device.log'.format(tag, stamp)

    try:
        sw.mode('#')
    except BaseException as exc:
        ev.log('ABORT: could not reach a privileged prompt on {}: {}: {}'
               .format(args.port, type(exc).__name__, exc))
        return 2
    out, err = safe_cmd(sw, ev, 'terminal length 0', max_wait=15)
    if err:
        ev.log('!! terminal length 0 failed ({}); relying on the driver\'s '
               'pager handling'.format(err))

    # Baseline block -- self-contained evidence; the DDM Vcc census doubles as
    # the known defect screen (faulty ...006 read Vcc 3.4167 V > 3.4000 High).
    for title, command in (('show system', 'show system'),
                           ('show stack', 'show stack'),
                           ('pluggable inventory', 'show system pluggable'),
                           ('DDM census / Vcc screen', CMD_B),
                           ('reboot history baseline', 'show reboot history')):
        out, err = safe_cmd(sw, ev, command)
        ev.block('baseline ' + title, err or out)
        if command == 'show stack' and out and 'Standalone unit' not in out:
            ev.log('!! WARNING: unit does not read as a standalone unit; '
                   'this run assumes no stack.')

    empty = 0
    for i in range(1, args.iterations + 1):
        for command in (CMD_A, CMD_B):
            t0 = time.time()
            out, err = safe_cmd(sw, ev, command)
            took = time.time() - t0
            kind = scan(out) or scan(sw.console.preCmdBuf)
            if kind:
                return lock_protocol(sw, ev, i, command, kind)
            if err:
                ev.log('iter {:>3}  {!r}  console error after {:.1f} s '
                       '({}) -- silent-wedge suspicion, watching'.format(
                           i, command, took, err))
                return lock_protocol(sw, ev, i, command, 'wedge')
            if len(out.strip()) < 40:
                # Evidence discipline: an empty read is UNMEASURED as a
                # stressor, not a pass.
                empty += 1
                ev.log('iter {:>3}  {!r}  {:.2f} s  !! EMPTY RESPONSE'.format(
                    i, command, took))
            else:
                ev.log('iter {:>3}  {!r}  {:.2f} s  ok ({} bytes)'.format(
                    i, command, took, len(out)))

    out, err = safe_cmd(sw, ev, 'show system pluggable')
    ev.block('final pluggable inventory', err or out)
    out, err = safe_cmd(sw, ev, 'show reboot history')
    ev.block('final reboot history', err or out)
    ev.log('COMPLETE: {} iterations of each command, 0 i2c events, '
           '{} empty responses.'.format(args.iterations, empty))
    return 0


if __name__ == '__main__':
    sys.exit(main())
