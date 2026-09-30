#!/bin/bash
# T38407 teardown -> group-setup state. The mirror removal is sent WITHOUT --stop-on-error because entering a
# mirror port prints a "% ... Use caution" line; its output is checked for any OTHER "% " line.
cd /tmp/ckvlan3
U5="python3 ckcon.py /dev/u5 115200 /tmp/ckvlan3/console-u5.log"
U3="python3 ckcon.py /dev/u3 115200 /tmp/ckvlan3/console-u3.log"
U0="python3 ckcon.py /dev/u0 9600 /tmp/ckvlan3/console-u0.log"
echo "### $(date +%T) DUT mirror off"
$U5 "configure terminal" "interface port1.0.9" "no mirror interface port1.0.2" "end" "show mirror" > /tmp/ckvlan3/38407/td-mirror.out 2>&1
cat /tmp/ckvlan3/38407/td-mirror.out
tr -d '\r' < /tmp/ckvlan3/38407/td-mirror.out | grep -a '^%' | grep -v 'currently configured as a mirror-port' && { echo "!!! unexpected % line"; exit 2; }
echo "### $(date +%T) DUT"
$U5 --stop-on-error "configure terminal" \
  "interface port1.0.9" "switchport access vlan 3992" \
  "interface port3.0.13" "no switchport vlan translation all" "switchport trunk allowed vlan remove 3995" "switchport mode access" \
  "interface port1.0.13" "switchport trunk allowed vlan remove 3995" "no switchport trunk native vlan" "switchport mode access" "switchport access vlan 3993" \
  "interface port1.0.2" "no switchport vlan translation all" "switchport trunk allowed vlan remove 3995" "no switchport trunk native vlan" "switchport mode access" "switchport access vlan 3991" \
  "exit" "vlan database" "no vlan 3995" "end" \
  "show vlan brief | include 399" "show interface switchport vlan translation" "show mirror" || exit 2
echo "### $(date +%T) SA"
$U3 --stop-on-error "configure terminal" \
  "interface port1.0.13" "switchport trunk allowed vlan remove 3995" "no switchport trunk native vlan" "switchport mode access" "switchport access vlan 3993" \
  "interface port1.0.2" "switchport trunk allowed vlan remove 3995" \
  "exit" "vlan database" "no vlan 3995" "end" "show vlan brief | include 399" || exit 2
echo "### $(date +%T) x230"
$U0 --stop-on-error "configure terminal" \
  "interface port1.0.3" "no switchport trunk native vlan" "switchport mode access" "switchport access vlan 3991" \
  "interface port1.0.4" "switchport trunk allowed vlan remove 3995,3997" "no switchport trunk native vlan" "switchport mode access" "switchport access vlan 3992" \
  "interface port1.0.1" "switchport trunk allowed vlan remove 3995,3997" \
  "exit" "vlan database" "no vlan 3995" "no vlan 3997" "end" "show vlan brief" || exit 2
echo "### $(date +%T) done"
