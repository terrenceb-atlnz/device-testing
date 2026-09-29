#!/bin/bash
# T38409 GVRP part B: give the test VLANs a live member, verify dynamic learning both ways, withdraw, teardown.
cd /tmp/ckvlan
U5="python3 ckcon.py /dev/u5 115200 /tmp/ckvlan/console-u5.log"
U3="python3 ckcon.py /dev/u3 115200 /tmp/ckvlan/console-u3.log"
echo "### $(date +%T) STEP 2c: live members — SA port1.0.2 (eth2, link up) -> vlan 301; DUT port1.0.9 (x230 leg, link up) -> vlan 302"
$U3 --stop-on-error "configure terminal" "interface port1.0.2" "switchport access vlan 301" "end" "show vlan 301" || exit 2
$U5 --stop-on-error "configure terminal" "interface port1.0.9" "switchport access vlan 302" "end" "show vlan 302" || exit 2
echo "### $(date +%T) waiting 30 s"; sleep 30
echo "### $(date +%T) DUT view (expect DYNAMIC 301 on port4.0.26)"
$U5 "show vlan dynamic" "show gvrp machine" "show vlan brief | include ^30|^399|^10 " "show gvrp statistics"
echo "### $(date +%T) SA view (expect DYNAMIC 302 on port1.0.26; 3992 gone, 3991 still)"
$U3 "show vlan dynamic" "show gvrp machine" "show vlan brief | include ^30|^399|^10 "
echo "### $(date +%T) STEP 2d: withdraw — SA port1.0.2 back to vlan 1, so 301 has no active member"
$U3 --stop-on-error "configure terminal" "interface port1.0.2" "no switchport access vlan" "end" "show vlan 301" || exit 2
echo "### $(date +%T) waiting 30 s"; sleep 30
echo "### $(date +%T) DUT view (expect 301 gone)"
$U5 "show vlan dynamic" "show gvrp machine"
echo "### $(date +%T) teardown DUT"
$U5 --stop-on-error "configure terminal" "interface port4.0.26" "no gvrp" "switchport mode access" "interface port1.0.1" "no switchport access vlan" "interface port1.0.9" "switchport access vlan 3992" "exit" "no gvrp dynamic-vlan-creation" "no gvrp enable" "vlan database" "no vlan 302" "exit" "interface port1.0.13" "no shutdown" "interface port4.0.9" "no shutdown" "end" "show gvrp configuration" "show vlan dynamic" "show vlan brief | include ^30|^399" "show running-config interface port4.0.26" || exit 2
echo "### $(date +%T) teardown SA"
$U3 --stop-on-error "configure terminal" "interface port1.0.26" "no gvrp" "switchport mode access" "interface port1.0.1" "no switchport access vlan" "exit" "no gvrp dynamic-vlan-creation" "no gvrp enable" "vlan database" "no vlan 301" "end" "show gvrp configuration" "show vlan dynamic" "show vlan brief | include ^30|^399|^1 " "show running-config interface port1.0.26" || exit 2
sleep 15
$U5 "show interface status | include 1.0.13 |4.0.9 |4.0.26 |1.0.9 "
echo "### $(date +%T) post-case running-configs"
$U5 "show running-config" | sed 1d > post-38409-u5.runcfg
$U3 "show running-config" | sed 1d > post-38409-u3.runcfg
wc -l post-38409-*.runcfg
