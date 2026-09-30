#!/bin/bash
# T38408 stage-0 config (feature OFF): S-VLAN 3995 on CE port3.0.13 (access) and the two provider-to-be trunks
# port1.0.13 (-> SA -> eth2) and port1.0.2 (-> x230 -> eth3); decoy VLAN 2100 (= the customer tag) on port1.0.9.
cd /tmp/ckvlan3
U5="python3 ckcon.py /dev/u5 115200 /tmp/ckvlan3/console-u5.log"
U3="python3 ckcon.py /dev/u3 115200 /tmp/ckvlan3/console-u3.log"
U0="python3 ckcon.py /dev/u0 9600 /tmp/ckvlan3/console-u0.log"
if [ -z "$SKIP_SA" ]; then
echo "### $(date +%T) SA: carry 3995 on 1.0.13 and the observer 1.0.2"
$U3 --stop-on-error "configure terminal" "vlan database" "vlan 3995 name ck-svlan" "exit" \
  "interface port1.0.13" "switchport mode trunk" "switchport trunk native vlan 3993" "switchport trunk allowed vlan add 3995" \
  "interface port1.0.2" "switchport trunk allowed vlan add 3995" "end" "show vlan brief | include 399" || exit 2
fi   # SKIP_SA=1: SA part already applied (16:22 try 1 applied every config line, stopped on its show form)
echo "### $(date +%T) x230: carry 3995 on 1.0.3 and the observer 1.0.1"
$U0 --stop-on-error "configure terminal" "vlan database" "vlan 3995 name ck-svlan" "exit" \
  "interface port1.0.3" "switchport mode trunk" "switchport trunk native vlan 3991" "switchport trunk allowed vlan add 3995" \
  "interface port1.0.1" "switchport trunk allowed vlan add 3995" "end" "show vlan brief" || exit 2
echo "### $(date +%T) DUT: VLANs 3995 + 2100, CE-to-be access, provider-to-be trunks, decoy"
$U5 --stop-on-error "configure terminal" "vlan database" "vlan 3995 name ck-svlan" "vlan 2100 name ck-cvlan-decoy" "exit" \
  "interface port3.0.13" "switchport access vlan 3995" \
  "interface port1.0.13" "switchport mode trunk" "switchport trunk native vlan 3993" "switchport trunk allowed vlan add 3995" \
  "interface port1.0.2" "switchport mode trunk" "switchport trunk native vlan 3991" "switchport trunk allowed vlan add 3995" \
  "interface port1.0.9" "switchport access vlan 2100" \
  "end" "show vlan 2100" "show vlan brief | include 399|2100" \
  "show running-config interface port3.0.13" "show running-config interface port1.0.13" "show running-config interface port1.0.2" "show running-config interface port1.0.9" || exit 2
