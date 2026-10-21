#!/usr/bin/env python3
"""Drive a device's OWN telnet / SSH CLIENT outward from its console, and grade what happened.

    devclient.py <tty> <baud> <transcript> --proto telnet|ssh --target HOST
                 [--port N] [--family ip|ipv6] [--user U] [--password P] [--cmd CMD]... [--hold S]
                 [--expect priv|user|fail|refused] [--no-logout] [--timeout S]
                 [--login-timeout S] [--accept-hostkey]

<tty>, <baud> and <transcript> are the usual console-tool arguments, e.g.
    /dev/u2 115200 /tmp/<campaign>/console-u2.log

It is the OUTBOUND twin of `netlogin.py`: that one drives the testbox's telnet/ssh client
INTO a device, this one drives the device's own client OUT to a far end.  A "Telnet Client"
or "SSH Client" case is about the device ORIGINATING a session, so no `show` command can
grade it and `netlogin.py` tests the wrong direction entirely.

What it does, in order:
  1. logs in on the console (console.py, CK_USER / CK_PASSWORD) and reaches exec;
  2. records the LOCAL prompt, so the remote session can be told apart from the local one;
  3. sends the client command (`telnet [ip|ipv6] <target> [PORT]` /
     `ssh [ip|ipv6] [port N] [user U] <target>`);
  4. answers the far end's login and password prompts, and an ssh host-key question with
     `--accept-hostkey`;
  5. runs each --cmd on the FAR END and prints its output;
  6. holds the session open for --hold seconds (so the far end's `show users` can be read
     from another console while it is live);
  7. leaves with `exit`, and if that does not come back, with the telnet escape (Ctrl-] quit)
     or ssh's `~.`;
  8. confirms the console is back at the LOCAL prompt and leaves it at exec.

Output: labelled blocks for each phase, then one line
    CLIENT RESULT: PRIV|USER|FAIL|REFUSED|EXEC|TIMEOUT  proto=  target=  user=  seconds=  prompt=
then one block per --cmd.

Exit: 0 remote privileged `#`, 1 remote unprivileged `>`, 2 the far end refused the
credential, 3 the connection was refused / unreachable (a first-class result: it is the
control leg of an on/off arc), 4 nothing recognisable / timed out, 5 --expect did not match,
6 usage, 7 the console could not be returned to its local prompt (the serious one).
With --expect, 0 means the outcome matched and 5 that it did not.

Traps this tool exists to handle:
  * An AW+ login lands at privilege 1 (`>`) even for a `privilege 15` username, so a client
    session's success is USER, not PRIV (platforms/x960.md 7E.6).
  * Both ends of a bench are often called `awplus`, so the prompt text alone cannot say
    which device you are on.  The privilege character does: the console is at `#` and a
    fresh remote login is at `>`.  Run a `--cmd show system` and compare serial numbers when
    you need proof rather than a heuristic.
  * The password is an argv value, so it is visible in `ps` on the box.  Use a worthless
    credential, as the standing orders require, or --password-stdin.
  * A failed login counts against the far end's lockout.  AW+ locks an account at 5 failures
    with a timer that restarts on each attempt: never retry in a loop.
"""
import argparse, os, re, sys, time

import console

LOGIN_RE    = re.compile(r'(?:[Ll]ogin|[Uu]sername)\s*:\s*$')
PASSWORD_RE = re.compile(r'[Pp]assword\s*:\s*$')
HOSTKEY_RE  = re.compile(r'(?i)Are you sure you want to continue connecting|'
                         r'fingerprint.*\(yes/no')
PROMPT_RE   = re.compile(r'(?:^|\r?\n)([\w.-]+)(?:\([\w -]+\))?([>#])[ \t]*$')
REFUSED_RE  = re.compile(r'(?i)connection refused|unable to connect|no route to host|'
                         r'network is unreachable|host is unreachable|connection timed out|'
                         r'name or service not known|could not resolve|'
                         r'connection closed by remote host|no address associated')
CLOSED_RE   = re.compile(r'(?i)connection closed|connection to .* closed|'
                         r'closed by foreign host')
DENIED_RE   = re.compile(r'(?i)login incorrect|permission denied|authentication fail|'
                         r'access denied|too many authentication failures')


def expect(c, pats, timeout):
    """Read until one of pats (list of (name, regex)) matches. Returns (name|None, buf)."""
    buf = ''
    deadline = time.time() + timeout
    while time.time() < deadline:
        text = c._read_some()
        if text:
            buf += text
            for nm, rx in pats:
                if rx.search(buf.rstrip('\r\n ') if rx is PROMPT_RE else buf):
                    time.sleep(0.2)
                    buf += c._read_some()
                    return nm, buf
        else:
            time.sleep(0.02)
    return None, buf


def block(title, text):
    print('--- %s ---' % title)
    print(text.rstrip('\n'))
    print('--- end %s ---' % title)


