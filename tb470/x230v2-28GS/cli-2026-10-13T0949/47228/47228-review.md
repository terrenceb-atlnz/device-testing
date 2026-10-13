# T47228 process review -- cli-2026-10-13T0949
Reviewed 2026-10-13 by /create-logs from `agent-a3ab1e57621c1d438.jsonl` and the working files.
Group-wide findings: [../REVIEW.md](../REVIEW.md).

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 41 | 82 | 72,018 | 8,192,742 | 7,474 | 44 | 773 s | 58,648 chars |
| *apportioned:* 37 | 74 | 68,821 | 7,259,900 | (not re-split) | 40 | ~730 s | 56,840 chars |

The measured segment ends at `RESULT 47228`, so it also holds the group's after-run checks (#41-#44:
`bench-state.md` diff, post-run probe, checkout, queue DONE; 932,842 cache-read). The apportioned row moves
those to overhead. Even so this case is about half (49%) of the group's cache reads: 37 calls each re-reading a context
of ~200k tokens.

## Process taken
1. #1 wrote `tools/restconf.py` (new, 3,152 output tokens); #2 compile + setup (vlan105 address) + qmark
   `service`/`restconf` + ping.
2. #3-#5 host-meta (404), the four roots, the yang-library to a file (3,944 chars back).
3. #6 first GETs (openconfig-vlan 404, port1.0.8 config/state).
4. #7-#9 downloaded YANG deviation modules to the session scratchpad and read them (5,288 chars).
5. #10-#12 container PATCHes (404), OPTIONS, ietf PATCH (404); #13-#14 downloaded the NETCONF/RESTCONF feature
   guide PDF and read three ranges of it (13,066 chars, #14 alone 10,538).
6. #15 leaf PUT with a qualified body (400) + system PATCH + `/ds` GET; #16-#18 leaf PUT/PATCH, CLI on u0/u1
   after each (`cli-10/11/12`).
7. #19 the controlled H1-H8 matrix + device log (4,077 chars).
8. #20-#22 VLAN survey, create W1-W5, CLI, phantom DELETE, access-vlan X3; #23-#24 CLI check, undo Y1,
   CLI VLAN create; #25-#26 DELETE Z2-Z5 with CLI.
9. #27 teardown + rcdiff; #28-#29 a RESTCONF "residue" GET after the teardown had removed the vlan105
   address (No route to host), then read the file.
10. #30-#34 two `restconf.py` fixes (error-message path, bad-JSON exit) + README entry; #35 teardown file
    checks; #36-#37 memory `awplus-restconf-api-reference` updated; #38-#39 working log; #40 commit.
11. (#41-#44 group after-run checks, moved to overhead); #45 RESULT.

## Wasted input
- #13-#14 (13,066 chars): the feature guide was fetched and three wide ranges read. Memory
  `awplus-restconf-api-reference` (read in overhead #9) already named the guide and its points; the
  log uses two sentences of it (host-meta, "no known limitations"). `grep -n -i 'host-meta\|limitation\|PATCH'`
  on the text would have been ~1k.
- #7-#9 (5,288 chars): YANG deviation modules downloaded and read to look for a VLAN container. The device
  answered the question directly (GET `openconfig-vlan:vlans` 404 in #6); the module list from the
  yang-library (one `python3 -c` over `yanglib.json`, ~1k) was enough to show no VLAN-database model.
- #5 (3,944 chars): the yang-library was saved to a file and also printed; only module names were needed.
- #28-#29: the residue GET ran after teardown removed the API address, so it could not connect; it should
  run before the teardown (2 calls wasted).

## Repetition
- The PATCH/PUT question was answered three times: the first leaf pass (#16, PUT and PATCH sent one second
  apart, so the effect could not be attributed), the enable pass (#17-#18), then the clean matrix (#19).
  Starting with the one-request-at-a-time matrix (state read after each) would have settled it in one call.
- `restconf.py` was written, then edited twice inside the case (#30, #32) after the residue error exposed a
  message bug. Writing a tool mid-case is allowed (logged-output.md §2), but it lengthened the case by ~5 calls.

## Accuracy risks
- **Link-partner proof of the enable.** The 4050 side is captured after the disable (port1.0.5 `down`) and after
  the PATCH enable (still `down`), but not after the PUT enable: only the x230's `port1.0.8 admin up running`
  (link up) shows it. The Results row says "proven at both link ends"; the final log claims the far end only
  for the disable. Next time, read u1 `show interface brief` after G1/H4.
- **The first leaf pass is ambiguous.** At 11:33:22-23 a PUT `{"enabled":false}` and a PATCH were sent a
  second apart; the disable seen at 11:33:24 cannot be assigned to either. The final log grades only the
  matrix (H1-H8) and the F1/G1 pair, where one request precedes each state read.
- **Device-log times for H3/H4 are not captured** (the `show log tail 10` at 11:36:32 starts at H7). The
  working log says "H3/H4 lines earlier"; the final log quotes only the H7/H8 lines.
- **X1's empty body** ("{}" in the working log) is printed only as `(2 bytes)`; the final log quotes the
  byte count.
- **"No VLAN-database model"** is an inference from 404s on three VLAN-list paths and the module list; the
  final log states those observations, not a model audit.
- Unsourced claims left out of the final log: none beyond the above wording choices.

## Next run: expected outputs (x230v2-28GS, awplus_main-20261008-57)
| request | expected |
| --- | --- |
| GET `/.well-known/host-meta` | 404 (nginx); use `--root /restconf` |
| PUT `data/openconfig-interfaces:interfaces/interface=<port>/config/enabled` `{"enabled":false}` | 204; state `DOWN/DOWN`; CLI `admin down`, `shutdown`; log `NSM: <port> user shutdown` |
| PUT same `{"enabled":true}` | 204; `UP/UP`; log `user no shutdown` |
| PUT `data/ietf-interfaces:interfaces/interface=<port>/enabled` false / true | 204, same effect |
| PATCH on the leaf, any body | 204, no effect (FAIL) |
| PATCH on `.../config` or `interface=<port>` | 404 "uri path not found" |
| PUT with `{"openconfig-interfaces:enabled":...}` | 400 "Invalid input parameter" |
| GET `openconfig-vlan:vlans`, `at-l2-topology:vlans` | 404 |
| PUT `ietf-interfaces:...interface=vlan3999` `{"interface":[{"name":"vlan3999"}]}` | 204, readable by GET, nothing in `show vlan brief` (FAIL) |
| DELETE of a CLI-created `interface=vlan3999` (ietf or openconfig) | 403 `access-denied` (FAIL) |

## Next run: scripts
- **`tools/restconf.py`** (existing, written in this case): use it as is.
- **`restconf.py --plan FILE`** (proposed extension): lines `METHOD path [body] => expect-code [; GET path
  =~ regex after N s]`, one request at a time with the state read after each, printing one PASS/FAIL row
  per line. The H1-H8 matrix and W1-W5 / Z2-Z5 become data files, and the table above is the plan.
- Pair it with one `ckcon.py` call per phase on u0 and u1 (`show interface brief`, `show vlan brief`,
  `show log | include NSM`), so both link ends are read after every state change.

## Next run: references
- Memory `awplus-restconf-api-reference` (updated by this case: root, PUT-on-leaf, PATCH no-op, VLAN 204/403).
- `platforms/x230v2-28GS.md` §2, the RESTCONF row.
- `tools/README.md` `restconf.py` entry ("AW+ facts it met").
- The feature guide only for `host-meta` (p.4) and "Limitations"; do not re-read it in full.
