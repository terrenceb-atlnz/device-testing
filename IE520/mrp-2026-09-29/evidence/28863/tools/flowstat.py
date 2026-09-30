#!/usr/bin/env python3
"""flowstat.py <outdir> [event_epoch ...]
Per flow: sent, received (unique), lost, duplicates, the longest run of consecutive
missing sequence numbers (= outage, in ms at the flow's pps), where it sat in wall
time relative to each event epoch, and every run of >=2 missing frames."""
import sys, os, collections
d = sys.argv[1]
events = [float(x) for x in sys.argv[2:]]
tx = {}
pps = None
for l in open(os.path.join(d, 'tx.txt')):
    p = l.split()
    if p[0] == 'pps':
        pps = int(p[1]); start = float(p[3])
    else:
        tx[p[0]] = int(p[1])
rxfile = {'B32': 'eth2', 'U32': 'eth2', 'B23': 'eth3', 'U23': 'eth3'}
seqs = collections.defaultdict(list)
for nic in ('eth2', 'eth3'):
    for l in open(os.path.join(d, 'rx-%s.txt' % nic)):
        tag, seq, ts, tr = l.split()
        if rxfile.get(tag) == nic:
            seqs[tag].append((int(seq), float(ts), float(tr)))
for tag in ('B32', 'B23', 'U32', 'U23'):
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
        if b - a + 1 >= 2 or True:
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
