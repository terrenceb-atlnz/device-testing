# T33374 process review -- authmodes-2026-10-23T1304
Reviewed 2026-10-28 by /create-logs from `agent-a2b85027e32e3d1df.jsonl` and the working files.

## Token usage

| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2 | 2,017 | 146,190 | 24 | 1 | 0 s | 0 chars |

🔴 **This row is a segmentation artefact, not a measurement of the case.** `case_tokens.py`
starts a case segment at the first tool call that touches `<id>/` and ends it at the `RESULT`
line. T33374 ran first in the group, so everything it actually did — the gate, the probe, the
rig read, the five supplicant legs, the console polling — happened *before* the group's first
`RESULT` line and is counted in the group's `overhead` row (122 calls, 22.1 M cache read).
The single call here is the `SendMessage` to the sentinel. **Do not read this case as cheap.**
The group total is in `REVIEW.md`, which is where this group's cost actually lives.

## Process taken
1. Console gate and probe of u2, then the group's one `show system` / `show boot` / clock
   reconciliation (charged to group overhead, shared by all five cases).
2. `qmark` self-test, then a read-only help probe of `auth reauthentication`,
   `auth timeout reauth-period` and `auth timeout`.
3. Baseline read of `show auth interface port1.0.48` (reAuthenticate disabled, reAuthPeriod 3600).
4. Health read, label `before-T33374`.
5. S0 control: `dot1x initialize`, then `eapol.py --timeout 120 --settle 105`, feature off.
6. S1: `auth reauthentication` + `auth timeout reauth-period 30`, read back in running-config
   and in `show auth`, then a 150 s supplicant run.
7. S2: period 60, one read back, a second 150 s run.
8. S3: period 15, supplicant run started **in the background first**, then four console reads
   during its window, plus `show radius local-server statistics` before and after.
9. S4: `no auth reauthentication` with the period left at 15, one 85 s run.
10. Restore `no auth timeout reauth-period`, read back every field of `show auth interface`.
11. Health read, label `after-T33374`; capture `swi_d.cfg`; write `work/run1.log`; `RESULT`.

## Wasted input
None found inside the case. The five `eapol.py` outputs are 0.9–2.7 kB each and every line of
them is evidence. The four `.out` captures kept under `work/` are the smallest artefacts in the
group. The console polling output (`dut-poll-during-reauth.out`, 2.6 kB) printed the full
`show auth supplicant interface port1.0.48` block at the first sample and the `brief` form at
the next two — that was the right choice, because the full block is what carries `currentId`.

## Repetition
- The same supplicant command was issued five times with only `--timeout`, `--settle`,
  `--label` and the two output paths changed. One wrapper that takes a period and a window
  would have replaced five hand-built command lines. See **scripts** below.
- `show auth interface port1.0.48 | include reAuth` was read after each of the three period
  changes. That is correct practice, not waste: each read is the evidence that the next
  frame table belongs to that period.

## Accuracy risks
- **None that affect the verdict.** Every number in the final log is a frame timestamp from a
  pcap table or a counter printed by the DUT. Nothing rests on inference.
- The one place where two instruments could have disagreed — wire count against the DUT's own
  RADIUS counters — was checked and they agree to the unit (+6 against 6).
- Claims left out of the final log for lack of a source in this case's working files: **none.**
- Minor: the step-3 interval list is quoted in the working log as "15.013 .. 15.030" in the
  summary table but the frame table gives 15.037, 15.027, 15.029, 15.028, 15.030. The final log
  uses the frame table for the per-interval figures and keeps the table's range as written.

## Next run: expected outputs
| step | what this bench gave |
| --- | --- |
| help probe | `auth timeout reauth-period ?` -> `<1-4294967295>  Seconds`; default 3600 |
| baseline | `reAuthenticate: disabled`, `reAuthPeriod: 3600`, hostMode single-host, CD both |
| S0, feature off | 6 EAPOL frames in 106 s, EAP-Success at 1.026 s |
| S1, period 30 | 26 frames, re-auth at 30.049 / 60.093 / 90.141 / 120.190 s |
| S2, period 60 | 16 frames, intervals 60.070 and 60.068 s |
| S3, period 15 | 31 frames, six authentications, intervals 15.037 / 15.027 / 15.029 / 15.028 / 15.030 s |
| S3, server | total Successes 31 -> 37, ckmulti1 16 -> 22, Failed Logins unchanged at 12 |
| S4, removed | 6 frames in 76 s with `reAuthPeriod: 15` still configured |
| server round trip | 1.00 s from MD5-Response to EAP-Success, on every cycle |

## Next run: scripts
- **Existing, reuse as is:** `tools/eapol.py` (via `tools/tb sudotool ... eapol`) and
  `tools/qmark.py`. Both did this case without modification.
- **Proposed `tools/reauthwatch.py`** (or a `--expect-interval` flag on `eapol.py`):
  arguments `--iface --supplicant --period <s> --cycles <n>`. It would size `--timeout` and
  `--settle` from the period and cycle count, then print the measured intervals and their
  deviation from the configured period as a table. That is the one derived number this case
  computed by hand five times.
- **Existing:** `tools/tb health` for the two health reads; `tools/tb ckcon` for the console.

## Next run: references
- `tb277/x960/platforms/x960.md` for the port map and the vlan 48 underlay, instead of
  re-deriving the host NIC to port mapping.
- Memory `two-console-calls-in-one-block-run-sequentially` — the reason step 3 started the
  supplicant in the background before polling the console. Following it saved the step.
- Memory `terminal-monitor-exec-only` — explains the `IMISH: Command [end] failed` log line,
  so the next tester does not investigate it.
- This log's **expected outputs** table above, instead of discovering the 1.00 s server round
  trip and the 3600 s default again.
