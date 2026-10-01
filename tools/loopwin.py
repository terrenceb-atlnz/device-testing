#!/usr/bin/env python3
"""loopwin.py <flowsdir> <nicA> <nicB> -- windows of loop evidence in an l2flows.py run
(same <nicA> <nicB> as the run): duplicate receptions and echoes (a NIC receiving frames
of a flow it sends), clustered with a 1 s gap; per window first/last receive epoch, span,
counts, max copies of one seq."""
import argparse, collections, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from l2flows import flow_tags

ap = argparse.ArgumentParser(description=__doc__,
                             formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('flowsdir', help='the l2flows.py <outdir>')
ap.add_argument('nicA'); ap.add_argument('nicB')
a = ap.parse_args()
d = a.flowsdir
(b_ab, b_ba, u_ab, u_ba), rxfile = flow_tags(a.nicA, a.nicB)
own = {a.nicB: (b_ba, u_ba), a.nicA: (b_ab, u_ab)}
ev = []
seen = collections.Counter()
for nic in (a.nicB, a.nicA):
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
