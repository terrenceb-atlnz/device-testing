---
name: awplus-restconf-api-reference
description: "The AW+ API" = RESTCONF (Terrence 2026-10-13). Enable: service http (+ service restconf before 5.5.4-1), HTTPS 443, a priv-15 user. Models: github.com/alliedtelesis/yang; guide PDF URL inside. Interface enable = openconfig-interfaces config/enabled
metadata:
  type: reference
---

**When a case says "API"** (T47228, "API-enable/disable interface, add/delete vlans"), it means
**RESTCONF** (RFC 8040), as Terrence confirmed on 2026-10-13. NETCONF is the SSH sibling, on port 830 with `service netconf`.

**Sources (fetched 2026-10-13; neither the wiki nor ck.db holds the request paths):**
- **Guide:** "NETCONF and RESTCONF Feature Overview and Configuration Guide", C613-22141-00 REV B, for AW+
  5.5.3-2.1 or later.
  - PDF: https://www.alliedtelesis.com/wp-content/uploads/2026/05/NETCONF_and_RESTCONF_Feature_Overview_Guide.pdf
  - The `/documents/…` landing page returns an empty 202 (a bot challenge), so WebFetch gets nothing; download the PDF with curl.
- **YANG models:** https://github.com/alliedtelesis/yang, in `models/<name>@<revision>.yang`. Use raw.githubusercontent for files
  and the GitHub contents API for the list.
- The lab wiki has only the enabling commands: `awplus_cli_wiki/commands/service-restconf.md`
  (platforms AR4050, x230, x908Gen2, x930, x950) and `families/netconf-commands.md`.

**Enable it.** The guide's own example:
- `user rest priv 15 password …`
- `http port none` (HTTPS only)
- `service http`
- `service restconf` ("not required after version 5.5.4-1")

The device then listens on HTTPS port 443, and needs an IP address the client can reach. The guide says no licence is needed on any device.

**Use it (RFC 8040; per the guide, the root is implementation-defined):**
1. `GET https://<ip>/.well-known/host-meta` finds the root, `{+restconf}`.
2. `GET {+restconf}/data/ietf-yang-library:…` lists the models this unit supports. **Read this
   before assuming any path below.**
3. Methods: GET, PUT (create or replace), PATCH (merge), POST (create), DELETE, OPTIONS and HEAD. The
   guide says AW+ has a running configuration only, so nothing is saved unless you `write`.

**Interfaces.** The repo has `openconfig-interfaces@2022-10-25`, `ietf-interfaces` and `at-interface`.
- AT's deviation `at-openconfig-interfaces-deviation@2024-10-24` marks these not supported or replaced: `config/name`,
  `description`, `type`, `loopback-mode`, `mtu`, `hold-time` and `subinterfaces`.
- **`config/enabled` is not deviated**, so enable and disable should be
  `PATCH {+restconf}/data/openconfig-interfaces:interfaces/interface=port1.0.5/config` with
  `{"openconfig-interfaces:config":{"enabled":false}}`.
- That path is **inferred from the models, not yet run on a unit.**

**VLANs: open.**
- `openconfig-vlan@2023-02-07` defines `grouping vlan-top` (`vlans/vlan[vlan-id]/config/{vlan-id,name,status}`)
  but never uses it at module top level. In OpenConfig it sits under `openconfig-network-instance`, which
  is NOT in AT's repo.
- So VLAN create and delete may live in `at-bridges@2025-02-26` instead.
- The per-port `oc-eth:ethernet/oc-vlan:switched-vlan` (`interface-mode`, `access-vlan`, `trunk-vlans`) is supported.
  AT's deviation drops only `tpid`, `subinterface vlan`, `aggregation switched-vlan` and `routed-vlan`.
- **Settle VLAN create and delete from the unit's yang-library** (step 2) the first time, then update this memory.

Related: [[awplus-cli-wiki-on-the-share]].
