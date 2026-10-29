# T44274 process review -- webauth-2026-10-29T1528
Reviewed 2026-10-30 by /create-logs from agent-a5c31a5061ad810f0.jsonl and the working files.

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 36 | 80 | 45,125 | 3,397,346 | 26,174 | 39 | 893 s | 27,226 chars |

## Process taken
1. Read the queue outline and git state; looked up the previous campaign's T33375 restore method (its final log and, via `git show`, its deleted working log).
2. STEP 0: added local RADIUS users (ckweb, ckdot1x, MAC user ff01); MAC auth and 802.1X enabled on port1.0.81; health before; swi_dut.cfg saved.
3. STEPs 1-5: `arpleg` ICMP legs (fake MACs ff09/ff11/ff12, eth6), `eapol` 802.1X (right and wrong password), `httpq` web login; `show auth supplicant brief` after each.
4. Health after, teardown, rcdiff.

## Wasted input
- `sed -n '330,360p' .../T33375/T33375.log` and `git show e1f54d4:.../T33375/work/run1.log | grep ...` (about 4.5 k chars): the restore recipe was already in the queue's group A recipe. Read the queue lines 186-229 instead.

## Repetition
- The eth6 control leg (t74eth6a) was sent with arpleg's default sender address and re-run. The final log gives only the valid leg.

## Accuracy risks
- ff12 failed 802.1X once (a wrong-password control by design). The working log names it as the control. The final log keeps it as the control.
- MAC and 802.1X clients were fake MACs on the same host NIC as the web client. The final log states this in CAVEAT.

## Next run: expected outputs
- STEP 1: unknown MAC 0/4 ICMP, supplicant brief empty or Connecting.
- STEP 2: MAC user `02-00-5e-c0-ff-01` -> brief `M ... Authenticated`, 4/4.
- STEP 3: 802.1X EAP-MD5 ckdot1x -> `D ... Authenticated`, 4/4; wrong password -> rejected, 0/4.
- STEP 4: web ckweb -> `W ... Authenticated`, 4/4.
- STEP 5: three rows (W, M, D) authenticated together on port1.0.81.

## Next run: scripts
- existing: `arpleg` (always pass `--src` explicitly: the default sender is 192.168.10.2), `eapol`, `httpq`, `tools/tb health`, `rcdiff.py`.
- proposed: `tools/authleg.py` (see dot1x-2026-10-29T1528/T44277/T44277-review.md): one call per leg, auth state + ICMP count as one row.

## Next run: references
- platforms/x980.md §1 (no `clear auth`; `dot1x initialize interface`; grade on supplicant brief).
- queue tb490/x980/CAMPAIGN-QUEUE-2026-10-29T1528.md, Group A recipe (lines 186-229).
