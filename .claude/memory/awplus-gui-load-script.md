---
name: awplus-gui-load-script
description: Updating an AW+ unit's web GUI = run /home/terrenceb/Load-gui9.sh ON the switch via `activate flash:/Load-gui9.sh`; the unit needs a route to awpbuild 10.32.18.135 (via tb470 eth2) first
metadata:
  type: reference
---

The Test Engineer's GUI updater is `Load-gui9.sh` (lab root, `/home/terrenceb/Load-gui9.sh` on
tb470; "the gui9 one was the correct script", 2026-10-05).

- It runs ON the switch (it calls `imish`). Run it with `activate flash:/Load-gui9.sh`, which takes
  no arguments. The script then:
  - fetches the newest `awplus-gui-YYYYMMDD_HHMM.gui` from `http://10.32.18.135/releases/awplus-gui/`;
  - renames it per the running build (`5.5.6-1.2` → `awplus-gui_556_99.gui`; a `main` build →
    `awplus-gui_999_99.gui`);
  - restarts `service http`.
- **The unit needs network first.** A fresh unit on `default.cfg` has none. On tb470 u1, port1.0.1
  goes to tb470 eth2 (`10.38.215.33/27`, and tb470 forwards). The temporary, unsaved setup used:
  vlan1 `10.38.215.60/27` + `ip route 10.32.18.135/32 10.38.215.33`. Deliver the script with
  `copy http://10.38.215.33:8080/Load-gui9.sh flash:/` from a user-space `python3 -m http.server`
  in tb470 `/tmp` (no root).
- Verify with `show http` → `GUI file in use`. The script does NOT delete the old `.gui`; delete it
  yourself if asked. Remove the temporary IP and route afterwards.
- A driver with stop-on-error trips on curl's `% Total` progress header. It's a false alarm.
- Done on an IE560 and an IE360 (both 5.5.6-1.2) 2026-10-05 → `awplus-gui-20261005_1020.gui`.
