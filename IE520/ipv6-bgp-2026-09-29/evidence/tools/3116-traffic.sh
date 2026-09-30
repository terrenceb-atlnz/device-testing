#!/bin/bash
# 3116-traffic.sh <seconds> <tag> <fw|rv|both> <len>   (on tb470, cwd /tmp/ck11)
# Line-rate routed unicast through the stack <-> IE520-sa BGP scenario, with tcpreplay --topspeed:
#   fw: eth1 (10.116.1.2, stack port3.0.13) -> stack -> SX link -> SA -> eth2 (10.116.3.2)
#   rv: eth2 (10.116.3.2, SA port1.0.2)   -> SA -> SX link -> stack -> eth1 (10.116.1.2)
# The receiving "hosts" are fake MACs (static ARP on the routers): 02:31:16:00:00:03 behind the SA,
# 02:31:16:00:00:01 behind the stack (tb470 forwards IP, so never a real NIC MAC).
# Exact per-direction receive counts: tcpdump -w /dev/null on each receiver; per-second sysfs.
E=/home/terrenceb/claude/device-testing/IE520/ipv6-bgp-2026-09-29/evidence/3116
cd /tmp/ck11 || exit 1
dur=$1; tag=$2; dirs=$3; len=$4; out=$E/3116-$tag
: > $out-summary.txt
if [ $dirs != rv ]; then
  sudo -n tcpdump -i eth2 -nn -s 64 -B 262144 -w /dev/null "ether dst 02:31:16:00:00:03 and udp dst port 9" 2> /tmp/ck11/td-fw-$tag.log & tf=$!; fi
if [ $dirs != fw ]; then
  sudo -n tcpdump -i eth1 -nn -s 64 -B 262144 -w /dev/null "ether dst 02:31:16:00:00:01 and udp dst port 9" 2> /tmp/ck11/td-rv-$tag.log & tr=$!; fi
( for i in $(seq 1 $((dur + 4))); do
    echo "$(date +%T) eth1_tx=$(cat /sys/class/net/eth1/statistics/tx_packets) eth1_rx=$(cat /sys/class/net/eth1/statistics/rx_packets) eth2_tx=$(cat /sys/class/net/eth2/statistics/tx_packets) eth2_rx=$(cat /sys/class/net/eth2/statistics/rx_packets)"
    sleep 1; done ) > $out-persec.txt &
pp=$!
sleep 1
echo "start $(date +%T)" | tee -a $out-summary.txt
[ $dirs != rv ] && { sudo -n tcpreplay -i eth1 --topspeed --no-flow-stats --duration=$dur --loop=0 p/fw$len.pcap > $out-tx-fw.txt 2>&1 & rf=$!; }
[ $dirs != fw ] && { sudo -n tcpreplay -i eth2 --topspeed --no-flow-stats --duration=$dur --loop=0 p/rv$len.pcap > $out-tx-rv.txt 2>&1 & rr=$!; }
[ -n "$rf" ] && wait $rf; [ -n "$rr" ] && wait $rr
echo "end $(date +%T)" | tee -a $out-summary.txt
sleep 3
[ -n "$tf" ] && { sudo -n kill -INT $(pgrep -P $tf tcpdump) 2>/dev/null; wait $tf; }
[ -n "$tr" ] && { sudo -n kill -INT $(pgrep -P $tr tcpdump) 2>/dev/null; wait $tr; }
wait $pp
for d in fw rv; do
  [ -f $out-tx-$d.txt ] || continue
  s=$(grep -oP 'Actual: \K[0-9]+' $out-tx-$d.txt); r=$(grep -oP '^[0-9]+(?= packets captured)' /tmp/ck11/td-$d-$tag.log)
  k=$(grep -oP '^[0-9]+(?= packets dropped by kernel)' /tmp/ck11/td-$d-$tag.log)
  echo "$d: $(grep -E '^Rated' $out-tx-$d.txt) | sent=$s received=$r kernel_drops=$k delivered=$(python3 -c "print('%.4f%%'%(100*$r/$s))")" | tee -a $out-summary.txt
done
