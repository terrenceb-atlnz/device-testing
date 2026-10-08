#!/bin/bash
# T22655 run 1 -- modbus dynamic changes. Runs ON tb470. Console = stack master /dev/u5 @115200.
# Usage: bash 22655.sh setup|s1|s2|s3|s4|teardown
ID=22655; W=/tmp/modbus-1008; T=$W/tools; H=10.38.215.10
D=~/claude/device-testing/tb470/IE520/modbus-2026-10-08T1131/$ID
CK()  { CKTO=${CKTO:-90} python3 $T/ckcon.py /dev/u5 115200 $W/console-u5.log --stop-on-error "$@"; }
MB()  { python3 $T/mb.py --host $H --log $W/mb-$ID.log "$@"; }
LOG='show log | include modbusd|NSM.*port1.0.2|port1.0.2'
P2="show interface port1.0.2 status"
case "$1" in
setup)
  echo "### $(date '+%F %T %Z') PRECONDITION"
  CK "show stack" "show scada modbus tcp server" "show running-config | include scada" "show static-channel-group" "$P2" "show running-config interface port1.0.2"
  MB probe
  CK "configure terminal" "scada modbus tcp server" "scada modbus tcp server access read-write" "end" \
     "show scada modbus tcp server" "show running-config | include scada" || exit 2
  MB read 0x0000 1 UINT "precondition: client retrieves Mapping Version"
  CK "show running-config" > $W/$ID-rc-after-setup.out
  python3 $T/rc2cfg.py $W/$ID-rc-after-setup.out $D/stk_a.cfg \
    "stk_a  IE520-stk  AT-IE520-28GSX  S/N 264A23061 (member 1), 264A23066 (member 3, master), 264A23052 (member 4)  main-calanm" \
    "case $ID, run 1, captured $(date '+%F %H:%M %Z') after setup, before step 1" "testbox tb470, console u5"
  ;;
s1)
  echo "### $(date '+%F %T %Z') STEP 1 -- dynamic TCP port change"
  CK "configure terminal" "scada modbus tcp server port 5020" "end" "show scada modbus tcp server" "show running-config | include scada" || exit 2
  MB --port 502 read 0x0000 1 UINT "old port 502"
  MB --port 5020 read 0x0000 1 UINT "new port 5020"
  CK "configure terminal" "no scada modbus tcp server port" "end" "show scada modbus tcp server" "show running-config | include scada" || exit 2
  MB --port 5020 read 0x0000 1 UINT "after restore: 5020"
  MB --port 502 read 0x0000 1 UINT "after restore: 502"
  ;;
s2)
  echo "### $(date '+%F %T %Z') STEP 2 -- dynamic disable / enable"
  CK "configure terminal" "no scada modbus tcp server" "end" "show scada modbus tcp server" "show running-config | include scada" || exit 2
  MB read 0x0000 1 UINT "server disabled"
  CK "configure terminal" "scada modbus tcp server" "end" "show scada modbus tcp server" "show running-config | include scada" || exit 2
  MB read 0x0000 1 UINT "server re-enabled"
  ;;
s3)
  echo "### $(date '+%F %T %Z') STEP 3 -- API disables then enables a port: port1.0.2 (unit 1, 0x500d current, 0x500e configured)"
  CK "$P2"
  MB --slave 1 read 0x500d 1 HEX "before: current"
  MB --slave 1 read 0x500e 1 HEX "before: configured"
  MB --slave 1 write 0x500e 0x0000 "API disable port1.0.2"
  sleep 5
  MB --slave 1 read 0x500d 1 HEX "after disable: current"
  MB --slave 1 read 0x500e 1 HEX "after disable: configured"
  CK "show interface port1.0.2" "$P2" "show running-config interface port1.0.2" "$LOG"
  MB --slave 1 write 0x500e 0xf000 "API enable port1.0.2"
  sleep 10
  MB --slave 1 read 0x500d 1 HEX "after enable: current"
  MB --slave 1 read 0x500e 1 HEX "after enable: configured"
  CK "show interface port1.0.2" "$P2" "show running-config interface port1.0.2" "$LOG" "show scada modbus tcp server"
  echo "### $(date '+%F %T %Z') STEP 3 control -- the same write on a NON-aggregator port, port1.0.1 (unit 1, 0x5001)"
  MB --slave 1 write 0x5001 0x0000 "API disable port1.0.1"
  MB --slave 1 read 0x5001 1 HEX "after disable"
  CK "show interface port1.0.1 status"
  MB --slave 1 write 0x5001 0xf000 "API enable port1.0.1"
  MB --slave 1 read 0x5001 1 HEX "after enable"
  CK "show interface port1.0.1 status" "show running-config interface port1.0.1"
  ;;
s4)
  echo "### $(date '+%F %T %Z') STEP 4 -- CLI shutdown, Modbus reflects it (port1.0.2)"
  CK "configure terminal" "interface port1.0.2" "shutdown" "end" "show interface port1.0.2" "$P2" || exit 2
  sleep 4
  MB --slave 1 read 0x500d 1 HEX "after CLI shutdown: current"
  MB --slave 1 read 0x500e 1 HEX "after CLI shutdown: configured"
  CK "configure terminal" "interface port1.0.2" "no shutdown" "end" || exit 2
  sleep 10
  MB --slave 1 read 0x500d 1 HEX "after CLI no shutdown: current"
  MB --slave 1 read 0x500e 1 HEX "after CLI no shutdown: configured"
  CK "show interface port1.0.2" "$P2" "show running-config interface port1.0.2" "show static-channel-group" "$LOG"
  ;;
teardown)
  echo "### $(date '+%F %T %Z') TEARDOWN"
  CK "configure terminal" "no scada modbus tcp server access" "no scada modbus tcp server" "end" "show scada modbus tcp server" \
     "show running-config | include scada" "$P2"
  MB probe
  CK "show running-config" > $W/$ID-rc-after-teardown.out
  python3 $T/rcdiff.py $W/baseline-rc.out $W/$ID-rc-after-teardown.out && echo "rcdiff rc=$? (no lines above = IDENTICAL)"
  ;;
esac
