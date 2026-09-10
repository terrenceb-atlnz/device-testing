#!/bin/bash
# Build the consolidated, time-aligned evidence window for TEST 38378 cycle 293.
# Every timestamped source is cut to the SAME window; the untimestamped console
# capture is included in full across the same span and anchored by content.
set -u
E=/tftproot/38378-evidence
RUN="$HOME/old test runs/IE520/stack-tests/failover-300"
OUT=/tmp/38378-window.txt

# The window, applied identically to every source.
W_START_Z="2026-08-25 22:33:00Z"
W_END_Z="2026-08-25 22:36:15Z"
GREP_WINDOW='22:3[3-6]:'          # UTC minutes 33..36 inclusive

{
cat <<'HDR'
================================================================================
TEST 38378 - CYCLE 293: ACTIVE MASTER WEDGE + WATCHDOG RESET
CONSOLIDATED EVIDENCE WINDOW
================================================================================

WINDOW (identical for every source in this file)
    2026-08-25 22:33:00Z  ->  2026-08-25 22:36:15Z        (device clocks, UTC)
  = 2026-08-26 10:33:00    ->  2026-08-26 10:36:15         (NZST, UTC+12)

BENCH
  tb470, AT-IE520-28GSX two-member VCStack
  virtual-chassis-id 3439 (0xd6f), VMAC 0000.cd37.0d6f
  member 1 = S/N 264A23066, MAC 84e3.2787.0740, console /dev/u5   <- WEDGED (was Active Master)
  member 2 = S/N 264A23052, MAC 84e3.2787.09c0, console /dev/u4   <- survivor (was Backup Member)
  Stacking: TWO pairs -- port1.0.28<->port2.0.27 and port1.0.27<->port2.0.28
            (both TE Connectivity 1-2127931-2 1xCOPPER PAS direct-attach)
  No resiliency link configured (both pairs are stackports).

SOFTWARE
  IE520-tomahawk_ie520-continuous.rel, build 08/19/26 02:20:43
  Booted from flash:/IE520-20260825.rel (sha256 8d699ce8...2bb6bb0)
  Bootloader 9.1.0 / U-Boot 2025.01-04844-gd2292467da4d (Jul 22 2026)

CLOCKS -- read this before comparing timestamps
  * Both switches log in UTC.
  * The test harness on tb470 logs in NZST (UTC+12).
  * The serial console capture has NO timestamps at all -- it is a raw byte
    stream. It is therefore anchored BY CONTENT, not by clock; see SOURCE A.

WHAT HAPPENED (one paragraph, evidence below)
  Cycle 293 shut stacking pair port1.0.27/port2.0.28. The first shutdown
  (port1.0.27) downed BOTH ends of that pair. A second, redundant shutdown was
  then issued against port2.0.28, already in disabled state. That is the last
  command member 1 ever acknowledged. Its CLI stopped echoing entirely, member 2
  lost TIPC contact ~22:33:27-29, HA failover completed correctly at 22:33:34,
  and member 1 spontaneously reset (BootROM) roughly two minutes later with no
  panic, oops, stack trace or shutdown sequence emitted.

*** CRITICAL EVIDENCE GAP -- STATED UP FRONT ***
  MEMBER 1 RETAINED NO LOG OF ITS OWN WEDGE. Its earliest surviving record of
  any kind is 22:35:34Z, i.e. AFTER the reset, when syslog-ng restarted. This
  was confirmed across four independent files pulled from it
  (messages.1, stacking.1, vcs-awplus-messages.2, startup_messages) -- all four
  begin at or after 22:35:34Z. There is no messages.2 on member 1.
  The hard reset gave syslog no opportunity to flush.
  => The ONLY record covering the wedge itself is SOURCE A (the tb470-side
     console capture) and the member 2 sources (B-F), which observe member 1
     from outside. No core file, crash dump or exception-log entry exists on
     either unit; that was checked and is a genuine absence, not an unread file.

================================================================================
SOURCE INDEX
================================================================================
  A  Serial console capture of MEMBER 1        - tb470 pyserial, no timestamps
  B  Stack permanent log (both members)        - device, UTC
  C  member 2 stacking trace (STK TRACE)       - device, UTC
  D  member 2 VCS/licensing messages           - device, UTC
  E  member 2 TIPC probe captures              - device, UTC
  F  member 2 HA-failover snapshot bundle      - device, UTC
  G  member 1 post-reset boot logs             - device, UTC (boot only)
  H  Test harness verdict log                  - tb470, NZST
================================================================================
HDR

echo
echo "================================================================================"
echo "SOURCE A - SERIAL CONSOLE CAPTURE OF MEMBER 1 (the unit that wedged)"
echo "================================================================================"
cat <<'A1'
  Captured by : tb470, pyserial reader in console.py, writing every byte as it
                arrived (never buffered-until-success, so a timeout cannot
                discard the bytes needed to diagnose it).
  Device      : member 1, console /dev/u5 (ttyUSB1), 115200 8N1
  File        : 38378-console-full.log  (1,360,311 bytes, whole 300-cycle run)
  Excerpt     : lines 34490-35115, reproduced verbatim below with `cat -v`
  Timestamps  : NONE. This is a raw serial byte stream.
  ANCHORING   : the excerpt is anchored by content, not clock --
                  line 34517 = first command with NO echo and no reply
                               (this is the wedge)
                  line 34521 = BootROM 1.41 banner (the reset)
                  line 35100 = FAT-fs (sda1) dirty-mount warning (post-reset)
                Correlate to UTC via SOURCE B: member 2 first reports lost
                contact at 22:33:29Z, and member 1's syslog restarts 22:35:34Z.
                The silence between console lines 34515 and 34521 therefore
                spans approximately 22:33:2xZ -> 22:35:2xZ.
  NOTE        : `>>>` lines are the harness echoing what IT sent; everything
                else is what the DEVICE emitted. Absence of a device echo after
                34515 is the finding.

A1
sed -n '34490,35115p' "$RUN/38378-console.log" | cat -v | awk '{printf "%6d  %s\n", NR+34489, $0}'

echo
echo "================================================================================"
echo "SOURCE B - STACK PERMANENT LOG (both members)"
echo "================================================================================"
cat <<'B1'
  Captured by : `show log permanent | include Aug 25 22:2` and `... 22:3`
                run over the console of the CURRENT master (member 2, /dev/u4).
  Why this one: the permanent log survives reboots and rotation, so unlike the
                debug: files it cannot roll off while being collected.
  File        : stack-permanent-log-2226-to-2239.txt
  Timestamps  : device UTC.

B1
grep -aE "$GREP_WINDOW" "$E/stack-permanent-log-2226-to-2239.txt" | sed 's/^/  /'

echo
echo "================================================================================"
echo "SOURCE C - MEMBER 2 STACKING TRACE (STK TRACE), covers the wedge"
echo "================================================================================"
cat <<'C1'
  Captured by : copy debug:/stacking.1 -> tftp, from the master console.
  Device      : member 2 (survivor). File spans 22:24:07Z -> 22:33:43Z, so it
                is the one device-side file that brackets the wedge itself.
  File        : m2-stacking.1
  Timestamps  : device UTC.

C1
grep -aE "$GREP_WINDOW" "$E/m2-stacking.1" | sed 's/^/  /'

echo
echo "================================================================================"
echo "SOURCE D - MEMBER 2 VCS / LICENSING MESSAGES"
echo "================================================================================"
cat <<'D1'
  Captured by : copy debug:/vcs-awplus-2-messages -> tftp.
  Device      : member 2. Records the instant member 1 was declared gone.
  File        : m2-vcs-awplus-2-messages
  Timestamps  : device UTC.

D1
grep -aE "$GREP_WINDOW" "$E/m2-vcs-awplus-2-messages" | sed 's/^/  /'
echo
echo "  -- and member 2's general messages across the window (m2-messages.2):"
grep -aE "$GREP_WINDOW" "$E/m2-messages.2" | sed 's/^/  /'

echo
echo "================================================================================"
echo "SOURCE E - MEMBER 2 TIPC PROBE CAPTURES"
echo "================================================================================"
cat <<'E1'
  Captured by : copy debug:/probe-2000ms.1 and debug:/probe-2500ms.1 -> tftp.
  Device      : member 2. Written automatically when TIPC keepalives to
                member 1 began timing out. These are the earliest machine
                record of member 1 going silent.
  Files       : probe-2000ms.1 , probe-2500ms.1
  Timestamps  : device UTC, in the file header line.
  NOTE        : the interface counters below are member 2's own vlan4094 (the
                stack management VLAN, 192.168.255.2). RX errors 0 -- the
                stacking link itself was healthy; member 1 simply stopped
                transmitting.

