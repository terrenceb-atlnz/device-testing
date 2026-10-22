#!/bin/bash
# T47228 VLAN step driver: one RESTCONF request (optional), then RESTCONF GETs of vlan3999/vlan3998 and the DUT CLI VLAN tables.
# usage: vstep.sh <label> <METHOD|-> [<path> [<json body>]]   (run from the repo root)
L=$1; M=$2; P=$3; B=$4
W=tb470/x230v2-28GS/mgmt-2026-10-22T1320/47228/work
RC="tools/tb tool tb470 mgmt1022 restconf 10.38.215.35"
{
date "+=== %T $L"
if [ "$M" != "-" ]; then
  if [ -n "$B" ]; then $RC $M "$P" --root /restconf --data "$B"; else $RC $M "$P" --root /restconf; fi
  echo "request-exit=$?"
fi
sleep 2
for v in vlan3999 vlan3998; do
  $RC GET data/ietf-interfaces:interfaces/interface=$v --root /restconf; echo "ietf-$v-exit=$?"
  $RC GET data/openconfig-interfaces:interfaces/interface=$v/state --root /restconf --grep 'name|type|admin-status|oper-status'; echo "oc-$v-exit=$?"
done
tools/tb ckcon tb470 mgmt1022 u1 115200 'show vlan brief | include 399' 'show interface brief | include vlan399' 'show running-config | include 399' 'show log tail 10'; echo "u1-exit=$?"
} > $W/$L.out 2>&1
grep -a -E '^===|^HTTP|exit=|"name"|"type"|status|error-message|error-tag|399|% ' $W/$L.out | grep -av '>>> ' | grep -av 'IMISH'
