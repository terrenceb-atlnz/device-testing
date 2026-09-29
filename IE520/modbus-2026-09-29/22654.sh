#!/bin/bash
# T22654 modbus - write. Console = stack master /dev/u5; client tb470 eth1 -> vlan1 10.38.215.10:502
cd /tmp/ckmodbus
C="python3 ckcon.py /dev/u5 115200 /tmp/ckmodbus/console-u5.log"
M="python3 mb.py --log /tmp/ckmodbus/mb-22654.log"
V6=fd32:b1f0:dff8:d701::10
LL=fe80::200:cdff:fe37:d6f%eth1
echo "### $(date) T22654 setup: server + read-write access"
$C --stop-on-error "configure terminal" "scada modbus tcp server" "scada modbus tcp server access read-write" "end" "show scada modbus tcp server | include MODBUS|Write|Port" "show running-config | include scada|alarm" "show running-config interface port1.0.1" || { echo SETUP-FAILED; exit 2; }
sleep 2
echo "### $(date) discovery: alarm #1 registers, unit 1 and unit 0"
$M --slave 1 read 0x3000 1 ENUM "alarm #1 type (member 1)"
$M --slave 1 read 0x3001 1 HEX  "alarm #1 config (member 1)"
$M --slave 1 read 0x3002 1 BOOL "alarm #1 status (member 1)"
$M --slave 1 read 0x3003 1 ENUM "alarm #2 type (member 1)"
$M --slave 0 read 0x3000 1 ENUM "alarm #1 type (unit 0)"
$M --slave 1 read 0x5001 1 HEX  "port #1 configured state before"
echo "### $(date) STEP 1: write 0x3001 alarm #1 config = 0x0001 (bit0 = LED), unit 1"
$M --slave 1 write 0x3001 0x0001 "step1 alarm #1 config LED on"
sleep 2
$M --slave 1 read 0x3001 1 HEX "step1 read-back"
$C "show alarm facility settings | include PSU|Alarm  " "show running-config | include alarm" "show log | include larm|ODBUS|odbus|SCADA"
echo "### $(date) STEP 1 restore: write 0x3001 = 0x0000"
$M --slave 1 write 0x3001 0x0000 "step1 alarm #1 config back to none"
sleep 2
$M --slave 1 read 0x3001 1 HEX "step1 restore read-back"
$C "show alarm facility settings | include PSU" "show running-config | include alarm"
echo "### $(date) STEP 2: write 0x5001 port #1 (port1.0.1) configured state = 0x0000 (down), unit 1"
$M --slave 1 write 0x5001 0x0000 "step2 port1.0.1 admin down"
sleep 3
$M --slave 1 read 0x5001 1 HEX "step2 read-back configured"
$M --slave 1 read 0x5000 1 HEX "step2 read-back current"
$C "show interface port1.0.1 | include Link|configured" "show running-config interface port1.0.1" "show interface port1.0.1 status" "show log | include port1.0.1|ODBUS|odbus|SCADA"
echo "### $(date) STEP 2 restore: write 0x5001 = 0xf000 (up, all auto)"
$M --slave 1 write 0x5001 0xf000 "step2 port1.0.1 admin up"
sleep 3
$M --slave 1 read 0x5001 1 HEX "step2 restore read-back"
$C "show interface port1.0.1 | include Link|configured" "show running-config interface port1.0.1"
echo "### $(date) STEP 3: write 0x5002 PoE configuration (no PoE on this platform: expect exception)"
$M --slave 1 read 0x5002 1 HEX "step3 PoE config read"
$M --slave 1 write 0x5002 0xff00 "step3 PoE data-pairs enable attempt"
$C "show power-inline" "show scada modbus tcp server | include illegal|single register"
echo "### $(date) STEP 4: global IPv6 on vlan1 then the port write over IPv6"
$C --stop-on-error "configure terminal" "interface vlan1" "ipv6 address $V6/64" "end" "show ipv6 interface brief" || { echo IPV6-FAILED; }
sleep 3
ping -6 -c 2 -W 2 $V6; echo ping6-rc=$?
$M --host $V6 --slave 1 write 0x5001 0x0000 "step4 IPv6 global: port1.0.1 admin down"
sleep 3
$M --host $V6 --slave 1 read 0x5001 1 HEX "step4 read-back over IPv6"
$C "show interface port1.0.1 | include Link|configured" "show scada modbus tcp server connections" "show log | include port1.0.1|ODBUS|odbus|SCADA"
$M --host $V6 --slave 1 write 0x5001 0xf000 "step4 IPv6 global: port1.0.1 admin up"
sleep 3
$M --host $V6 --slave 1 read 0x5001 1 HEX "step4 restore read-back over IPv6"
$C "show interface port1.0.1 | include Link|configured"
echo "### $(date) STEP 5: link-local IPv6 $LL"
ping -6 -c 2 -W 2 $LL; echo ping6-ll-rc=$?
$M --host "$LL" --slave 1 write 0x5001 0x0000 "step5 IPv6 link-local: port1.0.1 admin down"
sleep 3
$M --host "$LL" --slave 1 read 0x5001 1 HEX "step5 read-back over link-local"
$C "show interface port1.0.1 | include Link|configured" "show log | include port1.0.1|ODBUS|odbus|SCADA"
$M --host "$LL" --slave 1 write 0x5001 0xf000 "step5 IPv6 link-local: port1.0.1 admin up"
sleep 3
$M --host "$LL" --slave 1 read 0x5001 1 HEX "step5 restore read-back over link-local"
$C "show interface port1.0.1 | include Link|configured" "show running-config interface port1.0.1" "show scada modbus tcp server"
echo "### $(date) teardown"
$C --stop-on-error "configure terminal" "interface vlan1" "no ipv6 address $V6/64" "exit" "no scada modbus tcp server access" "no scada modbus tcp server" "end" "show scada modbus tcp server" "show ipv6 interface brief" "show running-config | include scada|alarm|ipv6 address"
$M probe
$C "show running-config" | sed 1d > /home/terrenceb/claude/device-testing/IE520/modbus-2026-09-29/post-test-configs/22654.u5.show_running-config.txt
echo "### $(date) done"
