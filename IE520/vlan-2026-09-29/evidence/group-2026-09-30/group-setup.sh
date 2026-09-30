#!/bin/bash
# VLAN group setup, redo 2026-09-30 (README "Group setup"), plus two OBSERVER trunks so every freed
# leg is visible on a tb470 NIC by its scratch VLAN tag:
#   x230 port1.0.1 (eth3): trunk, native 100 (= its baseline access VLAN), allowed + 3991,3992
#     -> DUT port1.0.2 egress arrives at eth3 tagged 3991, DUT port1.0.9 tagged 3992
#   SA port1.0.2 (eth2): trunk, native 1 (= baseline), allowed + 3993,3994
#     -> DUT port1.0.13 egress arrives at eth2 tagged 3993, DUT port4.0.9 tagged 3994
# vlan 10 / sa1 (AR4050S transit) and the SX link (4.0.26<->1.0.26, VLAN 4000) are not touched.
cd /tmp/ckvlan3
U5="python3 ckcon.py /dev/u5 115200 /tmp/ckvlan3/console-u5.log"
U3="python3 ckcon.py /dev/u3 115200 /tmp/ckvlan3/console-u3.log"
U0="python3 ckcon.py /dev/u0 9600 /tmp/ckvlan3/console-u0.log"
echo "### $(date +%T) stack: VLANs 3991-3994, shut the four legs, out of sa2/sa3 into scratch VLANs"
$U5 --stop-on-error "configure terminal" "vlan database" "vlan 3991,3992,3993,3994 state enable" "exit" \
  "interface port1.0.2" "shutdown" "interface port1.0.9" "shutdown" "interface port1.0.13" "shutdown" "interface port4.0.9" "shutdown" \
  "interface port1.0.2" "no static-channel-group" "switchport access vlan 3991" \
  "interface port1.0.9" "no static-channel-group" "switchport access vlan 3992" \
  "interface port1.0.13" "no static-channel-group" "switchport access vlan 3993" \
  "interface port4.0.9" "no static-channel-group" "switchport access vlan 3994" \
  "end" "show static-channel-group" "show vlan brief | include 399" || exit 2
echo "### $(date +%T) x230: 1.0.3->3991, 1.0.4->3992 (out of sa2); observer trunk port1.0.1"
$U0 --stop-on-error "configure terminal" "vlan database" "vlan 3991,3992 state enable" "exit" \
  "interface port1.0.3" "no static-channel-group" "switchport access vlan 3991" \
  "interface port1.0.4" "no static-channel-group" "switchport access vlan 3992" \
  "interface port1.0.1" "switchport mode trunk" "switchport trunk native vlan 100" "switchport trunk allowed vlan add 3991,3992" \
  "end" "show static-channel-group" "show vlan brief" || exit 2
echo "### $(date +%T) SA: 1.0.13->3993, 1.0.9->3994 (out of sa3); observer trunk port1.0.2"
$U3 --stop-on-error "configure terminal" "vlan database" "vlan 3993,3994 state enable" "exit" \
  "interface port1.0.13" "no static-channel-group" "switchport access vlan 3993" \
  "interface port1.0.9" "no static-channel-group" "switchport access vlan 3994" \
  "interface port1.0.2" "switchport mode trunk" "switchport trunk allowed vlan add 3993,3994" \
  "end" "show static-channel-group" "show vlan brief" || exit 2
echo "### $(date +%T) stack: legs up"
$U5 --stop-on-error "configure terminal" "interface port1.0.2" "no shutdown" "interface port1.0.9" "no shutdown" "interface port1.0.13" "no shutdown" "interface port4.0.9" "no shutdown" "end" || exit 2
sleep 20
$U5 "show interface status | include port1.0.2 |port1.0.9 |port1.0.13 |port4.0.9 |port4.0.26 |port3.0.13 " "show vlan brief" "show static-channel-group"
echo "### $(date +%T) done"
