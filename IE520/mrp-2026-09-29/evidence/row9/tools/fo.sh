#!/bin/bash
# fo.sh <name> <dur_s> <tty> <port> <shut_at_s> <restore_at_s> "<poll ttys>"
# Traffic (flows.py, 500 pps x 4 flows) for dur_s; at +shut_at `shutdown` <port> via <tty>
# (the device's console), at +restore_at `no shutdown`; `show mrp ring` pollers every 2 s on
# the listed ttys. Writes /tmp/ck9/<name>/ and touches ALLDONE.
cd /tmp/ck9; N=$1; D=$2; T=$3; P=$4; S=$5; RS=$6; PT=$7; R=/tmp/ck9/$N; rm -rf $R; mkdir -p $R
t0=$(date +%s.%N); echo "t0 $t0" > $R/events.txt
sudo -n python3 flows.py $D 500 $R/flows > $R/flows.log 2>&1 &
for p in $PT; do
  python3 poll.py /dev/$p 115200 /tmp/ck9/console-$p.log 2 $((D-5)) $R/poll-$p.DONE "show mrp ring" > $R/poll-$p.out 2>&1 &
done
until [ -f $R/flows/START ]; do sleep 0.1; done
st=$(cat $R/flows/START)
sleep $(python3 -c "import time;print(max(0,$st+$S-time.time()))")
echo "shut-launch $(date +%s.%N)" >> $R/events.txt
python3 cfg.py /dev/$T 115200 /tmp/ck9/console-$T.log "configure terminal" "interface $P" "shutdown" "end" "show mrp ring" > $R/shut.out 2>&1
echo "shut-rc $? $(date +%s.%N)" >> $R/events.txt
sleep $(python3 -c "import time;print(max(0,$st+$RS-time.time()))")
echo "noshut-launch $(date +%s.%N)" >> $R/events.txt
python3 cfg.py /dev/$T 115200 /tmp/ck9/console-$T.log "configure terminal" "interface $P" "no shutdown" "end" > $R/noshut.out 2>&1
echo "noshut-rc $? $(date +%s.%N)" >> $R/events.txt
sleep 6
python3 cfg.py /dev/$T 115200 /tmp/ck9/console-$T.log "show mrp ring" "show interface $P status" > $R/after.out 2>&1
wait
touch $R/ALLDONE
