#!/bin/bash
# 11346-prunegraft.sh <tag>   (on tb470, cwd /tmp/ck12)
# 40 s multicast stream at 1000 pps (eth1 -> stack -> SA -> eth2). The fake receiver sends an
# IGMPv2 Leave at +10 s and a Report (join) at +25 s. Every received frame is timestamped
# (tcpdump -tt), so the stop after the leave (SA IGMP last-member query + PIM-DM prune toward
# the stack) and the resume after the join (graft) can be read off as arrival gaps.
T=/home/terrenceb/claude/device-testing/IE520/routing-2026-09-29/evidence/tools
E=/home/terrenceb/claude/device-testing/IE520/routing-2026-09-29/evidence/11346
cd /tmp/ck12 || exit 1
tag=$1; out=$E/11346-$tag
: > $out-events.txt
sudo -n tcpdump -i eth2 -nn -tt -s 64 -B 262144 "ether dst 01:00:5e:71:01:01 and udp dst port 5001" > /tmp/ck12/rx-$tag.txt 2> /tmp/ck12/td-$tag.log & t1=$!
sleep 1
sudo -n python3 $T/igmp.py eth2 join 239.113.1.1 10.113.3.2 02:31:13:00:00:03 1 >> $out-events.txt
echo "stream_start $(date +%s.%N)" >> $out-events.txt
sudo -n tcpreplay -i eth1 --pps=1000 --no-flow-stats --duration=40 --loop=0 p/mc1514.pcap > $out-tx.txt 2>&1 & r=$!
sleep 10
echo "leave $(date +%s.%N)" >> $out-events.txt
sudo -n python3 $T/igmp.py eth2 leave 239.113.1.1 10.113.3.2 02:31:13:00:00:03 1 >> $out-events.txt
sleep 15
echo "join $(date +%s.%N)" >> $out-events.txt
sudo -n python3 $T/igmp.py eth2 join 239.113.1.1 10.113.3.2 02:31:13:00:00:03 1 >> $out-events.txt
wait $r
echo "stream_end $(date +%s.%N)" >> $out-events.txt
sleep 3
sudo -n kill -INT $(pgrep -P $t1 tcpdump) 2>/dev/null; wait $t1
python3 - "$out" /tmp/ck12/rx-$tag.txt <<'EOF' | tee $out-summary.txt
import sys
out, rx = sys.argv[1], sys.argv[2]
ev = {}
for l in open(out + "-events.txt"):
    p = l.split()
    if len(p) == 2 and p[0] in ("stream_start", "leave", "join", "stream_end"):
        ev[p[0]] = float(p[1])
ts = [float(l.split()[0]) for l in open(rx) if l[:1].isdigit()]
sent = [l for l in open(out + "-tx.txt") if l.startswith("Actual")]
print("tcpreplay:", sent[0].strip() if sent else "?")
print("received total:", len(ts))
L, J = ev["leave"], ev["join"]
before = [t for t in ts if t < L]; mid = [t for t in ts if L <= t < J]; after = [t for t in ts if t >= J]
print("before leave: %d frames" % len(before))
print("leave -> join (%.1f s): %d frames; last frame %.3f s after the leave" % (J - L, len(mid), (mid[-1] - L) if mid else float("nan")))
print("after join: %d frames; first frame %.3f s after the join" % (len(after), (after[0] - J) if after else float("nan")))
gaps = sorted(((b - a, a) for a, b in zip(ts, ts[1:])), reverse=True)[:3]
for g, a in gaps:
    print("gap %.3f s starting %.3f s after stream start" % (g, a - ev["stream_start"]))
EOF
