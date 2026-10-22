# T47228 process review -- mgmt-2026-10-22T1320
Reviewed 2026-10-22 by /create-logs from agent-a1aa72e7ae787e76c.jsonl (session f7014de7) and the working files.

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 47 | 94 | 76,109 | 4,293,722 | 9,568 | 48 | 899 s | 73,109 |

## Process taken
1. Calls 1-11 (group overhead, see ../REVIEW.md): queue line ranges (10.1 k), the 10-13 reviews' "Next run" sections, the
   RESTCONF memory (7.6 k), tools/README.md line ranges (13.2 k).
2. Calls 25-29: case text; read Group 1's run1.log header (6.4 k) and folder listing (4.2 k) as a template for the log layout.
3. Calls 30-45: gate, pre-reads on u1 and u0, health before, setup (`tools/tb cfg`), ping, both `.cfg` files.
4. Calls 46-52: RESTCONF discovery (host-meta, root, yang-library parsed with an inline python one-liner), wrote work/step.sh.
5. Calls 53-70: S1-S7 interface rows, one step.sh call each; one fix to the step script (`show log tail 6` is below the
   CLI minimum and answered `% Invalid input`).
6. Calls 71-90: VLAN reads, wrote work/vstep.sh, V0-V9.
7. Calls 91-100: health after, restore, drift diff, commit, RESULT.

## Wasted input
- Call 11: 13.2 k of tools/README.md (four line ranges). The case used restconf.py, ckcon, cfg, health and ping
  (about 3 k of entries).
- Calls 27 and 29: 10.6 k reading Group 1's case folder and run1.log to copy the working-log layout. logged-output.md §2
  already lists what a working log must hold; a short template file would do (see "scripts").

## Repetition
- The step script was edited once after its first run: `show log tail 6` gives `% Invalid input` (the minimum is 10).
  Small, but the same driver mistake is likely in every hand-written step script.
- step.sh and vstep.sh are two near-identical drivers (request, wait, the same set of reads). One would do.

## Accuracy risks
- **V3's 204 phantom.** The IETF PUT without a type answered 204 and the IETF GET then returned the entry. The tester
  checked the DUT CLI (no VLAN, no interface, no config line, no NSM line) and graded it a FAIL. A tester who trusted the
  RESTCONF GET would have graded a PASS. The CLI check is the step that matters; keep it.
- The OpenConfig config read lost its `enabled` leaf after the S6 PATCH (the only trace of the 204). Recorded, not graded.
- Persistence across a reboot was not measured ("no reboots"). That limb stays open for a session that allows reboots.

## Next run: expected outputs
| step | request | expected HTTP | expected DUT |
| --- | --- | --- | --- |
| discovery | GET /.well-known/host-meta / GET /restconf / yang-library | 404 / 200 / 200, 78 modules | - |
| S2 | PUT OC .../interface=port1.0.3/config/enabled {"enabled":false} | 204 | admin down, ` shutdown`, log "port1.0.3 user shutdown"; partner "Port down" |
| S3 | same, true | 204 | admin up running, `shutdown` gone |
| S4/S5 | PUT IE .../interface=port1.0.3/enabled false / true | 204 / 204 | as S2 / S3 |
| S6 | PATCH OC .../config/enabled {"enabled":false} | **204** | **no change** (the defect) |
| S7 | PATCH IE list entry | 404 "uri path not found" | no change |
| V2 | PUT IE interface=vlan3999 with type | 403 access-denied | no VLAN |
| V3 | PUT IE interface=vlan3999 without type | **204** | **no VLAN** (phantom in RESTCONF only; DELETE it with a 204 DELETE) |
| V4 | POST IE interfaces | 403 | no VLAN |
| V5 | PUT OC interface=vlan3998 | 404 | no VLAN |
| V8/V9 | DELETE IE / OC interface=vlan3999 (VLAN made by CLI) | 403 / 403 | VLAN still present |

## Next run: scripts
- **Proposed `tools/tb rcstep <TB> <run> <uN> <baud> --host IP --label L METHOD PATH [BODY] --read <cli cmd>...`**:
  one RESTCONF request through tools/restconf.py, then a fixed wait and the listed CLI reads into
  `/tmp/<run>/<label>.out`. It would replace work/step.sh and work/vstep.sh, and its default log read would use
  `show log tail 10` (the minimum).
- `tools/restconf.py` could print the module list from yang-library itself (`--modules`), replacing the inline python.

## Next run: references
- This case's final log STEP tables: every request and its exact answer.
- Memory `awplus-restconf-api-reference`: root /restconf, PUT-on-leaf, no VLAN-database model.
- logged-output.md §2 "The tester's working log": the list of what run1.log must hold, instead of another case's log.
