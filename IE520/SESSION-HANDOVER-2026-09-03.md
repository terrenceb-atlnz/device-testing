# IE520 bench — session handover, 2026-09-03

For the next session. Start with `/orient-ie520`; the bench source of truth is
`claude/IE520-testing/bench-setup/bench-state.md` (rebuilt this session).

## Bench state right now (clean, leave-as-is)
Flat single-vlan1 `.64/27` loop-free TREE, IE520 stack as hub, all links LLDP/host-confirmed:
```
tb470 eth3 ── IE520 port1.0.1 (mem1/swi_b)          IE520 stack "awplus"  vlan1 .66 static
                 ├─ port2.0.1 ── 4050 port1.0.3     AR4050S  vlan1 .70 static
                 └─ port2.0.9 ── x230 port1.0.4      x230-10GP vlan1 .71 static
admin-shut: 4050 port1.0.2 <-> x230 port1.0.2 (kept the triangle a tree; do not un-shut
            without RSTP active on all three — it is)
loopbacks:  IE520 port2.0.6/2.0.8/2.0.14/2.0.16 (SFP loopback plugs, RSTP-contained)
```
- RSTP enabled on all three. tb470 reaches `.66/.70/.71`. `.setup` regenerated + verified.
- **4050/x230 are STATIC** (not DHCP). Their AW+ DHCP clients wedged under the DoS port
  flaps, so we pinned them static (Terrence's call). `.70/.71` sit inside tb470's dhcpd pool
  `.68-.94` but nothing else DHCPs here, so no conflict — exclude them if that changes.
- LLDP was turned on for swi_c/swi_d this session (harmless, running-config only).

## What shipped this session (all logs under old test runs/IE520/)
- **switchports/** — MAC/Phy TLV autoneg (T9554-9559, T9709). FINDING: the cases' expected
  "Auto-neg Supported/Disabled" is a copy-paste error; auto-neg only reads Disabled when BOTH
  speed AND duplex are forced. See 9554.log + autoneg-mac-phy-clarification.txt.
- **dhcp-snooping/5897.log** — DHCP Snooping Database entries. PASS, all 3 steps, with a REAL
  downstream binding (x230 client on untrusted port2.0.9, tb470 as server). Key point: the
  switch's own SVI client leases but never binds; a downstream host on an untrusted access
  port is required.
- **dos/** — DoS suite T5437-T5442. See dos/DOS-METHOD.md first.
    teardrop, land, ping-of-death, smurf, synflood = PASS.
    **ipoptions (T5437) = N/A on this bench** — IP options are parsed only on the L3/routed
    path; the flat-L2 bench bridges them without inspection, so it never fires (proven: valid
    LSRR/RR options on the wire at rate, 0 detected). Needs a routed topology to exercise.

## The DoS tool (version-tracked)
`claude/Test-cases/ask-ck/test-composer/dos_campaign.py` — one file: build-up → all six cases
→ teardown in a `finally`. Run AS ROOT on tb470:
`ssh tb470 'cd /tmp/lldp && sudo -n PYTHONPATH=/home/st-art python3 dos_campaign.py [case ...]'`
Encoded lessons (also in the ie520-dos-test-method memory):
  1. attacks must TRANSIT the switch (dst = host behind it), NOT the switch's own MAC (CPU-punt
     bypasses the DoS ASIC → 0 detections);
  2. senders must be BATCHED — single-packet sendp(loop=1) is too slow for the rate threshold;
  3. disarm is `no dos <type>` (smurf: `no dos smurf`), NOT `... action shutdown`;
  4. poll the port back to `connected` before firing (err-disable recovery isn't instant) —
     the tool does this (`wait_connected` + one retry).

## Open items / next steps
- **T5437 IP OPTIONS** — the only DoS case not exercised. To do it: give the IE520 a routed
  path (ingress vlan1 → route to a 2nd vlan/subnet with the x230 re-addressed onto it), fire
  option-bearing packets so they're ROUTED and their options parsed. This mutates the clean
  flat-vlan1 bench, so it needs a deliberate setup (and teardown back to flat vlan1 after).
- **Silent-reboot weekend run** — still parked. See the ie520-silent-reboot-watch-2026-09-02
  memory: evidence survived, but the watcher script has 3 harness defects to fix first
  (65-min detection lag, both consoles relayed to master, tcpdump on wrong eth).
- **tftproot version mismatch** — 09-03 build in /tftproot vs 08-30 running; decision still
  open (from an earlier session).
- **Cleanup** — tb470:/tmp/lldp holds one-off drivers (apply_dev.py, fastdos.py, dos_suite2.py,
  the *_seq.py scripts) now superseded by dos_campaign.py; deletable.

## Suspect hardware reminder
IE520 stack member 1 (S/N 264A23066, = swi_b, /dev/u5) is suspect hardware with its own reboot
history — check `show reboot history` before calling any stack event a defect. See bench-state.md
§1 trap 3.
