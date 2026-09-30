# MRP group — IE520, tb470, 2026-09-22

5 cases. **0 executed — the whole group is hard-blocked, on the ring PARTNERS,
not on the DUT.**

| case | title | verdict |
| --- | --- | --- |
| 28863 | MRP - Stack failover master/slave | **UNMEASURED** here; the log moved (`git mv`, 2026-09-30) to [../mrp-2026-09-29/28863-fail.log](../mrp-2026-09-29/28863-fail.log), which supersedes it: re-run on a two-node ring with the IE520-sa |
| 38093 | MRP ring with DUT as MRM | **UNMEASURED** here; the log moved (`git mv`, 2026-09-30) to [../mrp-2026-09-29/38093-fail.log](../mrp-2026-09-29/38093-fail.log), which supersedes it (FAIL, two-node ring with the IE520-sa) |
| 38097 | MRP ring with DUT as MRC | **UNMEASURED** |
| 38098 | MRP ring switch over with 200ms recovery time | **UNMEASURED** |
| 38099 | MRP ring switch over with 500ms recovery time | **UNMEASURED** |

## The blocker

Every one of these cases requires a three-node MRP ring — "Configure sw1 with
the MRP MRC config", "Configure sw2 with the MRP MRC config". The bench has
exactly three devices and they are physically cabled as a ring, so the topology
is right. **But neither ring partner can run MRP.**

| device | `show mrp` | `show mrp ring` | config `mrp ?` | MRP in licence |
| --- | --- | --- | --- | --- |
| **IE520 stack (DUT)** | supported | supported | `ring  Configure a MRP ring` | YES |
| AR4050S-5G | `% Invalid input` | `% Invalid input` | `% Unrecognized command` | listed, but no CLI |
| x230-10GP (AW+ 5.5.5) | `% Invalid input` | `% Invalid input` | `% Unrecognized command` | no |

Checked in both EXEC and configure mode on each device, so this is not a
mode or PATH artefact.

**The DUT side is fine and is not what blocks this.** It carries the full
command set:
```
IE520-stk(config)# mrp ?
  ring   Configure a MRP ring
IE520-stk# show mrp ?
  ports  Display MRP ring ports
  ring   Display MRP ring configuration
```
MRP is also in its licence. A ring could be configured on the DUT today; it
would simply have no MRP peers to form a ring with, and `show mrp ring` would
never report operational — which is the state every one of these cases checks
first.

Note the AR4050S lists MRP as a licensed feature while exposing no MRP CLI at
all. Recorded as an observation for review; a licence entry is not a capability.

## To unblock

Two MRP-capable switches as ring partners. Any AlliedWare Plus switch with MRP
support would do — the existing cabling already forms the ring
(`stack port1.0.2 — x230 port1.0.3`, `x230 port1.0.2 — 4050 port1.0.2`,
`4050 port1.0.4 — stack port4.0.2`), so only the devices need swapping, not the
wiring.

## Bench state

Untouched by this group. No MRP was configured, and the x230↔4050 link was
deliberately left shut down — bringing it up without a working ring protocol
would create a loop on a bench with RSTP disabled on all three devices.
