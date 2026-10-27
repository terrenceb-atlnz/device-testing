# T33360 process review -- dot1x-2026-10-23T1304
Reviewed 2026-10-28 by /create-logs from `agent-a6601a35454174322.jsonl` and the working files.

**How to read the numbers.** The measurement work for this case is not in the segment below.
`tools/case_tokens.py` starts a case at its first tool call into its own folder, and this tester
only touched `T33360/` when it wrote the working log. Everything from the console reads to the
five supplicant runs is in the group `overhead` row in `REVIEW.md`. See that file for the shared
findings.

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | 12 | 15 578 | 1 754 537 | 104 | 6 (Bash 4, Write 1, SendMessage 1) | 202 s | 1 860 chars |

## Process taken
1. Build `T33360/swi_d.cfg` with a header that points at the `control-direction` finding (call 1).
2. Cut the console fragments for the working log out of the captured setup output (call 2).
3. Write the working-log template (call 3) and substitute the fragments into it with the
   `subst.py` helper already written for the previous case (call 4).
4. Update the `tools/eapol.py` status line in `tools/README.md` from "not yet re-verified on
   hardware" to verified (call 5).
5. Send the RESULT line (call 6).

This is the cheapest of the four write-ups, because the template and the substitution script
already existed from the previous case. That reuse is the right pattern.

## Wasted input
None found in this segment. The largest single read is 603 chars.

## Repetition
- A new fragment directory (`frag2`) was cut by hand for this case, with the same `sed` range
  pattern as the previous one. The template and the script were reused; the extraction was not.
  A `tools/mklog.py` helper would close the gap (proposed in the T44270 review).

## Accuracy risks
1. **`tools/eapol.py` was written during this case and its first two runs were wrong.** The first
   computed the MD5 digest over the wrong bytes, because scapy puts an MD5-Challenge in a field
   and leaves only Ethernet padding in `eap.payload`. The second ignored its own `--timeout`,
   because a scapy socket `recv()` blocks. Both were fixed and the fix was proved against
   `wpa_supplicant`, whose EAP-MD5 is not in doubt, before any measurement was taken. **The risk
   is the pattern, not this case:** a tool written inside the measurement window can produce a
   wrong number that looks like a product defect. **What would close it:** a fixed smoke leg, run
   against a known-good credential, as the first act of any case that uses a new traffic tool.
   This case did exactly that and it is why the defects were caught.
2. **The RADIUS server's counters are cumulative for the whole group** and include the two failed
   tool runs. `Unknown EAP auth type` went 0 to 4 and `Invalid packet from NAS` 2 to 4 during the
   case. No reading of either is sourced, so both are **left out of the final log**. Every step
   verdict rests on the EAPOL frames and on `show auth supplicant`, which are unambiguous.
   **What would close it:** a `clear radius local-server statistics` before each case, if such a
   command exists on this build; it was not probed.
3. **The `control-direction` finding rests on reading the running-config, not on a device
   message.** That is the finding: the device says nothing. The evidence quoted in the final log
   is `show running-config interface port1.0.48` and `show dot1x interface port1.0.48` before and
   after, which is as direct as the device allows.
4. Two tool defects in `tools/tb killmine` were found and fixed during this case. They are
   infrastructure, so they are **left out of the final log**.

## Next run: expected outputs
| step | what this bench gave |
| --- | --- |
| 0, single-host, 2 supplicants | 7 EAPOL frames; MAC `...3360` EAP-Success at 1.03 s; MAC `...3361` gets **nothing at all** in 40 s, so the tool reports `1/2 ... MISMATCH`, which is the correct baseline result |
| 1, enable | `show dot1x interface port1.0.48` -> `hostMode: multi-supplicant`, `portStatus: Unauthorized` |
| 2, 2 supplicants | 12 frames, both EAP-Success at 1.03 s; `authorizedSupplicantNum: 2`, two `Authenticated` rows |
| 3, plus bad-password MAC | 18 frames, 3/3 matched; the brief table reads `Authenticated`, `Authenticated`, `Held`, and the `Held` row's Username column is **blank** |
| 4, per-MAC check | ping from the host's own unauthenticated MAC -> 0 of 4 |
| 5, host MAC authenticates | 7 frames, EAP-Success; `authorizedSupplicantNum: 3`, `SupplicantUntaggedCount: 3`, `maxSupplicant: 1024`; ping 4 of 4 |
| after enabling | `dot1x control-direction` silently reads `in`; `no auth host-mode` leaves it `in` |

## Next run: scripts
- `tools/eapol.py <iface> --supplicant MAC:identity:password[:expect] [--supplicant ...]
  --timeout N --label L --pcap F --json F` is the tool for this case and is now verified on
  hardware. It is the only way to put several source MACs on one wire; `wpa_supplicant` drives
  one supplicant per interface and cannot do it.
- Declaring every supplicant `expect=success` in the OFF baseline is a good trick: the tool, not
  the tester, then states that the baseline admits only one.
- Put the control in the **same invocation** as the legs it controls for. That is what gave a
  single 1.04-second packet window covering all three supplicants.

## Next run: references
- The `control-direction` behaviour is now recorded in the campaign queue's findings section and
  reproduced independently in T33354. Expect it; do not re-diagnose it.
- `tools/README.md`, the `eapol.py` entry, carries the scapy padding trap: take EAP Type-Data
  from the raw bytes using the EAP header's own length field, never from `eap.payload`.
- `platforms/x960.md` section 7E for the `auth host-mode` command surface.
