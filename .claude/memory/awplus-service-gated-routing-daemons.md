---
name: awplus-service-gated-routing-daemons
description: "On IE520 awplus_main, OSPF/RIP/VRRP/PIM-SM/PIM6/BFD reject with \"daemon is not running (or feature license…)\" until `service ospf|rip|vrrp|pim|pim6|bfd` is issued — NOT a licence problem; never declare a feature unavailable from one rejected command (a 09-22 BFD verdict was)"
metadata: 
  verified: 2026-09-23
  node_type: memory
  type: feedback
  originSessionId: 49dcf692-ded5-46ac-ab73-fffb9e6ddec8
  modified: 2026-09-09T03:31:58.822Z
---

**What happened (2026-09-09, tb470):** `router ospf`, `router rip`, `router vrrp`, `ip pim sparse-mode`
all failed with `% <X> protocol daemon is not running or feature license is not available`. I read the
second clause, called OSPF/RIP/VRRP/PIM "license-gated / unavailable" and triaged 9 of 13 cases as
blocked. Terrence checked `show license` (all features present, incl. `AT-IE520-FL01` on u2) and then
asked whether I had run the **`service *` enablers first** — I had not.

**The fact:** on IE520 `awplus_main-20260905` the routing daemons are gated behind
`service ospf | service rip | service vrrp | service pim | service pim6 | service ospf6 | service ripng |
service isis`. `service X` starts the daemon **immediately** (no restart needed; the protocol config is
accepted straight after). Only **`no service X`** says "Save the config and restart for this change to
take effect" — the daemon keeps running until reboot. Licence is irrelevant (u4 without FL01 behaves
the same as u2 with it). **PIM-DM has no `service` command in the corpus and stays rejected** [SUPERSEDED 2026-09-29: `service ?` on awplus_main-20260923-20 (stack, IE520-sa) and on the AR4050S build lists `pdm  Dense Mode (PIM-DM)`; `show ip pim dense-mode interface` answers "daemon is not running" = gated, present. The x230 has no PIM-DM.] after
`service pim` — treat as unavailable on this build. `ip pim sparse-mode` additionally needs
`ip multicast-routing` ("IP Multicast Routing not activated").

**Why:** the "or feature license" clause is a generic catch-all; the first clause was literally true.
Rebooting is NOT an option on tb470 (IE520s TFTP-boot and have no dongle → hang), so an answer that
ends in "reboot to activate" is no answer.

**CONFIRMED AGAIN 2026-09-22, plus what comes AFTER the service command.** `service ospf6`
started OSPFv3 immediately as described. But starting the daemon is only step one — the part
that cost real time was **attaching an interface**:

```
interface vlan10
 ipv6 router ospf area 0        <- the command is `ipv6 router ...`, NOT `ipv6 ospf ...`
```

There is no `area` option under `ipv6 ospf ?` on the interface, and no attachment command in
the `router ipv6 ospf` sub-mode either, so probing leads you to conclude it cannot be done.
It is documented: [[awplus-cli-wiki-on-the-share]], page
`claude/github-copilot-awplus-wiki/awplus_cli_wiki/commands/ipv6-router-ospf-area.md` (checked 2026-09-23). Once
both ends had it, the adjacency went Full and survived 5/5 link flaps.

Two more from the same session: **`service bgp` is `% Incomplete command` on the AR4050S**
(BGP needs no enabler there) while the IE520 accepts it, so do not assume the gating set is
identical across platforms. And `no service ospf6` still reports "Save the config and restart
for this change to take effect" — the daemon lingers until reboot, which is harmless once
nothing references it.

**AGAIN 2026-09-24: BFD and PIM6.** `show bfd peer` says `% BFD protocol daemon is not
running` until `service bfd`. The 2026-09-22 38430 verdict ("the DUT exposes no BFD session
view") was built on never running it, and on `show bfd session`, which is not an AW+ command
(it is `show bfd peer`). With `service bfd` on both IE520s, BFD came up and fall-over worked.
`ipv6 multicast-routing` likewise needs `service pim6` first. The AR4050S has no BFD CLI at
all, and the x230 has neither BFD nor BGP, so the gating set really does differ per
platform. `no service bfd` drops the console out of config mode.

**How to apply:** when an AW+ protocol command says "daemon is not running", check
`show running-config | include service` and the corpus for `service <daemon>` BEFORE concluding
anything about licences or the image; verify with one accept/reject probe. Never build a triage
verdict on a single rejected command. Related: [[ie520-mcast-l3-test-method]],
[[awplus-cli-confirmations-need-enter]].
