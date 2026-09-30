#!/bin/bash
# run.sh <name> <reload_tty> <member> <poll_tty>
cd /tmp/ck15; N=$1; RT=$2; M=$3; PT=$4; R=/tmp/ck15/run$N; rm -rf $R; mkdir -p $R
sudo -n python3 flows.py 360 500 $R/flows > $R/flows.log 2>&1 &
python3 poll.py /dev/$PT 115200 /tmp/ck15/console-$PT.log 3 345 $R/poll-$PT.DONE "show clock" "show stack" "show mrp ring" > $R/poll-$PT.out 2>&1 &
python3 poll.py /dev/u3 115200 /tmp/ck15/console-u3.log 3 345 $R/poll-u3.DONE "show mrp ring" > $R/poll-u3.out 2>&1 &
sleep 30
python3 reload.py /dev/$RT 115200 /tmp/ck15/console-$RT.log $M 320 $R/reload.DONE > $R/reload.out 2>&1 &
wait
touch $R/ALLDONE
