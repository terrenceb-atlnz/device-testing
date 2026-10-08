#!/bin/bash
# T22653 run 1 -- read port information. Runs ON tb470. Console = stack master /dev/u5 @115200.
# Usage: bash 22653.sh setup|steps|teardown
ID=22653; W=/tmp/modbus-1008; T=$W/tools; H=10.38.215.10
D=~/claude/device-testing/tb470/IE520/modbus-2026-10-08T1131/$ID
CK()  { CKTO=${CKTO:-90} python3 $T/ckcon.py /dev/u5 115200 $W/console-u5.log --stop-on-error "$@"; }
CKN() { CKTO=${CKTO:-90} python3 $T/ckcon.py /dev/u5 115200 $W/console-u5.log "$@"; }   # an error is EXPECTED
MB()  { python3 $T/mb.py --host $H --log $W/mb-$ID.log "$@"; }
port_regs() {  # unit base-hex label
  local u=$1 b=$2 l=$3
  MB --slave $u read $(printf '0x%04x' $((b+0))) 1 HEX  "$l current state"
  MB --slave $u read $(printf '0x%04x' $((b+1))) 1 HEX  "$l configured state"
  MB --slave $u read $(printf '0x%04x' $((b+2))) 1 HEX  "$l PoE configuration"
  MB --slave $u read $(printf '0x%04x' $((b+3))) 1 UINT "$l PoE data-pairs power"
  MB --slave $u read $(printf '0x%04x' $((b+4))) 1 UINT "$l PoE spare-pairs power"
  MB --slave $u read $(printf '0x%04x' $((b+5))) 4 UINT "$l input bytes"
  MB --slave $u read $(printf '0x%04x' $((b+9))) 4 UINT "$l output bytes"
}
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
  echo "### $(date '+%F %T %Z') CLI before"
  CK "show interface port1.0.1" "show interface port1.0.1 status" "show running-config interface port1.0.1" "show system pluggable"
  CKN "show power-inline" "show power-inline interface port1.0.1"
  echo "### $(date '+%F %T %Z') STEPS 1-7: port #1 = port1.0.1, unit 1, block 0x5000"
  MB --slave 1 read 0x0120 5 RAW "unit 1 member info"
  port_regs 1 $((0x5000)) "s1-7 port1.0.1"
  MB --slave 1 read 0x5000 13 RAW "port1.0.1 whole 13-word block"
  CK "show interface port1.0.1"
  echo "### $(date '+%F %T %Z') EXTRA: linked port1.0.2 (unit 1, index 1, block 0x500d)"
  port_regs 1 $((0x500d)) "port1.0.2"
  CK "show interface port1.0.2" "show interface port1.0.2 status"
  echo "### $(date '+%F %T %Z') EXTRA: linked port3.0.13 (unit 3, index 12, block 0x509c) = the tb470 link"
  port_regs 3 $((0x509c)) "port3.0.13"
  CK "show interface port3.0.13"
  echo "### $(date '+%F %T %Z') unit 0 / unit 2 on 0x5000"
  MB read 0x5000 1 HEX "unit 0 0x5000"
  MB --slave 2 read 0x5000 1 HEX "unit 2 0x5000"
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
