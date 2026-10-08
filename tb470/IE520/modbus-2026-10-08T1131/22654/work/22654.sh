#!/bin/bash
# T22654 run 1 -- modbus write. Runs ON tb470. Console = stack master /dev/u5 @115200.
# Usage: bash 22654.sh setup|s1|s2|s3|s4|s5|teardown
ID=22654; W=/tmp/modbus-1008; T=$W/tools; H=10.38.215.10
H6=fd32:b1f0:dff8:d701::10; LL=fe80::200:cdff:fe37:d6f%eth1
D=~/claude/device-testing/tb470/IE520/modbus-2026-10-08T1131/$ID
CK()  { CKTO=${CKTO:-90} python3 $T/ckcon.py /dev/u5 115200 $W/console-u5.log --stop-on-error "$@"; }
CKN() { CKTO=${CKTO:-90} python3 $T/ckcon.py /dev/u5 115200 $W/console-u5.log "$@"; }   # an error is EXPECTED
MB()  { python3 $T/mb.py --log $W/mb-$ID.log "$@"; }
LOG='show log | include modbusd|user shutdown|user no shutdown|alarm'
case "$1" in
setup)
  echo "### $(date '+%F %T %Z') SETUP"
  CK "show stack" "show scada modbus tcp server" "show running-config | include scada|alarm" "show ipv6 interface brief"
  MB --host $H probe
  CK "configure terminal" "scada modbus tcp server" "scada modbus tcp server access read-write" "end" \
     "show scada modbus tcp server" "show running-config | include scada" || exit 2
  CK "show running-config" > $W/$ID-rc-after-setup.out
  python3 $T/rc2cfg.py $W/$ID-rc-after-setup.out $D/stk_a.cfg \
    "stk_a  IE520-stk  AT-IE520-28GSX  S/N 264A23061 (member 1), 264A23066 (member 3, master), 264A23052 (member 4)  main-calanm" \
    "case $ID, run 1, captured $(date '+%F %H:%M %Z') after setup, before step 1" "testbox tb470, console u5"
  ;;
s1)
  echo "### $(date '+%F %T %Z') STEP 1 -- alarm #1 configuration 0x3001, unit 1 (member 1, External PSU 1)"
  CK "show alarm facility settings | include PSU" "show running-config | include alarm" "show clock"
  MB --host $H --slave 1 read 0x3000 6 RAW "before: alarm #1 entry"
  MB --host $H --slave 1 write 0x3001 0x0001 "case literal bit 0 = 0x0001"
  MB --host $H --slave 1 read 0x3001 1 HEX "read-back after 0x0001"
  CK "show alarm facility settings | include PSU" "show running-config | include alarm"
  MB --host $H --slave 1 write 0x3001 0x8000 "LED bit, MSB-first = 0x8000"
  MB --host $H --slave 1 read 0x3000 6 RAW "read-back after 0x8000"
  CK "show alarm facility settings | include PSU" "show running-config | include alarm" "$LOG"
  MB --host $H --slave 1 write 0x3001 0x0000 "clear"
  MB --host $H --slave 1 read 0x3001 1 HEX "read-back after clear"
  CK "show alarm facility settings | include PSU" "show running-config | include alarm"
  ;;
s2)
  echo "### $(date '+%F %T %Z') STEP 2 -- port #1 (port1.0.1) configured state 0x5001, unit 1"
  CK "show interface port1.0.1" "show running-config interface port1.0.1"
  MB --host $H --slave 1 read 0x5001 1 HEX "before"
  MB --host $H --slave 1 write 0x5001 0x0000 "disable (state nibble 0, auto/auto/auto)"
  MB --host $H --slave 1 read 0x5001 1 HEX "read-back configured"
  MB --host $H --slave 1 read 0x5000 1 HEX "current"
  CK "show interface port1.0.1" "show running-config interface port1.0.1" "show interface port1.0.1 status" "$LOG"
  MB --host $H --slave 1 write 0x5001 0xf000 "enable (F, auto/auto/auto)"
  MB --host $H --slave 1 read 0x5001 1 HEX "read-back configured"
  CK "show interface port1.0.1" "show running-config interface port1.0.1" "$LOG"
  ;;
s3)
  echo "### $(date '+%F %T %Z') STEP 3 -- PoE configuration 0x5002, unit 1"
  MB --host $H --slave 1 read 0x5002 1 HEX "before"
  MB --host $H --slave 1 write 0x5002 0xff00 "data+spare pairs enabled"
  MB --host $H --slave 1 read 0x5002 1 HEX "read-back"
  CKN "show power-inline" "show power-inline interface port1.0.1"
  CK "$LOG"
  ;;
s4)
  echo "### $(date '+%F %T %Z') STEP 4 -- the port write over a GLOBAL IPv6 address"
  CK "configure terminal" "interface vlan1" "ipv6 address $H6/64" "end" "show ipv6 interface brief" || exit 2
  sleep 3; ping -6 -c 3 -I eth1 $H6
  MB --host $H6 --slave 1 write 0x5001 0x0000 "IPv6 global: disable port1.0.1"
  MB --host $H6 --slave 1 read 0x5001 1 HEX "IPv6 global: read-back"
  CK "show interface port1.0.1" "$LOG"
  MB --host $H6 --slave 1 write 0x5001 0xf000 "IPv6 global: enable port1.0.1"
  MB --host $H6 --slave 1 read 0x5001 1 HEX "IPv6 global: read-back"
  CK "show interface port1.0.1" "$LOG"
  ;;
s5)
  echo "### $(date '+%F %T %Z') STEP 5 -- the port write over LINK-LOCAL IPv6"
  ping -6 -c 3 -I eth1 ${LL%%%*}
  MB --host $LL --slave 1 write 0x5001 0x0000 "IPv6 link-local: disable port1.0.1"
  MB --host $LL --slave 1 read 0x5001 1 HEX "IPv6 link-local: read-back"
  CK "show interface port1.0.1" "$LOG"
  MB --host $LL --slave 1 write 0x5001 0xf000 "IPv6 link-local: enable port1.0.1"
  MB --host $LL --slave 1 read 0x5001 1 HEX "IPv6 link-local: read-back"
  CK "show interface port1.0.1" "show running-config interface port1.0.1" "$LOG" "show scada modbus tcp server"
  ;;
teardown)
  echo "### $(date '+%F %T %Z') TEARDOWN"
  CK "configure terminal" "interface vlan1" "no ipv6 address $H6/64" "exit" "no scada modbus tcp server access" \
     "no scada modbus tcp server" "end" "show scada modbus tcp server" "show running-config | include scada|alarm|ipv6 address"
  MB --host $H probe
  CK "show running-config" > $W/$ID-rc-after-teardown.out
  python3 $T/rcdiff.py $W/baseline-rc.out $W/$ID-rc-after-teardown.out && echo "rcdiff rc=$? (no lines above = IDENTICAL)"
  ;;
esac
