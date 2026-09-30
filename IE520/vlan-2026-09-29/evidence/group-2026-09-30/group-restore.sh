#!/bin/bash
# VLAN group restore 2026-09-30: evidence/group-restore.sh (09-29) + the two observer trunks undone.
cd /tmp/ckvlan3
U5="python3 ckcon.py /dev/u5 115200 /tmp/ckvlan3/console-u5.log"
U3="python3 ckcon.py /dev/u3 115200 /tmp/ckvlan3/console-u3.log"
U0="python3 ckcon.py /dev/u0 9600 /tmp/ckvlan3/console-u0.log"
echo "### $(date +%T) stack: shut the four legs, back into sa2/sa3, drop 3991-3994"
$U5 --stop-on-error "configure terminal" \
  "interface port1.0.2" "shutdown" "interface port1.0.9" "shutdown" "interface port1.0.13" "shutdown" "interface port4.0.9" "shutdown" \
  "interface port1.0.2" "no switchport access vlan" "static-channel-group 2" \
  "interface port1.0.9" "no switchport access vlan" "static-channel-group 2" \
  "interface port1.0.13" "no switchport access vlan" "static-channel-group 3" \
  "interface port4.0.9" "no switchport access vlan" "static-channel-group 3" \
  "exit" "vlan database" "no vlan 3991-3994" "end" "show static-channel-group" "show running-config interface sa2-3" || exit 2
echo "### $(date +%T) x230: observer trunk 1.0.1 back to access 100; 1.0.3/1.0.4 -> vlan 100 + sa2; drop 3991-3992"
$U0 --stop-on-error "configure terminal" \
  "interface port1.0.1" "switchport trunk allowed vlan remove 3991,3992" "no switchport trunk native vlan" "switchport mode access" "switchport access vlan 100" \
  "interface port1.0.3" "switchport access vlan 100" "static-channel-group 2" \
  "interface port1.0.4" "switchport access vlan 100" "static-channel-group 2" \
  "exit" "vlan database" "no vlan 3991-3992" "end" "show static-channel-group" "show running-config interface sa2" || exit 2
echo "### $(date +%T) SA: observer trunk 1.0.2 back to access; 1.0.13/1.0.9 -> sa3; drop 3993-3994"
$U3 --stop-on-error "configure terminal" \
  "interface port1.0.2" "switchport trunk allowed vlan remove 3993,3994" "switchport mode access" \
  "interface port1.0.13" "no switchport access vlan" "static-channel-group 3" \
  "interface port1.0.9" "no switchport access vlan" "static-channel-group 3" \
  "exit" "vlan database" "no vlan 3993-3994" "end" "show static-channel-group" "show running-config interface sa3" || exit 2
echo "### $(date +%T) stack: legs up"
$U5 --stop-on-error "configure terminal" "interface port1.0.2" "no shutdown" "interface port1.0.9" "no shutdown" "interface port1.0.13" "no shutdown" "interface port4.0.9" "no shutdown" "end" || exit 2
sleep 20
$U5 "show interface status | include port1.0.2 |port1.0.9 |port1.0.13 |port4.0.9 |port4.0.26 |port3.0.13 " "show static-channel-group" "show vlan brief | include 399|^10 |4000"
echo "### $(date +%T) done"
