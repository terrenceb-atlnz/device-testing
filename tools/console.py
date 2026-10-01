#!/usr/bin/env python3
"""AlliedWare Plus console driver that tolerates asynchronous log output.

Library, not a command: `import console` from a sibling script in the same
directory (each tools/ script puts its own directory on sys.path), then
    c = console.Console('<tty>', '<transcript>', baud=115200)
    c.login(); print(c.cmd('show system')); c.close()
<tty> is the AW+ unit's console device on the testbox you run it on; the
transcript is a path you choose.  Login credentials default to manager/friend
and are overridden by the env vars CK_USER / CK_PASSWORD (read at import), or
per call with login(username=..., password=...).

Why this exists rather than a last-line prompt check (e.g. the legacy
DeviceSkrips/_show.py): that helper decides it has a
privileged prompt by testing whether the LAST line of the drained output ends in
'#'.  On a stack under test the console interleaves unsolicited messages --
'switch: port 2(port2.0.1) entered forwarding state', VCS role changes, link
up/down -- so the prompt is very often not the last line, and a perfectly
healthy session is reported as 'not at a privileged prompt'.

The rule here instead: a command is finished when a prompt has appeared AFTER
the echoed command *and* the port has then gone quiet.  Async chatter in between
is captured, not fatal.

Everything read is written to the transcript file as it arrives, never buffered
until success -- a timeout must not discard the bytes needed to diagnose it.
"""
import os
import re
import time

import serial

BAUD = 115200
# AW+ factory defaults; override with CK_USER / CK_PASSWORD for a unit that
# uses other credentials.  Sibling scripts read these too, so one env setting
# covers every tool.
USERNAME = os.environ.get('CK_USER', 'manager')
PASSWORD = os.environ.get('CK_PASSWORD', 'friend')

# 'awplus#', 'awplus-2#', 'awplus(config)#', 'awplus(config-if)#'
PROMPT_RE = re.compile(r'[\w.-]+(?:\([\w -]+\))?#[ \t]*$')
# Same, but allowed to sit anywhere in the buffer rather than only at the end.
# It must be anchored at a LINE START and must NOT require anything particular
# after the '#'.  With `terminal monitor` on the device splices a log line
# directly onto the prompt:
#     awplus(config-if)#00:55:19 awplus NSM[742]: port1.0.28 user no shutdown
# An earlier version required newline-or-end after the '#', so it never matched
# that form and every such command ran to its full timeout -- measured as
# alternating 0-4 s and exactly-25 s iterations, 25 s being the timeout.
# Anchoring at line start is what keeps a stray '#' inside log text from
# matching, now that the trailing context is no longer required.
PROMPT_ANYWHERE_RE = re.compile(r'(?:^|\r?\n)[\w.-]+(?:\([\w -]+\))?#')


class ConsoleError(Exception):
    pass


