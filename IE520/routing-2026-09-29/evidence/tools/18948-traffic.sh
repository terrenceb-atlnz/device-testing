#!/bin/bash
# 18948-traffic.sh <seconds> <tag> <rate> <pcap>   (on tb470, cwd /tmp/ck12)
# Tagged routed UDP from 4 fake hosts in VLANs 3181-3184 on eth1 (stack port3.0.10, trunk) to
# the VRRP virtual MACs 0000.5e00.0151-54 -> stack (VRRP master) routes to 10.118.9.2 in
# vlan3189 -> SX link -> IE520-sa bridges 3189 -> SA port1.0.2 -> eth2. Counted at eth2: total
# (dst MAC 02:31:18:94:00:09, UDP 5001) and per ingress VLAN (UDP sport 5000+i).
# <rate> = pps number or "top" (--topspeed).
E=/home/terrenceb/claude/device-testing/IE520/routing-2026-09-29/evidence/18948
mkdir -p $E; cd /tmp/ck12 || exit 1
dur=$1; tag=$2; rate=$3; pcap=$4; out=$E/18948-$tag
: > $out-summary.txt
F="ether dst 02:31:18:94:00:09 and udp dst port 5001"
sudo -n tcpdump -i eth2 -nn -s 64 -B 524288 -w /dev/null "$F" 2> /tmp/ck12/td18-$tag-all.log & t0=$!
for i in 0 1 2 3; do
  sudo -n tcpdump -i eth2 -nn -s 64 -B 262144 -w /dev/null "$F and udp src port $((5000+i))" 2> /tmp/ck12/td18-$tag-v$i.log & eval t$((i+1))=\$!
done
sudo -n tcpdump -i eth2 -nn -e -v -c 4 "$F" > $out-first4.txt 2>/dev/null & t9=$!
sleep 2
if [ "$rate" = top ]; then R="--topspeed"; else R="--pps=$rate"; fi
echo "start $(date +%T.%N | cut -c1-12) rate=$rate pcap=$pcap" | tee -a $out-summary.txt
sudo -n tcpreplay -i eth1 $R --no-flow-stats --duration=$dur --loop=0 $pcap > $out-tx.txt 2>&1
echo "end $(date +%T.%N | cut -c1-12)" | tee -a $out-summary.txt
sleep 3
for p in $t0 $t1 $t2 $t3 $t4 $t9; do sudo -n kill -INT $(pgrep -P $p tcpdump) 2>/dev/null; done; wait
s=$(grep -oP 'Actual: \K[0-9]+' $out-tx.txt)
cnt(){ grep -oP '^[0-9]+(?= packets captured)' $1; }; drp(){ grep -oP '^[0-9]+(?= packets dropped by kernel)' $1; }
r=$(cnt /tmp/ck12/td18-$tag-all.log); k=$(drp /tmp/ck12/td18-$tag-all.log)
v="$(cnt /tmp/ck12/td18-$tag-v0.log)/$(cnt /tmp/ck12/td18-$tag-v1.log)/$(cnt /tmp/ck12/td18-$tag-v2.log)/$(cnt /tmp/ck12/td18-$tag-v3.log)"
vk="$(drp /tmp/ck12/td18-$tag-v0.log)/$(drp /tmp/ck12/td18-$tag-v1.log)/$(drp /tmp/ck12/td18-$tag-v2.log)/$(drp /tmp/ck12/td18-$tag-v3.log)"
echo "$(grep -E '^Rated' $out-tx.txt) | sent=$s received=$r kernel_drops=$k delivered=$(python3 -c "print('%.4f%%'%(100*$r/$s))") | per-VLAN 3181/3182/3183/3184 received=$v (drops $vk, expected $((s/4)) each)" | tee -a $out-summary.txt
