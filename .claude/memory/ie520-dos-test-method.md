---
name: ie520-dos-test-method
description: How to run the AWPTCM DoS suite (T5437-5442) on the tb470 IE520 bench — transit traffic, batched senders, disarm syntax; ipoptions RESOLVED 2026-09-28 = FAIL, CONFIRMED IE520 defect (x230 detects same stimulus; 4050 lacks the feature)
metadata:
  type: reference
---

`claude/device-testing/IE520/dos/DOS-METHOD.md` is the full method + per-case logs (5437-5442),
produced 2026-09-03. Attack source = tb470 eth3 (scapy tools in
`raw-data/test_scripts/tools/denial_of_service/`), DUT = IE520 port1.0.1, transit victim = x230.

Four non-obvious points that each cost a failed attempt:

1. **Send TRANSIT traffic** — dst = a host BEHIND the switch (x230 `10.38.215.71` /
   `00:1a:eb:91:cc:a1`), NOT the switch's own MAC. Frames to the switch's own MAC are
   CPU-punted and bypass the ingress DoS ASIC → 0 detections.
2. **Batch the sends** — the stock tools' single-packet `sendp(pkt, loop=1)` is too slow to
   cross the DoS rate threshold. Use a looped/repeated batch (`sendp([pkt]*2000)`). teardrop.py
   works out-of-the-box ONLY because it happens to send a 12-packet list.

The whole suite is now one version-tracked tool:
`claude/Test-cases/ask-ck/test-composer/dos_campaign.py` — build-up → all six cases → teardown
in a `finally`; run AS ROOT on tb470 (`sudo -n PYTHONPATH=/home/st-art python3 dos_campaign.py
[case ...]`). It polls the port back to `connected` before each attack + retries once, so it is
robust to the err-disable-recovery timing flake.
3. **Disarm is `no dos <type>`** (for smurf `no dos smurf`, dropping the `broadcast A.B.C.D`),
   NOT `no dos <type> action shutdown` — the latter is accepted but leaves detection enabled.
   Recover an err-disabled port with `no shutdown`.
4. **`dos ipoptions` is a NO-OP on the IE520 — FAIL, candidate product defect (2026-09-28).**
   Armed it shows Enabled but counts 0 and never shuts the port, verified with a valid unicast
   source MAC on BOTH a bridged path AND a genuinely routed path (scratch vlan90 SVI, dst = stack
   router MAC), RR and illegal LSRR options (wire-verified ihl 6/7), ~3200 pps vs a 20 pps
   threshold. The earlier 'needs L3 routed path' theory is DISPROVEN; the 2026-09-04 illegal
   multicast source MAC (01:00:01:00:00:01, fixed in dos_campaign.py 2026-09-28, Test-cases a41e838) was a real bug
   but not the cause. The other five DoS types fire on this bench, so the engine + method work —
   ipoptions specifically does not. CONTROL (2026-09-28): x230 detects the same stimulus (Attacks
   detected 1, err-disable); the AR4050S build has no `dos` feature at all. So it is a CONFIRMED
   IE520-specific defect, safe to file.
   Verdict: teardrop/land/ping-of-death/smurf/synflood PASS; ipoptions FAIL. Detail: 5437.log.

Pass criterion: armed+attack → port `err-disable` (`show dos interface`, Attacks detected > 0);
disarmed+attack → port stays connected.
