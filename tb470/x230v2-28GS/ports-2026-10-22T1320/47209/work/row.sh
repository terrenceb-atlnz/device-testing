#!/bin/bash
# T47209 run 1, one speed/duplex row on x230 port1.0.25 (the case's own step script; ports/VLAN written in).
# usage: row.sh <label> [config-if cmd ...]     env POLL=<s> (link-up poll, default 20)
#   1. the row's commands in `interface port1.0.25` (none = no config change)
#   2. link poll + status/running-config/counters of port1.0.25 and port1.0.26 (BEFORE counters)
#   3. tcpdump on tb470 eth1 (src = eth2's MAC) while eth2 sends 100 TEST frames (ip10, untagged, dst eth1)
#      and 100 CONTROL frames (ip20, 802.1Q vid 1000, dst eth1: must be dropped at access port1.0.10)
#   4. vcount on the pcap, then the AFTER counters and the log tail.
# Everything goes to work/row-<label>.out.
set -u
R=/media/terrenceb/mnt/testbox_home/claude/device-testing
W=$R/tb470/x230v2-28GS/ports-2026-10-22T1320/47209/work
S=x230p1022
E1=00:f0:4d:00:77:16
E2=00:f0:4d:00:77:17
L=$1; shift
cd "$R" || exit 9
{
  echo "### row $L  $(date '+%F %T %Z')  cmds: $*"
  if [ $# -gt 0 ]; then
    tools/tb ckcon tb470 $S u1 115200 'configure terminal' 'interface port1.0.25' "$@" 'end'
    echo "### ckcon(config) exit $?"
  fi
  tools/tb ckcon tb470 $S u1 115200 'terminal length 0' \
    "@poll ${POLL:-20} Link\\sis\\sUP show interface port1.0.25" \
    'show interface port1.0.25-1.0.26 status' 'show running-config interface port1.0.25-1.0.26' \
    'show interface port1.0.25' 'show interface port1.0.26' 'show interface port1.0.10' 'show interface port1.0.2'
  echo "### ckcon(before) exit $?"
  tools/tb capture tb470 $S eth1 25 "t47209-$L.pcap" ether src $E2 &
  CP=$!
  sleep 4
  tools/tb sudotool tb470 $S vsend eth2 100 ip10 --src $E2 --dst $E1 --tag "TEST_${L//-/_}"
  echo "### vsend TEST exit $?"
  tools/tb sudotool tb470 $S vsend eth2 100 ip20 --src $E2 --dst $E1 --vlan 1000 --tag "CTRL_${L//-/_}"
  echo "### vsend CTRL exit $?"
  wait $CP
  echo "### capture exit $?"
  tools/tb tool tb470 $S vcount "/tmp/$S/t47209-$L.pcap"
  echo "### vcount exit $?"
  tools/tb ckcon tb470 $S u1 115200 'terminal length 0' 'show interface port1.0.25-1.0.26 status' \
    'show interface port1.0.25' 'show interface port1.0.26' 'show interface port1.0.10' 'show interface port1.0.2' 'show log tail 15'
  echo "### ckcon(after) exit $?  $(date '+%T')"
} > "$W/row-$L.out" 2>&1
grep -a -E '^###|%|@poll|port1\.0\.2[56] +-|input packets|output packets|^Interface|Link is|configured|speed|duplex|CKVLAN|marker=|total|marked|sent|Unsupported|Failed|failed|EXFX|NSM' "$W/row-$L.out" | grep -a -v -E 'peak rate|^1[0-9]{9}' | head -${HEAD:-70}
