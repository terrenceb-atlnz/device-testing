# T44279 process review -- authmodes-2026-10-23T1304
Reviewed 2026-10-28 by /create-logs from `agent-a2b85027e32e3d1df.jsonl` and the working files.

## Token usage

| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 7 | 14 | 21,593 | 2,180,492 | 68 | 8 | 281 s | 2,537 chars |

This is the largest per-case segment in the group, and it is the one case where the segment
boundary is close to honest: T44279 ran last, so its `RESULT` line is followed by the group's
hand-back, and several of the group-closing calls (the final `ckcon` state read, the
`--read-only` probe, the `bench-state.md` restore, the queue hand-over block) landed in this
segment rather than in `overhead`. Those are **group** costs, not this case's. The real bench
work for the case is still pooled into the group's `overhead` row. See `REVIEW.md`.

## Process taken
1. Health read, label `before-T44279`.
2. `qmark` read-only probe of `auth-web` and `auth-web-server`.
3. Built the three-method rig in one configuration block: two `aaa` method lists, the web
   server address, two local users, and `auth host-mode multi-supplicant` + `auth-mac enable` +
   `auth-web enable` on the port. Read back `show auth`, the running-config and
   `show auth-web-server`.
4. **Noticed the auto-added `auth forward arp/dhcp/dns` and changed instrument because of it.**
   The other four cases in the group probe the dataplane with ARP; with `auth forward arp` in
   force that probe can no longer tell authorised from unauthorised. Switched to ICMP echo via
   `arpleg.py --icmp --gw-mac ... --answer`. This is the single best decision in the case: the
   case would otherwise have produced four false positives.
5. S0 control: an unauthenticated MAC, 4 ICMP, 0 replies.
6. S1: MAC authentication, 4 of 4, plus a repeat once the session had settled.
7. S2: 802.1X with its control **in the same packet window**, 4 of 4 against 0 of 4; diagnosed
   the 3.028 s EAP-Success from the DUT's own log.
8. S3: web authentication. Measured interception with a plain GET, read the login form out of
   the returned HTML, ran the **wrong-password control first**, then the correct password.
9. S4: re-measured the control with all three sessions up, and took the one
   `show auth supplicant brief` that is the case's headline.
10. S5: `no auth-web enable`, checked at three levels; recorded the `show auth` reporting
    inconsistency.
11. Teardown in the required order, read back; health read `after-T44279`; capture `swi_d.cfg`;
    write `work/run1.log`.

## Wasted input
- The three saved HTML artefacts (`webauth-login-page.html`,
  `webauth-POST-wrong-password.html`, `webauth-POST-valid.html`) are the right call: the login
  form is the evidence that no HTTP client was needed, and it is three lines of the page. No
  waste found — the pages were saved to files rather than read back whole into the context.
- One group-closing `ckcon` call in this segment read seven `show` commands at once
  (1,255 characters). That is an efficient batch, not waste.

## Repetition
- The dataplane probe was run six times with only the source MAC and sender IP changed. The
  same `arpmatrix.py` helper proposed in the T44277 and T33362 reviews would cover it, if it
  took an `--icmp` flag.
- `show auth supplicant interface port1.0.48 brief` was read after every leg. Necessary: the
  accumulating table *is* the case's evidence, and the final read is the headline.

## Accuracy risks
- **The verdict does not rest on inference.** The headline is one printed table showing three
  Modes (M, D, W) Authenticated at once, with three per-method counters each reading 1, and
  each session backed by a dataplane count.
- 🔴 **The instrument change is the one place a careless reader could go wrong.** The ICMP
  counts in this case are not comparable with the ARP counts used by the other four cases on
  the same bench. The final log says this in the topology section. Keep that sentence.
- **The `radiusd` process-id change is attributed by elimination**, not proved: no core file,
  no new exception-log entry, no reboot, and the server answered correctly throughout. The
  working log names the likely trigger (the method-list and server change, because adding a
  user alone did not restart it) and labels it as likely. **Evidence that would close it:** add
  only `auth-web-server ipaddress` on a quiet unit and read the pid before and after.
- **The `AAA: failed to update method-list default (unknown type 7)` line is recorded, not
  diagnosed.** Both commands took effect and the read-back proves it. The cause needs a
  developer.
- Claims left out of the final log for lack of a source: **none.**

## Next run: expected outputs
| step | what this bench gave |
| --- | --- |
| `auth-web enable` side effect | the DUT adds `auth forward arp`, `auth forward dhcp`, `auth forward dns` to the port by itself, visibly |
| probe choice | **use ICMP, not ARP** — `auth forward arp` makes an ARP probe unable to discriminate |
| S0 control | 0 echo replies of 4; IP Address column already filled from the forwarded ARP |
| S1 MAC auth | Mode **M**, Authenticated, 4 of 4 |
| S2 802.1X | Mode **D**, EAP-Success at **3.028 s** (not 1.02 s: the DUT tries MAC auth first for every new MAC, and that failed attempt costs about 2 s); control EAP-Failure at 3.032 s |
| web login page | `GET /` -> 200 with `<meta http-equiv="refresh" ... index.cgi?authenticating=1>`; the form is a POST of `USERNAME`, `PASSWORD`, `ACTION=login` to `/index.cgi` with **no cookie, no session token, no CSRF token** |
| web control | wrong password -> 200, body refreshes to the login page, client left Mode **W** Connecting, `webBasedAuthenticationSupplicantNum: 0` |
| S4 headline | `totalSupplicantNum: 4`, `authorizedSupplicantNum: 3`, macBased / dot1x / webBased counters all 1 |
| S5 removal | `totalSupplicantNum: 0`, host ping 4 of 4 -> 0 of 4, `GET` -> `TRANSPORT FAILED: <urlopen error timed out>` |
| S5 trap | `show auth` still reads `WEB-based Port Authentication : Enabled` until `no auth-web-server ipaddress` is also removed — it tracks the global server, not the port |
| teardown order | `dot1x control-direction both` is only accepted once `auth-mac` and `auth-web` are both off |

## Next run: scripts
- **Existing, reuse as is and unchanged:** `tools/httpq.py` with `--method POST --data` drove
  AW+ web authentication without modification. **This is the finding that saves the most time
  next run:** the dispatch expected the web limb to be blocked by tooling, and it was not.
- **Existing:** `tools/arpleg.py --icmp --gw-mac --answer`, `tools/eapol.py`, `tools/qmark.py`,
  `tools/tb ping`, `tools/tb ckcon`, `tools/tb health`.
- **Proposed:** add `--icmp` support to the `tools/arpmatrix.py` helper proposed in the T44277
  and T33362 reviews, so one wrapper covers both probe types.
- **Proposed `tools/triauthrig.py`**, or a documented snippet: build and tear down the
  three-method rig (two `aaa` lists, the web server address, the MAC and web users, the three
  port commands) with the teardown ordering constraint built in.

## Next run: references
- `tb277/x960/platforms/x960.md`, T47199 (2026-10-20) — the management HTTP server answers `/`
  with 404 on this unit. That is what makes the 200 response in STEP 3 attributable to the
  web-authentication server, and it was already on record.
- Memory `ie520-mac-auth-username-format` — the MAC credential format used here.
- **Left for a next run:** HTTPS web authentication (`auth-web-server ssl`, intercept port 443,
  a trustpoint); `redirect-url`, `session-keep`, `login-url`, `page`, `idle-timeout`,
  `max-auth-fail` (default 3, never engaged here because only one wrong password was sent);
  `auth-web-server dhcp`; and what happens when one MAC is eligible for two methods at once.
