#!/bin/bash
cd /tmp/ck15; R=/tmp/ck15/runA; mkdir -p $R
sudo -n python3 flows.py 360 500 $R/flows > $R/flows.log 2>&1 &
python3 poll.py /dev/u4 115200 /tmp/ck15/console-u4.log 3 345 $R/poll-u4.DONE "show stack" "show mrp ring" > $R/poll-u4.out 2>&1 &
python3 poll.py /dev/u3 115200 /tmp/ck15/console-u3.log 3 345 $R/poll-u3.DONE "show mrp ring" > $R/poll-u3.out 2>&1 &
sleep 30
python3 reload.py /dev/u5 115200 /tmp/ck15/console-u5.log 3 320 $R/reload.DONE > $R/reload.out 2>&1 &
wait
touch $R/ALLDONE
