# T28218 process review -- atmf-2026-10-27T0855
Reviewed 2026-10-27 by /create-logs from agent-ac199d3fbcfdc217f.jsonl (group 3 tester) and the working files.

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 40 | 80 | 76,787 | 4,250,373 | 35,639 | 40 | 1,664 s | 67,193 chars |

## Process taken
1. Read the 2026-10-21 queue's T28218 recipe and its review "Next run" section (5.3 KB), tools/README.md index and sections (14 KB), group 2's run1.log head (5.1 KB), and the case text (4.9 KB).
2. Gate: precheck FOUND (a minicom on u2, outside the session) -> NEEDS TEST ENGINEER; waited 90 s on a marker file on the box; the answer came by message ("dont touch u2, its irrelevant").
3. Peek, probe, re-triage reads (file systems, dir usb:, licence, atmf, provision nodes) in one ckcon.
4. show system + pre-case reads on u1 and u0; health before.
5. `atmf master` via ckyn; gate reads after a 20 s settle; swi_f.cfg.
6. Steps 1-5 in ONE `ckcon --stop-on-error` pass (CKTO=600), then dir recursive / show atmf backup.
7. Read the rewritten info file; health after.
8. Restore: provision delete, rmdir, `no atmf master`, reads; reload for the Restricted-login residue; post reads on both units; startup-config compare.
9. Post probe, logout, RESULT.

## Wasted input
- Call 31: `tools/tb waitfor tb470 /tmp/atmf-1027/answer.marker 90`. A relayed answer never arrives as a file on the box; it arrives as a message. 90 s of wall time, no tokens wasted, but the next tester should simply carry on with non-console work and end its turn.
- Call 19: the head of group 2's run1.log (5.1 KB) was read only to copy the tool invocations. The tools/README.md entries already give them.

## Repetition
- tools/README.md read again (third group in the same campaign). See ../../platform-2026-10-27T0855/REVIEW.md.

## Accuracy risks
- The step 2 side effect: provisioning REWROTE a file that was already on the stick, `usb:/atmf/Enterprise-AMF/info/backup_future_node.info`, which the 2026-10-21 run had left there. Its earlier content was not read before this run, so it is lost. The working log records this; the final log shows the file in step 2's `dir` output only. Next time, `show file` any pre-existing `info/backup_<node>.info` before provisioning the same node name.
- One AMF residue needs a reload to clear: after `no atmf master`, "Restricted login" stays Disabled until the unit restarts. A run that does not allow reloads would leave it.

## Next run: expected outputs
- `atmf master` -> no output, no y/n; `show atmf` Role Master, Restricted login Disabled; `show atmf nodes` Master Y, Depth 0.
- `atmf provision node future_node` -> prompt `x230-28GSv2[atmf-provision]#` after ~28 s.
- `copy flash:/<x230 .rel> ./<rel>` -> "Copying..." / "Successful operation" in ~45 s (36,747,551 B to usb:).
- `show atmf provision nodes` -> Backup Media USB, future_node, Provision Path `usb:/atmf/Enterprise-AMF/nodes/future_node/flash/`, both boot entries "(file exists)", Default boot config "(file not found)".
- Restore: provision `delete` leaves an empty `nodes/future_node/` and the node still listed until `rmdir`; `no atmf master` then a reload (169 s) to bring Restricted login back to Enabled.

## Next run: scripts
- Proposed `tools/atmf_provision.py <tty> <baud> <transcript> --node <name> --rel <file> --cfg <file>`: run steps 1-5 and the full restore (delete, rmdir, `no atmf master`), and print the before/after `dir recursive` of the AMF tree. This campaign and 2026-10-21 both built the same sequence by hand.

## Next run: references
- This case's final log (all five steps with outputs).
- memory `atmf-recovery-residue-and-reboots` for the reload after `no atmf master`.
- memory `x230v2-atmf-campaign-2026-10-21` for the empty node directory left by `delete`.
