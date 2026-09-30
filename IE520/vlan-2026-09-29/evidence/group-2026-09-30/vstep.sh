#!/bin/bash
# vstep.sh <case> <label> <send-iface> <src-mac> <dst-mac> <spec> <outer|-> <inner|-> <cap-ifaces...>
# Capture INBOUND frames from <src-mac> on each named tb470 NIC (tcpdump -Q in, stopped by PID), read the DUT
# port counters ($CNT_PORTS), send 100 marked frames (vsend.py), read the counters again, count captures (vcount.py).
cd /tmp/ckvlan3; K=$1; L=$2; SIF=$3; SRC=$4; DST=$5; SPEC=$6; OUT=$7; IN=$8; shift 8; CAPS="$@"
mkdir -p /tmp/ckvlan3/$K; W=/tmp/ckvlan3/$K
C="python3 ckcon.py /dev/u5 115200 /tmp/ckvlan3/console-u5.log"
CNT="show interface ${CNT_PORTS:-port3.0.13,port1.0.2,port1.0.9,port1.0.13,port4.0.9} | include Interface|input packets|output packets"
PIDS=""
for i in $CAPS; do sudo -n tcpdump -Q in -i $i -nn -e -w $W/$K-$L-$i.pcap "ether src $SRC" >$W/td-$L-$i.log 2>&1 & PIDS="$PIDS $!"; done
sleep 3
echo "### $(date +%T) $K $L counters before"; $C "$CNT"
A="--src $SRC --dst $DST --tag $L"; [ "$OUT" != "-" ] && A="$A --outer $OUT"; [ "$IN" != "-" ] && A="$A --vlan $IN"
sudo -n python3 vsend.py $SIF 100 $SPEC $A
sleep 3
echo "### $(date +%T) $K $L counters after"; $C "$CNT"
sudo -n kill $PIDS; sleep 2
echo "### tcpdump logs"; for i in $CAPS; do cat $W/td-$L-$i.log; done
echo "### captures"; sudo -n chmod a+r $W/$K-$L-*.pcap; python3 vcount.py $(for i in $CAPS; do echo $W/$K-$L-$i.pcap; done)
