# tb490 + tb5 / x980 — session handover, 2026-10-30

The second x980 auth campaign (queue `CAMPAIGN-QUEUE-2026-10-29T1528.md`), started 2026-10-29 15:28 and
finished 2026-10-30 09:36 NZDT. The DUT is on tb490; the client side is on tb5.

## Session facts

Test Engineer: jacobm@jacobm-dl
Testbox: tb490 (DUT, and the box that runs the cases) + tb5 (the rest of the network) — "Same as 10-29"
Consoles: tb490 u2 = swi_dut; tb5 u0 = swi_x950, u1 = swi_x530, u2 = swi_ar ("Same as 10-29")
PDU: none on either box ("Same as 10-29")
Constraints: "no shared boxes all mine, run the test probe, u0 and u1 on tb490 are not to be touched";
             `lldp run` stays off, so every probe runs `--read-only`;
             "if anything touvhes u2 please stop" (never triggered);
             python3 processes on tb490 not on u2 are the Test Engineer's own (x980nos).

Copied from [CAMPAIGN-QUEUE-2026-10-29T1528.md](CAMPAIGN-QUEUE-2026-10-29T1528.md).

## TL;DR

**Campaign complete. 9 cases: 7 PASS, 2 UNSUPPORTED, 1 NOT TESTED. Final logs CREATED for the 4 cases run
here. The bench is whole.** swi_dut is standalone, on build -90, with no reload (uptime 23 h 16 m at 09:36),
running-config equal to the campaign baseline. The sentinel stood down (Monitor stopped, cron deleted, no
stray watcher). Nothing is running on either box.

🔴 **36 commits (including this wrap) are local and NOT pushed.** `git push origin main` is yours.

🔴 **tb5 eth6 carries the Test Engineer's runtime `192.168.50.10/24`** (re-added 2026-10-30 08:26 with
`sudo ip addr add 192.168.50.10/24 dev eth6`). It was missing on 10-30 morning (tb5 had not rebooted). It
does not survive a reboot of tb5; every client leg in this bench needs it.

🔴 **Corrected platform fact:** the x980 web-auth DHCP server does NOT need `service dhcp-server` (10-29's
claim was wrong). See Findings.

## Current bench state and how to verify it

```bash
cd ~/claude/device-testing      # or the repo root on your dev host
tools/tb precheck tb490 u2      # never u0/u1 on tb490
tools/tb precheck tb5 0-2       # ser2net (pid 593, ttyS0/S1 only) is always FOUND; it is not a holder
tools/tb probe tb490 --consoles u2 --baud 115200 --read-only --no-prompt     # MATCH expected
tools/tb probe tb5 --consoles 0-2 --baud 115200 --read-only --no-prompt      # MISMATCH 3 + NEEDS-CHECK 1 expected (read-only artefacts)
ssh tb5 'ip -br -4 addr show eth6'      # 10.37.5.129/27 192.168.50.10/24
tools/tb sudotool tb5 <scratch> hostnet show     # both routes absent
```

Topology: [bench-setup/tb490/bench-state.md](../../bench-setup/tb490/bench-state.md) (Generated
2026-10-29T203646Z, i.e. 2026-10-30 09:36 NZDT, **MATCH**) and
[bench-setup/tb5/bench-state.md](../../bench-setup/tb5/bench-state.md) (Generated 2026-10-29T203654Z,
**MISMATCH 3 + NEEDS-CHECK 1**, all from read-only mode: no LLDP to prove x530↔x950; eth6 placed on swi_x950
port1.0.39; no MAC learned on eth4→swi_ar). The deployed `tb5.setup` is correct; nothing was applied.

### Per unit, as left (read 09:36 NZDT)

