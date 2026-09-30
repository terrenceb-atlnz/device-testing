#!/usr/bin/env python3
"""loopwin.py <flowsdir> -- windows of loop evidence: duplicate receptions and echoes
(a NIC receiving frames of a flow it sends), clustered with a 1 s gap; per window
first/last receive epoch, span, counts, max copies of one seq."""
import sys, os, collections
d = sys.argv[1]
own = {'eth2': ('B23', 'U23'), 'eth3': ('B32', 'U32')}
rxfile = {'B32': 'eth2', 'U32': 'eth2', 'B23': 'eth3', 'U23': 'eth3'}
ev = []
seen = collections.Counter()
for nic in ('eth2', 'eth3'):
    for l in open(os.path.join(d, 'rx-%s.txt' % nic)):
        tag, seq, ts, tr = l.split(); tr = float(tr)
        if tag in own[nic]:
            ev.append((tr, 'echo-' + nic, tag, seq))
        elif rxfile.get(tag) == nic:
            seen[(tag, seq)] += 1
            if seen[(tag, seq)] > 1:
                ev.append((tr, 'dup', tag, seq))
ev.sort()
wins = []
for e in ev:
    if wins and e[0] - wins[-1][-1][0] < 1.0:
        wins[-1].append(e)
    else:
        wins.append([e])
mx = max(seen.values()) if seen else 0
for w in wins:
    c = collections.Counter(x[1] for x in w)
    print('window %.3f..%.3f span %.0f ms: %s' % (w[0][0], w[-1][0], (w[-1][0]-w[0][0])*1e3, dict(c)))
print('max copies of one seq: %d' % mx)
print('windows: %d' % len(wins))
