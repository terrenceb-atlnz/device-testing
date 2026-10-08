#!/usr/bin/env python3
"""case_tokens.py -- per-case token usage and process metrics from a tester's transcript.

Reads a Claude Code transcript (.jsonl) of the tester that ran a campaign group (a bench-runner
subagent, or a two-session worker) and splits it into one segment per case, using the tester's
`RESULT <id> ...` SendMessage lines as the case boundaries (logged-output.md §2). For each case
and for the group overhead (gates before the first case, hand-back after the last) it reports:

  - API calls (unique assistant messages) and tokens: input, cache-write, cache-read, output;
  - wall time;
  - tool calls by tool name, and the characters of tool output read back into the context;
  - the largest tool outputs (the "wasteful input" candidates);
  - commands repeated verbatim (the repetition candidates).

A case's segment starts at the first tool call after the previous RESULT that touches the
case's own folder (`/<id>/` in its input); everything between is overhead. Used by /create-logs (§3b) to write each case's
REVIEW.md. Runs on the dev host; touches no testbox.

  case_tokens.py --transcript <file.jsonl> --cases 22650,22651 [--json]
  case_tokens.py --find <projects-dir> --cases 22650,22651 [--json]
      --find searches <dir>/*.jsonl and <dir>/*/subagents/*.jsonl for the transcript that sent
      `RESULT <first case>`; the projects dir is ~/.claude/projects/<repo path, non-alnum -> '-'>.
"""
import argparse
import collections
import glob
import json
import os
import sys
from datetime import datetime


def load(path):
    rows = []
    with open(path) as f:
        for line in f:
            try:
                rows.append(json.loads(line))
            except ValueError:
                pass
    return rows


def find_transcript(base, first_case):
    needle = '"RESULT %s ' % first_case
    hits = []
    for f in glob.glob(os.path.join(base, '*.jsonl')) + \
            glob.glob(os.path.join(base, '*', 'subagents', '*.jsonl')):
        with open(f) as fh:
            for line in fh:
                if needle in line and '"tool_use"' in line and 'SendMessage' in line:
                    hits.append(f)
                    break
    if not hits:
        sys.exit('no transcript under %s sent RESULT %s' % (base, first_case))
    return sorted(hits, key=os.path.getmtime)[-1]


def ts(s):
    return datetime.fromisoformat(s.replace('Z', '+00:00'))


def events(rows):
    """Flatten to a time-ordered list of (time, kind, payload)."""
    seen_usage = {}
    out = []
    pending = {}
    for r in rows:
        t = r.get('timestamp')
        if not t:
            continue
        m = r.get('message') or {}
        if r.get('type') == 'assistant':
            mid = m.get('id')
            if mid and m.get('usage'):
                seen_usage[mid] = (t, m['usage'])      # last row of a message carries the final usage
            for b in m.get('content') or []:
                if b.get('type') == 'tool_use':
                    inp = b.get('input') or {}
                    out.append((t, 'tool', {'id': b['id'], 'name': b['name'], 'input': inp}))
                    pending[b['id']] = b['name']
        elif r.get('type') == 'user' and isinstance(m.get('content'), list):
            for b in m['content']:
                if b.get('type') == 'tool_result':
                    c = b.get('content')
                    if isinstance(c, list):
                        c = ''.join(x.get('text', '') for x in c if isinstance(x, dict))
                    out.append((t, 'result', {'id': b.get('tool_use_id'), 'chars': len(c or ''),
                                              'tool': pending.get(b.get('tool_use_id'), '?')}))
    for mid, (t, u) in seen_usage.items():
        out.append((t, 'usage', u))
    out.sort(key=lambda e: e[0])
    return out


def cmd_text(name, inp):
    if name == 'Bash':
        return inp.get('command', '')
    if name in ('Read', 'Write', 'Edit'):
        return '%s %s' % (name, inp.get('file_path', ''))
    return '%s %s' % (name, json.dumps(inp, sort_keys=True)[:200])


