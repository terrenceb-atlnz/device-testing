# T44277 process review -- authmodes-2026-10-23T1304
Reviewed 2026-10-28 by /create-logs from `agent-a2b85027e32e3d1df.jsonl` and the working files.

## Token usage

| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | 10 | 14,893 | 926,644 | 80 | 5 | 171 s | 599 chars |

🔴 **Read this row with care.** The tool segments on `RESULT` lines, so only the tail of the
case falls inside the segment: the `work/run1.log` heredoc, a `ckcon` read, the
byte-identical `diff` against a sibling capture, the commit and the `SendMessage`. The bench
work is pooled into the group's `overhead` row. 171 s against a case that ran 15:41 to 15:54
confirms it. The group total is in `REVIEW.md`.

## Process taken
1. Health read, label `before-T44277`.
2. `qmark` self-test, then a read-only probe of `auth supplicant-mac`, its parameter list and
   its `port-control` sub-options. **The help text gave the shape of the feature before a single
   command was sent**, and that is what saved this case from being designed wrongly.
3. S0 baseline: both MACs, 4 ARP each, 0 replies each.
4. S1: the bare `auth supplicant-mac 020d.b900.4277`. Two measurements, both negative — the
   named MAC is not admitted (0 of 4) and the port is not restricted (an unnamed MAC
   authenticates, EAP-Success at 1.024 s).
5. S3: `port-control force-authorized`. Two dataplane legs back to back, 3 of 4 against 0 of 4.
6. S4: `port-control force-unauthorized`. First attempt put both MACs in one `eapol.py` run and
   **both** timed out; diagnosed as `auth host-mode single-host` taking the port. Re-run one at
   a time with `dot1x initialize` between: named MAC 1 frame in 40 s, control MAC EAP-Success
   at 1.025 s.
7. The single-valued-entry finding, isolated deliberately in four commands with a read after
   each.
8. S5: removal, read back, and a dataplane leg proving 0 of 4 again.
9. Health read `after-T44277`; capture `swi_d.cfg`; `diff` it against the sibling capture;
   write `work/run1.log`.

## Wasted input
None found. The largest tool output in the segment is 599 characters across five calls.
`show auth interface port1.0.48` was read in full rather than filtered, but the per-MAC block it
prints is the evidence for the finding in step 7, so the full read earned its size.

## Repetition
- `arpleg.py` was invoked eight times with only the source MAC, sender IP and tag changed. A
  matrix helper would have replaced all eight. See **scripts**.
- The S4 leg was run twice: once as a pair in one window, then once per MAC. The first attempt
  was not waste — it produced the diagnosis that single-host takes the port — but a next run
  that already knows this does not need to repeat it. **Expected outputs** below records it.
- `show running-config interface port1.0.48` after every configuration change: correct practice.

## Accuracy risks
- **The verdict does not rest on inference.** Every claim is a frame count or a line the DUT
  printed. The two headline legs are additionally named by MAC in the DUT's own log
  (`Force Authorized` / `Force Unauthorized`).
- **3 of 4, not 4 of 4**, in the force-authorized leg. The working log attributes the missing
  first reply to the entry still being created, and supports it with `No supplicants` read
  moments earlier. That is a reasonable reading and the comparison that carries the verdict is
  3 against 0. **Evidence that would close it:** send one throwaway frame to create the entry,
  then run the 4-request leg, and expect 4 of 4.
- **The single-valued-entry finding is proved from the configuration, not from behaviour.** The
  working log says so and gives the reason (a behavioural check needs a 3600 s window). The
  finding is still solid: three commands, three reads, each immediately after its own command.
  **Evidence that would close it:** one overnight leg at the default period.
- **Not established, and the working log says so:** whether one setting per entry is intended.
  That needs the command reference or a developer.
- Claims left out of the final log for lack of a source: **none.**

## Next run: expected outputs
| step | what this bench gave |
| --- | --- |
| help probe | parameters `mask`, `max-reauth-req`, `max-req`, `port-control`, `quiet-period`, `reauth-period`, `reauthentication`, `server-timeout`, `supp-timeout`, `<cr>` |
| `port-control ?` | `auto`, `force-authorized`, `force-unauthorized`, `skip-second-auth` |
| S0 | both MACs 0 of 4 |
| S1 bare command | named MAC 0 of 4; `show auth supplicant brief` reads `No supplicants` while the entry exists |
| S1 control | unnamed MAC authenticates, EAP-Success at 1.024 s |
| force-authorized | named MAC **3 of 4** with zero EAPOL frames; `port1.0.48 48 NONE 020d.b900.4277 ForceAuthorized -- --`; control 0 of 4 |
| force-unauthorized | named MAC **1 EAPOL frame in 40 s**, no EAP-Failure, refusal is silence; control EAP-Success at 1.025 s |
| both MACs in one window | **both time out** under `auth host-mode single-host` — run them one at a time |
| single-valued entry | `reauthentication` then `reauth-period 15` leaves only the period; `reauthentication` again leaves only `reAuthenticate: enabled` with period back to 3600 |
| removal | named MAC back to 0 of 4 |

## Next run: scripts
- **Existing, reuse as is:** `tools/arpleg.py`, `tools/eapol.py`, `tools/qmark.py`,
  `tools/tb ckcon`, `tools/tb health`.
- **Proposed `tools/arpmatrix.py`**, a thin wrapper over `arpleg.py`: arguments
  `--iface --target <ip> --pairs <mac>:<sender-ip>[,<mac>:<sender-ip>...] --count N --tag`.
  It would run every pair against the target in one invocation and print a reply-count table.
  This case hand-built eight `arpleg.py` lines; T33362 hand-built five more against two targets,
  which is the same shape with a second axis. One helper serves both.
- **Existing:** `tools/tb health` and the `HEALTH-DIFF` output it produces; nothing to add.

## Next run: references
- Memory `scapy-for-traffic-tests` and `STANDING-ORDERS` §7 — the reason the probe is a crafted
  ARP request and not a ping.
- Memory `tcpdump-nfs-root-squash-capture` — the rule that a zero counts only once the same
  instrument has returned a non-zero. This case follows it; the control leg is what licenses
  every zero in the log.
- Memory `stp-mode-change-reenables-spanning-tree` — the same defect shape as the
  single-valued-entry finding.
- **Left for a next run:** per-MAC `quiet-period`, `supp-timeout`, `max-req` and
  `max-reauth-req` are all measurable the same way (a per-MAC value differing from the
  port-wide one, timed on the wire). `quiet-period` is the cheapest at about 30 s a leg. The
  `mask` sub-option (a MAC range) is untested.
