#!/bin/bash
# 11346-traffic.sh <seconds> <tag> <rate> <pcap>   (on tb470, cwd /tmp/ck12)
# Multicast source on eth1 (stack port3.0.13, vlan3111) -> stack (PIM-DM) -> SX link ->
# IE520-sa (PIM-DM) -> SA port1.0.2 (vlan3113) -> eth2, counted exactly at eth2.
# <rate> = a pps number, or "top" for --topspeed.  Receiver count: tcpdump -w /dev/null on eth2
# for the group's MAC and UDP 5001; eth1 is also watched for the group so a frame looped back
# to the source port would show.
E=/home/terrenceb/claude/device-testing/IE520/routing-2026-09-29/evidence/11346
mkdir -p $E; cd /tmp/ck12 || exit 1
dur=$1; tag=$2; rate=$3; pcap=$4; out=$E/11346-$tag
: > $out-summary.txt
sudo -n tcpdump -i eth2 -nn -s 64 -B 262144 -w /dev/null "ether dst 01:00:5e:71:01:01 and udp dst port 5001" 2> /tmp/ck12/td-rx-$tag.log & t1=$!
sudo -n tcpdump -i eth2 -nn -e -c 3 "ether dst 01:00:5e:71:01:01 and udp dst port 5001" > $out-first3.txt 2>/dev/null & t3=$!
sleep 1
if [ "$rate" = top ]; then R="--topspeed"; else R="--pps=$rate"; fi
echo "start $(date +%T.%N | cut -c1-12) rate=$rate" | tee -a $out-summary.txt
sudo -n tcpreplay -i eth1 $R --no-flow-stats --duration=$dur --loop=0 $pcap > $out-tx.txt 2>&1
echo "end $(date +%T.%N | cut -c1-12)" | tee -a $out-summary.txt
sleep 3
sudo -n kill -INT $(pgrep -P $t1 tcpdump) 2>/dev/null; wait $t1
sudo -n kill -INT $(pgrep -P $t3 tcpdump) 2>/dev/null; wait $t3 2>/dev/null
s=$(grep -oP 'Actual: \K[0-9]+' $out-tx.txt); r=$(grep -oP '^[0-9]+(?= packets captured)' /tmp/ck12/td-rx-$tag.log)
k=$(grep -oP '^[0-9]+(?= packets dropped by kernel)' /tmp/ck12/td-rx-$tag.log)
echo "$(grep -E '^Rated' $out-tx.txt) | sent=$s received=$r kernel_drops=$k delivered=$(python3 -c "print('%.4f%%'%(100*$r/$s))")" | tee -a $out-summary.txt
