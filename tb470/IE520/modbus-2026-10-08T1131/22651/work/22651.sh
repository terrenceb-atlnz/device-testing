#!/bin/bash
# T22651 run 1 -- read Sensor information. Runs ON tb470. Console = stack master /dev/u5 @115200.
# Usage: bash 22651.sh setup|steps|teardown
ID=22651; W=/tmp/modbus-1008; T=$W/tools; H=10.38.215.10
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
  CK "show system environment"
  for u in 1 3 4 0; do
    echo "### $(date '+%F %T %Z') unit $u"
    MB --slave $u read 0x1000 1 ENUM  "unit $u step1 #1 Sensor Type"
    MB --slave $u read 0x1001 2 FLOAT "unit $u step2 #1 Sensor Reading"
    MB --slave $u read 0x1003 1 ENUM  "unit $u step3 #1 Sensor Units"
    MB --slave $u read 0x1004 1 UINT  "unit $u step4 #1 Sensor Fault Status"
    MB --slave $u read 0x1005 1 ENUM  "unit $u step5 #2 Sensor Type"
    MB --slave $u read 0x1006 2 FLOAT "unit $u step5 #2 Sensor Reading"
    MB --slave $u read 0x1008 1 ENUM  "unit $u step5 #2 Sensor Units"
    MB --slave $u read 0x1009 1 UINT  "unit $u step5 #2 Sensor Fault Status"
    MB --slave $u read 0x1000 25 RAW  "unit $u sensors 1-5 block"
    MB --slave $u read 0x1019 5 RAW   "unit $u past sensor 5"
  done
  CK "show system environment" "show scada modbus tcp server"
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
