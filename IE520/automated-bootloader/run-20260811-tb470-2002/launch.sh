#!/bin/bash
# Launch 5700 suite 2002 against the tb470 IE520 on /dev/u4.
#
# RUN THIS ON tb470, AS ROOT-CAPABLE terrenceb:
#   SSH_AUTH_SOCK=/run/user/1971/keyring/ssh ssh tb470
#   cd ~/copilot/run-20260811-tb470-2002 && ./launch.sh
#
# Why this directory exists at all: the framework writes its logs into the CWD
# (test-5700.NNNN.log, swi_a.log, setup.log, power-*.log) and OVERWRITES them
# unless -a is given.  There are THREE concurrent campaigns in this shared NFS
# home - another session's 2005 on tb504 in run-20260810/, this 2002, and the
# 2003 next door - so each gets its own directory and they never collide.
#
# ./framework is a COPY of run-20260810/framework taken 2026-08-11, which is
# bidhanc's original campaign tree plus the local fixes (ATTestCase.py and
# ATDrivers/ATBootLoader.py, each with a .orig beside it).  It is a snapshot:
# if that tree is patched again, re-copy it here deliberately.
# /home/st-art/framework is read-only and a different version; do not point at it.
#
# No .atpylib_publisher.json is present here, so ATPublisher stays disabled and
# nothing is written to the shared results DB.
#
# MUST run as root.  ATTestBox.Eth reads /etc/NetworkManager/system-connections/
# ethN.nmconnection, which is 0600 root:root.  ConfigParser.read() ignores an
# unreadable file WITHOUT raising, so as a normal user the NetworkManager branch
# finds no [ipv4] section, yet still sets loadFromCommand=False - which skips the
# "ip addr show" fallback that would have worked.  ipv4addr ends up '', init_eth()
# returns None, and Setup.py reports it as "tb eth port eth1 not found" then
# sys.exit(2).  The interface is fine; only the read permission is missing.
#
# Usage:  ./launch.sh [testcase ...]
#   e.g.  ./launch.sh 22 42 60
set -u

SUITE=2002
SETUP=tb470-u4.setup
CONSOLE=/dev/u4

RUN_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="$(dirname "$RUN_DIR")"

# --- guard 1: the setup file still carries the PDU placeholder ----------------
# Without a real powerlink, restore_boot_from_tftp()'s dut.off() logs an error and
# returns False WITHOUT raising, so the suite does not fail fast - it waits for a
# <Ctrl+B> banner that can never appear, at the inherited 1800 s default.  2002
# calls it 24 times.  Fail here instead, in one second.
if grep -q 'SOCKET_TBD' "$SRC_DIR/$SETUP"; then
    echo "REFUSING TO LAUNCH: $SETUP still has the SOCKET_TBD placeholder." >&2
    echo "  The IE520 needs a real PDU socket on 10.36.150.14 before 2002 can run." >&2
    exit 1
fi

# --- guard 2: somebody else is on the console --------------------------------
# Two processes on one serial port interleave in BOTH directions: your reads
# swallow bytes theirs is waiting on, and your writes land in their session.
if [ -e "/var/lock/LCK..$(basename "$CONSOLE")" ] || pgrep -f "minicom.*$CONSOLE" >/dev/null; then
    echo "REFUSING TO LAUNCH: $CONSOLE is held by another session." >&2
    ls -l "/var/lock/LCK..$(basename "$CONSOLE")" 2>/dev/null >&2
    pgrep -af "minicom.*$CONSOLE" >&2
    exit 1
fi

# Re-sync the patched scripts every launch so an edit to the staging copy in
# ~/copilot is always picked up without having to remember to copy it.
cp -f "$SRC_DIR/library_5700.py"     "$RUN_DIR/" || exit 1
cp -f "$SRC_DIR/test-5700.$SUITE.py" "$RUN_DIR/" || exit 1
cp -f "$SRC_DIR/$SETUP"              "$RUN_DIR/" || exit 1
chmod +x "$RUN_DIR/test-5700.$SUITE.py"
rm -rf "$RUN_DIR/__pycache__"

cd "$RUN_DIR" || exit 1

STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="$RUN_DIR/console-$SUITE-$STAMP.out"

echo "run dir : $RUN_DIR"
echo "suite   : $SUITE   dut: $CONSOLE   cases: ${*:-<all>}"
echo "setup   : $SETUP"
echo "stdout  : $OUT"

sudo -n setsid nohup ./test-5700."$SUITE".py -v -u -p -s "$SETUP" "$@" \
    > "$OUT" 2>&1 < /dev/null &

echo "pid     : $!"
