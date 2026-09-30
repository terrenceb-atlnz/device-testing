#!/bin/bash
# T38408 teardown -> group-setup state (legs in 3991-3994, observer trunks carrying 3991-3994 only).
cd /tmp/ckvlan3
U5="python3 ckcon.py /dev/u5 115200 /tmp/ckvlan3/console-u5.log"
U3="python3 ckcon.py /dev/u3 115200 /tmp/ckvlan3/console-u3.log"
U0="python3 ckcon.py /dev/u0 9600 /tmp/ckvlan3/console-u0.log"
echo "### $(date +%T) DUT"
$U5 --stop-on-error "configure terminal" \
  "interface port3.0.13" "no switchport vlan-stacking" "no switchport access vlan" \
  "interface port1.0.13" "no switchport vlan-stacking" "switchport trunk allowed vlan remove 3995" "no switchport trunk native vlan" "switchport mode access" "switchport access vlan 3993" \
  "interface port1.0.2" "no switchport vlan-stacking" "switchport trunk allowed vlan remove 3995" "no switchport trunk native vlan" "switchport mode access" "switchport access vlan 3991" \
  "interface port1.0.9" "switchport access vlan 3992" \
  "exit" "vlan database" "no vlan 2100" "no vlan 3995" "end" \
  "show vlan brief | include 399|2100" "show running-config interface port3.0.13" "show running-config interface port1.0.2" "show running-config interface port1.0.9" "show running-config interface port1.0.13" || exit 2
echo "### $(date +%T) SA"
$U3 --stop-on-error "configure terminal" \
  "interface port1.0.13" "switchport trunk allowed vlan remove 3995" "no switchport trunk native vlan" "switchport mode access" "switchport access vlan 3993" \
  "interface port1.0.2" "switchport trunk allowed vlan remove 3995" \
  "exit" "vlan database" "no vlan 3995" "end" "show vlan brief" || exit 2
echo "### $(date +%T) x230"
$U0 --stop-on-error "configure terminal" \
  "interface port1.0.3" "switchport trunk allowed vlan remove 3995" "no switchport trunk native vlan" "switchport mode access" "switchport access vlan 3991" \
  "interface port1.0.1" "switchport trunk allowed vlan remove 3995" \
  "exit" "vlan database" "no vlan 3995" "end" "show vlan brief" || exit 2
echo "### $(date +%T) done"
