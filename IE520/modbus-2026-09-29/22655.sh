#!/bin/bash
# T22655 modbus - dynamic changes. Console = stack master /dev/u5; client tb470 eth1 -> vlan1 10.38.215.10
cd /tmp/ckmodbus
C="python3 ckcon.py /dev/u5 115200 /tmp/ckmodbus/console-u5.log"
M="python3 mb.py --log /tmp/ckmodbus/mb-22655.log"
echo "### $(date) precondition: server enabled read-write, client reads OK on 502"
$C --stop-on-error "configure terminal" "scada modbus tcp server" "scada modbus tcp server access read-write" "end" "show scada modbus tcp server | include MODBUS|Write|Port  " || { echo SETUP-FAILED; exit 2; }
sleep 2
$M read 0x0000 1 UINT "precondition: mapping version on 502"
echo "### $(date) STEP 1: dynamic change of the TCP port to 5020"
$C --stop-on-error "configure terminal" "scada modbus tcp server port 5020" "end" "show scada modbus tcp server | include Port  " "show running-config | include scada"
sleep 2
$M --port 502 read 0x0000 1 UINT "step1 old port 502 (expect refused)"
$M --port 5020 read 0x0000 1 UINT "step1 new port 5020"
$C "show scada modbus tcp server | include holding"
echo "### $(date) STEP 1 restore: port back to 502 (no form first)"
$C "configure terminal" "no scada modbus tcp server port" "end" "show scada modbus tcp server | include MODBUS|Port  " "show running-config | include scada"
sleep 2
$M --port 5020 read 0x0000 1 UINT "step1 restore: 5020 (expect refused)"
$M --port 502 read 0x0000 1 UINT "step1 restore: 502 works again"
echo "### $(date) STEP 2: dynamic disable / enable"
$C --stop-on-error "configure terminal" "no scada modbus tcp server" "end" "show scada modbus tcp server"
sleep 2
$M read 0x0000 1 UINT "step2 disabled (expect refused)"
$C --stop-on-error "configure terminal" "scada modbus tcp server" "end" "show scada modbus tcp server | include MODBUS|Write|Port  " "show running-config | include scada"
sleep 2
$M read 0x0000 1 UINT "step2 re-enabled"
echo "### $(date) STEP 3: API disables then enables port1.0.2 (member 1 index 1: 0x500d current, 0x500e configured)"
$M --slave 1 read 0x500d 1 HEX "step3 before: current"
$M --slave 1 read 0x500e 1 HEX "step3 before: configured"
$M --slave 1 write 0x500e 0x0000 "step3 API: port1.0.2 down"
sleep 5
$M --slave 1 read 0x500d 1 HEX "step3 after API down: current"
$M --slave 1 read 0x500e 1 HEX "step3 after API down: configured"
$C "show interface port1.0.2 | include Link" "show interface port1.0.2 status" "show running-config interface port1.0.2" "show log | include port1.0.2"
$M --slave 1 write 0x500e 0xf000 "step3 API: port1.0.2 up"
sleep 10
$M --slave 1 read 0x500d 1 HEX "step3 after API up: current"
$M --slave 1 read 0x500e 1 HEX "step3 after API up: configured"
$C "show interface port1.0.2 | include Link" "show interface port1.0.2 status" "show running-config interface port1.0.2"
echo "### $(date) STEP 4: CLI shutdown port1.0.2, Modbus reflects it"
$C --stop-on-error "configure terminal" "interface port1.0.2" "shutdown" "end" "show interface port1.0.2 | include Link" "show interface port1.0.2 status"
sleep 4
$M --slave 1 read 0x500d 1 HEX "step4 after CLI shutdown: current"
$M --slave 1 read 0x500e 1 HEX "step4 after CLI shutdown: configured"
$C --stop-on-error "configure terminal" "interface port1.0.2" "no shutdown" "end"
sleep 10
$M --slave 1 read 0x500d 1 HEX "step4 after CLI no shutdown: current"
$M --slave 1 read 0x500e 1 HEX "step4 after CLI no shutdown: configured"
$C "show interface port1.0.2 | include Link" "show interface port1.0.2 status" "show running-config interface port1.0.2" "show static-channel-group" "show scada modbus tcp server"
echo "### $(date) teardown"
$C --stop-on-error "configure terminal" "no scada modbus tcp server access" "no scada modbus tcp server" "end" "show scada modbus tcp server" "show running-config | include scada"
$M probe
$C "show running-config" | sed 1d > /home/terrenceb/claude/device-testing/IE520/modbus-2026-09-29/post-test-configs/22655.u5.show_running-config.txt
echo "### $(date) done"
