#!/bin/bash
# T47228 step driver: one RESTCONF request (optional), then the state read at RESTCONF, the DUT CLI and the partner CLI.
# usage: step.sh <label> <METHOD|-> [<path> [<json body>]]   (run from the repo root)
L=$1; M=$2; P=$3; B=$4
W=tb470/x230v2-28GS/mgmt-2026-10-22T1320/47228/work
RC="tools/tb tool tb470 mgmt1022 restconf 10.38.215.35"
OC=data/openconfig-interfaces:interfaces/interface=port1.0.3
IE=data/ietf-interfaces:interfaces/interface=port1.0.3
{
date "+=== %T $L"
if [ "$M" != "-" ]; then
  if [ -n "$B" ]; then $RC $M "$P" --root /restconf --data "$B"; else $RC $M "$P" --root /restconf; fi
  echo "request-exit=$?"
fi
sleep ${SETTLE:-3}
$RC GET $OC/state --root /restconf --grep 'admin-status|oper-status|"enabled"'; echo "oc-state-exit=$?"
$RC GET $OC/config --root /restconf; echo "oc-config-exit=$?"
$RC GET $IE --root /restconf; echo "ietf-exit=$?"
tools/tb ckcon tb470 mgmt1022 u1 115200 'show interface brief | include port1.0.3 ' 'show running-config interface port1.0.3' 'show log tail 10'; echo "u1-exit=$?"
tools/tb ckcon tb470 mgmt1022 u0 115200 'show interface brief | include port1.0.3 ' 'show log tail 10'; echo "u0-exit=$?"
} > $W/$L.out 2>&1
grep -a -E '^===|^HTTP|exit=|admin-status|oper-status|enabled|port1.0.3|shutdown|% ' $W/$L.out | grep -av '>>> ' | grep -av 'IMISH'
