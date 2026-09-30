#!/bin/bash
# seq.sh <tag> <name:tty:port:polls> ... -- run fo.sh (80 s, shut +20, restore +50) for each
# spec in turn; after each: flowstat, loopwin, and the stack's `show mrp ring` + `show log tail 60`.
cd /tmp/ck9; TAG=$1; shift; S=/tmp/ck9/$TAG.summary; : > $S
for spec in "$@"; do
  IFS=: read N T P PL <<< "$spec"
  ./fo.sh $N 80 $T $P 20 50 "${PL//,/ }" > /tmp/ck9/$N.log 2>&1
  ev=$(awk "/launch/{print \$2}" $N/events.txt)
  { echo "##### $N  shut $P via $T"; python3 flowstat.py $N/flows $ev | grep -E "sent|LONGEST|missing seq"; python3 loopwin.py $N/flows; } > $N/summary.txt
  python3 cfg.py /dev/u3 115200 /tmp/ck9/console-u3.log "show mrp ring" "show log tail 60" > $N/mrmlog.out 2>&1
  grep -a -E "Network Status|Port[12]:|  Status:" $N/mrmlog.out >> $N/summary.txt
  cat $N/summary.txt >> $S
done
touch /tmp/ck9/$TAG.DONE
