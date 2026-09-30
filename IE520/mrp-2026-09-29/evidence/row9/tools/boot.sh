#!/bin/bash
# boot.sh <name> <reload_tty> <listen_ttys> <sa_poll_tty> <command...>
# 420 s of flows; SA/partner `show mrp ring` poller every 3 s; at +30 s <command> on <reload_tty>
# (y/n answered), passive recorders on <listen_ttys>. Touches ALLDONE.
cd /tmp/ck9; N=$1; RT=$2; LT=$3; PT=$4; shift 4; R=/tmp/ck9/$N; rm -rf $R; mkdir -p $R
sudo -n python3 flows.py 420 500 $R/flows > $R/flows.log 2>&1 &
python3 poll.py /dev/$PT 115200 /tmp/ck9/console-$PT.log 3 410 $R/poll-$PT.DONE "show mrp ring" > $R/poll-$PT.out 2>&1 &
for l in $LT; do python3 listen.py /dev/$l 115200 /tmp/ck9/console-$l.log 400 $R/listen-$l.DONE > $R/listen-$l.out 2>&1 & done
until [ -f $R/flows/START ]; do sleep 0.1; done
st=$(cat $R/flows/START); sleep $(python3 -c "import time;print(max(0,$st+30-time.time()))")
python3 reloadc.py /dev/$RT 115200 /tmp/ck9/console-$RT.log 380 $R/reload.DONE "$@" > $R/reload.out 2>&1 &
wait
touch $R/ALLDONE
