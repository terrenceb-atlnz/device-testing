#!/bin/bash
# $1=label  $2..=config commands to apply on vlan48 before the leg
S=/tmp/dhcp-2026-10-15T1458
W=$HOME/claude/device-testing/tb277/x960/dhcp-client-2026-10-15T1458/T35370/work
LBL=$1; shift
cd $S/tools || exit 1
ARGS=()
for c in "$@"; do ARGS+=("$c"); done
python3.8 cfg.py /dev/u2 115200 $S/console-u2.log "configure terminal" "interface vlan48" \
  "${ARGS[@]}" "end" > $W/$LBL-cfg.log 2>&1
echo "cfg exit=$? for: ${ARGS[*]}"; grep -n "^% " $W/$LBL-cfg.log || echo "  no CLI errors"
bash $S/runlegC.sh $LBL
