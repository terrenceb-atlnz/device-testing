---
name: two-box-campaign-dut-and-client-on-different-testboxes
description: How the first two-testbox /test-mode campaign was run (tb490 DUT, tb5 client side, 2026-10-29) — the tooling is single-box, so each box is its own bench and the client host is the far box
metadata:
  type: project
---

The first campaign spanning two testboxes ran 2026-10-29 (jacobm): DUT swi_dut (x980-16CDQ) on **tb490 u2**,
the rest of the network on **tb5** (u0 swi_x950, u1 swi_x530, u2 swi_ar). Test Engineer's words: *"the 490 runs
it, tb5 is for console access and logging"*. 4 auth cases, 4 PASS.

**The tooling is single-box everywhere** (precheck, `bench_probe.py`, the `.setup`, `sentinel.sh BOX=`, the
queue's one `Testbox:` line). What worked:
- Treat each box as its own bench: precheck, probe, `.static` and `apply` per box. The one cross-box link
  (DUT port1.0.81 ↔ x950 port1.0.49) cannot be a `[portlink]` in either `.setup`; it is a comment in both.
- Arm the sentinel on the box that holds the DUT (`BOX=tb490`).
- **The client host is the FAR box.** tb490's only DUT-facing NIC is eth1 to the DUT's eth0 (management);
  every client leg ran from tb5 eth6 (192.168.50.0/24) through swi_x530 → swi_x950 → DUT. That segment and any
  root change on tb5 (a route via the DUT) were the Test Engineer's decisions (STANDING-ORDERS §4), asked at
  triage. `tools/hostnet.py` is the narrow, approved root helper for the tb5 route and jm1–jm5 macvlans.
- tb5's `python3` is 3.6 → `BOX_PY` in `tools/tb` uses python3.8 there. ckcon on tb5 u2 (AR4050S) hangs after
  logout every time; kill it by PID with `killmine`.
- Neither box had a `bench-setup/<TB>/` or deployed `.setup` before 2026-10-29; both do now.

**Why:** the next two-box campaign will otherwise re-discover all of this at triage cost (the D1/D2 questions
blocked all four cases until answered).

**How to apply:** at `/test-mode` §1, when the Test Engineer names two boxes, ask up front which box hosts the
client NIC and its segment, and whether root on that box is allowed. Read `tb490/x980/CAMPAIGN-QUEUE-2026-10-29T1304.md`
(Session facts, Triage) and `platforms/x980.md` before dispatch. Related: [[shared-testbox-console-occupancy]],
[[campaigns-measured-for-token-waste]], [[eap-tls-needs-tls12-supplicant]].