| unit | power | state | boot | config |
| --- | --- | --- | --- | --- |
| swi_dut (tb490 u2) | on | standalone; uptime 23 h 16 m, no new reboot; build awplus_main-20261029-90 (Wed Oct 28 20:43:01 UTC 2026) | `flash:/x980-tb490.rel (file exists)`, `flash:/x980-autoorder.cfg (file exists)` | running = campaign baseline (rcdiff 0 after every case); `no service dhcp-server`; no `lldp run`; no test users left. Running still differs from startup exactly as on 10-29 (startup has the two-step rig) |
| swi_x950 (tb5 u0) | on | — | `x950-5.5.5-2.1.rel (file exists)` | not configured this campaign; no `lldp run` |
| swi_x530 (tb5 u1) | on | — | boot image "Not set" | not configured this campaign; no `lldp run` |
| swi_ar (tb5 u2) | on | — | `AR4050S-awplus_main-20251103-998.rel (file exists)` | not configured this campaign; `lldp run` present (found so on 10-29, not ours) |

- eth6 (0090.0b2a.11c3) on swi_dut port1.0.81 is web-authenticated as `ckrestore`, a user since deleted.
- tb5 host: eth6 UP 10.37.5.129/27 + 192.168.50.10/24 (the Test Engineer's); no 8.8.8.0/24 or 192.168.60.0/24 route.
- Nothing is shut down or powered off. No `write` on any unit. All consoles logged out.
- Scratch left in `/tmp/{sm1528,tri1029,tri1528,wa1030,wa1528}` on both boxes (tool copies and console
  transcripts). Scratch only; delete or let it go.

## What was accomplished

- **Triage** of 9 AWPTCM auth cases. None had authored steps; T33354's only text is "Not Support". The DUT's
  local RADIUS offers MAC/EAP-MD5/EAP-TLS/EAP-PEAP only.
- **Runs:** T44274, T44275, T44276 (5 runs), T44277 on the DUT.
- **The Test Engineer's own verdicts** for T33355, T33354, T44271, T44272 ("already tested and finished"), and
  T33358 "do not need to test".
- **Tools:** `tools/httpq.py --proxy HOST:PORT`. `tools/hostnet.py route60-add|route60-del` (192.168.60.0/24
  via 192.168.50.1 dev eth6), approved by the Test Engineer 2026-10-30, commit 74f32d0.
- **platforms/x980.md §1.1** updated (web-auth DHCP), and corrected on 10-30 (9272735).
- **`/create-logs`** run: 4 final logs, group READMEs, process reviews.

## Results — final logs CREATED

| case | verdict | graded | final log |
| --- | --- | --- | --- |
| T44274 (204) Multiple Authentication | PASS | tester | [webauth-2026-10-29T1528/T44274/T44274.log](webauth-2026-10-29T1528/T44274/T44274.log) |
| T44275 (207) Proxy Server for Web Auth | PASS | tester | [webauth-2026-10-29T1528/T44275/T44275.log](webauth-2026-10-29T1528/T44275/T44275.log) |
| T44276 (208) DHCP Server for Web Auth | PASS (run 5, all steps; clean) | tester | [webauth-2026-10-29T1528/T44276/T44276.log](webauth-2026-10-29T1528/T44276/T44276.log) |
| T44277 (214) Supplicant MAC | PASS (clean) | tester | [dot1x-2026-10-29T1528/T44277/T44277.log](dot1x-2026-10-29T1528/T44277/T44277.log) |
| T33355 (192) 802.1X-2004 | PASS | Test Engineer (already tested and finished) | — |
| T33354 (191) EAP-Notification | PASS | Test Engineer (already tested and finished) | — |
| T44271 (197) EAP-LEAP | UNSUPPORTED | Test Engineer ("Not Supported") | — |
| T44272 (198) EAP-OTP | UNSUPPORTED | Test Engineer ("Not Supported") | — |
| T33358 (195) EAP-TTLS | NOT TESTED | Test Engineer ("do not need to test T33358") | — |

/create-logs commits: abd225a (dot1x), 278d53c (eap, README only), cd84bb9 (webauth). Reviews:
[webauth REVIEW.md](webauth-2026-10-29T1528/REVIEW.md), [dot1x REVIEW.md](dot1x-2026-10-29T1528/REVIEW.md).

T44276 CAVEAT for review: the step 5 login was sent from eth6's own 192.168.50.10 through the host route,
not from the leased 192.168.60.x address. The DUT accepted it.

## Findings

### Measured (x980, build awplus_main-20261029-90)
- **The web-auth DHCP server serves without `service dhcp-server`** (run 5 step 1a: `show ip dhcp server
  summary` "DHCP Server service is disabled", OFFER/ACK still sent). **A MAC's first DISCOVER is never
  answered.** Default lease 20 s; `lease` range 20-60; addresses go up by one; the login page at 192.168.60.1
  was served to a client sourcing 192.168.50.10. In platforms/x980.md §1.1.
- `auth-web-server intercept-port 8080` intercepts a proxied request; a login POST sent THROUGH a proxy gets
  no reply ("No Proxy" for the login network, Tips & Tricks rev D p.65).
- `auth supplicant-mac`: bare form admits nothing; force-authorized admits only that MAC; force-unauthorized
  ends a valid session; a 2nd parameter silently replaces the 1st.
- The first ICMP leg after an auth change lost 1-3 of 4 replies more than once; the next leg was 4/4.

### Corrected
- **10-29's "the web-auth DHCP needs `service dhcp-server`" was WRONG.** It came from run 1's single-DISCOVER
  tries (first DISCOVER never answered), "confirmed" by run 2 which changed two things at once. Lesson in
  memory `campaign-measurement-discipline` §5.

### Inferred, not measured
- 192.168.50.254/24 (inside vlan1's subnet) as the web-auth DHCP address "got no OFFER" only with single
  DISCOVERs: unproven either way.

## OPEN

1. **`bench_probe.py precheck` missed a live `python3 -m x980nos load-release -u u2`** (10-29 15:21: CLEAR while
   the process existed). Its python-script check does not see `python3 -m <module>`. Fix or accept?
2. **tb5 `ckcon … exit` hangs every time** (the console prints `login:`, not a prompt): each tb5 logout costs a
   timeout + `killmine`. A `--logout` mode that waits for `login:` would fix it.
3. **`.cfg` headers:** T44274/T44275/T44276 `swi_dut.cfg` keep the echoed `x980-CDQ#show running-config` line;
   T44277's header is not the logged-output.md §2 three-line format. Not edited.
4. **ck.db is not reachable from the dev host** (`tools/ckcase.py` looks under `~/claude/Test-cases`). The
   tester read it on tb490 at `/home/terrenceb/claude/Test-cases/ask-ck/db/ck.db`.
5. Proposed helpers (not built): `tools/dhcpleg.py` (K DISCOVERs per MAC), `tools/authleg.py` (auth state +
   ICMP per leg). Details in the REVIEW.md files.

## Ordered next steps

1. `git push origin main` (36 commits).
2. Review the 4 final logs and attach them in Zephyr (T44276: decide on the CAVEAT).
3. Decide OPEN 1-2.

## Recipes

```bash
# Client legs run from tb5 eth6 (192.168.50.10) -> swi_x530 port1.0.16 -> swi_x950 -> swi_dut port1.0.81.
# Before every auth leg:  x980-CDQ(config)# do dot1x initialize interface port1.0.81
# eth6 address missing?   ssh tb5; sudo ip addr add 192.168.50.10/24 dev eth6        (runtime only)
# Off-subnet legs (approved helper only):
tools/tb sudotool tb5 <scratch> hostnet route-add | route-del          # 8.8.8.0/24 via 192.168.50.1
tools/tb sudotool tb5 <scratch> hostnet route60-add | route60-del      # 192.168.60.0/24 via 192.168.50.1
# DHCP client: always 2+ tries per MAC (first DISCOVER is never answered):
tools/tb sudotool tb5 <scratch> dhcp4 client eth6 --mac <mac> --wait 10
# arpleg: always pass --src (default sender is 192.168.10.2)
```

## Pointers

- Queue and Results: [CAMPAIGN-QUEUE-2026-10-29T1528.md](CAMPAIGN-QUEUE-2026-10-29T1528.md)
- Platform: [platforms/x980.md](../../platforms/x980.md) §1.1
- Previous handover: [SESSION-HANDOVER-2026-10-29.md](SESSION-HANDOVER-2026-10-29.md)
- Memory updated: `campaign-measurement-discipline` (§5).
- Sentinel stood down at this wrap.
