# T33354 process review -- dot1x-2026-10-23T1304
Reviewed 2026-10-28 by /create-logs from `agent-a6601a35454174322.jsonl` and the working files.

**How to read the numbers.** The segment below starts at the tester's first tool call into
`T33354/`, which is the write-up. It also carries the group's closing work, because this was the
last case: the end-of-group console reads, the re-probe, the queue update and the artefact
collection all fall inside it. The three measured legs themselves are in the group `overhead`
row in `REVIEW.md`.

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 16 | 32 | 27 467 | 7 068 484 | 197 | 16 (Bash 14, Write 1, SendMessage 1) | 389 s | 10 864 chars |

## Process taken
1. Build `T33354/swi_d.cfg` with a header naming the case-only RADIUS configuration (call 1).
2. Cut console fragments (call 2), write the template (call 3), substitute (call 4).
3. Add the `tools/radeap.py` entry to `tools/README.md` (call 5).
4. Commit the case (call 6).
5. Group close: read back `show boot`, `show auth`, `show radius`, `show radius local-server nas`
   on the console (call 7); re-probe the bench (call 8); restore `bench-setup/tb277/bench-state.md`
   and prove both legs with pings (call 9).
6. Pull, then write the Results rows and the findings section into the campaign queue
   (calls 10, 11, 12).
7. Copy every leg's decoded JSON off the box into the case folders (calls 13, 14) and commit
   (call 15).
8. Send the RESULT line (call 16).

## Wasted input
- Call 10, 5 591 chars: `git pull` plus a grep of the Results heading plus a `sed` of the whole
  Issues section of the campaign queue. The queue had already been read in full in the group
  overhead (24 318 chars). A targeted `grep -n` for the two anchor lines about to be edited
  would have been a few hundred characters.
- Call 13, 1 091 chars, combined a console tail with a `find` of the group directory. Small, and
  it was the deliverables check, so it earns its place.
- Nothing else here is large.

## Repetition
- A fourth fragment directory (`frag4`) was cut by hand with the same `sed` range pattern used
  for the three earlier cases. Same gap as before; see the proposed `tools/mklog.py`.
- The campaign queue was read in full once in the overhead and partly again here. Read it once,
  keep the line numbers.

## Accuracy risks
1. **The DUT's own log holds no trace of the notification**, so the switch cannot corroborate the
   feature. The verdict rests on two independent instruments that are both outside the DUT: the
   frames captured on the supplicant's wire, and `tools/radeap.py`'s own log and counters. This
   is stated in the final log's CAVEAT. The A/B pair is what makes it safe: the control leg,
   differing in one server flag, produces 6 frames and `NOTIFICATIONS SENT=0`, so the extra two
   frames in leg B cannot come from the rig.
2. **`tools/radeap.py` was written for this case and had never run before it.** Its correctness
   is load-bearing for the result. The control leg is also the tool's own proof: the same server,
   with the flag off, sends nothing and the authentication still succeeds. **What would close it
   further:** decode the pcap with an independent dissector and confirm the Notification frame's
   EAP type is 2, rather than relying on the tool's own decoder for both ends.
3. **The notification text is the only thing proving the relay is faithful.** The final log quotes
   the raw hexadecimal Type-Data so a reader can decode it without trusting the tool's printed
   line. The string was deliberately made distinctive so nothing else on the bench could produce
   it.
4. **The authored objective says `Not Support` and the TPS row says `Yes`.** The measurement
   agrees with the TPS. Taking the objective at face value would have produced an UNSUPPORTED
   verdict with no packet sent. The disagreement is reported in the final log's VERDICT.
5. The leg C run used `auth host-mode multi-supplicant`, which silently changed
   `dot1x control-direction` to `in`. That did not affect the result, because the notification
   travels on ingress frames, and `both` was restored and read back.

## Next run: expected outputs
| step | what this bench gave |
| --- | --- |
| 0, point dot1x at the testbox | `show radius` lists both `127.0.0.1` port 1812 and `10.38.22.33` port 11812 |
| A, control, no notification | 6 EAPOL frames, EAP-Success at 1.03 s; server prints `NOTIFICATIONS SENT=0  RESPONSES RELAYED BACK=0` |
| B, with notification | 8 frames; frame 4 is `EAP-Request/Notification id=2 len=50`; raw Type-Data `636b2d...64617973`; frame 5 is the empty Response; EAP-Success at 1.04 s |
| B, server side | `EAP code=2(Response) id=2 type=Notification len=0` arrives back at the server |
| C, good and bad together | 16 frames; both MACs get the notification; good password EAP-Success 1.05 s, wrong password EAP-Failure 0.05 s; server prints `NOTIFICATIONS SENT=2  RESPONSES RELAYED BACK=2` |
| DUT log | nothing about the notification at all |

## Next run: scripts
- `tools/radeap.py --secret S --client IP --user NAME:PASSWORD [--notify TEXT] [--auth-port N]
  [--seconds N] [--log F]` is the server. It binds port 11812, which is unprivileged, so it
  needs no root. `tools/radsrv.py` cannot be used: it is PAP only and cannot carry an
  EAP-Message.
- **Start the server with `run_in_background` BEFORE the supplicant call.** Two tool calls issued
  in one block run one after the other, so a server started beside the supplicant is not
  listening when the supplicant starts.
- `--seconds N` bounds the server's life, so nothing is left listening if a leg dies.

## Next run: references
- RFC 3748 section 5.2 is the specification being tested: a Notification is EAP type 2, carries
  displayable text, and the peer must answer with an empty Response of the same type.
- RFC 3579 requires a Message-Authenticator on any RADIUS packet carrying an EAP-Message.
  `tools/radius.py` already has the codec and the helper; `radeap.py` is a state machine on top
  of it.
- `platforms/x960.md` section 7E.1: never point the **login** method list at RADIUS on this unit.
  Only `aaa authentication dot1x` was changed here, through a named server group, so the DUT's
  own local server stayed in place for the rest of the group.
- Use the other leg (eth3, vlan 10, port1.0.10) for the DUT's RADIUS traffic. The port under test
  must not carry it.
