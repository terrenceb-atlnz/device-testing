# Session handover — 2026-10-20 (12:50–16:10 NZDT): tb101 IE520s updated to awplus_main-20261019-75, re-formed as one 4-member stack, clean bench config, probe run; `apply` is yours

Session `9343853c…` (VS Code), Test Engineer terrenceb@terrenceb-dl. No test case ran, no sentinel.

## Session facts
Testbox: tb101 · Consoles: u0–u3 (all 115200) · PDU: **none** · Build source: `/tftproot/IE520-tb101.rel`
(`.info` = `IE520-awplus_main-20261019-75.rel`, 40,347,063 B, sha256 matched its `.sha256sum`).

The Test Engineer's direction, verbatim:
- *"update the devices to the latest .rel on the testbox … copy the .rel to the devices' flash, reboot them,
  change the default flash .rel to the newest one, and then bring the device online and delete the old .rel from
  flash. If there's currently an old .rel on the flash, delete that first."*
- *"im going to go connect them together in a four stack, after that's done they will need a reconfiguration and
  then we can run the bench probe and apply the results"*
- *"Renumber them top to bottom, member 1,2,3,4 = u0,1,2,3 … use the bench probe after the renumber and make sure
  that the ports connected to nics are in the correct subnets, remove any other config except for the IXIA ports on
  u2 port 25 and u3 port 25 … theres No Pdu. Names are fine."*
- *"please sort out as much as possible and then apply the new .setup, ill have to pick this up later"*

## TL;DR — what you need to do

1. **Run the apply yourself** (it is hard-denied for Claude sessions by `.claude/ask-ck-campaign.settings.json` /
   STANDING-ORDERS §4, even with your consent). From the dev host, in this repo:
   ```bash
   python3 bench-setup/bench_probe.py --box tb101 apply
   tools/tb probe tb101 --consoles 0-3 --baud 115200 --no-prompt      # expect MATCH (tools/tb uses python3.8 on tb101 since 2026-10-21; before that: TB_PY=python3.8)
   ```
   `bench_probe.py` now writes `/home/st-art/configs/tb101.setup` on tb101 (see "probe path" below) because
   `/home/st-art/st-art -> /nfsHome/st-art` dangles there.
2. **One stack link is down:** `port4.0.28` reads `Down`, `port1.0.27` reads `Discovering neighbor`; the other
   seven stackports are up, so the stack is a chain 1–2–3–4, not a ring (`Operational Status: Not all stack
   ports are up`). Both ends of that cable are `1xCOPPER PAS` DACs on tb470's old pairing. Reseat or swap it.
3. **Optional, root:** `/nfsHome` has no fstab entry on tb101 (`mount: /nfsHome: can't find in /etc/fstab`).
   tb470's line is `10.36.250.11:/home /nfsHome nfs4 rw,vers=4.2,rsize=524288,wsize=524288,hard,proto=tcp 0 0`.
   tb101 already mounts that same share at `/home`, so `/home/st-art/configs` IS the directory the symlink
   would reach; the fallback above makes the mount unnecessary for the probe.

## Bench state left (16:04 NZDT)

Measured: [bench-setup/tb101/bench-state.md](../bench-setup/tb101/bench-state.md) (capture `2026-10-20T030414Z`).

| member | console | S/N | name | role | host NIC | notes |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | u0 | 264A23061 | swi_a | Backup, **priority 1** | eth4 10.37.101.65/27 ↔ port1.0.1 | wins the NEXT election (no pre-emption) |
| 2 | u1 | 264A23068 | swi_b | Backup | eth3 10.37.101.33/27 ↔ port2.0.1 | |
| 3 | u2 | 264A23052 | swi_d | Backup | eth2 10.37.101.1/27 ↔ port3.0.1 | IXIA TOP on port3.0.25 → VLAN 3, 3.3.3.3/24 |
| 4 | u3 | 264A23066 | swi_c | **Active Master** | — | IXIA BOTTOM on port4.0.25 → VLAN 2, 2.2.2.2/24; port4.0.26 (copper SFP) is `connected` in vlan1 — unknown peer |

- Hostname `IE520`, chassis-id **3439**, virtual MAC **0000.cd37.0d6f** (was 0000.cd37.0a66 before the
  re-form: IXIA must re-resolve both gateways). All four run `awplus_main-20261019-75` from flash, bootloader
  9.2.0, each bootloader forced to `IE520-awplus_main-20261019-75.rel` (Boot Menu 2→1→file).
