# T33362 process review -- authmodes-2026-10-23T1304
Reviewed 2026-10-28 by /create-logs from `agent-a2b85027e32e3d1df.jsonl` and the working files.

## Token usage

| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | 6 | 15,160 | 797,183 | 48 | 3 | 161 s | 216 chars |

🔴 **Read this row with care.** The tool segments on `RESULT` lines, so only the tail of the
case is inside the segment. The rig build (two VLANs, two RADIUS groups, two users), the
sixteen measurement legs and the teardown are pooled into the group's `overhead` row. 161 s
against a case that ran 16:12 to 16:26 confirms it. The group total is in `REVIEW.md`.

## Process taken
1. Health read, label `before-T33362`.
2. `qmark` read-only probe of `auth dynamic-vlan-creation`, its `type` and `rule` sub-options,
   `auth multi-vlan-session`, the local-server `user` options and the group `vlan` keyword.
   **This is where the rig design came from:** the local server has no per-user `vlan` keyword,
   so the VLAN must be carried by a group.
3. Built the rig: vlan 362 and vlan 363 with L3 addresses, groups ckdvg1 and ckdvg2, users
   ckdv1 and ckdv2. Read back `show radius local-server user` and `... group`.
4. Set `auth host-mode multi-supplicant`; observed the known `control-direction` rewrite.
5. S0 control, feature off: both clients authenticate, both land in VID 48; five ARP legs, four
   zeros and one 3-of-3 in vlan 48 as the instrument control.
6. S1: `type multi` + `auth multi-vlan-session`; `show auth supplicant brief`, `show vlan brief`,
   then five ARP legs forming the 2x2 matrix plus the vlan 48 re-check.
7. S2: `type single`, run twice, the second with ckdv2 declared `--expect failure`.
8. The `rule permit|deny` investigation: three host-modes x the combined form, then `rule` alone
   with a read after each command.
9. Teardown, including the refused `no interface vlan362`; read back the port, the server, the
   VLAN list, `show auth interface` and the spanning tree.
10. Health read `after-T33362`; capture `swi_d.cfg`; write `work/run1.log`.

## Wasted input
None found inside the case. The health samples are the largest files in the folder (25.8 kB
before, 40.2 kB after) but they are the §8 requirement and `tools/tb health` already reduces
them to a `HEALTH-DIFF` block.

## Repetition
- Eleven `arpleg.py` legs were hand-built across S0 and S1, differing only in source MAC,
  sender IP and target. This is the same shape as T44277's eight legs. One matrix helper would
  serve both — see **scripts**.
- S2 was run twice. The second run exists only to declare ckdv2 `--expect failure` so the
  instrument states the outcome. That is sound method, but the expectation could have been
  declared on the first run and the repeat avoided. **One leg saved.**
- `show auth interface port1.0.48 | include dynamicVlan` after every change: correct practice.

## Accuracy risks
- **The verdict does not rest on inference.** The diagonal matrix, `show vlan brief` and
  `taggedVlansupplicantNum: 0` are all printed output.
- **The attribution of the `type single` refusal to the switch is an inference from three
  independent sources, and they agree:** the 0.039 s timing against the normal 1.037 s, the
  server's own counter (`ckdv2 Successes 4 Failures 0`), and the DUT's log line
  `VLAN is not valid for given supplicant`. This is as closed as it can be from this bench.
- **`rule permit|deny` is characterised, not diagnosed.** The working log says so. The two
  refusal messages contradict each other and no host-mode accepts the combination. **Evidence
  that would close it:** the AW+ command reference for `auth dynamic-vlan-creation`, or a
  developer. The wiki has no x960 pages.
- Claims left out of the final log for lack of a source: **none.**

## Next run: expected outputs
| step | what this bench gave |
| --- | --- |
| local server VLAN path | no per-user `vlan` keyword; use `group <name>` + `vlan <id>`, then put the user in the group |
| S0, feature off | both clients Authenticated in **VID 48**; the server's VLAN attribute is ignored |
| S0, instrument control | 3 of 3 ARP replies in vlan 48 — this is what licenses the zeros |
| S1, `type multi` | VID 362 and VID 363 in `show auth supplicant brief`; `untaggedVlansupplicantNum: 3`, `taggedVlansupplicantNum: 0` |
| S1, `show vlan brief` | `port1.0.48(u)` under **both** 362 and 363 |
| S1, matrix | 3 / 0 and 0 / 3 on the diagonal; the mover drops from 3 of 3 to 0 of 3 in vlan 48 |
| S2, `type single` | first VLAN admitted at 1.037 s; second refused **EAP-Failure at 0.039 s**; port removed from 363 in `show vlan brief` |
| S2, attribution | server counts `ckdv2 Successes 4 Failures 0`; log says `VLAN is not valid for given supplicant` |
| `rule` with `type multi` | `% port1.0.48: Vlan assignment rule is not configured on assignment-per-user port` (multi-supplicant) or `% ... Vlan assignment per user is not configured on single supplicant port` (multi-host, single-host) |
| `rule` alone | accepted silently, and `dynamicVlanCreation` drops to `single-dynamic-vlan` |
| teardown trap | `no interface vlan362` -> `% Removal of interface not allowed`; delete the VLAN in `vlan database` instead |

## Next run: scripts
- **Existing, reuse as is:** `tools/arpleg.py`, `tools/eapol.py`, `tools/qmark.py`,
  `tools/tb ckcon`, `tools/tb health`.
- **Proposed `tools/arpmatrix.py`** — same helper as T44277's review proposes, with a second
  axis: `--targets <ip>[,<ip>...] --pairs <mac>:<sender-ip>[,...]`. It would run the full
  cross product in one invocation and print the matrix. This case built the matrix by hand from
  eleven separate legs, and the matrix *is* the result.
- **Proposed `tools/dynvlanrig.py`**, or a documented snippet: build and tear down N
  (vlan, L3 address, local-server group, user) tuples in one call, including the
  `vlan database` teardown order. The rig is five minutes of typing and the teardown has a trap
  in it.

## Next run: references
- Memory `tcpdump-nfs-root-squash-capture` — the zero-counts-only-after-a-non-zero rule, which
  the fifth leg of S0 satisfies for the whole case.
- Memory `awplus-cli-wiki-on-the-share` — the wiki has no x960 pages, so do not spend time
  looking there for `auth dynamic-vlan-creation`.
- **Left for a next run:** a tagged dynamic VLAN (this case is the untagged variant);
  `Egress-VLANID` and `Egress-VLAN-Name` on the local-server group; a real
  `Tunnel-Private-Group-ID` from an external RADIUS server, which would test the attribute
  decode rather than the port behaviour.
