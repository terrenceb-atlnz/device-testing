#!/bin/bash
# T22650 run 1 -- read System information. Runs ON tb470. Console = stack master /dev/u5 @115200.
# Usage: bash 22650.sh <phase>   phase = setup | reads | teardown
ID=22650; W=/tmp/modbus-1008; T=$W/tools; H=10.38.215.10
CK()  { CKTO=${CKTO:-90} python3 $T/ckcon.py /dev/u5 115200 $W/console-u5.log --stop-on-error "$@"; }
MB()  { python3 $T/mb.py --host $H --log $W/mb-$ID.log "$@"; }
case "$1" in
setup)
  echo "### $(date '+%F %T %Z') SETUP"
  CK "show stack" "show scada modbus tcp server"
  MB probe
  CK "configure terminal" "scada modbus tcp server" "end" "show scada modbus tcp server" "show running-config | include scada"
  CK "show running-config" > $W/$ID-rc-after-setup.out
  ;;
reads)
  echo "### $(date '+%F %T %Z') CLI REFERENCE"
  CKTO=120 CK "show system" "show system mac" "show stack" "show stack detail" "show running-config | include hostname|provision" \
     "show system environment" "show alarm facility settings" "show alarm facility status" "show clock"
  echo "### $(date '+%F %T %Z') READS -- the case's literal addresses (unit 0)"
  MB read 0x0000 1 UINT  "s1 Mapping Version"
  MB read 0x0001 32 ASCII "s2 (case: Board Name)"
  MB read 0x0021 32 ASCII "s3 (case: Serial Number)"
  MB read 0x0041 1 UINT  "s4 (case: Number of Sensors)"
  MB read 0x0042 1 UINT  "s5 (case: Number of Alarms)"
  MB read 0x0043 1 UINT  "s6 (case: Number of Ports)"
  MB read 0x0044 1 UINT  "s7 (case: Number of Faults)"
  MB read 0x0045 32 ASCII "s8 (case: Software Version)"
  MB read 0x0065 32 ASCII "s9 (case: System Name)"
  MB read 0x0085 3 HEX   "s10 (case: HW Mac Address)"
  echo "### $(date '+%F %T %Z') READS -- Mapping Version 5 addresses (unit 0)"
  MB read 0x0000 1 UINT  "v5 Mapping Version"
  MB read 0x0001 32 ASCII "v5 System Name"
  MB read 0x0021 32 ASCII "v5 Software Version"
  MB read 0x0041 3 HEX   "v5 HW MAC"
  MB read 0x0044 1 HEX   "v5 stack-member bitmap"
  MB read 0x0045 1 UINT  "v5 Number of Ports"
  MB read 0x0046 1 UINT  "v5 Number of Faults"
  MB read 0x0047 1 UINT  "v5 Number of Sensors"
  MB read 0x0048 1 UINT  "v5 Number of Alarms (global)"
  MB read 0x0049 1 UINT  "v5 Number of Alarms (per-member total)"
  echo "### $(date '+%F %T %Z') READS -- per member (unit id = member), 1..4"
  for u in 1 2 3 4; do
    MB --slave $u read 0x0120 5 RAW   "unit $u member info [boards,ports,faults,sensors,alarms]"
    MB --slave $u read 0x0200 1 UINT  "unit $u board class"
    MB --slave $u read 0x0202 32 ASCII "unit $u Board Name"
    MB --slave $u read 0x0222 32 ASCII "unit $u Serial Number"
    MB --slave $u read 0x0242 3 HEX   "unit $u board MAC"
  done
  CK "show scada modbus tcp server"
  ;;
teardown)
  echo "### $(date '+%F %T %Z') TEARDOWN"
  CK "configure terminal" "no scada modbus tcp server" "end" "show scada modbus tcp server" "show running-config | include scada"
  MB probe
  CK "show running-config" > $W/$ID-rc-after-teardown.out
  python3 $T/rcdiff.py $W/baseline-rc.out $W/$ID-rc-after-teardown.out && echo "rcdiff rc=$? (no lines above = IDENTICAL)"
  ;;
esac
