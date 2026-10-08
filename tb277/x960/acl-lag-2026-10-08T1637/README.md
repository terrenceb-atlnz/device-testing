# tb277 — AT-x960-56YSQ (Marvell 98CX8514 Falcon) — 2026-10-08

| case | title | log | verdict |
| --- | --- | --- | --- |
| T44992 | ACL: Named Hardware on static LAG - IP | [T44992/T44992.log](T44992/T44992.log) | **PASS**. A named hardware IP ACL bound to the static LAG `sa1` denies the traffic its rule matches and permits everything else, and is effective on each member port independently (proven by shutting each member in turn). Host and network address forms both select correctly, the `vlan` qualifier narrows the match, first match wins by sequence, non-IP (ARP) traffic is unaffected, the same ACL enforces via `service-policy input` as via `access-group`, the configuration and its enforcement survive a reload, and removal leaves no config or classifier residue. The stored steps' stack-straddle and stack-failover clauses were withdrawn by the Test Engineer for this platform and were not run. |
