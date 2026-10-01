#!/usr/bin/env python3
"""flowstat.py <outdir> <nicA> <nicB> [event_epoch ...]
Analyse an l2flows.py run (give it the same <nicA> <nicB> as the run; the flow tags are
derived from them the same way). Per flow: sent, received (unique), lost, duplicates,
the longest run of consecutive missing sequence numbers (= outage, in ms at the flow's
pps), where it sat in wall time relative to each event epoch, and every run of >=2
missing frames (single lost frames count in 'lost' but are not listed)."""
import argparse, collections, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from l2flows import flow_tags

ap = argparse.ArgumentParser(description=__doc__,
                             formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('outdir', help='the l2flows.py <outdir>')
ap.add_argument('nicA'); ap.add_argument('nicB')
ap.add_argument('event_epoch', type=float, nargs='*', help='epochs to show outages relative to')
args = ap.parse_args()
d = args.outdir
events = args.event_epoch
tags, rxfile = flow_tags(args.nicA, args.nicB)
tx = {}
pps = None
for l in open(os.path.join(d, 'tx.txt')):
    p = l.split()
    if p[0] == 'pps':
        pps = int(p[1]); start = float(p[3])
    else:
        tx[p[0]] = int(p[1])
seqs = collections.defaultdict(list)
for nic in (args.nicB, args.nicA):
    for l in open(os.path.join(d, 'rx-%s.txt' % nic)):
        tag, seq, ts, tr = l.split()
        if rxfile.get(tag) == nic:
            seqs[tag].append((int(seq), float(ts), float(tr)))
for tag in tags:
    n = tx.get(tag, 0)
    got = seqs[tag]
    c = collections.Counter(s for s, _, _ in got)
    uniq = set(c)
    dups = sum(v - 1 for v in c.values() if v > 1)
    lost = n - len(uniq)
    runs = []
    run_start = None
    for i in range(n):
        if i not in uniq:
            if run_start is None:
                run_start = i
        elif run_start is not None:
            runs.append((run_start, i - 1)); run_start = None
    if run_start is not None:
        runs.append((run_start, n - 1))
    longest = max(runs, key=lambda r: r[1] - r[0], default=None)
    print('%s sent=%d rx_unique=%d lost=%d dups=%d' % (tag, n, len(uniq), lost, dups))
    for a, b in runs:
        if b - a + 1 >= 2:                 # runs of >=2 only, as documented
            t_a = start + a / pps
            rel = ' '.join('ev%d%+.3fs' % (k, t_a - e) for k, e in enumerate(events))
            print('   missing seq %d..%d = %d frames = %.0f ms, starts %.3f %s'
                  % (a, b, b - a + 1, (b - a + 1) * 1000.0 / pps, t_a, rel))
    if longest:
        print('   LONGEST outage %.0f ms' % ((longest[1] - longest[0] + 1) * 1000.0 / pps))
    if dups:
        dd = sorted(s for s, v in c.items() if v > 1)
        print('   duplicate seqs (first 10): %s' % dd[:10])
    lat = sorted(tr - ts for _, ts, tr in got)
    if lat:
        print('   latency ms: median %.3f p99 %.3f max %.3f'
              % (lat[len(lat)//2]*1e3, lat[int(len(lat)*0.99)]*1e3, lat[-1]*1e3))