E1
for f in probe-2000ms.1 probe-2500ms.1; do
  echo "  ---------- $f ----------"
  head -14 "$E/$f" | sed 's/^/  /'
done

echo
echo "================================================================================"
echo "SOURCE F - MEMBER 2 HA-FAILOVER SNAPSHOT BUNDLE"
echo "================================================================================"
cat <<'F1'
  Captured by : the switch itself, automatically, into debug:/hafailover/ the
                moment member 2 detected the master had failed. Pulled to tb470
                by copy -> tftp.
  Device      : member 2 (survivor). NOTE: this bundle describes the SURVIVOR's
                own state, not the wedged unit's. It does not show why member 1
                wedged.
  Files/mtimes: hafailover-monitor            22:33:35Z
                hafailover-mgmtvlan (on-box)  22:33:35Z
                hafailover-cpu                22:33:36Z
                hafailover-platform_counters  22:33:44Z
  Timestamps  : file mtimes, device UTC.

F1
echo "  ---------- hafailover-cpu : first 12 lines (load at the failover instant) ----------"
head -12 "$E/hafailover-cpu" | sed 's/^/  /'
echo
echo "  ---------- hafailover-monitor : interrupt rows of interest ----------"
grep -aE "i2c|watchdog|MPIC" "$E/hafailover-monitor" | head -8 | sed 's/^/  /'

