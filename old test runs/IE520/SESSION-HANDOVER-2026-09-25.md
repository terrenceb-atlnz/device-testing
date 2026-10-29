# Session handover — 2026-09-25 (wrapped ~13:10 NZST)

## TL;DR

- **The bench is whole and unchanged in topology.** Stack 1/3/4 `Normal operation`, member 3
  Active Master; every device boots `flash:/tb470-bench.cfg` (Terrence's restored 16:58
  09-24 config, done by the Ask-CK session at ~10:40). `bench_probe.py run` read **MATCH**
  against the deployed `.setup` at 10:55. Nothing of mine is running-only or unrecovered.
- **Parallel work in flight at wrap:** the Ask-CK session (test-cases-2d) is restoring
  licences (the ART run at 07:50 stripped `NZ`/`FULL` from the IE520s, `FULL` from the 4050 and
  `access` from the x230). It held u1 and u3 at 12:58. That is theirs; do not touch licences.
- **New tool:** `bench-setup/bench_probe.py` is now THE bench-state tool (capture → generated
  bench-state.md → diff → apply). `bench_setup.py` and `bench_topology.py` are gone.
  bench-state.md is generated and carries no prose; hand facts live in `tb470.static`.
- **Corosync DLF bug: NOT REPRODUCED** in three line-rate runs (master ingress, non-master
  ingress via sa3, both at once). Logs in `IE520/corosync-dlf-2026-09-25/`.
- **New agent:** `.claude/agents/bench-runner.agent.md`, symlinked from Test-cases; Ask-CK's
  agent was renamed `test-composer` (Terrence) and hands every tb470 run to it.
- Commits: `e3598fa`, `5bef00c`, `aa6d3a7`, `262a730`, `37dc4f8`, `97e6823` + this wrap —
  **committed, NOT pushed**. Test-cases `a6aeb1f` (the bench_probe.md pointer only).

## 1. Bench state and how to verify it

Topology: [bench-setup/bench-state.md](../bench-setup/bench-state.md) (generated
2026-09-24T225534Z = 10:55 NZST; MATCH). Read at 12:57 UTC-on-device 00:57:

```
show stack        1/3/4 Ready, member 3 Active Master, Normal operation, Stack MAC 0000.cd37.0d6f
show boot         Current boot image flash:/IE520-tb470.rel (file exists); Current boot config flash:/tb470-bench.cfg (file exists)
reboot history    new since 09-24 evening, ALL members: 2026-09-24 21:20:35 and 22:34:52 Expected User Request
                  (= Terrence's ART run 33235 and the config restore). No Unexpected entries today.
running-config    `lldp run` present on the stack (baseline). No storm-control, no terminal monitor.
host              eth1/eth2/eth3 carrier 1; 10.38.215.1/.33/.65 /27; /nfsHome mounted; no ethtool changes.
builds            stack + IE520-sa awplus_main-20260923-20; 4050 awplus_main-20260924-26 (Terrence loaded it
                  today and pointed the boot image at the new AR4050S-tb470.rel); x230 awplus_5.5.5_2-20260918-7.
```

Verify next time (ON tb470, ~2 min; wait until nobody holds a console — `sudo -n fuser -v /dev/u*`):

```bash
cd ~/claude/device-testing/bench-setup && ./bench_probe.py run      # expect MATCH
```

**Skipped at this wrap (Terrence):** the wrap-time probe re-run, because the licence restore
held two consoles. A rejected call had already run once at 12:57 (capture
`captures/2026-09-25T005755Z/`): it correctly reported u1 and u3 CONSOLE_BUSY → NEEDS-CHECK,
and toggled `lldp run` on the x230 (off → on → off, running-config only). Its partial
bench-state.md was discarded (`git checkout`); the 10:55 one stands.

## 2. What was accomplished

1. **bench_probe.py consolidation** (Terrence's design: "see what's actually THERE" with a
   short list of `show` commands, parse offline, generate bench-state.md in `.setup` format,
   diff). Decisions recorded in memory `bench-probe-one-tool` and plan item E-11 of
   `CAMPAIGN-QUEUE-2026-09-24.md`. First live run 1 m 56 s, six consoles, MATCH.
2. **Docs sweep** for the retired scripts: orient-dt (§0 table, §1, §3; snapshot
   `SKILL.md.pre-20260925`), wrap-dt (§4 procedure, §6, §7; snapshot), TESTBOX-ACCESS.md,
   test-harness README, memories (routing, nfshome, console-access, no-stray-scripts), the
   Test-cases pointer `ask-ck/functions/test-composer/bench_probe.md`.
