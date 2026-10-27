# T33369 process review -- authmodes-2026-10-23T1304
Reviewed 2026-10-28 by /create-logs from `agent-a2b85027e32e3d1df.jsonl` and the working files.

## Token usage

| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 4 | 8 | 14,683 | 903,812 | 64 | 4 | 162 s | 409 chars |

🔴 **Read this row with care.** `case_tokens.py` segments on `RESULT` lines, so only the tail of
the case — writing `work/run1.log`, the commit and the `SendMessage` — falls inside the segment.
The bench work itself is pooled into the group's `overhead` row. 162 s of wall time against a
case that ran from 15:57 to 16:09 confirms it. The group total is in `REVIEW.md`.

## Process taken
1. Health read, label `before-T33369`.
2. `qmark` read-only probe of `auth two-step`, `auth two-step order`, `auth-mac`,
   `auth-mac method` and `aaa authentication`.
3. Rig discovery, three findings, each costing one step:
   a. `auth-mac enable` alone made a supplicant entry but sent **no** RADIUS request. The
      missing line is `aaa authentication auth-mac default group radius`.
   b. The MAC-auth user name was **read off the device**, not guessed: one ARP frame put
      `02-0d-b9-00-33-69` under `Users NOT present in the User Database`.
   c. `auth-mac enable` deleted `dot1x control-direction both`.
4. S0 control: two-step off, MAC auth alone, 4 ARP -> 3 replies, Authorized.
5. S1a: `auth two-step enable` only; same MAC, same frames, 0 replies, Unauthorized.
6. S1b: second step with valid 802.1X credentials -> EAP-Success, 4 of 4.
7. S1c: second step with a wrong password -> EAP-Failure at 1.022 s, Held, 0 of 4.
8. S2: a MAC that fails the first step -> 1 EAPOL frame in 45 s, no Identity request.
9. S3 (not asked for by the dispatch): reverse the order keyword, same client, 1 frame -> 8.
10. Restore in the required order (`no auth-mac enable` before `dot1x control-direction both`),
    read back; health read `after-T33369`; capture `swi_d.cfg`; write `work/run1.log`.

## Wasted input
None found. The legs are 1 to 8 frames each. The largest tool output charged to this segment is
231 characters.

## Repetition
- `dot1x initialize interface port1.0.48` before every leg: necessary, not waste. It is what
  removed the superseded-EAP-session anomaly seen earlier in the campaign.
- `show auth supplicant interface port1.0.48` was read in full after each of the five legs. The
  case only ever uses three fields from it (`authenticationMethod`, `portStatus`, `PAE: state`).
  `| include` on those three would have cut each read to three lines without losing evidence —
  but the full block is also what let the final log show the method flipping, so this is a close
  call and the full read is defensible.

## Accuracy risks
- **None that affect the verdict.** The headline is an A/B in which exactly one command changed,
  and both halves were measured with the same instrument.
- The `MISMATCH` printed in STEP 2 is the intended design: the leg was declared
  `--expect success` so the tool, not the tester, would state the shortfall. A reader who greps
  for `MISMATCH` to find failures will mis-read it; the final log says so explicitly.
- The doubled `EAP-Request/Identity id=1` in the reversed-order leg is recorded as seen and not
  explained. It did not change the outcome. **Evidence that would close it:** repeat the
  reversed-order leg three times and see whether the duplicate is constant.
- Claims left out of the final log for lack of a source: **none.**

## Next run: expected outputs
| step | what this bench gave |
| --- | --- |
| MAC-auth user name | `02-0d-b9-00-33-69` — the MAC in lower case with hyphens, and it is also the password |
| missing rig line | `aaa authentication auth-mac default group radius` |
| S0, two-step off | 4 ARP -> 3 replies, `authenticationMethod: MAC-based Authentication`, Authorized |
| S1a, two-step on | same MAC, 4 ARP -> 0 replies, method flips to `802.1X`, `PAE: Connecting` |
| S1b, both steps pass | 6 EAPOL frames, EAP-Success at 1.023 s, 4 of 4, supplicant renamed `ckmulti1` |
| S1c, MAC ok, 802.1X bad | 6 frames, EAP-Failure at 1.022 s, `PAE: Held`, 0 of 4 |
| S2, MAC fails | **1** frame in 45 s, no Identity request, method stays `MAC-based Authentication` |
| S3, order reversed | **8** frames, EAP-Success at 1.009 s, still Unauthorized 0 of 4 |
| the conflict message | `% port1.0.48: DOT1X control-direction cannot be modified on a Web-auth or Mac-auth enabled port` |

## Next run: scripts
- **Existing, reuse as is:** `tools/eapol.py`, `tools/arpleg.py`, `tools/qmark.py`,
  `tools/tb ckcon`, `tools/tb health`.
- **Proposed `tools/macauthuser.py`**, or a `--discover-mac-user` mode on `eapol.py`: send one
  frame from a new MAC, then read `show radius local-server statistics` and print the name the
  DUT tried under `Users NOT present in the User Database`. This case spent a step on it and the
  method is free and exact on any platform. It is worth a tool because it also disposes of the
  question "is the username format platform-specific".

## Next run: references
- Memory `ie520-mac-auth-username-format` — the same `00-f0-4d-00-77-17` style format. This run
  confirmed it on the x960, so the format is AW+'s, not the IE520's.
- Memory `stp-mode-change-reenables-spanning-tree` — the same defect shape as the
  `control-direction` deletion found here (a setting discarded without a message).
- **Left for a next run and recorded so it is not lost:**
  `auth supplicant-mac <MAC> port-control skip-second-auth`, found in T44277's help probe. By
  its name it exempts a named MAC from the second step. It is cheap to test with this rig: set
  it for the passing MAC, repeat S1a, and see whether MAC alone authorises again. Also
  unexercised: `auth-mac method pap` against `eap-md5`, and `auth-mac reauth-relearning`.
