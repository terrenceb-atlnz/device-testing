#!/bin/bash
# T22652 run 1 -- read alarm information. Runs ON tb470. Console = stack master /dev/u5 @115200.
# Usage: bash 22652.sh setup|steps|teardown
ID=22652; W=/tmp/modbus-1008; T=$W/tools; H=10.38.215.10
D=~/claude/device-testing/tb470/IE520/modbus-2026-10-08T1131/$ID
CK()  { CKTO=${CKTO:-90} python3 $T/ckcon.py /dev/u5 115200 $W/console-u5.log --stop-on-error "$@"; }
MB()  { python3 $T/mb.py --host $H --log $W/mb-$ID.log "$@"; }
case "$1" in
setup)
  echo "### $(date '+%F %T %Z') SETUP"
  CK "show stack" "show scada modbus tcp server"
  MB probe
  CK "configure terminal" "scada modbus tcp server" "end" "show scada modbus tcp server" "show running-config | include scada" || exit 2
  CK "show running-config" > $W/$ID-rc-after-setup.out
  python3 $T/rc2cfg.py $W/$ID-rc-after-setup.out $D/stk_a.cfg \
    "stk_a  IE520-stk  AT-IE520-28GSX  S/N 264A23061 (member 1), 264A23066 (member 3, master), 264A23052 (member 4)  main-calanm" \
    "case $ID, run 1, captured $(date '+%F %H:%M %Z') after setup, before step 1" "testbox tb470, console u5"
  ;;
steps)
  echo "### $(date '+%F %T %Z') CLI REFERENCE"
  CKTO=120 CK "show alarm facility settings" "show alarm facility status" "show system environment" "show interface status" "show running-config | include alarm"
  echo "### $(date '+%F %T %Z') the case literal addresses, unit 1"
  MB --slave 1 read 0x3600 1 ENUM "case s1 #1 Alarm Type"
  MB --slave 1 read 0x3601 1 HEX  "case s2 #1 Alarm Configuration"
  MB --slave 1 read 0x3602 1 BOOL "case s3 #1 Alarm Status"
  for u in 1 3 4; do
    echo "### $(date '+%F %T %Z') unit $u, map-v5 alarm block 0x3000 (6 words per alarm)"
    MB --slave $u read 0x3000 1 ENUM "unit $u step1 #1 Alarm Type"
    MB --slave $u read 0x3001 1 HEX  "unit $u step2 #1 Alarm Configuration"
    MB --slave $u read 0x3005 1 BOOL "unit $u step3 #1 Alarm Status"
    MB --slave $u read 0x3002 3 RAW  "unit $u #1 reserved words"
    MB --slave $u read 0x3006 6 RAW  "unit $u #2 External PSU 2"
    MB --slave $u read 0x300c 6 RAW  "unit $u #3 Link down portN.0.1"
    MB --slave $u read 0x3012 6 RAW  "unit $u #4 Link down portN.0.2"
    MB --slave $u read 0x30b4 6 RAW  "unit $u #31 Temperature"
  done
  MB read 0x3000 6 RAW "unit 0 #1"
  CK "show scada modbus tcp server"
  ;;
teardown)
  echo "### $(date '+%F %T %Z') TEARDOWN"
  CK "configure terminal" "no scada modbus tcp server" "end" "show scada modbus tcp server" "show running-config | include scada"
  MB probe
  CK "show running-config" > $W/$ID-rc-after-teardown.out
  python3 $T/rcdiff.py $W/baseline-rc.out $W/$ID-rc-after-teardown.out && echo "rcdiff rc=$? (no lines above = IDENTICAL)"
  cp $W/$ID.out $W/mb-$ID.log $D/work/ 2>/dev/null
  ;;
esac