echo
echo "================================================================================"
echo "SOURCE G - MEMBER 1 POST-RESET BOOT LOGS  (begins AFTER the reset)"
echo "================================================================================"
cat <<'G1'
  Captured by : copy debug:/<file> -> flash: on member 1 via `remote-login 1`,
                then copy awplus-1/flash:/<file> -> tftp from the master.
                (A backup member cannot copy to a remote filesystem directly:
                 "% Copying to/from remote file systems is only supported from
                  the stack master".)
  Device      : member 1 (the unit that wedged).
  Files       : m1-messages-prereboot.log   (debug:/messages.1)
                m1-startup_messages         (debug:/startup_messages)
                m1-stacking.1               (debug:/stacking.1)
                m1-vcs-awplus-messages.2    (debug:/vcs-awplus-messages.2)
  Timestamps  : device UTC.
  *** The filename m1-messages-prereboot.log is a MISNOMER kept for continuity:
      it contains the POST-reset boot, not pre-reboot content. Member 1 retained
      nothing from before 22:35:34Z. ***

G1
echo "  ---------- earliest surviving line in each member-1 file ----------"
for f in m1-messages-prereboot.log m1-startup_messages m1-stacking.1 m1-vcs-awplus-messages.2; do
  printf "  %-32s " "$f"
  grep -aoE "2026-08-25T[0-9:]{8}|Aug 25 [0-9:]{8}" "$E/$f" | head -1
done
echo
echo "  ---------- member 1, the reset and the dirty USB mount ----------"
grep -aE "$GREP_WINDOW" "$E/m1-messages-prereboot.log" | head -22 | sed 's/^/  /'

echo
echo "================================================================================"
echo "SOURCE H - TEST HARNESS VERDICT LOG  (tb470, NZST)"
echo "================================================================================"
cat <<'H1'
  Captured by : test_38378.py on tb470.
  Timestamps  : NZST (UTC+12). Subtract 12 h to compare with the device logs.
  File        : 38378.log
  Cycle 293 is the failing cycle. Cycles 294-300 are UNMEASURED for a TOOLING
  reason, not a product one: the harness has no mid-run re-login, so after
  member 1 rebooted it was typing into a login prompt.

H1
grep -aE "cycle +(29[0-9]|300)/300|-> |RESULT" "$RUN/38378.log" | sed 's/^/  /'

echo
echo "================================================================================"
echo "END OF WINDOW"
echo "================================================================================"
} > "$OUT"

sudo -n cp "$OUT" "$E/38378-cycle293-CONSOLIDATED-WINDOW.txt"
sudo -n chmod 666 "$E"/*
wc -l "$E/38378-cycle293-CONSOLIDATED-WINDOW.txt"
