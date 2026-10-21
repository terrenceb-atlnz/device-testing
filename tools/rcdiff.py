#!/usr/bin/env python3
"""rcdiff.py [--last] <before.log> <after.log>

Unified diff (1 line of context) of the full `show running-config` in two saved console
transcripts: the stdout of ckcon.py / cfg.py, where every command starts with a header line
`HH:MM:SS >>> <cmd>` (cfg.py may prefix an epoch: `1792544570.250 14:02:50 >>> <cmd>`).

Only a header whose command is EXACTLY `show running-config` starts a dump. A filtered
`show running-config | include ...` or `remote-diff all show running-config` earlier in the same
capture is skipped. (Until 2026-10-21 the first match of the text was used, so a filtered read
taken before the full dump gave a false diff; T17584 on tb101 showed 128 lines of it.)

A dump runs to the next header line. Blank lines, CRs, an echoed `show running-config` line and a
trailing bare prompt (`IE520#`) are dropped. With several full dumps in one file the FIRST is
used; --last uses the last one.

Exit 0 = no difference, 1 = difference printed, 2 = usage error or a file with no full dump.
Reads files only; runs anywhere.
"""
import argparse, difflib, re, sys

HDR = re.compile(r'^(?:\d+(?:\.\d+)? )?\d\d:\d\d:\d\d >>> (.*?)\s*$')
PROMPT = re.compile(r'^\S+[#>]\s*$')
CMD = 'show running-config'


def dumps(path):
    """Every full `show running-config` section in a transcript, as lists of lines."""
    found, cur = [], None
    for line in open(path, errors='replace').read().replace('\r', '').split('\n'):
        m = HDR.match(line)
        if m:
            if cur is not None:
                found.append(cur)
            cur = [] if m.group(1) == CMD else None
            continue
        if cur is not None and line.strip() and line.strip() != CMD:
            cur.append(line.rstrip())
    if cur is not None:
        found.append(cur)
    for d in found:
        while d and PROMPT.match(d[-1]):
            d.pop()
    return found


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--last', action='store_true', help='use the last full dump in each file')
    ap.add_argument('before')
    ap.add_argument('after')
    a = ap.parse_args(argv)
    sides = []
    for path in (a.before, a.after):
        try:
            d = dumps(path)
        except OSError as e:
            print('rcdiff: cannot read %s: %s' % (path, e), file=sys.stderr)
            return 2
        if not d:
            print('rcdiff: no full `%s` header in %s' % (CMD, path), file=sys.stderr)
            return 2
        sides.append(d[-1] if a.last else d[0])
    diff = list(difflib.unified_diff(sides[0], sides[1], a.before, a.after, lineterm='', n=1))
    for line in diff:
        print(line)
    return 1 if diff else 0


if __name__ == '__main__':
    sys.exit(main())
