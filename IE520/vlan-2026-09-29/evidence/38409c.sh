#!/bin/bash
# T38409 GVRP run 2: pin the declaration behaviour. GVRP up first, then new static VLANs with live members,
# then port-level GVRP restart, then global restart; teardown at the end.
cd /tmp/ckvlan
U5="python3 ckcon.py /dev/u5 115200 /tmp/ckvlan/console-u5.log"
U3="python3 ckcon.py /dev/u3 115200 /tmp/ckvlan/console-u3.log"
V5='show vlan dynamic'; M='show gvrp machine'; B='show vlan brief | include ^30|^399|^10 '
echo "### $(date +%T) loop guard: shut DUT 1.0.13 / 4.0.9"
$U5 --stop-on-error "configure terminal" "interface port1.0.13" "shutdown" "interface port4.0.9" "shutdown" "end" || exit 2
echo "### $(date +%T) GVRP up on both (no test VLANs yet)"
$U5 --stop-on-error "configure terminal" "gvrp enable" "gvrp dynamic-vlan-creation" "interface port4.0.26" "switchport mode trunk" "gvrp" "end" || exit 2
$U3 --stop-on-error "configure terminal" "gvrp enable" "gvrp dynamic-vlan-creation" "interface port1.0.26" "switchport mode trunk" "gvrp" "end" || exit 2
sleep 20
echo "### $(date +%T) baseline views"; $U5 "$M" "$V5"; $U3 "$M" "$V5"
echo "### $(date +%T) TEST A: new static VLANs with LIVE members, created after GVRP came up — SA vlan 301 + port1.0.2 (eth2, up); DUT vlan 302 + port1.0.9 (up)"
$U3 --stop-on-error "configure terminal" "vlan database" "vlan 301 state enable" "exit" "interface port1.0.2" "switchport access vlan 301" "end" "show vlan 301" || exit 2
$U5 --stop-on-error "configure terminal" "vlan database" "vlan 302 state enable" "exit" "interface port1.0.9" "switchport access vlan 302" "end" "show vlan 302" || exit 2
sleep 30
echo "### $(date +%T) TEST A views (DUT then SA)"; $U5 "$V5" "$M" "$B" "show gvrp statistics"; $U3 "$V5" "$M" "$B"
echo "### $(date +%T) TEST B: restart GVRP on the ports (no gvrp / gvrp)"
$U5 --stop-on-error "configure terminal" "interface port4.0.26" "no gvrp" "gvrp" "end" || exit 2
$U3 --stop-on-error "configure terminal" "interface port1.0.26" "no gvrp" "gvrp" "end" || exit 2
sleep 30
echo "### $(date +%T) TEST B views"; $U5 "$V5" "$M" "$B"; $U3 "$V5" "$M" "$B"
echo "### $(date +%T) TEST C: restart GVRP globally (no gvrp enable / gvrp enable / dynamic-vlan-creation / port gvrp)"
$U5 --stop-on-error "configure terminal" "no gvrp enable" "gvrp enable" "gvrp dynamic-vlan-creation" "interface port4.0.26" "gvrp" "end" || exit 2
$U3 --stop-on-error "configure terminal" "no gvrp enable" "gvrp enable" "gvrp dynamic-vlan-creation" "interface port1.0.26" "gvrp" "end" || exit 2
sleep 30
echo "### $(date +%T) TEST C views"; $U5 "$V5" "$M" "$B" "show gvrp configuration" "show running-config | include gvrp"; $U3 "$V5" "$M" "$B" "show gvrp configuration" "show running-config | include gvrp"
echo "### $(date +%T) teardown DUT"
$U5 --stop-on-error "configure terminal" "interface port4.0.26" "no gvrp" "switchport mode access" "interface port1.0.9" "switchport access vlan 3992" "exit" "no gvrp dynamic-vlan-creation" "no gvrp enable" "vlan database" "no vlan 302" "exit" "interface port1.0.13" "no shutdown" "interface port4.0.9" "no shutdown" "end" || exit 2
echo "### $(date +%T) teardown SA"
$U3 --stop-on-error "configure terminal" "interface port1.0.26" "no gvrp" "switchport mode access" "interface port1.0.2" "no switchport access vlan" "exit" "no gvrp dynamic-vlan-creation" "no gvrp enable" "vlan database" "no vlan 301" "end" || exit 2
sleep 15
$U5 "show gvrp configuration" "$V5" "show vlan brief | include ^30|^399" "show interface status | include 1.0.13 |4.0.9 |4.0.26 |1.0.9 " "show running-config interface port4.0.26" "show running-config | include gvrp"
$U3 "show gvrp configuration" "$V5" "show vlan brief | include ^30|^399|^1 " "show running-config interface port1.0.26" "show running-config | include gvrp"
echo "### $(date +%T) post-case running-configs"
$U5 "show running-config" | sed 1d > post-38409-u5.runcfg
$U3 "show running-config" | sed 1d > post-38409-u3.runcfg
wc -l post-38409-*.runcfg