def segment(evs, cases):
    """Assign each event to a case id or to 'overhead'."""
    bounds = []                                   # index of each case's RESULT tool call
    for cid in cases:
        idx = next((i for i, (t, k, p) in enumerate(evs)
                    if k == 'tool' and p['name'] == 'SendMessage'
                    and str(p['input'].get('message', '')).startswith('RESULT %s ' % cid)), None)
        bounds.append(idx)
    label = ['overhead'] * len(evs)
    prev = -1
    for cid, end in zip(cases, bounds):
        if end is None:
            continue
        # the case starts at the first tool call into its own folder (<group>/<id>/); a bare id
        # also matches queue reads and older flat logs, which are gate/overhead work
        start = next((i for i in range(prev + 1, end + 1)
                      if evs[i][1] == 'tool' and '/%s/' % cid in json.dumps(evs[i][2]['input'])), end)
        for i in range(start, end + 1):
            label[i] = cid
        # tool results and usage that land just after the RESULT call belong to it too
        j = end + 1
        while j < len(evs) and evs[j][1] in ('result', 'usage') and evs[j][0] == evs[end][0]:
            label[j] = cid
            j += 1
        prev = end
    return label, bounds


def summarise(evs, label, key):
    s = {'api_calls': 0, 'input': 0, 'cache_write': 0, 'cache_read': 0, 'output': 0,
         'tools': collections.Counter(), 'tool_output_chars': 0, 'start': None, 'end': None,
         'largest': [], 'repeats': []}
    cmds = collections.Counter()
    ids = {}
    for (t, k, p), lab in zip(evs, label):
        if lab != key:
            continue
        s['start'] = s['start'] or t
        s['end'] = t
        if k == 'usage':
            s['api_calls'] += 1
            s['input'] += p.get('input_tokens', 0)
            s['cache_write'] += p.get('cache_creation_input_tokens', 0)
            s['cache_read'] += p.get('cache_read_input_tokens', 0)
            s['output'] += p.get('output_tokens', 0)
        elif k == 'tool':
            s['tools'][p['name']] += 1
            c = cmd_text(p['name'], p['input'])
            cmds[c] += 1
            ids[p['id']] = c
        elif k == 'result':
            s['tool_output_chars'] += p['chars']
            s['largest'].append((p['chars'], ids.get(p['id'], p['tool'])))
    s['largest'] = sorted(s['largest'], reverse=True)[:5]
    s['repeats'] = [(n, c) for c, n in cmds.most_common() if n > 1][:10]
    # wall time spent IN this segment: overhead is split around the cases, so sum the gaps
    # between consecutive events that both belong to it rather than first-to-last
    s['wall_s'] = sum((ts(evs[i][0]) - ts(evs[i - 1][0])).total_seconds()
                      for i in range(1, len(evs)) if label[i] == key and label[i - 1] == key)
    s['tools'] = dict(s['tools'])
    return s


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--transcript')
    g.add_argument('--find', metavar='PROJECTS_DIR')
    ap.add_argument('--cases', required=True, help='comma-separated case ids, in run order')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    cases = [c.strip() for c in a.cases.split(',') if c.strip()]
    path = a.transcript or find_transcript(os.path.expanduser(a.find), cases[0])
    evs = events(load(path))
    label, bounds = segment(evs, cases)
    report = {'transcript': path, 'cases': {}, 'missing': [c for c, b in zip(cases, bounds) if b is None]}
    for key in cases + ['overhead']:
        report['cases'][key] = summarise(evs, label, key)
    if a.json:
        print(json.dumps(report, indent=1))
        return
    print('transcript: %s' % path)
    if report['missing']:
        print('no RESULT line found for: %s' % ', '.join(report['missing']))
    hdr = '%-9s %5s %8s %9s %10s %7s %6s %7s %10s' % (
        'segment', 'calls', 'input', 'cache_wr', 'cache_rd', 'output', 'tools', 'wall_s', 'tool_out')
    print(hdr)
    for key in cases + ['overhead']:
        s = report['cases'][key]
        print('%-9s %5d %8d %9d %10d %7d %6d %7d %10d' % (
            key, s['api_calls'], s['input'], s['cache_write'], s['cache_read'], s['output'],
            sum(s['tools'].values()), s['wall_s'], s['tool_output_chars']))
    for key in cases + ['overhead']:
        s = report['cases'][key]
        print('\n[%s] tools %s' % (key, s['tools']))
        for n, c in s['largest']:
            print('  largest output %7d chars: %s' % (n, c.replace('\n', ' ')[:150]))
        for n, c in s['repeats']:
            print('  repeated x%d: %s' % (n, c.replace('\n', ' ')[:150]))


if __name__ == '__main__':
    main()
