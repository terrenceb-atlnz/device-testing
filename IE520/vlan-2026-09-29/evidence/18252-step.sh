#!/bin/bash
# 18252-step.sh <label> <send-iface> <src-mac> <cap-iface1> <cap-iface2>
# One T18252 step: capture on two host NICs (by PID), read DUT output counters, send five
# 100-frame bursts (ip10 ip20 ipx ipv6 other) with a counter read after each, stop, count.
cd /tmp/ckvlan
L=$1; SIF=$2; SRC=$3; CAP1=$4; CAP2=$5
C="python3 ckcon.py /dev/u5 115200 /tmp/ckvlan/console-u5.log"
CNT="show interface port3.0.13,port1.0.2,port1.0.9,port1.0.13,port4.0.9,port4.0.26 | include Interface|output packets"
sudo -n tcpdump -i $CAP1 -nn -e -w /tmp/ckvlan/18252-$L-$CAP1.pcap "ether src $SRC" >/tmp/ckvlan/td-$L-1.log 2>&1 & P1=$!
sudo -n tcpdump -i $CAP2 -nn -e -w /tmp/ckvlan/18252-$L-$CAP2.pcap "ether src $SRC" >/tmp/ckvlan/td-$L-2.log 2>&1 & P2=$!
sleep 3
echo "### $(date +%T) counters before any burst"; $C "$CNT"
for spec in ip10 ip20 ipx ipv6 other; do
  sudo -n python3 vsend.py $SIF 100 $spec --src $SRC --tag $L$spec
  sleep 2
  echo "### $(date +%T) counters after $spec"; $C "$CNT"
done
sleep 2; sudo -n kill $P1 $P2; sleep 2
echo "### tcpdump logs"; cat /tmp/ckvlan/td-$L-1.log /tmp/ckvlan/td-$L-2.log
echo "### captures"; sudo -n chmod a+r /tmp/ckvlan/18252-$L-*.pcap; python3 vcount.py /tmp/ckvlan/18252-$L-$CAP1.pcap /tmp/ckvlan/18252-$L-$CAP2.pcap
