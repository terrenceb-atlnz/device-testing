# T44270 process review -- dot1x-2026-10-23T1304
Reviewed 2026-10-28 by /create-logs from `agent-a6601a35454174322.jsonl` and the working files.

**How to read the numbers.** `tools/case_tokens.py` splits a transcript on the tester's `RESULT`
lines, and a case's segment starts at its first tool call into its own case folder. This tester
drove the bench from its scratchpad and only touched `T44270/` when it came to write the working
log, so the segment below covers the **write-up**, not the measurement. The bench work for all
four cases sits in the group `overhead` row in `REVIEW.md`. Do not read the small figure here as
efficiency.

One more thing to know: the tester wrote its boundary lines as `RESULT AWPTCM-T44270 ...`, and
`case_tokens.py` matches `^RESULT T?<id> `. `--find` therefore returns empty rows for every case
in this campaign. The numbers below came from a copy of the transcript with `RESULT AWPTCM-T`
rewritten to `RESULT T`. Fixing the regex in `case_tokens.py` would remove that manual step.

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 22 | 44 | 52 076 | 4 586 769 | 214 | 22 (Bash 19, Write 2, SendMessage 1) | 748 s | 13 630 chars |

## Process taken
1. Build `T44270/swi_d.cfg` from the captured running-config with a written header (calls 1, 3).
2. Check the header against the file, and count `auth log` lines in it (call 2).
3. Read `logged-output.md` lines 132-171 for the working-log rules (call 4).
4. Pull the case records for all three remaining group A cases in one loop (call 5).
5. Build the working log out of fragments cut from the captured console output plus a template
   and a substitution script (calls 6, 15, 16, 17, 18).
6. Check the one artefact whose JSON disagreed with its own printed RESULT (calls 12, 13).
7. Re-send `dot1x initialize interface port1.0.48` and confirm no tool was left running
   (calls 8, 14).
8. Add the `wpasup.py` entry to `tools/README.md` (calls 19, 20).
9. Commit, then send the RESULT line (calls 21, 22).

## Wasted input
- Call 4, `sed -n '132,171p' logged-output.md`, 2 749 chars. The same rules were read again in the
  group overhead before the first case. Read once per group, not once per case.
- Call 12 loaded `T44270-S4-peap-nouser.json` through a Python snippet that printed four fields.
  A `tools/tb` read of the three fields would have been smaller, but the cost here is small
  (2 112 chars) and the check was worth making.
- Nothing else in this segment is large. The group's large reads are in `REVIEW.md`.

## Repetition
- The working log was assembled with a scratchpad template plus `subst.py`, and that pattern was
  then rebuilt for each later case with a new fragment directory (`frag`, `frag2`, `frag4`). The
  script was reused; the fragment extraction was redone each time. A `tools/` helper would make
  it one call per case (see below).
- `tools/wpasup.py` was edited twice and `tools/eapol.py` three times across the group, because
  both were written during the run. Writing and proving a tool is not waste, but it belongs
  before the measurement window, not inside it.

## Accuracy risks
1. **A tool artefact that contradicted itself, and is therefore not in the final log.** The first
   run of control B printed 22 EAPOL frames and `MATCH` with exit 0, while the JSON file written
   beside it recorded `"verdict": "timeout"` and `"eapol_frames": 2`. The tester re-ran the leg
   unchanged and graded the second run, whose stdout and JSON agree. The cause was never found.
   **What would close it:** make `wpasup.py` write the JSON from the same objects it prints from,
   and have it fail loudly if the two disagree. Until then, every run must compare them, which is
   what T9032's later run did for all five of its legs.
2. **`Invalid packet from NAS` went 0 to 2 during the case and nobody can say why.** Every other
   NAS counter stayed 0. It is recorded in the working log as an observation and is **left out of
   the final log**, because no reading of it is sourced. **What would close it:** a packet capture
   of the loopback RADIUS exchange, or a developer's reading of what that counter counts on this
   platform.
3. **The very first PEAP attempt of the session failed and five later ones did not.** The working
   log characterises it: the authenticator had already sent an Identity request before the
   supplicant was listening, and the rejection came 0.0002 s later with every RADIUS counter still
   zero. The final log carries only the method consequence, in the CAVEAT: every leg was started
   after `dot1x initialize`. **What would close it:** one deliberate leg with no `dot1x initialize`
   before it, captured, to show whether a superseded session is always rejected this way.
4. The local RADIUS server's counters are shared by the whole group, so they cannot be attributed
   to one case. The final log quotes them and says what the doubling means, and rests no verdict
   on them.

## Next run: expected outputs
| step | what this bench gave |
| --- | --- |
| 0, feature off | `tools/tb ping tb277 eth4 10.38.22.66 4` -> 4 received, 0% loss |
| 1, dot1x on | `show dot1x interface port1.0.48` -> `portStatus: Unauthorized`, `hostMode: single-host`, `PAE: quietPeriod: 60`; ping -> 0 received |
| 1, rig check | `show radius local-server statistics` -> `Enabled methods : MAC EAP-MD5 EAP-TLS EAP-PEAP`, `EAP trustpoints : local` |
| 2, PEAP valid | 24 EAPOL frames; offered methods Identity, MD5-Challenge, PEAP; EAP-Success at about 1.038 s; `portStatus: Authorized`; first ping 3 of 4 (ARP), second 4 of 4 |
| 2, certificate seen | CA `/O=Allied Telesis, Inc./CN=AlliedWarePlusCAA2WQS700B`, leaf `/O=Allied-Telesis/CN=AlliedwarePlusSystem/serialNumber=NULL` |
| 3, wrong password | 22 frames, EAP-Failure at about 1.035 s, `Supplicant name: -`, ping 0 of 4 |
| 4, unknown identity | 22 frames, EAP-Failure at about 1.035 s; radiusd logs `mschap: FAILED: No NT-Password` and `via TLS tunnel` |
| 5, valid again | 24 frames, EAP-Success |
| counters | 2 Successes per PEAP authentication; an unknown identity gets no user-table row |

## Next run: scripts
- `tools/wpasup.py <iface> --method peap --identity U --password P --expect success|failure
  --timeout 45 --label L --pcap F --json F` already does the whole leg. Use it; do not hand-build
  a supplicant.
- **Proposed:** `tools/mklog.py <case-dir> --template T --fragments D`. The three cases in this
  group each rebuilt the same fragment-plus-template assembly by hand in the scratchpad. One
  helper that cuts named ranges out of a captured console file and substitutes them into a
  template would remove that work from every future case.
- **Proposed fix, not a new script:** `tools/case_tokens.py` should accept `RESULT AWPTCM-T<id>`
  as well as `RESULT T<id>`. One regex.

## Next run: references
- `platforms/x960.md` section 7E for the RADIUS and 802.1X command surface on this platform,
  including that `auth log dot1x` writes no running-config line because it is the default.
- `platforms/x960.md` section 6.5: every SVI on this platform shares one MAC, which is why every
  EAPOL frame from the authenticator has source `e0:1a:ea:d4:70:43`.
- The group rig recipe is the authored precondition of T9032. `radius-server host 127.0.0.1` is
  part of it and is load-bearing: without it `group radius` has nothing to reach, even though the
  local server is listening on 127.0.0.1.
- Trustpoint `local` already exists on this unit and PKI state does not appear in
  `show running-config`. Do not create or delete it.
- The capture filter `ether proto 0x888e` is mandatory on tb277: loop protection sends one frame
  per second on 57 instances.