3. **Corosync DLF test** — three runs, all clean (see §3).
4. **bench-runner agent** agreed with the Ask-CK session and built; `genpop` → `test-composer`.
5. **`IE520/tools/linerate.py`**: standalone scapy + tcpreplay + tcpdump sender/counter; the
   DLF drivers and their console helpers archived under `IE520/corosync-dlf-2026-09-25/driver/`.

## 3. Results

| run | shape | result | clean? |
| --- | --- | --- | --- |
| warm-up 1 | known-unicast 100 / 500 / line rate from eth3, then 10 s DLF at line rate into the master (port3.0.9) | flooded 100% to eth1 and eth2 (via sa3); CPU rx ~1.1k; no corosync line | clean (wrapper timeout cut only the driver's final log dump; device log covers it) |
| run 2 | 10 s DLF from eth2 → IE520-sa → sa3 → members 1/4 | flooded 100% to eth1 and eth3; CPU ~1k/member; nothing logged | clean |
| run 3 | eth3 (master) + eth2 (sa3) at once | eth1's 1G egress saturated (387k+436k), cross paths 100%; CPU ~1.3k/member; one dhclient console line | clean |

tcpreplay: 984 Mbps of frame bytes with 1500-byte frames = 1G line rate; 957 Mbps on the
second concurrent sender (host limit). Full detail: `IE520/corosync-dlf-2026-09-25/*.log`.

## 4. Findings

Measured:
- `bench_probe.py`'s 9600-baud path reads the x230 cleanly (the old "garbage at all bauds"
  defect is gone: NULs stripped, two attempts per baud, longer quiet at 9600).
- The stack's `show system` lists a "Stack member N" block per member with model, serial and
  bootloader — no zip-by-order needed.
- AW+ `show lldp neighbors` prints local ports without the `port` prefix and leaves Sys Name
  blank on this build; identifying neighbours by chassis MAC against each device's CPU MAC
  entries works for all four devices.
- Rejected tool calls still run on tb470 (twice today: the `no shutdown` map script, and the
  wrap-time probe). Memory `rejected-tool-calls-keep-running-remotely` stands.

Inferred:
- The corosync symptom is not triggered by 1G software DLF on this build; the bug report's
  Ixia repro may need 10G ingress or a direct member NIC (cause NOT established).

## 5. OPEN

- **Apply the generated `.setup`?** Sections are identical to the deployed file; only the
  hand-written `###` header would go. Terrence's call (bookmarked in plan E-11).
- **Licences** — in progress by the Ask-CK session; the x230's `ACCESS` retry waits for
  Terrence (a key leaked once through a wrapped console echo; see bench-runner's secret rule).
- **PDU 10.36.150.14 unreachable from tb470** all day (Ask-CK session's finding): any
  `powerlink` test hits the framework's silent-False path.
- **Ask-CK's server run path (`pt_exec.py`) launches without `--noupdate --nodefaultcfg`** —
  backend change, raised with Terrence; bench-runner refuses that path meanwhile.
- **Two small relocations not done** (the call was rejected with the probe run): the 4050
  boot-pointer decision ("leave it", Terrence 09-24) into memory
  `tb470-bench-structural-limits`, and the 2026-09-23 TFTP-write timing observation (206–268 s,
  +0 bytes) as a dated note on orient-dt §2's SPIFlash row.
- Direct member-1 ingress for the DLF test awaits Terrence's recable (an eth port to member 1
  replacing the x230 link); then repeat run 3.

## 6. Next steps, in order

1. `bench_probe.py run` once the licence restore is finished → MATCH; read Advisories.
2. Decide E-11's `apply`.
3. The two relocations above (5 minutes).
4. After the recable: rerun DLF run 3 with `driver/tdlf2.py` (edit the sender map) or
   `IE520/tools/linerate.py` ×2.

## 7. Recipes

Line-rate DLF, one command (on tb470, root):
```bash
sudo python3 ~/claude/device-testing/IE520/tools/linerate.py --tx eth3 --dst-mac 02:00:00:00:99:99 --rate top --rx eth1,eth2
```
The console half (terminal monitor + sdma counters) and the exact invocation of today's
drivers: `IE520/corosync-dlf-2026-09-25/driver/README.md`.

Config diff against a recorded .cfg after any probe run:
```bash
diff bench-setup/captures/<stamp>/u5.show_running-config.txt <your.cfg>
```

## 8. Pointers

- Tool memory: `.claude/memory/bench-probe-one-tool.md`; routing memory updated.
- Agent: `.claude/agents/bench-runner.agent.md` (Test-cases symlinks to it; one writer per repo).
- Plan: `IE520/CAMPAIGN-QUEUE-2026-09-24.md` §E item 11 (built) and I-10 (resolved).