class Console:
    def __init__(self, port, transcript, baud=BAUD, echo=False):
        self.port = port
        self.echo = echo
        self._t = open(transcript, 'a', buffering=1, errors='replace')
        self._t.write('\n===== opened {} at {} =====\n'.format(
            port, time.strftime('%Y-%m-%d %H:%M:%S')))
        # Opening the port drops DTR, which the IE520 sees as a BREAK; the next
        # character would then be eaten as a sysrq key.  Clearing HUPCL first
        # stops the drop on close, and the bare CR in login() absorbs the open.
        # IE520-specific workaround; harmless on other AW+ products and on any
        # tty where stty fails (the error is discarded).
        os.system('stty -F {} -hupcl 2>/dev/null'.format(os.path.realpath(port)))
        self.s = serial.Serial(port, baud, timeout=0.2)

    # ---- low level -------------------------------------------------------

    def _read_some(self):
        chunk = self.s.read(4096)
        if not chunk:
            return ''
        text = chunk.decode(errors='replace')
        self._t.write(text)
        if self.echo:
            print(text, end='')
        return text

    def read_until_quiet(self, quiet=0.8, timeout=30.0, need_prompt=True):
        """Read until `quiet` seconds pass with no new bytes.

        With need_prompt, keep going past a quiet spell until a prompt has been
        seen, so a slow command is not mistaken for a finished one.
        """
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
                # No prompt yet.  Do NOT give up on silence: an IE520 writing
                # ~41 MB to SPIFlash answers nothing at all for ~12 minutes,
                # and an earlier version of this returned after 20 s and
                # reported a perfectly healthy transfer as a failure.  Silence
                # is not an outcome -- only the prompt or `timeout` is.
                pass
            time.sleep(0.05)
        return buf

    def send(self, line, quiet=0.8, timeout=60.0, need_prompt=True):
        self._t.write('\n>>> {}\n'.format(line))
        self.s.write((line + '\r').encode())
        return self.read_until_quiet(quiet=quiet, timeout=timeout,
                                     need_prompt=need_prompt)

    # ---- session ---------------------------------------------------------

    def login(self, timeout=60.0, monitor=False, username=None, password=None):
        """Reach a privileged prompt, logging in only if the console asks.

        `username` / `password` default to the module USERNAME / PASSWORD
        (manager/friend unless CK_USER / CK_PASSWORD are set).

        `monitor` decides whether the device mirrors its log messages to this
        console.  It is an EXPLICIT argument rather than something a caller
        re-enables afterwards: during the cycle-293 wedge the console capture
        was the only surviving record of the event, so whether logging is on is
        a decision that must be declared at the point of connection and must not
        depend on statement ordering elsewhere.
          monitor=False -> quiet console, easier parsing (test runs)
          monitor=True  -> maximum device output (reproducers, witness logging)
        """
        username = USERNAME if username is None else username
        password = PASSWORD if password is None else password
        self.s.write(b'\r')
        out = self.read_until_quiet(quiet=1.0, timeout=10.0, need_prompt=False)

        if re.search(r'login:\s*$', out.rstrip()) or 'login:' in out[-200:].lower():
            self.s.write((username + '\r').encode())
            self.read_until_quiet(quiet=1.0, timeout=15.0, need_prompt=False)
            self.s.write((password + '\r').encode())
            out = self.read_until_quiet(quiet=1.2, timeout=timeout,
                                        need_prompt=False)

        if 'new password' in out.lower():
            raise ConsoleError(
                'console is in the forced password-change dialog; refusing to '
                'commit a value. Tail: {!r}'.format(out[-300:]))

        # '>' user-exec -> enable.  Check the tail only, so an old '#' earlier
        # in the scrollback cannot satisfy this.
        if not PROMPT_RE.search(out.rstrip()[-120:]):
            self.s.write(b'enable\r')
            out = self.read_until_quiet(quiet=1.0, timeout=20.0,
                                        need_prompt=False)

        if not PROMPT_ANYWHERE_RE.search(out):
            raise ConsoleError(
                'no privileged prompt on {}. Tail: {!r}'.format(
                    self.port, out[-300:]))

        # No paging either way.  Log mirroring follows `monitor`.  Both are
        # best-effort: some platform messages ('switch: port N entered ...') are
        # printed to the console below the AW+ log layer and appear regardless.
        self.send('terminal length 0', quiet=0.6, timeout=15.0)
        self.send('terminal monitor' if monitor else 'terminal no monitor',
                  quiet=0.6, timeout=15.0)
        self.monitor = monitor
        return True

    def send_until_prompt(self, line, timeout=60.0, settle=0.15):
        # Sets self.last_prompt_seen so the caller can distinguish
        # "command finished" from "no prompt ever came back".
        """Send `line`; return as soon as a prompt appears AFTER its echo.

        `read_until_quiet` waits for the port to fall silent, which is the wrong
        completion signal when `terminal monitor` is on: the device logs our own
        keystrokes back at us ("IMISH[...]: [manager@ttyS0]interface port1.0.27")
        and MSTP chatters continuously, so the console is rarely quiet and each
        command paid ~5-9 s of pure waiting.  Measured: 20-30 s per loop
        iteration with monitor on, vs the 2-3 s the loop was designed around.

        The real completion signal is the prompt coming back.  We search for it
        only PAST the echoed command, so a prompt already sitting in the buffer
        from the previous command cannot satisfy this one.  A prompt with log
        text spliced after it on the same line still matches, which is the
        common case with monitor on:
            awplus(config-if)#00:31:00 awplus MSTP[989]: ...
        """
        self._t.write('\n>>> {}\n'.format(line))
        self.s.write((line + '\r').encode())
        buf = ''
        echo_end = -1
        deadline = time.time() + timeout
        while time.time() < deadline:
            text = self._read_some()
            if not text:
                time.sleep(0.02)
                continue
            buf += text
            if '--More--' in text:
                self.s.write(b' ')
            if echo_end < 0 and line.strip():
                i = buf.find(line.strip())
                if i >= 0:
                    echo_end = i + len(line.strip())
            start = echo_end if echo_end >= 0 else 0
            if PROMPT_ANYWHERE_RE.search(buf, start):
                # Short settle so trailing bytes land in the transcript too.
                time.sleep(settle)
                buf += self._read_some()
                self.last_prompt_seen = True
                return buf
        # Ran out of time with no prompt back.  Callers driving a box that may
        # WEDGE must be able to tell this from a normal completion -- returning
        # a partial buffer silently would make a wedge look like a clean result.
        self.last_prompt_seen = False
        return buf

    def cmd_fast(self, line, timeout=60.0):
        """cmd() semantics, prompt-based completion. For monitor-on loops."""
        raw = self.send_until_prompt(line, timeout=timeout)
        lines = raw.splitlines()
        if lines and line.strip() and line.strip() in lines[0]:
            lines = lines[1:]
        while lines and PROMPT_RE.search(lines[-1].rstrip()):
            lines.pop()
        return '\n'.join(lines).strip()

    def cmd(self, line, quiet=0.8, timeout=60.0):
        """Run one command and return its output with echo and prompt trimmed."""
        raw = self.send(line, quiet=quiet, timeout=timeout)
        lines = raw.splitlines()
        # Drop the echoed command and any trailing prompt-only lines.
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


if __name__ == '__main__':
    # A library: running it directly only explains how to use it.
    import sys
    print(__doc__.strip().splitlines()[0])
    print('usage: import console  (library; run a driver such as ckcon.py instead)')
    sys.exit(0 if sys.argv[1:2] in (['-h'], ['--help']) else 2)
