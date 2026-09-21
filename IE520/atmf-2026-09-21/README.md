# ATMF case run — tb470, 2026-09-21

Five ATMF cases executed against the tb470 bench. Per-case deliverable is the
`<case>.log`; each carries its verdict, the evidence, and the raw transcripts.

| case | title | verdict |
| --- | --- | --- |
| [38473](38473.log) | ATMF - Member | **PASS** |
| [38478](38478.log) | ATMF - remote login | **PASS** |
| [38476](38476.log) | ATMF - crosslink | **PASS** (degenerate at 2 nodes) |
| [38477](38477.log) | ATMF - Virtual link | **PASS** (with negative control) |
| [38472](38472.log) | ATMF - Master | **FAIL** — steps 1/2/3/5 pass, step 4 (secure mode) fails |
| [38480](38480.log) | ATMF - Application proxy - IP filter | **PASS** |
| [38481](38481.log) | ATMF - Application proxy - mac filter | **PASS** |

## Bench

Two AMF nodes, which is the ceiling here: the **four IE520s are one VCStack and
therefore ONE AMF node** (`IE520-stk`), plus the **AR4050S-5G** (`4050-5g`).
AMF network-name `tb470`. The other bench consoles (`/dev/u0`, `/dev/u6`) are
dead/absent, so there is no third node.

## The finding

`atmf secure-mode enable-all` enables secure mode on both nodes and issues
valid certificates, but **the network never re-forms** — both sides sit at
`OneWay / Blocking` while naming each other correctly as adjacent. Disabling
secure mode brings the same link straight back to `Full / Forwarding`.

**Untested confound:** the AMF link is an LACP aggregate. Whether a single
physical AMF link behaves the same was not established. See 38472.log for the
exact next step to localize it.

## Still to run (from the 10-case ATMF set)

- **38479** node provision — **unblocked** as of 2026-09-21: the x230-10GP is a
  usable spare DUT, `x230-tb470.rel` is in tb470 `/tftproot`, and the x230 is
  already cabled to a stack port that can be the provisioning port. Running it
  wipes the x230 and removes it from the AMF network, which is the point.
- **38474** backup/restore — needs a decision: `atmf cleanup` wipes the DUT's
  flash. Also `rsync` is NOT installed on tb470 (sftp is), so the remote file
  server needs sorting first.
- **38475** recover from USB — the USB stick is in **stack member 1**, so the DUT
  must be the IE520 stack; there is no low-risk substitute. Destructive.

## Bench state at exit

Restored and verified: vlan10 ping 3/3, LAG both links `synchronized`, stack
`Normal operation`, AMF 2/2 nodes, secure mode off.

**Divergence from `bench-setup/bench-state.md`:** the bench now carries AMF
config that the documented baseline does not — stack hostname is `IE520-stk`
(was `awplus`), `atmf network-name tb470` + `atmf master` on the stack,
`atmf network-name tb470` on the 4050, and `po1` is a **trunk** with
`switchport atmf-link` carrying vlan10 as native (it was `access vlan 10`).
`00-baseline.txt` holds the pre-change running-config of both devices.
Decide whether to fold this into bench-state.md or revert it.
