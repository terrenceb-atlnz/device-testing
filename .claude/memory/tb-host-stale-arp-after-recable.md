---
name: tb-host-stale-arp-after-recable
description: After a host NIC is recabled to a different unit, the testbox's ARP cache keeps the OLD unit's MAC for the IP, so pings fail until the entry fails and re-resolves — check `ip neigh` before suspecting the DUT
metadata:
  type: project
---

**Measured 2026-10-06, tb470 eth2 → x230-28GS V2 (u0) port1.0.1.** The x230 answered on
`10.38.215.40/27`, but tb470's first `ping -I eth2 10.38.215.40` lost 4/4. `ip neigh show dev eth2`
still mapped `.40` to `00:00:cd:37:0d:6f`, the IE520 stack's MAC from before eth2 was recabled. The
host sent unicast frames to that MAC, and the x230 does not answer frames addressed to another MAC.
Once the entry went `FAILED`, the next ping re-ARPed by broadcast and got 10/10 with the x230's own
MAC (`00c2.8f3f.0f5d`). Nothing on either device needed changing. Terrence had been hitting this
("that was the issue!").

**Why:** Linux re-probes a `STALE`/`DELAY` neighbour by **unicast** to the cached MAC first. When an
IP moves to a different unit behind the same NIC (a recable, a unit swap, an address reused), those
probes go to a MAC that is no longer there, and the host does not broadcast until they have failed.

**How to apply:**
- When host↔DUT pings fail after any cabling, unit or address change, run
  `ip neigh show dev ethN to <ip>` on the box first. If the lladdr is not the DUT's MAC (check
  `show system mac` / the DUT's `show arp` CPU entry), the fault is the cache, not the DUT.
- Fix it either way: wait a few seconds and ping again (the entry goes FAILED, then a broadcast
  resolves it), or `sudo ip neigh flush dev ethN`. The flush needs root on the box:
  [[tb470-root-changes-go-through-terrence]].
- The same trap applies to a DUT's own ARP cache when the host behind a port changes.
