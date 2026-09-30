# VLAN group — IE520 stack, tb470, 2026-09-29

Queue: [../CAMPAIGN-QUEUE-2026-09-29.md](../CAMPAIGN-QUEUE-2026-09-29.md) row 7. Hand-driven cases (no
framework script): `ckcon.py` (a console.py wrapper, prompt-driven login, `--stop-on-error` on any `% `
line) on the stack master `/dev/u5`, the IE520-sa `/dev/u3` and the x230 `/dev/u0` (9600), plus
`vsend.py`/`vcount.py` (scapy) and tcpdump on tb470's NICs. Run through `/test-mode` with the
bench-runner agent as tester, Terrence away. Tooling copies are in `evidence/`; the live copies and raw
console transcripts are in tb470 `/tmp/ckvlan/` (tmpfs).

**State: IN PROGRESS (resumed 2026-09-30 16:15, section "2026-09-30 resume" below).** Earlier: 2 of the 5 runnable cases done. The first tester ran out of usage at 14:57
after T38409's teardown, before writing its log. A successor wrote the log from the evidence and
restored the bench at 17:14–17:16 (verified 17:17). **Resume next session with 38408, 38407, 18302,
18303. The group setup below must be redone first**, because the bench is back at the standing topology.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T18252 | vlan classifier and tag vlan | [18252.log](18252.log) | **PASS**. Five frame types were classified by ipv4-subnet/proto rules into 210/220 and flooded to exactly the predicted ports in both directions: host captures 100/100 with the right tags, DUT output deltas +100/0 (commit 09bba4f) |
| T38409 | GVRP - basic functionality | [38409.log](38409.log) | **PASS**. GVRP ran on stack port4.0.26 ↔ SA port1.0.26 (1G SX). The SA learned the DUT's 3991/3992 and later 302 as DYNAMIC. The DUT learned the SA's 301 as DYNAMIC (registrar INN). Observation O-1 (not graded): a VLAN created, or getting its first live member, after GVRP is up is not declared until `no gvrp`/`gvrp` on the port. Seen on both IE520s |
| T38408 | QinQ basic | [38408.log](38408.log) | **PASS** (2026-09-30). Port-based QinQ: CE port3.0.13 added S-tag 3995 to customer-tagged and untagged frames and popped it on egress. Provider ports 1.0.13/1.0.2 switched double-tagged frames on the outer tag, provider → provider still double-tagged. Decoy VLAN = inner VID got nothing. Feature-OFF baseline dropped 100/100. 100/100 in every stage |
| T38407 | VLAN translation basic | — | **NOT YET RUN**: resume next session |
| T18302 | Private VLAN send from uplink port | — | **NOT YET RUN**: resume next session |
| T18303 | Private VLAN send from private port | — | **NOT YET RUN**: resume next session |
| T27887 | vlan-based QinQ interop with vlan translation | [27887-unsupported.log](27887-unsupported.log) | **UNSUPPORTED** (2026-09-30). The licence bits are on (FULL: VlanDT, VLAN-TRANS-FULL/LITE on members 1/3/4 and the SA), but the global VLAN-based QinQ command `vlan-stacking vlan … outer-vlan …` is `% Unrecognized command` on both IE520s. Supplementary, not graded: port-based QinQ + translation on one provider port was accepted and translates the OUTER tag (100/100 each way). O-2: the translation `outer-vlan` double-tag drops the customer tag |
| T38410 | Voice VLAN basic | [38410.log](38410.log) | **PASS** (2026-09-30). `switchport voice vlan 3997` on port3.0.13 → the DUT's LLDP-MED Network Policy TLV to a scapy Class III phone on eth1 was voice, Tagged, VLAN 3997, L2 priority 5, DSCP 0 (none at baseline). Tagged DHCP was leased 192.168.97.100 from the DUT's own pool (OFFER/ACK in 3997), the MAC was learned in 3997, and ICMP 3/3. The mirror step was skipped: no capture point, and eth1 is the observer |

## 2026-09-30 run (queue row 13: T27887, T38410)
Baseline `pre-test-configs/2026-09-30/` (12:50, includes the x230's `lldp run` and the SX link's VLAN 4000). Scratch in tb470 `/tmp/ckvlan30/`. No group isolation was needed. Each case builds and removes its own config. Group close 13:13–13:14: running-config IDENTICAL to that baseline on u0/u1/u3/u5 (`post-test-configs/2026-09-30/`), boot config tb470-bench.cfg on all, probe 2026-09-30T001356Z MATCH.

