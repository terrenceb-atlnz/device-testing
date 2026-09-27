#!/usr/bin/env python3
"""Restore the 2026-09-24 16:58 bench config to a tb470 device as flash:/tb470-bench.cfg and make
it the boot config. Runs ON tb470 from /tmp/ck33235/ (files in /tmp/ck33235/restore/).

    python3 restore_cfg.py stack|sa|x230|4050 [--check]

stack / sa / 4050 : the file is written through `start-shell` one `echo '<line>' >> <tmp>` at a time
             (the framework's own method, ATSwitch.write_config_file), checked by md5sum against
             the local copy and rewritten on a mismatch, then moved into place. For the stack it is
             written on EVERY member (`start-shell <id>`), since each boots from its own flash.
             Then `boot config-file flash:/tb470-bench.cfg`, `reboot`, wait, and diff the running
             config against the 16:58 copy. `start-shell` needs the ACCESS feature (the licence the
             framework added at 07:50, or FULL).
x230       : no shell (its `access` licence was removed). Its running config is identical to 16:58,
             so `copy running-config flash:/tb470-bench.cfg` + `boot config-file`, then the saved
             file is read back and diffed. No reboot.
--check    : read-only preflight: prompt, show stack, show boot, show license brief. Sends nothing
             else.
Never sends `?`. The AR4050S (u1) only once Terrence says his work on it is done.
"""
import hashlib
import re
import sys
import time

sys.path.insert(0, '/tmp/ck33235')
from console import Console, ConsoleError   # noqa: E402

FILE = 'tb470-bench.cfg'
DEVS = {'stack': ('/dev/u5', 115200), 'sa': ('/dev/u3', 115200), 'x230': ('/dev/u0', 9600),
        '4050': ('/dev/u1', 115200)}
SHELL_RE = re.compile(r'\][#$]\s*$')
TRACE = '/flash/.configs/tracelog_control'


def log(rep, title, text=''):
    rep.write('\n######## {}\n{}\n'.format(title, text))
    rep.flush()


def ref_lines(tag):
    name = {'stack': 'stk', '4050': 'ar'}.get(tag, tag)    # final.out's section labels
    lines = open('/tmp/ck33235/restore/{}.running.txt'.format(name)).read().split('\n')
    while lines and lines[0] == '':
        lines.pop(0)
    return lines[:lines.index('end') + 1]


def to_cli(c):
    """From any prompt (config mode, root shell, user exec) to the privileged CLI prompt."""
    for _ in range(4):
        out = c.send('', quiet=1.0, timeout=8, need_prompt=False).rstrip()
        if SHELL_RE.search(out) or re.search(r'\(config[^)]*\)#$', out):
            c.send('exit' if SHELL_RE.search(out) else 'end', quiet=1.0, timeout=10, need_prompt=False)
            continue
        break
    c.login(monitor=False)


def sh(c, line, timeout=20.0):
    """One shell command; returns output once the `]#`/`]$` prompt is back. None if it is not
    (a lost quote leaves the shell at its `> ` continuation prompt)."""
    c.s.reset_input_buffer()
    c._t.write('\n>>> {}\n'.format(line))
    c.s.write((line + '\r').encode())
    buf, deadline = '', time.time() + timeout
    while time.time() < deadline:
        buf += c._read_some()
        if SHELL_RE.search(buf.rstrip()):
            return buf
        time.sleep(0.03)
    return None


def enter_shell(c, member=None):
    out = c.send('start-shell' + ('' if member is None else ' {}'.format(member)),
                 quiet=1.5, timeout=20, need_prompt=False)
    if not SHELL_RE.search(out.rstrip()):
        raise ConsoleError('start-shell {} gave no shell: {!r}'.format(member or '', out[-200:]))


def write_file(c, rep, lines, label):
    if any("'" in ln for ln in lines):
        raise ConsoleError('a config line holds a single quote; the echo writer cannot send it')
    want = hashlib.md5(('\n'.join(lines) + '\n').encode()).hexdigest()
    # Built in the shell's /tmp: a member shell (`]$`) is not root and may not write /flash.
    tmp = '/tmp/{}.tmp'.format(FILE)
    for attempt in range(3):
        ok = sh(c, ': > {}'.format(tmp)) is not None
        for ln in lines:
            if not ok:
                break
            ok = sh(c, "echo '{}' >> {}".format(ln, tmp)) is not None
        if not ok:
            c.s.write(b'\x03')
            time.sleep(1)
            c.read_until_quiet(quiet=1.0, timeout=5, need_prompt=False)
            log(rep, '{}: attempt {} lost the shell prompt; rewriting'.format(label, attempt + 1))
            continue
        out = sh(c, 'md5sum {}'.format(tmp)) or ''
        got = re.search(r'\b([0-9a-f]{32})\b', out)
        log(rep, '{}: attempt {} md5 want {} got {}'.format(
            label, attempt + 1, want, got.group(1) if got else out[-120:]))
        if got and got.group(1) == want:
            sh(c, 'sudo cp {} /flash/{}; rm -f {}'.format(tmp, FILE, tmp))
            out = sh(c, 'md5sum /flash/{}; ls -la /flash/{}'.format(FILE, FILE)) or ''
            log(rep, '{}: in flash'.format(label), out)
            if want in out:
                return True
            log(rep, '{}: flash copy md5 does not match -- not using it'.format(label))
            return False
    sh(c, 'rm -f {}'.format(tmp))
    return False


