---
name: ixia-chassis-82-tcl-access
description: "IXIA chassis 82 (10.36.10.82, XGS12, IxOS 9.20) is driveable from a testbox with the lab's IxTclHal 6.80 client in /home/ixos-IxNetwork via its IxTclServer on 4555; reads work without port ownership; the framework's ATIxia cannot do 82 (sys.exit); IxNetwork VMs expose RDP only, no REST"
metadata:
  type: reference
---

**Measured 2026-10-21 from tb101** (read-only; nothing owned or written).

- Chassis `ixia82.st.atlnz.lc` = 10.36.10.82, `Ixia XGS12`, ixServer `9.20.2700.23`. Open: 22, 443 (REST needs an API key, 401), 4500/4501, **4555 = IxTclServer**.
- Client: `/home/ixos-IxNetwork` (-> ixos-6.80_IxNetwork, IxTclHal 6.80, its own `bin/tclsh8.5`). Env: `IXIA_HOME=$H IXIA_TCL_DIR=$H/lib TCLLIBPATH=$H/lib TCL_LIBRARY=$H/lib/tcl8.5 TK_LIBRARY=$H/lib/tk8.5 LD_LIBRARY_PATH=/usr/lib:$H/lib IXIA_VERSION=9.20`. The system tclsh/python tkinter cannot find IxTclHal.
- **`ixConnectToTclServer <ip>` FIRST, then `ixConnectToChassis <ip>`.** Without the Tcl server step the package loads but `chassis`/`card`/`port` are "invalid command name".
- Without ownership these work: `chassis get`, `card get`, `port get` (shows `-owner`), `stat get statAllStats 1 <card> <port>` (link, framesSent/Received, fcsErrors), `stat getRate`. So a run can READ counters while someone else's IxNetwork owns the ports.
- Writing streams/starting traffic needs `ixPortTakeOwnership`, which steals the ports from their owner; the auto-mode classifier blocked a script containing it ("Interfere With Workloads"). Get the owner's release/OK first. A 6.80 client writing to a 9.20 server: PROVEN, see below.
- Framework `ATDrivers/ATIxia.py` knows only chassis 72-81 (82 -> `sys.exit('Specified IXIA does not exist')`) and assumes `10.36.10.<n>`; a patched staging copy or a direct Tcl driver is needed for 82.
- IxNetwork VMs (`ixia-vmNN-vNN.atlnz.lc`, 10.32.19.x; free/busy list at `https://intranet.atlnz.lc/ixiavms/api.php`) answer RDP 3389 only: no IxNetwork REST (11009) from the lab or dev host. The SVT scripts' `ixnetwork_restpy` path therefore needs the API server enabled on a VM first.

**Added 2026-10-21 16:10 (a second session measured the same things; merged here):**
- Card 10 = FlexAP1040SQ (20 ports); ports 5/6 = LAN SFP+ 10GBASE-SR/LR, 10000/full, autoneg off, link 1, cabled to
  tb101's IE520 stack port3.0.25 (vlan3) / port4.0.25 (vlan2); which is which: measure by counters, never assume.
- `port cget -owner` read **`IxNetwork/ixia-vm18-v10/terrenceb`** = Terrence's own IxNetwork session on VM18; the
  string is `<app>/<vm>/<user>`. That VM's 11009 was closed, so his session cannot be driven over REST.
- Stream idiom (ck.db `test_scripts/8003_x8100/test-9999.021.py`): `stream setDefault; stream config -sa … -da …
  -percentPacketRate N; stream set 1 <card> <port> 1; set portList {{1 10 5} {1 10 6}}; ixWriteConfigToHardware
  portList; ixStartTransmit portList; ixStopTransmit portList; ixClearPortStats 1 10 5`. The older driver that did the
  TclServer step is `test_scripts/5009_performance_failover/ATPylib/ATIxia.py` (ck.db).
- `.setup` form: `[ixia] ixia_a = <num>, <user>`; `[portlink] swi-ixia_a = portX-<num>.<card>.<port>` (`Setup.py:923`).
- python3.8 on tb101 has `requests` 2.18.4, no `ixnetwork_restpy`.

**Added 2026-10-21 17:50 (from the second copy's deleted draft, `ixia-chassis-82-driving.md`):**
- Versions: chassis ixServer 9.20.2700.23, IxTclHAL server `9.20.2700.17 Patch1` (`version get`); the 6.80 client
  proxies to it. `/home/ixos-IxNetwork` is on the NFS `/home` that every testbox mounts, NOT on the dev host: run the
  client from a testbox.
- Why the framework driver is out, not just its whitelist: it calls `ixInitialize` with no Tcl server step, and it
  loads IxTclHal inside python's tkinter (python3.8 on tb101 = Tcl 8.6, the client libs are Tcl 8.5). Drive the
  chassis from the client's own `tclsh8.5` instead.
- IxNetwork's REST (11009) is up on a VM only while someone runs the GUI with its API server on. The lab's
  `~/ixia.sh` (Terrence's, lab home root) lists free/busy VMs from the intranet API.
- Rate reads: `stat getRate allStats <ch> <card> <port>` then `stat cget -framesSent/-framesReceived/-bitsSent/-bitsReceived`.

**PROVEN 2026-10-21 17:45 (Terrence: "take the ixia sessions by force"):**
- `ixLogin <name>` then `ixTakeOwnership {{1 10 5} {1 10 6}} force` -> 0; owner reads `<name>`, and it PERSISTS across
  later connections that `ixLogin` with the same name (no re-take needed). With Terrence's explicit OK the auto-mode
  classifier allowed it.
- The 6.80 client DOES write to the 9.20 server: `port setFactoryDefaults`; `protocol config -name ipV4 -ethernetType
  ethernetII`; `ip config -sourceIpAddr/-destIpAddr/-ipProtocol ipV4ProtocolUdp; ip set`; `udp set`; `stream config
  -sa/-da {00 00 00 00 00 01} -framesize 512 -rateMode usePercentRate -percentPacketRate N -dma stopStream -numFrames
  100; stream set 1 10 P 1`; `ixWriteConfigToHardware portList`; `ixClearStats portList`; `ixStartTransmit` /
  `ixStopTransmit portList`. Each port sent exactly 100; `stream get` read every field back. (`-dma
  contPacket` for a continuous run.)
- Cabling, measured by MAC learning: **10/5 <-> tb101 port3.0.25 (member 3), 10/6 <-> port4.0.25 (member 4).**

Related: [[tb101-ie520-bench-map]] (IXIA on port3.0.25 / port4.0.25).
