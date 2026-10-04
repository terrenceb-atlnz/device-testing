#!/bin/bash
# T27887 supplementary (2026-10-05T1052) -- one traffic stage, run ON tb470.
# usage: stage.sh <name> <tx-nic> <src-mac> <dst-mac> [vsend options ...]
#   e.g. stage.sh s0f eth1 00:00:5e:00:53:01 00:00:5e:00:53:ff --vlan 2100
# It reads the DUT port counters on u5 (stack console) before and after, captures INBOUND
# frames from <src-mac> on eth1 AND eth3 (tcpdump -Q in), sends 100 x ip10 with vsend.py
# (marker CKVLAN-<name>), and counts the captures with vcount.py.
# Case-specific: ports port1.0.9/port1.0.10, NICs eth1/eth3, console /dev/u5 are written in.
set -u
name=$1; tx=$2; src=$3; dst=$4; shift 4
S=/tmp/ckvlan1052; T=$S/tools
cnt() { echo "### $(date +%T) counters $1"
  ( cd $T && timeout 120 python3 ckcon.py /dev/u5 115200 $S/console-u5.log \
      "show interface port1.0.9,port1.0.10 | include Interface|input packets|output packets" ) ; }
cnt before
for n in eth1 eth3; do
  sudo -n timeout 14 /usr/bin/tcpdump -i $n -Q in -U -nn -s0 -w $S/27887-$name-$n.pcap ether src $src \
      > $S/27887-$name-$n.tcpdump.log 2>&1 &
done
sleep 3
( cd $T && sudo -n python3 vsend.py $tx 100 ip10 --src $src --dst $dst --tag $name "$@" )
wait
cnt after
echo "### tcpdump logs"; cat $S/27887-$name-eth1.tcpdump.log $S/27887-$name-eth3.tcpdump.log
echo "### captures"
( cd $T && python3 vcount.py $S/27887-$name-eth1.pcap $S/27887-$name-eth3.pcap )