- **Boot config `flash:/tb101-bench.cfg`** on every member (synced). It is the running config, saved in place: `username
  manager`, `no banner motd`, `stack virtual-mac`, `stack virtual-chassis-id 3439`, `stack 1 priority 1`, `lldp run`,
  `switch 1-4 provision ie520-28`, `no spanning-tree rstp enable`, `no lacp global-passive-mode enable`, VLANs 1/2/3
  only, every port `switchport mode access` in vlan1 except the two IXIA ports, stackports 27/28 on all four,
  `interface vlan1` = 10.37.101.10/27 + .40/27 secondary + .70/27 secondary, vlan2 2.2.2.2/24, vlan3 3.3.3.3/24,
  `line con 0 exec-timeout 0 0`. Verified: all three host NICs ping their vlan1 address (3/3 each); vlan2 and vlan3
  `running`; no static-channel-groups left.
  - `stack 1 priority 1` is MY addition (so u0 = member 1 becomes master at the next reload, "easier to
    troubleshoot"). Remove it if unwanted: `no stack 1 priority`, `write`.
  - `security-password minimum-length 8` / `history 1` and `snmp-server` are the build's own rendering, left alone.
- **Flash leftovers** (not deleted — only old `.rel` files were in scope): on member 4 `coro-repro.cfg`,
  `tb101-prep.cfg`, `stephenh.cfg`, `tb470-bench.cfg`, `tb470-oldstack.cfg`, `u2-standalone.cfg`, two
  `debug-duplicate-master-…tgz` + `exception.log` from the merge at 14:58/15:03; member 3 also `tech-support*.gz`;
  members 1/2 the old tb470 `.cfg` files. `tb101-prep.cfg` was my interim save (chassis-id change) — safe to delete.
- **tb101 host:** `/tftproot/tb101-bench.cfg` (my clean config, 1,413 B) left beside your images; `/tmp/relup/` (tmpfs)
  holds every console transcript. `ser2net` runs on the box and makes `bench_probe.py precheck` report FOUND; fuser
  showed it holding no `/dev/u*`, so the probe went ahead.

## What was done, in order
1. **Image update** (12:50–13:18): consoles identified (u0 `IE520-stk`, u1 `IE520-sa`, u2/u3 the 2-member stack
   `IE520`), host-NIC mapping by MAC learning, TFTP of the new image to each unit (211–213 s each), `boot system`,
   `bootmenu_park --reload` / `reload stack-member`, `bootmenu_escape`, verify, delete old `.rel`s. On u0 the old
   `IE520-tb470.rel` had to go FIRST (27 MB free) after `no boot system backup` + `boot system` to the running file.
2. **Re-form as a 4-stack** (15:40–16:00): you cabled the stackports while I was waiting for your ID choice, and the
   four units merged on their own (two masters merged; NSM logged "audit inconsistencies — member should reboot";
   forwarding was unreliable until the reload: `% Network is unreachable` for a 1.4 KB TFTP). All consoles then
   reached one master, so my per-unit renumbers landed on the merged stack; corrected to 1=061, 2=068, 3=052,
   4=066 (`stack N renumber M`, pending until reboot), `stack virtual-chassis-id 3439`, `no stack 2 priority`,
   saved as `tb101-prep.cfg` (not over `coro-repro.cfg`), one whole-stack `reload` (login after ~3.5 min).
3. **Clean config in place** (16:03): `no static-channel-group` on port1.0.1-2/2.0.1-2, access VLANs cleared,
   `no vlan 100/200/1000`, `no alarm facility vcs-member-output-control` (that also erased the power-supply alarm line),
   IXIA ports to VLANs 3/2, vlan1 addresses, `lldp run`, `stack 1 priority 1`; `copy running-config
   flash:/tb101-bench.cfg`; `boot config-file flash:/tb101-bench.cfg`. No second reload.
4. **Probe** `2026-10-20T030414Z` on u0–u3: four devices, three NIC links proven by MAC learning, no advisories;
   `bench-setup/tb101/tb101.static` created (4 serials, names as on tb470, no PDU). `apply`: denied for me (above).

## Repo changes (this commit)
- `bench-setup/bench_probe.py`: `remote_path()` — when `/home/st-art/st-art/configs` is missing on the box but
  `/home/st-art/configs` exists, the deployed `.setup` lives there (prints a `note:`); used by `live_setup`,
  `write_setup`, `on_box`, `default_template`.
- `bench-setup/tb101/tb101.static`, `bench-setup/tb101/bench-state.md` (generated), this handover.
- Memory: `tb101-ie520-bench-map` (new), `ie520-image-update-procedure` (tb101 run notes).
- NOT touched: `bench-setup/bench-state.md` (tb470) was already modified before this session — left unstaged.

## Open
1. `apply` + MATCH probe (you).
2. Stack link port4.0.28 ↔ port1.0.27 down (cable).
3. Decide on `stack 1 priority 1`; the master only changes at the next reload.
4. `port4.0.26` copper SFP `connected` in vlan1 on member 4: what is on the other end? (not in the probe's links: no
   LLDP neighbour, no host MAC).
5. Flash housekeeping (old `.cfg`, debug tarballs) if wanted.