## 2026-09-30 resume (queue row 7: T38408, T38407, T18302, T18303)
Scratch in tb470 `/tmp/ckvlan3/` (console transcripts `console-u{0,3,5}.log`). Pre-group capture
`pre-test-configs/2026-09-30b/` (16:16, IDENTICAL to the 12:50 baseline). Probe 2026-09-30T031557Z MATCH.
Group setup 16:19–16:21 = the 14:27 recipe below **plus two observer trunks**, so every freed leg can be
seen or driven from a tb470 NIC by its scratch-VLAN tag (`evidence/group-2026-09-30/group-setup.sh`, `.out`):
- x230 port1.0.1 (eth3): `switchport mode trunk`, `trunk native vlan 100` (its baseline access VLAN),
  `trunk allowed vlan add 3991,3992` → DUT port1.0.2 appears at eth3 as tag 3991, DUT port1.0.9 as 3992.
- SA port1.0.2 (eth2): `switchport mode trunk` (native 1 = baseline), `trunk allowed vlan add 3993,3994`
  → DUT port1.0.13 appears at eth2 as tag 3993, DUT port4.0.9 as 3994.
The group-setup reference config (what each case's teardown must return to) is
`post-test-configs/2026-09-30b/38408.u{5,3,0}.out`. Its diff against the pre-group capture is exactly the lines above.

## Group setup (14:27–14:31) — redo before the next case
The 2-leg aggregators sa2 (stack ↔ x230) and sa3 (stack ↔ SA) were freed into scratch VLANs, so that each
leg is a separate observable path (STP is off everywhere; VLAN isolation prevents loops):
- stack (u5): VLANs 3991–3994. Each leg was shut, then `no static-channel-group` and access vlan:
  port1.0.2→3991, port1.0.9→3992, port1.0.13→3993, port4.0.9→3994, then `no shutdown`.
  `interface sa2-3` auto-deletes. Evidence: `evidence/setup-u5-step1.out`, `setup-u5-step3.out`.
- x230 (u0): VLANs 3991, 3992; port1.0.3→3991, port1.0.4→3992, both out of sa2 (`sa2` auto-deletes).
  Evidence: `evidence/setup-u0-step2.out`.
- IE520-sa (u3): VLANs 3993, 3994; port1.0.13→3993, port1.0.9→3994, both out of sa3 (`sa3` auto-deletes).
  Evidence: `evidence/setup-u3-step2.out`.
vlan 10 / sa1 (the AR4050S transit) is never touched.

## Group restore (17:14:09–17:16:13) — done once, after T38409
Evidence: `evidence/group-restore.sh` and `group-restore.out`, no `% ` line.
- stack: shut the four legs; on each, `no switchport access vlan` then `static-channel-group 2`
  (1.0.2, 1.0.9) or `3` (1.0.13, 4.0.9); `no vlan 3991-3994`. `show static-channel-group` read sa1/sa2/sa3
  with their pre-test members, and `interface sa2-3` read `switchport` / `switchport mode access`.
- x230: port1.0.3 and port1.0.4 → `switchport access vlan 100` then `static-channel-group 2`;
  `no vlan 3991-3992`. `interface sa2` read access vlan 100.
- SA: port1.0.13 and port1.0.9 → `no switchport access vlan` then `static-channel-group 3`; `no vlan 3993-3994`.
- stack legs `no shutdown`. At 17:16:08 all four read connected a-full a-1000 in VLAN 1.

## Verification (17:16–17:18)
- `show running-config` on u5, u3, u0 and u1, captured after the restore, is **IDENTICAL** to
  `pre-test-configs/` (the 14:22–14:23 capture) on all four.
- `show boot`: Current boot config `flash:/tb470-bench.cfg (file exists)` on u5, u3, u0 and u1.
- `bench_probe.py run` at 2026-09-29T041748Z (17:17:48 NZDT) gave **MISMATCH (1)**, and that one is only
  the pending SX link: `[portlink] swi_b-swi_d`, bench `{port1.0.26-port4.0.26, port1.0.9-port4.0.9}`
  vs template `port1.0.9-port4.0.9`. Terrence's apply is still pending and was NOT applied.
  bench-state.md was regenerated.
- Consoles free afterwards (`fuser -v /dev/u*` empty).

## What is in this directory
- `<id>[-verdict].log`: one log per case, latest run, the name is the verdict (STANDING-ORDERS §2).
- `pre-test-configs/u0,u1,u3,u5.show_running-config.txt`: the group baseline, 14:22–14:23.
- `post-test-configs/<id>.uN.show_running-config.txt`: running configs after each case's teardown.
  They equal the group-setup state, not the baseline, because the group isolation stays in place between
  cases (STANDING-ORDERS §6).
- `evidence/`: per-case driver scripts (`.sh`), their stdout (`.out`), pcaps, and the group
  setup/restore transcripts.
