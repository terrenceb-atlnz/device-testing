# T45543 process review -- cli-2026-10-13T0949
Reviewed 2026-10-13 by /create-logs from `agent-a3ab1e57621c1d438.jsonl` and the working files.
Group-wide findings: [../REVIEW.md](../REVIEW.md).

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 4 | 3,342 | 276,498 | 40 | 3 | 7 s | 328 chars |
| *apportioned:* 5 | 10 | 6,521 | 667,237 | (not re-split) | 6 | ~35 s | 3,130 chars |

**Under-counted by the tool.** `case_tokens.py` starts a case at its first call naming `/45543/`, and this
case's device run (#11-#13 of the T30403 segment: the `ckcon` capture, the MANUAL-ONLY grep and
`sed -n 8,20p MANUAL-ONLY.md`) ran before the T30403 working log was written, so it was counted under
T30403. The RESULT SendMessage timestamps (T30403 22:24:37Z, T45543 22:25:04Z) bound only the Write,
commit and RESULT. The apportioned row adds those three calls (per-call usage measured from the transcript).

## Process taken
1. (T30403 #11) one `ckcon` (CKTO=180): `show platform full-debug | grep tpm`, `show system tpm`,
   `show lldp local-info interface port1.0.5` (for the system MAC), `show running-config` -> `steps.out`.
2. (T30403 #12-#13) grep MANUAL-ONLY.md for the T45543 row, then read its lines 8-20 (the PARTIAL rule).
3. #1 working log; #2 commit + queue; #3 RESULT.

## Wasted input
- none found. 3,130 chars in all; the `show lldp local-info` call doubled as the group's source for the x230's
  MAC address, which every TOPOLOGY needed.

## Repetition
- none found.

## Accuracy risks
- Step 2's verdict rests on a ruling, not on the case's expected text: "TPM is instantiated" vs expected
  "TPM is OK". The ruling is recorded (queue Session facts, MANUAL-ONLY.md row) and quoted in the log.
- The software-TPM observation (`tpm2-abrmd --tcti=mssim` to `/usr/bin/tpm_server` on localhost:2321) is
  recorded ungraded; the Test Engineer has since said it is how the unit talks to the idevid servers
  (queue, "Test Engineer's answers after the campaign"), and `platforms/x230v2-28GS.md` §2 now carries it.
  Whether the TPM is a hardware part was not established by any output; nothing more is claimed.

## Next run: expected outputs
| step | command | expected on this build |
| --- | --- | --- |
| 1 | `show platform full-debug \| grep tpm` | `/usr/sbin/tpm2-abrmd --tcti=mssim:host=localhost,port=2321` (tss) and `/usr/bin/tpm_server` (tss), LISTEN 127.0.0.1:2321/2322 and ::1:2321/2322 |
| 2 | `show system tpm` | `TPM is instantiated` (= OK by ruling) |
| 3 | - | NOT RUN, MANUAL-ONLY (idevid account + DUT internet access) |

`show platform full-debug` takes long enough that `CKTO=180` was set; keep it.

## Next run: scripts
- One `tools/ckcon.py` call covers steps 1-2. No new script.

## Next run: references
- `MANUAL-ONLY.md` row T45543 (what a person must provide for step 3; the PARTIAL rule in its header).
- `platforms/x230v2-28GS.md` §2, the `tpm2-abrmd --tcti=mssim` row.