def client_command(a):
    # AW+: `telnet [ip|ipv6] <host> [PORT]` and `ssh [ip|ipv6] [port N] [user U] <host> [LINE]`.
    # --family forces the address family explicitly, which is what an "(IPv4)" case wants to
    # exercise rather than leaving the client to choose.
    fam = (' ' + a.family) if a.family else ''
    if a.proto == 'telnet':
        cmd = 'telnet%s %s' % (fam, a.target)
        if a.port:
            cmd += ' %s' % a.port
    else:
        cmd = 'ssh' + fam
        if a.port:
            cmd += ' port %s' % a.port
        if a.user:
            cmd += ' user %s' % a.user
        cmd += ' %s' % a.target
        if a.exec_line:
            # AW+ `ssh ... <HOSTNAME> LINE`: run ONE command on the far end and come
            # straight back.  There is no interactive session, so no prompt to leave.
            cmd += ' %s' % a.exec_line
    return cmd


def main(argv):
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument('tty'); p.add_argument('baud', type=int); p.add_argument('transcript')
    p.add_argument('--proto', required=True, choices=('telnet', 'ssh'))
    p.add_argument('--target', required=True)
    p.add_argument('--port')
    p.add_argument('--family', choices=('ip', 'ipv6'),
                   help="force the AW+ address-family keyword: `telnet ip <host>` / `ssh ipv6 ...`")
    p.add_argument('--user')
    p.add_argument('--password')
    p.add_argument('--password-stdin', action='store_true',
                   help='read the password from stdin instead of argv (it is not in `ps`)')
    p.add_argument('--password-env', metavar='NAME',
                   help='read the password from this environment variable instead of argv. '
                        '`tools/tb` forwards any CK_PASSWORD* / CK_USER* variable to the box '
                        'over stdin and exports it there, so this is the safe way to pass a '
                        'far-end password through the wrapper.')
    p.add_argument('--cmd', action='append', default=[])
    p.add_argument('--exec', dest='exec_line',
                   help='ssh only: the AW+ `ssh ... <host> LINE` form -- run ONE command on the\n'
                        'far end non-interactively and return. Graded EXEC.')
    p.add_argument('--hold', type=float, default=0.0)
    p.add_argument('--timeout', type=float, default=45.0)
    p.add_argument('--login-timeout', type=float, default=30.0)
    p.add_argument('--expect', choices=('priv', 'user', 'fail', 'refused', 'exec'))
    p.add_argument('--no-logout', action='store_true')
    p.add_argument('--accept-hostkey', action='store_true')
    p.add_argument('-h', '--help', action='store_true')
    a = p.parse_args(argv)
    if a.help:
        print(__doc__)
        return 0
    if a.password_env:
        if a.password_env not in os.environ:
            print('devclient: $%s is not set on the box -- refusing to send an empty password'
                  % a.password_env)
            return 6
        a.password = os.environ[a.password_env]
    elif a.password_stdin:
        a.password = sys.stdin.readline().rstrip('\n')
    if (a.password_env or a.password_stdin) and not a.password:
        # An empty password here is never a test: it means the value did not arrive, and
        # sending it costs the far-end account a failed login that re-arms its lockout timer.
        # That is exactly what happened on tb277 2026-10-21 when `tools/tb` forwarded a
        # secret over stdin and so swallowed the password piped in behind it.
        print('devclient: the password arrived EMPTY (%s) -- refusing to send it'
              % ('--password-env ' + a.password_env if a.password_env else '--password-stdin'))
        return 6

    c = console.Console(a.tty, a.transcript, baud=a.baud)
    rc, result, remote_prompt, t0 = 4, 'TIMEOUT', '', time.time()
    local, back, outputs = None, None, []
    try:
        if not c.login(timeout=60.0, monitor=False):
            print('CLIENT RESULT: TIMEOUT  (could not reach the local console prompt)')
            return 7
        c.to_exec()
        local = console.Console._last_prompt(c.send_until_prompt('', timeout=15.0)) or '?'
        print('local console prompt: %s' % local)

        cmd = client_command(a)
        print('client command: %s' % cmd)
        c._t.write('\n>>> %s\n' % cmd)
        c.s.write((cmd + '\r').encode())

        pats = [('refused', REFUSED_RE), ('hostkey', HOSTKEY_RE),
                ('login', LOGIN_RE), ('password', PASSWORD_RE), ('prompt', PROMPT_RE)]
        nm, buf = expect(c, pats, a.login_timeout)
        if nm == 'hostkey' and a.accept_hostkey:
            block('connect', buf)
            c._t.write('\n>>> yes\n'); c.s.write(b'yes\r')
            nm, buf = expect(c, pats, a.login_timeout)
        if nm == 'login':
            block('before the username prompt', buf)
            c._t.write('\n>>> %s\n' % (a.user or ''))
            c.s.write(((a.user or '') + '\r').encode())
            nm, buf = expect(c, pats, a.login_timeout)
        if nm == 'password':
            block('before the password prompt', buf)
            c._t.write('\n>>> <password>\n')
            c.s.write(((a.password or '') + '\r').encode())
            nm, buf = expect(c, [('denied', DENIED_RE), ('login', LOGIN_RE),
                                 ('password', PASSWORD_RE), ('refused', REFUSED_RE),
                                 ('prompt', PROMPT_RE)], a.timeout if a.exec_line else a.login_timeout)
            block('after the password was sent (the far end login banner)'
                  if not a.exec_line else 'the remote command output, then the LOCAL prompt', buf)
            if a.exec_line and nm == 'prompt':
                # The far end ran the command and exited, so the prompt we see is our own.
                outputs.append((a.exec_line, buf))
                result, rc = 'EXEC', 0
            elif nm in ('denied', 'login', 'password'):
                result, rc = 'FAIL', 2
            elif nm == 'refused':
                result, rc = 'REFUSED', 3
            elif nm == 'prompt':
                m = PROMPT_RE.search(buf.rstrip('\r\n '))
                remote_prompt = (m.group(1) + m.group(2)) if m else ''
                result, rc = ('PRIV', 0) if m and m.group(2) == '#' else ('USER', 1)
        elif nm == 'refused':
            block('connect', buf)
            result, rc = 'REFUSED', 3
        elif nm == 'prompt':
            block('connect', buf)
            # Back at a prompt with no credential asked: either the far end needs none,
            # or the client gave up and we never left home.
            m = PROMPT_RE.search(buf.rstrip('\r\n '))
            remote_prompt = (m.group(1) + m.group(2)) if m else ''
            result, rc = ('PRIV', 0) if m and m.group(2) == '#' else ('USER', 1)
            if remote_prompt == local:
                result, rc = 'FAIL', 2
        else:
            block('connect (no recognised prompt)', buf)

        print('CLIENT RESULT: %s  proto=%s  target=%s  user=%s  seconds=%.1f  prompt=%s'
              % (result, a.proto, a.target, a.user or '-', time.time() - t0,
                 remote_prompt or '-'))

        if result in ('PRIV', 'USER'):
            for one in a.cmd:
                out = c.cmd_fast(one, timeout=a.timeout)
                outputs.append((one, out))
                block('far end: %s' % one, out)
            if a.hold:
                print('holding the session open for %.0f s' % a.hold)
                time.sleep(a.hold)
            if not a.no_logout:
                c._t.write('\n>>> exit\n'); c.s.write(b'exit\r')
                nm, buf = expect(c, [('closed', CLOSED_RE), ('prompt', PROMPT_RE)], 20.0)
                block('logout', buf)
    finally:
        back = recover(c, a, local)
        c.close()
    if back is False:
        print('CLIENT RESULT: the console did NOT come back to its local prompt')
        return 7
    if a.expect:
        want = {'priv': 'PRIV', 'user': 'USER', 'fail': 'FAIL', 'refused': 'REFUSED',
                'exec': 'EXEC'}[a.expect]
        print('expected %s, got %s' % (want, result))
        return 0 if result == want else 5
    return rc


