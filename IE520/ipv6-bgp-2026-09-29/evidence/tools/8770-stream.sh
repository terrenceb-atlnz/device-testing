#!/bin/bash
# 8770-stream.sh <pcap> <seconds> <tag>   (on tb470, cwd /tmp/ck11; the NS responder runs on eth1)
# Line-rate stream from eth2 (tcpreplay --topspeed, looped) to every destination in <pcap>,
# routed by the DUT onto vlan3971 -> eth1. Counts, per second, eth2 tx and eth1 rx
# (sysfs counters), and exactly (tcpdump -w /dev/null) the frames reaching eth1 for
# the fake neighbour MACs 02:87:70:*. A 2 s capture near the end measures coverage
# (distinct neighbour MACs delivered). Then the DUT's neighbour + hardware counts.
E=/home/terrenceb/claude/device-testing/IE520/ipv6-bgp-2026-09-29/evidence/8770
cd /tmp/ck11 || exit 1
pcap=$1; dur=$2; tag=$3; out=$E/8770-$tag
F='ether[0]=0x02 and ether[1]=0x87 and ether[2]=0x70'
sudo -n tcpdump -i eth1 -nn -s 64 -B 262144 -w /dev/null "$F" 2> /tmp/ck11/td-$tag.log &
tdp=$!
( for i in $(seq 1 $((dur + 4))); do
    echo "$(date +%T) eth2_tx=$(cat /sys/class/net/eth2/statistics/tx_packets) eth1_rx=$(cat /sys/class/net/eth1/statistics/rx_packets)"
    sleep 1; done ) > $out-persec.txt &
pp=$!
( sleep $((dur - 3)); sudo -n timeout 2 tcpdump -i eth1 -nn -s 64 -B 262144 -w /tmp/ck11/p/cov-$tag.pcap "$F" 2>/dev/null ) &
sleep 1
cp resp.json $out-resp-before.json
echo "start $(date +%T)"
sudo -n tcpreplay -i eth2 --topspeed --no-flow-stats --duration=$dur --loop=0 $pcap > $out-tcpreplay.txt 2>&1
echo "end $(date +%T)"
sleep 3
sudo -n kill -INT $(pgrep -P $tdp tcpdump) 2>/dev/null; wait $tdp
wait $pp
cp resp.json $out-resp-after.json
grep -E "Actual|Rated|Successful|Failed" $out-tcpreplay.txt
cat /tmp/ck11/td-$tag.log | grep -E "captured|dropped" | tee $out-rxcount.txt
echo "coverage: distinct neighbour MACs in the 2 s capture = $(tcpdump -r /tmp/ck11/p/cov-$tag.pcap -nn -e 2>/dev/null | awk '{print $4}' | sort -u | wc -l), frames = $(tcpdump -r /tmp/ck11/p/cov-$tag.pcap -nn 2>/dev/null | wc -l)" | tee $out-coverage.txt
CKTO=600 python3 ckcon.py /dev/u5 115200 /tmp/ck11/console-u5.log "show ipv6 neighbors" "show platform table ipv6" > $out-tables.out 2>&1
awk '/>>> show ipv6 neighbors/{s="nbr"} />>> show platform table/{s="hw"} /^Stack member/{m=$3} s=="nbr" && /2001:db8:8770:1::1:[0-9a-f]+ +[0-9a-f]{4}\./{n++} s=="hw" && /2001:db8:8770:1::1:[0-9a-f]+\/128/{c[m]++} END{printf "after: neighbours=%d",n; for(k in c) printf " hw[%s]=%d",k,c[k]; print ""}' $out-tables.out