def tracelog(c, rep, label):
    """Put tracelog_control back only if the framework's .backup exists and the original does not."""
    out = sh(c, 'ls {0} {0}.backup 2>&1'.format(TRACE)) or ''
    has_bak = re.search(r'^{}\.backup\s*$'.format(re.escape(TRACE)), out, re.M)
    has_orig = re.search(r'^{}\s*$'.format(re.escape(TRACE)), out, re.M)
    if has_bak and not has_orig:
        log(rep, '{}: tracelog restore'.format(label), sh(c, 'sudo mv {0}.backup {0}; ls -la {0}'.format(TRACE)))
    else:
        log(rep, '{}: tracelog untouched'.format(label), out)


def wait_login(c, rep, timeout=900):
    buf, deadline = '', time.time() + timeout
    while time.time() < deadline:
        buf += c._read_some()
        if re.search(r'login:\s*$', buf.rstrip()[-40:] + ' ') or buf.rstrip().endswith('login:'):
            return True
        time.sleep(0.2)
    log(rep, 'NO LOGIN PROMPT after reboot', buf[-800:])
    return False


def diff_running(c, rep, tag):
    import difflib
    now = c.cmd('show running-config', timeout=300).replace('\r', '').split('\n')
    now = now[:now.index('end') + 1] if 'end' in now else now
    d = list(difflib.unified_diff(ref_lines(tag), now, 'ref-16:58', 'now', lineterm=''))
    log(rep, '{}: running-config vs 16:58 -- {} diff lines'.format(tag, len(d)), '\n'.join(d))
    return not d


def member_ids(c):
    out = c.cmd('show stack', timeout=60)
    # ID  Pending-ID  MAC ...   (a Provisioned-only member shows '-' for its MAC and is skipped)
    return [m.group(1) for m in re.finditer(
        r'^\s*(\d+)\s+\S+\s+[0-9a-f]{4}\.[0-9a-f]{4}\.[0-9a-f]{4}', out, re.M)], out


def main():
    tag = sys.argv[1]
    check = '--check' in sys.argv
    port, baud = DEVS[tag]
    rep = open('/tmp/ck33235/restore/{}.{}.txt'.format(tag, 'check' if check else 'restore'), 'w')
    c = Console(port, '/tmp/ck33235/restore/{}.transcript.txt'.format(tag), baud=baud)
    try:
        to_cli(c)
        if check:
            for cmd in (['show stack'] if tag in ('stack', 'sa') else []) + ['show boot', 'show license brief']:
                log(rep, cmd, c.cmd(cmd, timeout=90))
            return
        if tag == 'x230':
            if not diff_running(c, rep, tag):
                log(rep, 'x230 running-config differs from 16:58 -- NOT saving it')
                return
            log(rep, 'copy', c.cmd('copy running-config flash:/{}'.format(FILE), timeout=120))
        else:
            ids, out = member_ids(c) if tag == 'stack' else ([None], '')
            log(rep, 'members', '{}\n{}'.format(ids, out))
            if tag == 'stack' and len(ids) != 3:
                log(rep, 'expected 3 stack members -- stopping')
                return
            for mid in ids:
                label = '{} member {}'.format(tag, mid or '-')
                enter_shell(c, mid)
                done = write_file(c, rep, ref_lines(tag), label)
                tracelog(c, rep, label)
                c.send('exit', quiet=1.5, timeout=10, need_prompt=False)
                to_cli(c)
                if not done:
                    log(rep, '{}: FILE WRITE FAILED after 3 attempts -- stopping, boot config untouched'.format(label))
                    return
        for cmd in ('configure terminal', 'boot config-file flash:/{}'.format(FILE), 'end'):
            log(rep, cmd, c.cmd(cmd, timeout=60))
        log(rep, 'show boot', c.cmd('show boot', timeout=60))
        if tag == 'x230':
            saved = c.cmd('show file flash:/{}'.format(FILE), timeout=120).replace('\r', '').split('\n')
            import difflib
            d = list(difflib.unified_diff(ref_lines(tag), [x for x in saved], 'ref', 'file', lineterm=''))
            log(rep, 'x230 saved file vs 16:58 -- {} diff lines'.format(len(d)), '\n'.join(d))
            return
        c.send('reboot', quiet=1.5, timeout=15, need_prompt=False)
        log(rep, 'reboot confirm', c.send('y', quiet=2.0, timeout=15, need_prompt=False))
        if not wait_login(c, rep):
            return
        time.sleep(30)
        c.login(monitor=False)
        if tag == 'stack':
            for _ in range(20):
                ids, out = member_ids(c)
                if len(ids) == 3 and out.count('Ready') >= 3:
                    break
                time.sleep(15)
            log(rep, 'show stack after reboot', out)
        log(rep, 'show boot after reboot', c.cmd('show boot', timeout=60))
        diff_running(c, rep, tag)
    finally:
        try:
            c.send('', quiet=0.6, timeout=5, need_prompt=False)
        finally:
            c.close()
            rep.close()


if __name__ == '__main__':
    main()
