#!/bin/bash
# 10624-traffic.sh <seconds> <tag> <rate> <pcap> [distinct]   (on tb470, cwd /tmp/ck12)
# Routed UDP from fake host 10.106.1.2 on eth1 (stack port3.0.10, vlan3101) to one host in
# each of the 500 OSPF-learned prefixes 10.124.0.0/24-10.125.243.0/24 -> stack -> SX link ->
# IE520-sa (static routes, redistributed into OSPF) -> fake host 10.106.3.2 (MAC
# 02:31:10:62:40:03) on SA port1.0.2 -> eth2, counted there. <rate> = pps or "top".
# "distinct" also writes every received frame's destination and reports how many distinct
# prefixes arrived (use only on short/slow runs).
E=/home/terrenceb/claude/device-testing/IE520/routing-2026-09-29/evidence/10624
mkdir -p $E; cd /tmp/ck12 || exit 1
dur=$1; tag=$2; rate=$3; pcap=$4; out=$E/10624-$tag
: > $out-summary.txt
F="ether dst 02:31:10:62:40:03 and udp dst port 6001"
sudo -n tcpdump -i eth2 -nn -s 64 -B 524288 -w /dev/null "$F" 2> /tmp/ck12/td24-$tag.log & t1=$!
[ "$5" = distinct ] && { sudo -n tcpdump -i eth2 -nn -s 64 -B 262144 "$F" > /tmp/ck12/rx24-$tag.txt 2>/dev/null & t2=$!; }
sudo -n tcpdump -i eth2 -nn -e -v -c 2 "$F" > $out-first2.txt 2>/dev/null & t3=$!
sleep 2
if [ "$rate" = top ]; then R="--topspeed"; else R="--pps=$rate"; fi
echo "start $(date +%T.%N | cut -c1-12) rate=$rate pcap=$pcap" | tee -a $out-summary.txt
sudo -n tcpreplay -i eth1 $R --no-flow-stats --duration=$dur --loop=0 $pcap > $out-tx.txt 2>&1
echo "end $(date +%T.%N | cut -c1-12)" | tee -a $out-summary.txt
sleep 3
for p in $t1 $t2 $t3; do [ -n "$p" ] && sudo -n kill -INT $(pgrep -P $p tcpdump) 2>/dev/null; done; wait
s=$(grep -oP 'Actual: \K[0-9]+' $out-tx.txt); r=$(grep -oP '^[0-9]+(?= packets captured)' /tmp/ck12/td24-$tag.log)
k=$(grep -oP '^[0-9]+(?= packets dropped by kernel)' /tmp/ck12/td24-$tag.log)
x=""; [ "$5" = distinct ] && x=" | distinct destination prefixes received=$(grep -oP '> \K10\.12[45]\.[0-9]+' /tmp/ck12/rx24-$tag.txt | sort -u | wc -l)"
echo "$(grep -E '^Rated' $out-tx.txt) | sent=$s received=$r kernel_drops=$k delivered=$(python3 -c "print('%.4f%%'%(100*$r/$s))")$x" | tee -a $out-summary.txt
