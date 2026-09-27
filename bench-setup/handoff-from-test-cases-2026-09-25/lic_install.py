#!/usr/bin/env python3
"""Install one feature licence on one tb470 device with the framework's own key, the way the
framework does it. Runs ON tb470 from /tmp/ck33235/.

    python3 lic_install.py <tag> <key-file section> <licence name>
    e.g. lic_install.py x230 x230 ACCESS  |  lic_install.py sa IE520 FULL

`license <name> <key>` at the privileged prompt, `y` to its "(y/n)" confirmation, `exit` and log in
again (the framework's "to ensure the ACCESS license is properly activated"), then the licence list
again (`member all` on the stack). For ACCESS it also proves `start-shell` gives a shell.

The key is read from /home/st-art/feature_license_keys.env and NEVER printed: the console WRAPS the
echoed command, so the key is matched with optional whitespace between every character and every
12-character slice of it is scrubbed too, in the report, in exception text and in the transcript.
Never sends `?`.
"""
import configparser
import re
import sys

sys.path.insert(0, '/tmp/ck33235')
from console import Console   # noqa: E402

DEVS = {'stack': ('/dev/u5', 115200), 'sa': ('/dev/u3', 115200), '4050': ('/dev/u1', 115200),
        'x230': ('/dev/u0', 9600)}
SHELL_RE = re.compile(r'\][#$]\s*$')

tag, section, name = sys.argv[1:4]
port, baud = DEVS[tag]
stem = '/tmp/ck33235/lic.{}.{}'.format(tag, name)
TRANSCRIPT, REPORT = stem + '.transcript.txt', stem + '.txt'

k = configparser.ConfigParser()
k.optionxform = str
k.read('/home/st-art/feature_license_keys.env')
KEY = k.get(section, name)
KEY_RE = re.compile(r'\s*'.join(re.escape(ch) for ch in KEY))
FRAGMENTS = [KEY[i:i + 12] for i in range(len(KEY) - 11)]


def red(text):
    text = KEY_RE.sub('<{}-KEY>'.format(name), text)
    for f in FRAGMENTS:
        text = text.replace(f, '<KEY-FRAGMENT>')
    return text


show = 'show license brief member all' if tag == 'stack' else 'show license brief'
rep = []
c = Console(port, TRANSCRIPT, baud=baud)
try:
    c.login(monitor=False)
    rep.append('== before: ' + show + '\n' + c.cmd(show, timeout=120))
    out = c.send('license {} {}'.format(name, KEY), quiet=3.0, timeout=60, need_prompt=False)
    rep.append('== license {} <KEY>\n'.format(name) + red(out))
    if '(y/n)' not in out:
        raise RuntimeError('no (y/n) confirmation after the license command -- stopping here')
    rep.append('== y\n' + red(c.send('y', quiet=8.0, timeout=600)))
    rep.append('== exit\n' + c.send('exit', quiet=3.0, timeout=30, need_prompt=False))
    c.login(monitor=False)
    rep.append('== after: ' + show + '\n' + c.cmd(show, timeout=120))
    if name.upper() == 'ACCESS':
        shell = c.send('start-shell', quiet=2.0, timeout=30, need_prompt=False)
        ok = bool(SHELL_RE.search(shell.rstrip()))
        rep.append('== start-shell\n' + shell)
        rep.append('== RESULT: start-shell ' + ('gave a shell' if ok else 'gave NO shell'))
        if ok:
            c.send('exit', quiet=1.5, timeout=15, need_prompt=False)
except Exception as e:     # a console error's tail may hold the echo: redacted, no traceback
    rep.append('== ERROR ' + type(e).__name__ + ': ' + red(str(e)))
finally:
    c.close()
    t = open(TRANSCRIPT, errors='replace').read()
    open(TRANSCRIPT, 'w').write(red(t))
    body = red('\n'.join(rep))
    open(REPORT, 'w').write(body + '\n')
    print(body)
