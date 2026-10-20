#!/usr/bin/env python3
"""awshell.py <tty> <baud> <transcript> [--member N] [--timeout S] [--keep-shell] CMD [CMD ...]

Run shell commands inside an AlliedWare Plus `start-shell` root shell on one console,
print each command with its output, then leave the console back at the AW+ exec prompt.

Why it exists: an AW+ switch is Linux underneath, and things the CLI does not expose are
readable and writable there -- the hwmon sensor tree (`/sys/class/hwmon/hwmonN/tempN_max`),
`/proc`, flash contents. The CLI surface is not the device's surface. The maintained console
drivers (ckcon, cfg, ...) cannot do this: console.PROMPT_RE matches `host#` / `host(mode)#`
and never the shell's `[root@host flash]#`, so every shell command runs to its full timeout
and the driver then abandons the batch.

    awshell.py /dev/u2 115200 /tmp/ck/console-u2.log \
        'ls /sys/class/hwmon/' 'cat /sys/class/hwmon/hwmon0/name'

Options:
  --member N     `start-shell N` -- the shell of stack member N (a member shell is NOT root)
  --timeout S    per-command timeout in seconds (default 30); also env CKSHTO
  --keep-shell   do not `exit` back to the CLI (for a caller that will do it itself).
                 Without it the console is ALWAYS returned to exec, even after a failure.

  CK_USER / CK_PASSWORD set the login credentials (default manager / friend).

🔴 This is root on the DEVICE UNDER TEST. STANDING-ORDERS §1 puts device state in play and §4
reserves root on the TESTBOX -- they are not the same thing, and this tool only ever reaches
the device. It is still root: a write here is not in `show running-config`, so `rcdiff.py`
cannot see it and cannot prove you put it back. Read every value you are about to change
first, record the exact bytes, and read it back after restoring.

Exit codes: 0 every command ran · 2 usage · 3 no shell (`start-shell` refused, or the device
lacks the ACCESS/FULL feature) · 4 a command did not return the shell prompt · 5 the console
did not come back to the AW+ exec prompt (the serious one: say so in the log).
"""
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

USAGE = ("usage: awshell.py <tty> <baud> <transcript> [--member N] [--timeout S] "
         "[--keep-shell] CMD [CMD ...]")

# The shell prompt: `[root@awplus flash]#`, or `]$` for a non-root member shell.
SHELL_RE = re.compile(r'\][#$]\s*$')


def main(argv):
    if len(argv) < 4 or argv[1] in ('-h', '--help'):
        print(__doc__.strip() if argv[1:2] in (['-h'], ['--help']) else USAGE)
        return 0 if argv[1:2] in (['-h'], ['--help']) else 2
    try:
        tty, baud, transcript = argv[1], int(argv[2]), argv[3]
    except ValueError as e:
        print(USAGE)
        print('bad argument: %s' % e)
        return 2

    args = argv[4:]
    member = None
    keep_shell = False
    timeout = float(os.environ.get('CKSHTO', '30'))
    while args and args[0].startswith('--'):
        opt = args.pop(0)
        if opt == '--keep-shell':
            keep_shell = True
        elif opt in ('--member', '--timeout'):
            if not args:
                print(USAGE)
                return 2
            val = args.pop(0)
            if opt == '--member':
                member = val
            else:
                timeout = float(val)
        else:
            print(USAGE)
            print('unknown option %r' % opt)
            return 2
    if not args:
        print(USAGE)
        print('no commands given')
        return 2
    for cmd in args:
        if '\n' in cmd or '\r' in cmd:
            print(USAGE)
            print('a command may not contain a newline: %r' % cmd)
            return 2

    import console

    c = console.Console(tty, transcript, baud=baud)
    rc = 0
    in_shell = False
    try:
        c.login(monitor=False)
        out = c.send('start-shell' + ('' if member is None else ' ' + member),
                     quiet=1.5, timeout=30.0, need_prompt=False)
        if not SHELL_RE.search(out.rstrip()):
            print('NO SHELL -- `start-shell%s` did not give a shell prompt.'
                  % ('' if member is None else ' ' + member))
            print('tail: %r' % out[-300:])
            return 3
        in_shell = True
        print('SHELL  %s' % out.rstrip().splitlines()[-1].strip())

        for cmd in args:
            buf = shell_cmd(c, cmd, timeout)
            print('\n>>> %s' % cmd)
            if buf is None:
                print('!! NO SHELL PROMPT within %.0fs -- command abandoned' % timeout)
                rc = 4
                # Try to get the shell's attention back before the next command.
                c.s.write(b'\x03')
                time.sleep(0.5)
                c._read_some()
                continue
            print(trim(buf, cmd))
    finally:
        if in_shell and not keep_shell:
            back = leave_shell(c)
            if not back:
                print('\n!! THE CONSOLE DID NOT RETURN TO THE AW+ EXEC PROMPT')
                rc = 5
            else:
                print('\nEXEC   %s' % back)
        try:
            if not keep_shell:
                c.monitor_off()
        except Exception:
            pass
        c.close()
    return rc


def shell_cmd(c, line, timeout):
    """One shell command. Returns the raw buffer once the `]#` / `]$` prompt is back,
    or None if it never came (a lost quote leaves the shell at its `> ` continuation)."""
    c._t.write('\n>>> %s\n' % line)
    c.s.write((line + '\r').encode())
    buf = ''
    deadline = time.time() + timeout
    while time.time() < deadline:
        buf += c._read_some()
        if SHELL_RE.search(buf.rstrip()):
            time.sleep(0.1)
            buf += c._read_some()
            return buf
        time.sleep(0.03)
    return None


def leave_shell(c, tries=3):
    """`exit` out of the shell and confirm the AW+ exec prompt. Returns the prompt text,
    or '' if it never appeared."""
    for _ in range(tries):
        out = c.send('exit', quiet=1.0, timeout=20.0, need_prompt=False)
        tail = out.rstrip()
        if console_prompt(tail):
            return console_prompt(tail)
        if not SHELL_RE.search(tail):
            # Neither a shell nor a recognisable CLI prompt: one bare CR, then look again.
            out = c.send('', quiet=1.0, timeout=10.0, need_prompt=False)
            if console_prompt(out.rstrip()):
                return console_prompt(out.rstrip())
    return ''


def console_prompt(tail):
    m = re.search(r'([\w.-]+(?:\([\w -]+\))?#)[ \t]*$', tail)
    return m.group(1) if m else ''


def trim(buf, line):
    lines = buf.splitlines()
    if lines and line.strip() and line.strip() in lines[0]:
        lines = lines[1:]
    while lines and SHELL_RE.search(lines[-1].rstrip()):
        lines.pop()
    return '\n'.join(lines).rstrip()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
