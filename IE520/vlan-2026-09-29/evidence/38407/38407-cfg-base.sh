#!/bin/bash
# T38407 stage-0 config (feature OFF): internal VLAN 3995 on three DUT trunks, no translation rule yet.
#   port3.0.13 (eth1, customer wire side) trunk +3995 (native stays 1)
#   port1.0.13 (-> SA -> eth2) trunk +3995 native 3993      port1.0.2 (-> x230 -> eth3) trunk +3995 native 3991
# Partners: SA 1.0.13 trunk native 3993 +3995, SA 1.0.2 +3995; x230 1.0.3 trunk native 3991 +3997 ONLY (the
# translated wire VID of port1.0.2), x230 1.0.1 +3995,3997, x230 1.0.4 trunk native 3992 +3995 (mirror path).
cd /tmp/ckvlan3
U5="python3 ckcon.py /dev/u5 115200 /tmp/ckvlan3/console-u5.log"
U3="python3 ckcon.py /dev/u3 115200 /tmp/ckvlan3/console-u3.log"
U0="python3 ckcon.py /dev/u0 9600 /tmp/ckvlan3/console-u0.log"
echo "### $(date +%T) SA"
$U3 --stop-on-error "configure terminal" "vlan database" "vlan 3995 name ck-xl-int" "exit" \
  "interface port1.0.13" "switchport mode trunk" "switchport trunk native vlan 3993" "switchport trunk allowed vlan add 3995" \
  "interface port1.0.2" "switchport trunk allowed vlan add 3995" "end" "show vlan brief | include 399" || exit 2
echo "### $(date +%T) x230"
$U0 --stop-on-error "configure terminal" "vlan database" "vlan 3995 name ck-xl-int" "vlan 3997 name ck-xl-wire2" "exit" \
  "interface port1.0.3" "switchport mode trunk" "switchport trunk native vlan 3991" "switchport trunk allowed vlan add 3997" \
  "interface port1.0.4" "switchport mode trunk" "switchport trunk native vlan 3992" "switchport trunk allowed vlan add 3995" \
  "interface port1.0.1" "switchport trunk allowed vlan add 3995,3997" "end" "show vlan brief" || exit 2
echo "### $(date +%T) DUT"
$U5 --stop-on-error "configure terminal" "vlan database" "vlan 3995 name ck-xl-int" "exit" \
  "interface port3.0.13" "switchport mode trunk" "switchport trunk allowed vlan add 3995" \
  "interface port1.0.13" "switchport mode trunk" "switchport trunk native vlan 3993" "switchport trunk allowed vlan add 3995" \
  "interface port1.0.2" "switchport mode trunk" "switchport trunk native vlan 3991" "switchport trunk allowed vlan add 3995" \
  "end" "show vlan brief | include 399" \
  "show running-config interface port3.0.13" "show running-config interface port1.0.13" "show running-config interface port1.0.2" "show interface switchport vlan translation" || exit 2
