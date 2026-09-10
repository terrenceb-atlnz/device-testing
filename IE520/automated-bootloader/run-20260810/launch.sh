#!/bin/bash
# Launch a 5700 TestSet from an isolated run directory.
#
# Why a separate run dir: the framework writes its logs into the CWD
# (test-5700.NNNN.log, swi_a.log, setup.log, power-*.log) and OVERWRITES them
# unless -a is given.  Running in ~/copilot would destroy bidhanc's 2026-08-07
# campaign logs, which are the evidence base for the whole RCA.
#
# The framework is imported from ./framework (CWD is sys.path[0]).  This is a
# COPY of /home/bidhanc/5700_bootloader/framework - the exact tree that ran the
# original campaign - so results are comparable.  /home/st-art/framework is
# read-only and a different version; do not point at it.
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
# Usage:  ./launch.sh <suite> [testcase ...]
#   e.g.  ./launch.sh 2005 1 2 3
set -u

RUN_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="$(dirname "$RUN_DIR")"
SUITE="${1:?usage: launch.sh <suite> [testcase ...]}"
shift

# Re-sync the patched scripts every launch so an edit to the staging copy in
# ~/copilot is always picked up without having to remember to copy it.
cp -f "$SRC_DIR/library_5700.py"        "$RUN_DIR/" || exit 1
cp -f "$SRC_DIR/test-5700.$SUITE.py"    "$RUN_DIR/" || exit 1
cp -f "$SRC_DIR/default.setup"          "$RUN_DIR/" || exit 1
chmod +x "$RUN_DIR/test-5700.$SUITE.py"
rm -rf "$RUN_DIR/__pycache__"

cd "$RUN_DIR" || exit 1

STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="$RUN_DIR/console-$SUITE-$STAMP.out"

echo "run dir : $RUN_DIR"
echo "suite   : $SUITE   cases: ${*:-<all>}"
echo "stdout  : $OUT"

sudo -n setsid nohup ./test-5700."$SUITE".py -v -u -p -s default.setup "$@" \
    > "$OUT" 2>&1 < /dev/null &

echo "pid     : $!"
