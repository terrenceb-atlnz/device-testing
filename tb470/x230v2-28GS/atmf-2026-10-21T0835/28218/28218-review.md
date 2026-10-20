# T28218 process review -- atmf-2026-10-21T0835
Reviewed 2026-10-21 by /create-logs from agent-a1531ba7f0ac26939.jsonl and the working files.

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 7 | 224 | 10,506 | 1,218,412 | 74 | 7 (Bash 6, SendMessage 1) | 3.3 min | 3,806 chars |

## Process taken
1. Pre-step `show running-config` on u1 (the x230, to prove nothing changed since T46810), `.cfg` files for both units with `tools/rc2cfg.py`.
2. All five steps in ONE `tools/tb ckcon --stop-on-error` call with `CKTO=600` (for the 36.7 MB usb-to-usb copy): `show atmf provision nodes`, `atmf provision node future_node`, `create`, `locate`, the two `copy` + `configure boot ...` pairs, `exit`, `show atmf provision nodes`, `dir`, `show atmf backup`. Only the part from the second `show atmf provision nodes` was read back (2.8 KB).
3. Health-after reads on u1 and u0, awk-filtered before reading back.
4. Working log, commit, `RESULT` line.

## Wasted input
none found. The 7 calls read back 3.8 KB in total.

## Repetition
none found. The HEALTH BEFORE sample reused T46810's after sample (the same unit, 3 min earlier, nothing in between); the working log says so.

## Accuracy risks
- Steps 1, 2 and the two `configure boot ...` commands print nothing on success. Their PASS rests on the absence of a `% ` line plus the step-5 output that shows their effect (Date, Provision Path, both "(file exists)"). The step-5 output closes the gap; a run without it would be absence-of-evidence.
- The `locate` command is from the case's precondition text, not from its steps. The log labels it as such.
- The provision-mode `delete` in the restore removed `future_node/flash/` but left an empty `future_node/` directory on usb: (the tester found it at 09:35 and ran `rmdir`). The restore evidence is in the working files (`work/restore-u0-dir.out`, `restore-u0-rmdir.out`), which this skill deletes; git history keeps them (commit adfe1fa). The restore commands themselves were only logged on the box (`/tmp/atmf-0835/console-u0.log`), because the tester's local process was killed by the sentinel session's restart; that transcript is tmpfs and is not in the repo.

## Next run: expected outputs
- `atmf provision node future_node` -> prompt `4050-5g[atmf-provision]#`, no text.
- `create` / `locate` / `configure boot system <rel>` / `configure boot config <cfg>` -> no text on success.
- `copy usb:/.../x230-28GSv2/flash/<rel> ./<rel>` -> `Copying...` / `Successful operation` after about 23 s for 36.7 MB.
- `show atmf provision nodes` -> Node Name `future_node`, Provision Path `usb:/atmf/Enterprise-AMF/nodes/future_node/flash/`, Current boot image and Current boot config `(file exists)`, Default boot config `flash:/default.cfg (file not found)`.
- `show atmf backup` -> row `future_node  -  -  No  Yes  Provisioned`.
- Restore: `atmf provision node future_node` / `delete` / `exit`, then `rmdir usb:/atmf/Enterprise-AMF/nodes/future_node` -> `Successful operation`.

## Next run: scripts
- Existing: `tools/tb ckcon --stop-on-error` with `CKTO=600` (the whole case is one console pass); `tools/console.py` now matches the `[atmf-provision]#` prompt and leaves that mode with `exit` (commit b29652b).
- Proposed: none. If option (c) (real provisioning with `atmf cleanup` on the member and recovery) is ever run, `IE520/atmf-2026-09-21/38479.log` has the step sequence and timings; a `tools/` recovery watcher that follows the member's `show log permanent | include atmffsd` through BOTH reboots would be the one helper to build (memory `atmf-recovery-residue-and-reboots`).

## Next run: references
- The case's precondition text (ck.db `zephyr_cases` key AWPTCM-T28218) holds the full command sequence; read it instead of the wiki page.
- Prior run of the same provisioning sequence with an x230 as the DUT, including the ordering traps (`create` refuses while a backup of the same node name exists; `configure boot` refuses while the name is a live member): `IE520/atmf-2026-09-21/38479.log`.
- Group recipe and restore: `tb470/x230v2-28GS/CAMPAIGN-QUEUE-2026-10-21T0835.md`.
- Group-level findings: [../REVIEW.md](../REVIEW.md).
