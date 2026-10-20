---
name: tb101-ie520-bench-map
description: "tb101 (2026-10-20) = the four ex-tb470 IE520s as ONE 4-member stack `IE520`, members 1-4 = consoles u0-u3 (S/N 061/068/052/066 = swi_a/b/d/c), chassis-id 3439, eth4->port1.0.1, eth3->port2.0.1, eth2->port3.0.1, IXIA on port3.0.25 (vlan3) + port4.0.25 (vlan2); no PDU; python3.8 (tools/tb picks it); /nfsHome unmounted so the deployed .setup is /home/st-art/configs/tb101.setup; `apply` is hard-denied for sessions"
metadata:
  node_type: memory
  type: project
  originSessionId: 9343853c-0e7c-43fe-90a6-7f5840c4f716
  modified: 2026-10-20T03:06:19.735Z
---

**Measured 2026-10-20 on tb101** (re-verify: consoles and cables rot). Full record:
`tb101/SESSION-HANDOVER-2026-10-20.md`; generated state `bench-setup/tb101/bench-state.md`.

| member | console | S/N | name | host NIC ↔ port | notes |
| --- | --- | --- | --- | --- | --- |
| 1 | u0 | 264A23061 | swi_a | eth4 10.37.101.65/27 ↔ port1.0.1 | `stack 1 priority 1` (my addition, wins next election) |
| 2 | u1 | 264A23068 | swi_b | eth3 10.37.101.33/27 ↔ port2.0.1 | |
| 3 | u2 | 264A23052 | swi_d | eth2 10.37.101.1/27 ↔ port3.0.1 | IXIA TOP port3.0.25 vlan3 3.3.3.3/24 |
| 4 | u3 | 264A23066 | swi_c | — | IXIA BOTTOM port4.0.25 vlan2 2.2.2.2/24; master after the 10-20 reload |

- Hostname `IE520`, chassis-id 3439, VMAC 0000.cd37.0d6f, build `awplus_main-20261019-75`, bootloader 9.2.0,
  boot config `flash:/tb101-bench.cfg` (vlan1 = .10/27 + .40/27 + .70/27 secondaries so every host NIC pings).
- All consoles 115200. `tools/tb` runs `python3.8` here by itself since 2026-10-21 (python3 is 3.6.9; bench_probe.py needs 3.7+). No PDU: `tb101.static` has no
  `[pdu]` and every outlet `-`.
- **Probe path:** `/home/st-art/st-art -> /nfsHome/st-art` dangles (no fstab entry); tb101 mounts the same
  `10.36.250.11:/home` share at `/home`, so `bench_probe.py remote_path()` (added 2026-10-20) uses
  `/home/st-art/configs/tb101.setup`. `precheck` reports FOUND for the `ser2net` daemon (holds no `/dev/u*`).
- **`bench_probe.py apply` is HARD-DENIED for Claude sessions** by the auto-mode settings even when Terrence asks
  for it in chat (2026-10-20): hand him the command (`python3 bench-setup/bench_probe.py --box tb101 apply`)
  in the handover, as [[tb470-root-changes-go-through-terrence]] does for root changes.
- **Merging live units into a stack by cabling** (what happened 2026-10-20 while I waited for an ID decision):
  two masters merge, the surviving master's config applies, IDs are reassigned on collision, NSM logs "audit
  inconsistencies — member N should reboot" and forwarding is unreliable (`% Network is unreachable` for a TFTP
  that pinged) until a whole-stack reload. Every console then reaches ONE master, so per-unit commands land on
  the merged stack. Renumber (`stack N renumber M`, pending until reboot) and set chassis-id BEFORE cabling.
- `/tftproot` here is tmpfs (fstab) but survived the 10-19 reboot's listing — Terrence's images live there.

Related: [[ie520-image-update-procedure]], [[shared-testbox-console-occupancy]], [[bench-probe-one-tool]].
