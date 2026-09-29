#!/bin/bash
# T38409 GVRP part A: loop guard, configure GVRP on DUT (port4.0.26) and IE520-sa (port1.0.26), wait, check both ways.
cd /tmp/ckvlan
U5="python3 ckcon.py /dev/u5 115200 /tmp/ckvlan/console-u5.log"
U3="python3 ckcon.py /dev/u3 115200 /tmp/ckvlan/console-u3.log"
echo "### $(date +%T) loop guard: shut DUT legs 1.0.13 and 4.0.9 (SA static 3993/3994 will be declared over the GVRP trunk)"
$U5 --stop-on-error "configure terminal" "interface port1.0.13" "shutdown" "interface port4.0.9" "shutdown" "end" "show interface status | include 1.0.13 |4.0.9 |4.0.26 " || exit 2
echo "### $(date +%T) STEP 1a DUT: gvrp enable + dynamic-vlan-creation, port4.0.26 trunk + gvrp, static vlan 302 (member port1.0.1)"
$U5 --stop-on-error "configure terminal" "vlan database" "vlan 302 state enable" "exit" "gvrp enable" "gvrp dynamic-vlan-creation" "interface port4.0.26" "switchport mode trunk" "gvrp" "interface port1.0.1" "switchport access vlan 302" "end" "show gvrp configuration" "show running-config | include gvrp" || exit 2
echo "### $(date +%T) STEP 1b SA: the same with vlan 301 on port1.0.26"
$U3 --stop-on-error "configure terminal" "vlan database" "vlan 301 state enable" "exit" "gvrp enable" "gvrp dynamic-vlan-creation" "interface port1.0.26" "switchport mode trunk" "gvrp" "interface port1.0.1" "switchport access vlan 301" "end" "show gvrp configuration" "show running-config | include gvrp" || exit 2
echo "### $(date +%T) waiting 30 s for join/leaveall"; sleep 30
echo "### $(date +%T) STEP 2 DUT view"
$U5 "show gvrp configuration" "show gvrp machine" "show gvrp statistics" "show vlan dynamic" "show vlan brief | include ^30|^399|^10 " "show vlan 301" "show vlan 302" "show interface switchport | include port4.0.26|Trunking|Native|Allowed|Dynamic" "show interface port4.0.26 switchport"
echo "### $(date +%T) STEP 2 SA view"
$U3 "show gvrp configuration" "show gvrp machine" "show gvrp statistics" "show vlan dynamic" "show vlan brief | include ^30|^399|^10 " "show vlan 302" "show vlan 301" "show interface port1.0.26 switchport"
