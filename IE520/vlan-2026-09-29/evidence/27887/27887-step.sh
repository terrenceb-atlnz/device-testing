#!/bin/bash
# 27887-step.sh <label> <send-iface> <src-mac> <outer|-> <inner> <cap-ifaces...>
# Capture on the named host NICs (by PID), read port counters, send 100 marked frames, stop, count.
cd /tmp/ckvlan30
L=$1; SIF=$2; SRC=$3; OUT=$4; IN=$5; shift 5; CAPS="$@"
C="python3 ckcon.py /dev/u5 115200 /tmp/ckvlan30/console-u5.log"
CNT="show interface port3.0.13,port4.0.26 | include Interface|input packets|output packets"
PIDS=""
for i in $CAPS; do sudo -n tcpdump -i $i -nn -e -w /tmp/ckvlan30/27887-$L-$i.pcap "ether src $SRC" >/tmp/ckvlan30/td-$L-$i.log 2>&1 & PIDS="$PIDS $!"; done
sleep 3
echo "### $(date +%T) counters before"; $C "$CNT"
if [ "$OUT" = "-" ]; then sudo -n python3 vsend.py $SIF 100 ip10 --src $SRC --vlan $IN --tag $L
else sudo -n python3 vsend.py $SIF 100 ip10 --src $SRC --outer $OUT --vlan $IN --tag $L; fi
sleep 3
echo "### $(date +%T) counters after"; $C "$CNT"
sudo -n kill $PIDS; sleep 2
echo "### tcpdump logs"; for i in $CAPS; do cat /tmp/ckvlan30/td-$L-$i.log; done
echo "### captures"; sudo -n chmod a+r /tmp/ckvlan30/27887-$L-*.pcap; python3 vcount.py $(for i in $CAPS; do echo /tmp/ckvlan30/27887-$L-$i.pcap; done)
