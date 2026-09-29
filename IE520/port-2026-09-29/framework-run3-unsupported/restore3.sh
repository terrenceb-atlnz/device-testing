#!/bin/bash
# T33234 run 3 restore: boot pointer back to tb470-bench.cfg, delete the frame cfg files. One console per call.
cd /tmp/ck33234
run() { tty=$1; baud=$2; dev=$3; shift 3
  python3 ckcon.py /dev/$tty $baud /tmp/ck33234/console-$tty-run3.log --stop-on-error \
    "show boot" "dir" "configure terminal" "boot config-file flash:/tb470-bench.cfg" "end" \
    "delete force ${dev}_9001_33234.cfg" "show boot" "dir" "show running-config | include boot|scada"
  echo "== $tty rc=$?"; }
run u5 115200 stk_a &
run u3 115200 swi_b &
run u1 115200 swi_e &
run u0 9600 swi_f &
wait