def recover(c, a, local):
    """Get the console back to its own exec prompt, whatever the session did.

    🔴 It must NEVER type a word into a login or password prompt. `exit` typed at
    `user@host's password:` is a password GUESS, and each one re-arms the far end's
    account lockout -- measured on tb277 2026-10-21, where a recovery loop turned one
    empty-password bug into three failed logins. When the tail is a credential prompt the
    only safe keystrokes are the application's escape.
    """
    for attempt in range(3):
        raw = c.send_until_prompt('', timeout=12.0)
        if c.last_prompt_seen:
            p = console.Console._last_prompt(raw)
            if p and (local is None or p == local or p.endswith('#')):
                c.to_exec(); c.monitor_off()
                print('console returned to %s' % p)
                return True
        at_credential = bool(LOGIN_RE.search(raw.rstrip('\r\n ')) or
                             PASSWORD_RE.search(raw.rstrip('\r\n ')))
        if attempt == 0 and not at_credential:
            # still inside the far-end session: leave it the application's own way
            c._t.write('\n>>> exit (recovery)\n'); c.s.write(b'exit\r'); time.sleep(2)
        else:
            # escape hatch: telnet Ctrl-] quit, ssh ~.
            if a.proto == 'telnet':
                c._t.write('\n>>> <Ctrl-]>quit (recovery)\n')
                c.s.write(b'\x1d'); time.sleep(0.5); c.s.write(b'quit\r')
            else:
                c._t.write('\n>>> <Enter>~. (recovery)\n')
                c.s.write(b'\r'); time.sleep(0.5); c.s.write(b'~.')
            time.sleep(4)
    # One last look: the escape often lands just after the final check above.
    raw = c.send_until_prompt('', timeout=12.0)
    if c.last_prompt_seen:
        p = console.Console._last_prompt(raw)
        if p and (local is None or p == local or p.endswith('#')):
            c.to_exec(); c.monitor_off()
            print('console returned to %s (after the escape)' % p)
            return True
    return False


if __name__ == '__main__':
    if not sys.argv[1:] or sys.argv[1] in ('-h', '--help'):
        print(__doc__)
        sys.exit(0 if sys.argv[1:] else 6)
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except Exception as e:
        print('devclient: %s: %s' % (type(e).__name__, e))
        sys.exit(4)
