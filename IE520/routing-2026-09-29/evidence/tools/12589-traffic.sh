#!/bin/bash
# 12589-traffic.sh <tag> [pps] [loops] [pcap]   (on tb470, cwd /tmp/ck16)
# Sends the mk12589.py pcap (Pkts1 = src 192.168.10.1-127 / UDP sport 5001, Pkts2 = src
# 192.168.10.128-254 / sport 5002, VLAN 3210 tagged) out eth1 -> stack port3.0.10, and counts
# where the DUT forwarded each kind:
#   VLAN40 path = stack vlan3240 -> SX link -> IE520-sa routes -> SA port1.0.2 (vlan 3289 tagged) -> eth2,
#                 dst MAC 02:12:58:90:00:40 (the SA's static ARP for 172.16.89.2)
#   VLAN30 path = stack vlan3230 -> sa2 -> x230 routes -> x230 port1.0.1 (vlan 3289 tagged) -> eth3,
#                 dst MAC 02:12:58:90:00:30 (the x230's static ARP for 172.16.89.2)
# eth2/eth3 count promiscuously (fake MACs keep tb470's own stack out of the path).
# eth1 inbound counts frames the DUT sent BACK to tb470 (the misdirection seen at step 2).
# Each run is bracketed with tb470 IpForwDatagrams and the pkts counter of Terrence's
# `FORWARD -s 192.168.10.0/24 -j DROP` rule (added 2026-10-01 ~09:3x), and the tb470 uplink
# (dev network) is captured for any 192.168.10.0/24 source, so a leak is measured, not assumed.
# (On kernel 6.12 IpForwDatagrams counts BEFORE the FORWARD hook, so it rises even when dropped.)
E=/home/terrenceb/claude/device-testing/IE520/routing-2026-09-29/evidence/12589
cd /tmp/ck16 || exit 1
tag=$1; pps=${2:-1000}; loops=${3:-10}; pcap=${4:-/tmp/ck16/p12589.pcap}; out=$E/12589-$tag
: > $out-summary.txt
F40="vlan 3289 and ether dst 02:12:58:90:00:40 and udp dst port 5009"
F30="vlan 3289 and ether dst 02:12:58:90:00:30 and udp dst port 5009"
declare -A P
F1="udp dst port 5009"
fw(){ nstat -az IpForwDatagrams | awk '/IpForw/{print $2}'; }
dr(){ sudo -n /usr/sbin/iptables -L FORWARD -v -n -x | awk '$3=="DROP" && $8=="192.168.10.0/24"{print $1}'; }
fw0=$(fw); dr0=$(dr)
for k in 40:1 40:2 30:1 30:2 1:1 1:2; do
  n=${k%%:*}; c=${k##*:}; ifc=eth2; [ $n = 30 ] && ifc=eth3; [ $n = 1 ] && ifc="eth1 -Q in"; f=F$n
  sudo -n tcpdump -i $ifc -nn -s 96 -B 65536 -w /dev/null "${!f} and udp src port 500$c" 2> /tmp/ck16/td-$tag-v$n-p$c.log & P[$k]=$!
done
sudo -n tcpdump -i network -nn -s 96 -w /dev/null "src net 192.168.10.0/24" 2> /tmp/ck16/td-$tag-uplink.log & up=$!
sudo -n tcpdump -i network -nn -s 64 -w /dev/null 2> /tmp/ck16/td-$tag-uplinkall.log & ua=$!   # liveness: every frame on the uplink
sudo -n tcpdump -i eth2 -nn -e -v -c 2 "$F40" > $out-first-eth2.txt 2>/dev/null & f2=$!
sudo -n tcpdump -i eth3 -nn -e -v -c 2 "$F30" > $out-first-eth3.txt 2>/dev/null & f3=$!
sleep 2
echo "start $(date +%T.%N | cut -c1-12) pps=$pps loops=$loops pcap=$pcap" | tee -a $out-summary.txt
sudo -n tcpreplay -i eth1 --pps=$pps --loop=$loops --no-flow-stats $pcap > $out-tx.txt 2>&1
echo "end $(date +%T.%N | cut -c1-12)" | tee -a $out-summary.txt
sleep 3
for k in "${!P[@]}"; do sudo -n kill -INT $(pgrep -P ${P[$k]} tcpdump) 2>/dev/null; done
for p in $f2 $f3 $up $ua; do sudo -n kill -INT $(pgrep -P $p tcpdump) 2>/dev/null; done; wait
s=$(grep -oP 'Actual: \K[0-9]+' $out-tx.txt); fl=$(grep -oP 'Failed packets:\s*\K[0-9]+' $out-tx.txt)
cnt(){ grep -oP '^[0-9]+(?= packets captured)' /tmp/ck16/td-$tag-$1.log; }
drp(){ grep -oP '^[0-9]+(?= packets dropped by kernel)' /tmp/ck16/td-$tag-$1.log; }
echo "sent=$s (Pkts1=$((s/2)) Pkts2=$((s/2))) tcpreplay_failed=$fl" | tee -a $out-summary.txt
echo "VLAN40 path (eth2): Pkts1=$(cnt v40-p1) Pkts2=$(cnt v40-p2)   | VLAN30 path (eth3): Pkts1=$(cnt v30-p1) Pkts2=$(cnt v30-p2)   | back to eth1: Pkts1=$(cnt v1-p1) Pkts2=$(cnt v1-p2)   | kernel drops $(drp v40-p1)/$(drp v40-p2)/$(drp v30-p1)/$(drp v30-p2)/$(drp v1-p1)/$(drp v1-p2)" | tee -a $out-summary.txt
fw1=$(fw); dr1=$(dr)
echo "tb470 IpForwDatagrams $fw0 -> $fw1 (forward attempts $((fw1-fw0)), counted before the FORWARD hook)   FORWARD DROP 192.168.10.0/24 pkts $dr0 -> $dr1 (dropped $((dr1-dr0)))   on the uplink (dev network, src 192.168.10.0/24): $(cnt uplink) of $(cnt uplinkall) uplink frames captured in the window" | tee -a $out-summary.txt
