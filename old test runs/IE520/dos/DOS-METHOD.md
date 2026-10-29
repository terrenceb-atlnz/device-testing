# DoS test method — tb470 IE520 bench (2026-09-03)

Shared setup and hard-won gotchas for the AWPTCM DoS suite (T5437–T5442). Read this before
re-running any of the per-case logs in this directory.

## Topology / roles
- DUT / detector : IE520 stack, DoS armed on **port1.0.1** (`dos <type> action shutdown`).
- Attack source  : **tb470 eth3**, cabled directly to IE520 port1.0.1 (LLDP/host-confirmed,
  see bench-state.md 2026-09-03). scapy 2.6.1, root.
- Transit victim : **x230** `10.38.215.71` / `00:1a:eb:91:cc:a1` (a host BEHIND the switch).
- Original suite assumes `[IXIA]==(port1.0.1)[DUT](port1.0.2)==[IXIA]`; the IXIA is replaced
  by tb470 + the lab scapy tools in raw-data/test_scripts/tools/denial_of_service/.

## THREE gotchas that cost real time

1. **Send TRANSIT traffic, not to-the-switch.** Frames addressed to the IE520's own MAC
   (`00:00:cd:37:0d:6f`) are punted to the CPU and BYPASS the ingress DoS ASIC — 0 detections.
   Aim at a host BEHIND the switch (x230) so the fragments/packets transit port1.0.1.

2. **Rate: the single-packet lab tools are too SLOW.** `sendp(pkt, loop=1)` on ONE packet does
   not cross the DoS rate threshold (measured ~nothing). The detection is rate-based. Fix: send
   a BATCH — `sendp([pkt]*3000, loop=1)`. teardrop.py works out-of-the-box ONLY because it
   happens to send a 12-packet LIST. Use `fastdos.py <type> eth3` (staged tb470:/tmp/lldp),
   which sends the same packets as the lab tools but batched.

3. **Disarm is `no dos <type>`** — NOT `no dos <type> action shutdown` (that is accepted but
   leaves detection ENABLED; the port shuts again). For smurf it is `no dos smurf` (drop the
   `broadcast A.B.C.D` too). Recover an err-disabled port with `no shutdown`.

## PASS criterion
Armed + attack → port1.0.1 goes **err-disable** (`show dos interface` Attacks detected > 0,
Port status Disabled). Disarmed + same attack → port stays **connected**. Both required.

## Result summary (2026-09-03)
| Case  | Type          | Armed → attack           | Disarmed → attack | Verdict |
|-------|---------------|--------------------------|-------------------|---------|
| T5442 | teardrop      | err-disable (2585)       | stays up          | PASS |
| T5438 | land          | err-disable (108)        | stays up          | PASS |
| T5439 | ping-of-death | err-disable (2977)       | stays up          | PASS |
| T5440 | smurf         | err-disable (detected)   | stays up          | PASS |
| T5441 | synflood      | err-disable (detected)   | stays up          | PASS |
| T5437 | ipoptions     | NOT detected (any path)  | stays up          | FAIL — armed but 0 detections on bridged AND routed paths (2026-09-28); candidate product defect. See 5437.log |

**IP OPTIONS — RESOLVED 2026-09-28: FAIL, candidate product defect.** `dos ipoptions` on the
IE520 (awplus_main-20260923-20) is accepted and shows Enabled, but never counts or shuts the port.
Verified on BOTH a bridged path (access vlan1, dst = a host behind the switch) AND a genuinely
routed path (scratch vlan90 SVI, dst = stack router MAC, dst IP in another subnet — the DUT
L3-routes and parses the options), with Record-Route AND the illegal LSRR option, wire-verified
(ihl 6/7), valid unicast source MAC, ~3200 pps (threshold is 20 pps). Attacks detected stayed 0
every time; the port never err-disabled.

This overturns the earlier readings. The 2026-09-03 'needs L3 routed path' theory is DISPROVEN
(the routed path also fails). The 2026-09-04 illegal-MAC bug (source MAC 01:00:01:00:00:01, from
`dos_campaign.py`'s `b_ipoptions`, dropped before counting) was real but not the whole story.
The other five DoS types fire on this same bench, so the DoS engine and the transit method work
on the IE520 — ipoptions specifically is a no-op. Arming works on a master-member port; the old
port1.0.1 'Cannot update hardware filter' was member-1-specific. One caveat: no cross-platform
control was run (no host NIC lands directly on the wiki-listed x230/4050), so confirm on a
**Cross-platform control done 2026-09-28 (caveat resolved).** eth3 recabled to reference
platforms: the AR4050S build (arc-awplus_main-20260924-26) has NO `dos` switchport feature at all
(`dos ?`/`show dos` unrecognized) — not a usable control. The x230-10GP (which HAS the feature)
DID detect: armed `dos ipoptions` on port1.0.1, fired the same Record-Route frames from eth3 ->
Attacks detected : 1, port err-disable, immediately. So the IE520's 0-detections is a genuine
IE520-specific defect, safe to file. Full method + evidence: 5437.log.

## The tool (version-tracked)
`claude/Test-cases/ask-ck/test-composer/dos_campaign.py` — the whole suite in one file:
builds up the scenario, runs all six cases (arm → batched transit fire → verify err-disable →
recover → disarm → negative re-fire), and tears down to baseline in a `finally`. Run AS ROOT on
tb470 so scapy and the framework console share one process:
```
scp .../dos_campaign.py tb470:/tmp/lldp/ ; ssh tb470 \
  'cd /tmp/lldp && sudo -n PYTHONPATH=/home/st-art python3 dos_campaign.py [case ...]'
```
Optional argv filters to a subset (e.g. `dos_campaign.py land teardrop`). It polls the port
back to `connected` before every attack (`wait_connected`) + retries once, so timing flakes
don't produce false FAILs. Verified end-to-end 2026-09-03: land/pod/smurf/synflood/teardrop
PASS, ipoptions N/A.
(The earlier one-off drivers `fastdos.py` / `dos_suite2.py` under tb470:/tmp/lldp are
superseded by this and can be deleted.)
