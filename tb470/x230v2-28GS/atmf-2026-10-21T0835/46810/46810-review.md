# T46810 process review -- atmf-2026-10-21T0835
Reviewed 2026-10-21 by /create-logs from agent-a1531ba7f0ac26939.jsonl and the working files.

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 17 | 544 | 28,640 | 2,613,763 | 1,327 | 17 (Bash 15, ToolSearch 1, SendMessage 1) | 7.7 min | 9,846 chars |

## Process taken
1. Pre-run reads on u0 and u1 in one `tools/tb ckcon` call each (clock, system, boot, running-config, reboot history, exception log, filtered log, cpu, memory, atmf), saved to `work/prerun-u*.out`; only a grep of each file was read back.
2. Setup on u0 in one `tools/tb cfg` call (network name, management/domain VLAN, master, port1.0.2 trunk + atmf-link), then `@poll` for the x230 in `show atmf nodes`, `show atmf links`, `show atmf backup`.
3. Post-setup `show running-config` on both units, converted to `swi_e.cfg` / `swi_f.cfg` with `tools/rc2cfg.py`.
4. Step 1 in one call: `atmf backup now`, `@poll` on `show atmf backup` for the Good row, `dir usb:...`, `show atmf backup`, `show log | include atmffsd|backup`.
5. Health-after reads on u1 and u0 (same command list as step 1 of the prerun), awk-filtered before reading back.
6. Working log written in pieces as each leg passed; commit; `RESULT` line.

## Wasted input
none found. The largest read-backs were 2.5 KB (the step-1 grep) and 2.5 KB (the setup grep); the 26 KB prerun captures were never read in full.

## Repetition
none found (no command repeated verbatim; `case_tokens.py` reports no repeats).

## Accuracy risks
- The verdict rests on an assumed definition of the case (ck.db has one empty step). The final log and the Results row say so. Closing it needs the Test Engineer's written definition of T46810 in the case database.
- `show cpu` on this x230 build prints busy averages, not an idle figure. The HEALTH line reports busy %. A reader expecting "idle" must note the label.
- The `dir usb:` dates are the x230's UTC file times rendered in the 4050's NZDT (+13 h). The log says so; a reader comparing them with the x230's own `dir flash:` output will see a 13 h offset.

## Next run: expected outputs
- setup -> `show atmf` on the 4050: `Role : Master`, `Network Name : Enterprise-AMF`; log line `x230-28GSv2 has joined. 2 members in total.` within 1-2 s of `switchport atmf-link`.
- setup -> `show atmf links` on the 4050: `1.0.2  Downlink  Up  Full  x230-28GSv2  5001  Forwarding`.
- setup -> `show atmf backup`: `Backup Media .......... USB (Total 29584.1MB, Free 29284.5MB)`; x230 row `Yes No -`.
- step 1 -> `atmf backup now x230-28GSv2`: `Backup successfully initiated`; the Good row after about 32 s; free space drops by about 36.1 MB; `dir usb:/atmf/Enterprise-AMF/nodes/x230-28GSv2/flash/` lists the .rel (36747551), tb470-bench.cfg (1914), default.cfg (678), burnin.log (34718).

## Next run: scripts
- Existing: `tools/tb cfg` for the setup block, `tools/tb ckcon` with `@poll <secs> <regex> <command>` for the join and for the Good row (used here; keep the regex `x230-28GSv2.*Yes\s+Yes\s+(Good|Errors|Failed)`), `tools/rc2cfg.py` for the .cfg files.
- Proposed: none needed. A one-line `tools/README.md` note under ckcon saying "AMF backup: poll `show atmf backup` with the regex above; `atmf backup now` returns before the job ends" would save the next tester the lookup.

## Next run: references
- Group recipe (setup, restore, the `rmdir` of the empty node directory): `tb470/x230v2-28GS/CAMPAIGN-QUEUE-2026-10-21T0835.md`, "Run, group 1" section.
- The 4050 can be AMF master (licence FULL + AMF-MASTER): memory `ie520-master-ignores-remote-backup-server`.
- The x230's saved config already carries Enterprise-AMF, management vlan 3500, domain vlan 1234 and port1.0.1 atmf-link: `swi_f.cfg` in this folder; the master must match those two VLANs.
- Group-level findings: [../REVIEW.md](../REVIEW.md).
