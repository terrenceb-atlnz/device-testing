---
name: awplus-restconf-api-reference
description: "The AW+ API" = RESTCONF (Terrence 2026-10-13). Enable: service http (+ service restconf before 5.5.4-1), HTTPS 443, a priv-15 user. Guide + YANG repo LOCATIONS inside. MEASURED x230v2 2026-10-13 (T47228): root /restconf (host-meta 404); writes = PUT on a LEAF, unqualified body; PATCH-on-leaf 204 does nothing; NO VLAN-database model (VLAN add/delete not possible)
metadata:
  type: reference
---

**When a case says "API"** (T47228, "API-enable/disable interface, add/delete vlans"), it means
**RESTCONF** (RFC 8040), as Terrence confirmed on 2026-10-13. NETCONF is the SSH sibling, on port 830 with `service netconf`.

**Sources: track the LOCATION, not a copy.** Allied Telesis revises the guide periodically (Terrence,
2026-10-13), so always fetch the current one from where it lives and note the revision you read:
- **Guide, landing page (the location of record):**
  https://www.alliedtelesis.com/us/en/documents/netconf-and-restconf-feature-overview-and-configuration-guide
  ("NETCONF and RESTCONF Feature Overview and Configuration Guide"). It answers WebFetch and plain
  curl with an empty 202 (a bot challenge).
- **Stable download link that always serves the current PDF:**
  `curl -sL https://www.alliedtelesis.com/sites/default/files/documents/feature-guides/netconf_and_restconf_feature_overview_guide.pdf -o guide.pdf`
  then `pdftotext -layout`. It redirects to a dated upload (2026-10-13: `wp-content/uploads/2026/05/…`,
  C613-22141-00 REV B, "AW+ 5.5.3-2.1 or later"). Never cite the dated upload as the source.
- **YANG models:** https://github.com/alliedtelesis/yang (`models/<name>@<revision>.yang`, new revisions
  added over time; raw.githubusercontent for files, the GitHub contents API for the list).
- The lab wiki has only the enabling commands: `awplus_cli_wiki/commands/service-restconf.md`
  (AR4050, x230, x908Gen2, x930, x950) and `families/netconf-commands.md`.

**Enable it.** The guide's own example:
- `user rest priv 15 password …`
- `http port none` (HTTPS only)
- `service http`
- `service restconf` ("not required after version 5.5.4-1")

The device then listens on HTTPS port 443, and needs an IP address the client can reach. The guide says no licence is needed on any device.

**Use it (RFC 8040; per the guide, the root is implementation-defined):**
1. `GET https://<ip>/.well-known/host-meta` finds the root, `{+restconf}`. **On the x230v2-28GS
   (awplus_main-20261008-57, 2026-10-13) it answers 404 (nginx)** although the guide documents it; the root is
   `/restconf` (`GET /restconf` -> `ietf-restconf:restconf`; `/api` also answers).
2. `GET {+restconf}/data/ietf-yang-library:yang-library` lists the models (yang-library 2019-01-04, module-set
   `common`). **Read this before assuming any path below.**
3. Methods: GET, PUT (create or replace), PATCH (merge), POST (create), DELETE, OPTIONS and HEAD. The
   guide says AW+ has a running configuration only, so nothing is saved unless you `write`.
4. Client: `tools/restconf.py` (stdlib; `--root /restconf`).

**Measured on the x230v2-28GS, 2026-10-13 (T47228, `tb470/x230v2-28GS/cli-2026-10-13T0949/47228/work/run1.log`):**
- **Writes that work: PUT on a leaf with an UNQUALIFIED body.**
  `PUT /restconf/data/openconfig-interfaces:interfaces/interface=port1.0.8/config/enabled` `{"enabled":false}`
  -> 204, log `port1.0.8 user shutdown`; `{"enabled":true}` -> `no shutdown`. The same works on
  `.../ietf-interfaces:interfaces/interface=<port>/enabled`.
- A module-qualified leaf body (`{"openconfig-interfaces:enabled":false}`) on PUT -> **400 "Invalid input
  parameter"** (RFC 7951 expects the qualified name).
- **PATCH on a container** (`.../config`, `.../interface=<port>`, `openconfig-system:system/config`) -> **404 "uri
  path not found"**.
- **PATCH on the leaf -> 204 No Content and NOTHING changes** (either body form; state stays as it was). Treat a 204
  as unproven: GET `.../state` (admin-status/oper-status) and check the CLI.
- **VLANs: no model on this unit holds the VLAN database.** `openconfig-vlan:vlans` -> 404; no
  `openconfig-network-instance`, no `at-bridges`; `at-interface` has no VLAN node. Only per-port
  `.../openconfig-if-ethernet:ethernet/openconfig-vlan:switched-vlan` (`interface-mode`, `access-vlan`) is readable.
  - `PUT .../ietf-interfaces:interfaces/interface=vlan3999` `{"interface":[{"name":"vlan3999"}]}` -> 204 and a GET
    then returns it, but **no VLAN or interface exists on the device** (a phantom held only by the RESTCONF
    server; `DELETE` removes it with 204).
  - `PUT .../switched-vlan/config/access-vlan` `{"access-vlan":3999}` for a VLAN that does not exist -> 204;
    config reads 3999, state stays 1, CLI unchanged.
  - A VLAN created by CLI appears as `ietf-interfaces` `vlan3999` (type `l3ipvlan`); **`DELETE` of it -> 403
    `access-denied`** (as manager, priv 15).
  - So VLAN add/delete via RESTCONF is not possible on this build; recorded as the T47228 finding.
- `POST .../ietf-interfaces:interfaces` with a qualified list body -> 404; unqualified -> 409 "object already
  exists" when present.

**Models in the repo (for reading):** `openconfig-interfaces@2022-10-25`, `ietf-interfaces`, `at-interface`;
AT's deviation `at-openconfig-interfaces-deviation@2024-10-24` marks `config/name`, `description`, `type`,
`loopback-mode`, `mtu`, `hold-time` and `subinterfaces` not supported or replaced (`config/enabled` is not
deviated). `openconfig-vlan@2023-02-07` defines `vlan-top` but never uses it at module top level (it lives under
`openconfig-network-instance` in OpenConfig); AT's `at-openconfig-vlan-deviation@2024-02-15` drops `tpid`,
`subinterface vlan`, `aggregation switched-vlan` and `routed-vlan`.

Related: [[awplus-cli-wiki-on-the-share]].
