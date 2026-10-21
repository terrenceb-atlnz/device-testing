# T46421 process review -- platform-ports-2026-10-21T1323
Reviewed 2026-10-21 by /create-logs from agent-ad7157fdc1eed0717.jsonl and the working files. Case: "Link flap".

## Token usage
The segment runs from the show cases' RESULT message to this case's RESULT message. It also holds T47208's setup reads
(1 call, 1,026 chars), read before this RESULT was sent. Other segments: [../REVIEW.md](../REVIEW.md).

| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 9 | 288 | 33,477 | 1,513,259 | 56 | 14 | 600 s | 11,254 chars |

## Process taken
1. Step A, one `ckcon` call on u1: health before, then 9 local flaps (`shutdown` / `no shutdown` on port1.0.1) at auto
   1000, 100 and 10, then back to auto (2,734 chars read back).
2. Counted step A's Port down / Port up log lines (1,195 chars).
3. Step B, remote flaps from the 4050 (u0) port1.0.2: 3 at 1000, then the x230 set to auto 100 and 3 more, then auto 10
   and 3 more. Five calls, plus one call to tally the 4050's log lines.
4. Restore on the x230: back to auto, final reads, health after, running-config (1,359 chars). 4050 diff, boot, reboot history.
5. Wrote the working log and `.cfg` files, diffed, committed.
6. Read `tools/qmark.py` to see how it leaves the console (1,320 chars), in preparation for T47208.

## Wasted input
- Reading `tools/qmark.py` source (1,320 chars) to learn how it exits config mode. Its README entry should say it. Add one
  line there saying how the tool leaves the console after `--mode`.

## Repetition
- The remote flaps took three separate calls (one per speed), each preceded by a separate call to set the x230's speed.
  One call per speed that sets the DUT, flaps the partner 3 times and polls both ends would cut this from 5 calls to 3.
  The proposed `tools/tb speedrow` in ../REVIEW.md covers it.

## Accuracy risks
- The case text is one precondition only ("conduct link flap at supported speed and check status"). "Supported speed"
  was read as 1000, 100 and 10, the three speeds the copper module and the 4050 both run. Accepted at grading.
- The x230 logs an `ATMF Sec_Audit - Possible DOS attack, link resets on port1.0.1 exceed limit by 4` line after 9 local
  flaps in 77 s. port1.0.1 is its atmf-link. Not a fault, but a reader may mistake it for one. The final log explains it.
- Every link change also logs `snmpd ... send_trap: Failure in sendto (Network is unreachable)`, because the saved trap
  host is unreachable while tb470's host NICs are down. Recorded in the queue's Issues.

## Next run: expected outputs
- Each flap: one `Port down` and one `Port up` notification in the x230 log.
- Link back in 2.8 to 4.5 s at the speed it had before: `a-full a-1000`, `a-full a-100` or `a-full a-10`.
- LLDP neighbour re-learned on both ends after every flap.
- After the 9 local flaps in 77 s: the ATMF `Sec_Audit` line above (`exceed limit by 4`).

## Next run: scripts
- `tools/tb ckcon tb470 <scratch> u1 115200 "configure terminal" "interface port1.0.1" "shutdown" "@poll 20 disabled do show interface port1.0.1 status" "no shutdown" "@poll 40 a-full\s+a-1000\s do show interface port1.0.1 status" ...`
  as used here. The same with u0 and port1.0.2 for the remote flaps.
- Proposed `tools/tb speedrow` and `tools/tb health` (../REVIEW.md).

## Next run: references
- [platforms/x230v2-28GS.md](../../../../platforms/x230v2-28GS.md) §2: the AMF member row (atmf-link behaviour).
- This case's final log: the flap table with every time.
