#!/bin/bash
# usage: fc_measure.sh <label> <pause:yes|no> [period_ms] [quanta]
# 10 s of tcpreplay --topspeed from eth1 (IXIA1) to eth3's MAC, optionally with PAUSE
# frames from eth3 (IXIA2) for the whole window. Host counters before/after, raw.
set -u
D=/tmp/ckorient/t12067; L=$1; P=$2; PER=${3:-67}; Q=${4:-0xFFFF}
E=/usr/sbin/ethtool
cd $D
snap() { for n in eth1 eth3; do echo "== $n"; $E -S $n | command grep -E ' (rx_packets|tx_packets|rx_bytes|tx_bytes|rx_flow_control_xon|rx_flow_control_xoff|tx_flow_control_xon|tx_flow_control_xoff|rx_missed_errors|rx_no_buffer_count):'; done; }
echo "##### $L  pause=$P period=${PER}ms quanta=$Q  $(date '+%F %T')"
snap > $L.before
if [ "$P" = yes ]; then
  sudo -n python3 $D/fc_host.py pause eth3 13 $PER $Q > $L.pause.out 2>&1 &
  PP=$!
  sleep 1.5
fi
sudo -n /usr/bin/tcpreplay -i eth1 --topspeed --duration=10 --loop=0 $D/load.pcap > $L.tcpreplay 2>&1
[ "$P" = yes ] && wait $PP
snap > $L.after
echo "--- tcpreplay"; command grep -E 'Actual|Rated|Statistics|Successful|Failed|Truncated|Retried' $L.tcpreplay
[ "$P" = yes ] && { echo "--- pause"; cat $L.pause.out; }
echo "--- host counter deltas"
paste <(sed 's/^ *//' $L.before) <(sed 's/^ *//' $L.after) | awk -F'\t' '
  /^==/ {print $1; next}
  { split($1,a,": "); split($2,b,": "); printf "   %-24s %14d\n", a[1], b[2]-a[2] }'
