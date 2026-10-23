# Campaign queue — tb277 x960-56YSQ, 11 AWPTCM Authentication & Security cases, from 2026-10-23 13:04 NZDT

The ask, verbatim: *"Okay lets do the next set of test cases"*, with the AWPTCM "Not Executed"
panel for x960-56YSQ showing **11 test cases**, all Authentication & Security.

**This file is the resume point.** `/test-mode --resume tb277/x960/CAMPAIGN-QUEUE-2026-10-23T1304.md`
picks up at the first row that is not DONE or BLOCKED.

## Session facts

Recorded 2026-10-23 13:0x NZDT from the Test Engineer's own answers to `/test-mode` §1.

Test Engineer: bidhanc@bidhanc-dl
Testbox: tb277
Consoles: u2 = swi_d (AT-x960-56YSQ, the DUT), u3 = swi_b, u5 = swi_a
PDU: 10.36.230.212 outlets u2=1 **and u2=8** (swi_d has TWO PSUs — see below), u3=7;
     10.36.230.35 outlet u5=3
Constraints: Window: **UNATTENDED** — nothing may block on the Test Engineer. Anything needing a
             decision is recorded BLOCKED with its reason and the campaign runs on.
             **T44287 runs LAST, with a written recovery plan.**
             **T9032 is redesigned with `wpa_supplicant` on tb277.**
             🔴 **NEW, 2026-10-23 13:1x, verbatim:** *"If you have to remove vlan or
             change config on a switch because you need to execute the test, please dont ask
             me - just go ahead and do it"* — **so `vlan 60` is NO LONGER off-limits**, and no
             device-config change is a question. See below.

### ✅ THE CREDENTIAL GATE IS OPEN (2026-10-23 13:09 NZDT)

`~/.ckenv` now exists: mode **0600**, outside the repo, holding `export CK_PASSWORD_U3=...`
and `export CK_PASSWORD_U5=...`. Created at the Test Engineer's instruction (*"Go ahead and
create it for me"*) with the password they gave on 2026-10-21. Verified by sourcing it in a
subshell: both variables set, 11 characters, identical. **The value was never printed, never
put on a command line, and is not in this repo.**

**So u3 and u5 MAY now be opened** — always as `. ~/.ckenv && tools/tb ...`, never with the
password as an argument. The gate below still governs: test `[ -f ~/.ckenv ]` before every
such call, because a future session may not have it.

### 🔴 The credential gate — u3 and u5 are opened ONLY if `~/.ckenv` exists

The Test Engineer chose **"All three — I'll put the password in `~/.ckenv`"**. At campaign start
**that file did not exist**, and `CK_PASSWORD_U3` / `CK_PASSWORD_U5` are not in the environment.

**AW+ locks an account at five failed logins and every further failure re-arms the five-minute
timer.** A probe that opens u3 or u5 without the credential falls back to trying three default
passwords — the exact path that locked swi_b on 2026-10-21. The window is unattended, so waiting
is not an option either.

**The rule for this campaign:**

- **Before any call that would open u3 or u5, test `[ -f ~/.ckenv ]`.**
  - **Exists** → `. ~/.ckenv && tools/tb ...`. The value then never appears in argv, in a
    transcript or in the repo.
  - **Missing** → **do not open u3 or u5.** Run the case DUT-only if it can be, else mark it
    **BLOCKED** with the unblock written out: *"create `~/.ckenv` (chmod 600, outside the repo)
    holding `export CK_PASSWORD_U3=...` and `export CK_PASSWORD_U5=...`"*. A `--resume` picks it
    up with no re-triage.
- **Never put the password on a command line** — `ps` is readable by other users on this shared
  box. **Never put it in this repo**, in any form.

**Most of these cases do not need a partner switch.** The DUT is the authenticator, **tb277 is
the supplicant** (`wpa_supplicant`), and **the DUT runs its own local RADIUS server** — which is
exactly what T9032's authored precondition config does (`radius-server local` / `server enable`
/ `nas 127.0.0.1`). Establish that at triage before declaring anything blocked on a partner.

## Rules

- Verdicts, working logs, the `RESULT` line, the results list and the final log template:
  **[logged-output.md](../../logged-output.md)**. Final logs are made only by `/create-logs`.
- `STANDING-ORDERS.md` in full — especially **§7 (scapy, not ping)** and **§8 (a health read
  before step 1 and after the last step, every case)**. `/create-logs` refuses a case whose log
  has no sourced `HEALTH:` block.
- `platforms/x960.md` — §7E is AAA and RADIUS, measured 2026-10-20. **Read it before designing
  anything**: it already holds this platform's RADIUS behaviour.
- `MANUAL-ONLY.md` — a listed case or step is reported MANUAL-ONLY and never run unattended; a
  new person-needed step found here is added to it, dated.

## The eleven cases — and the three that have authored text

Read from `ck.db` on tb277, 2026-10-23. **Eight have no authored text at all** (`has_objective
= 0`, a 53-character empty-JSON placeholder), which is normal on this suite. **Three do**, and
two of those change the plan:

| case | title | authored? |
| --- | --- | --- |
| AWPTCM-T33369 | (210) ..._TwoStepAuthentication - Mac-based 1st then 802.1x 2nd | none |
| AWPTCM-T44279 | (218) ... - Tri-Authentication | **objective only**: *"Confirm that dot1,MAC authentications is possible."* No steps |
| AWPTCM-T9032 | EAP-TLS | 🔴 **objective + precondition + 15 steps**, `src=xml` (legacy corpus), status **Approved** |
| AWPTCM-T44277 | (214) ... - Supplicant MAC | none |
| AWPTCM-T33374 | (216) ... - Re-authentication option | none |
| AWPTCM-T44287 | (228) ..._CyptSecureMode - Disable Telnet, SNMPv1/v2, all privilege levels except 1 and 15, weak crypto (MD5, RSA1, DSA) | none |
| AWPTCM-T44270 | (177) ..._IEEE 802.1XEncryptionType - EAP-PEAP | none |
| AWPTCM-T33362 | (201) ..._DynamicVlan - Multiple Dynamic VLAN (Un-tag) | none |
| AWPTCM-T33368 | (209) ..._SMTP - SMTP server authentication | none |
| AWPTCM-T33354 | (191) ..._IEEE 802.1X - EAP-Notification | 🔴 **objective is literally `Not Support`** |
| AWPTCM-T33360 | (199) ..._IEEE 802.1XEncryptionType - Multiple Authentication | none |

🔴 **The bracketed number is NOT the TPS row.** On this suite the brackets run **+2 ahead** of
the TPS row number (measured 2026-10-22). **Never look one of these cases up by its bracketed
number** — read the TPS by feature name instead.

### 🔴 T33354's authored objective is `Not Support`

That is a strong signal the case is UNSUPPORTED **by design**, not by this bench. **Confirm it
against the TPS row for EAP-Notification and against the DUT's own CLI surface** before grading.
If the TPS says No, it is a desk UNSUPPORTED with the TPS line quoted as the proof. If the TPS
says **Yes** and the DUT lacks it, that is a **finding**, not a bench limit.

### 🔴 T9032 EAP-TLS — the authored steps cannot be followed on this bench, and that is recorded

The 15 authored steps are a **Windows PC driving Internet Explorer's certificate import wizard**
("Click Tool button… Click Contents tab… Click Import button…"). **There is no Windows PC on
tb277.**

**Test Engineer's decision, 2026-10-23: redesign with `wpa_supplicant` on tb277.** That measures
what the authored **objective** asks for — *"Confirm that an authenticator exchanges
authentication messages between the supplicant and Radius server"* — graded on the packet
exchange rather than on a GUI. **The log must say plainly that the authored GUI steps were not
followed, and why.** Do not pretend the authored procedure was run.

The authored **precondition** is still gold and should be used: it gives the local-RADIUS recipe
(`radius-server local`, `server enable`, `nas 127.0.0.1 key ...`, `user ... encrypted password`,
`crypto pki trustpoint local`, `crypto pki enroll local`) and the certificate export commands
the redesign needs:

```
crypto pki export local pem url flash:/localca.cer        # the CA certificate
crypto pki enroll local user <user>
crypto pki export local pkcs12 <user> flash:/<user>.p12   # the supplicant certificate
```

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| A | T33354 EAP-Notification; T44270 EAP-PEAP; T33360 Multiple Authentication; T9032 EAP-TLS | `dot1x-2026-10-23T1304` | **RUNNING** | The EAP / encryption-type family. **Build the local RADIUS server + supplicant rig ONCE as group setup** and let all four inherit it. T33354 is likely a desk UNSUPPORTED (`Not Support`) — confirm against the TPS, do not assume. T9032 is the redesign; use its authored precondition for the RADIUS and certificate recipe |
| B | T33369 Two-step (MAC then 802.1X); T44279 Tri-Authentication; T44277 Supplicant MAC; T33374 Re-authentication option; T33362 Multiple Dynamic VLAN (un-tag) | `authmodes-2026-10-23T1304` | QUEUED | Authentication modes and dynamic VLAN. Inherits group A's rig. 🔴 **T44277 "Supplicant MAC" may need the DUT to act as SUPPLICANT toward an authenticator** — that is the one case here most likely to need a partner switch, so it is the one most likely to hit the credential gate. Decide that at triage and say so. T33362 needs **two** dynamic VLANs assigned from RADIUS to different supplicants, untagged |
| C | T33368 SMTP server authentication | `smtp-2026-10-23T1304` | QUEUED | A different subsystem: the DUT authenticating to an **SMTP server**, not 802.1X. Needs an SMTP listener that requires AUTH. **tb277 almost certainly does not run one** — establish at triage what exists before designing, and grade on the SMTP dialogue on the wire (the `AUTH` verb and the server's reply), never on `show`. Starting a service on the box is a root change (STANDING-ORDERS §4) |
| D | T44287 CryptSecureMode | `securemode-2026-10-23T1304` | **BLOCKED (unattended) — safe half runs LAST as PARTIAL** | 🔴 **Test Engineer's decision: this case runs after every other row is DONE or BLOCKED**, so a DUT that comes back awkward costs nothing already measured. On AW+ secure mode disables telnet, SNMPv1/v2, most privilege levels and weak crypto, **needs a reboot, and can drop configuration**. **Before enabling anything, write the exact recovery steps into this file.** If recovery cannot be stated with confidence, report **BLOCKED** rather than risk an unrecoverable unit — the window is unattended |

Groups run **sequentially**: there is one DUT console. A, B, C, then D last.

## 🔴 What the bench already carries — do not mistake it for your own residue

Confirmed at the 2026-10-23 wrap of the previous campaign:

- **The L3 underlay is in startup-config**: vlan10 `10.38.22.34/27` (port1.0.10 ↔ box eth3),
  vlan48 `10.38.22.66/27` (port1.0.48 ↔ box eth4). **Campaign infrastructure — do not remove.**
- ✅ **`vlan 60` `ckMGMT-A` `10.38.22.97/27` on port1.0.2 (tagged) is in running- AND
  startup-config — and as of 2026-10-23 it is YOURS TO REMOVE if it is in your way.**
  The Test Engineer's instruction: *"If you have to remove vlan or change config on a switch
  because you need to execute the test, please dont ask me - just go ahead and do it"*.
  It is leftover campaign residue, not infrastructure. **If a case needs it gone, remove it
  (`no interface vlan60` / `no vlan 60`), say so in the working log, and say whether you put
  it back.** 🔴 It sits on `port1.0.2`, the RSTP **root port** — so **re-read
  `show spanning-tree brief` after removing it** and record what the tree did. If no case
  needs it gone, leave it: removing it is not an errand, it is a means to an end.
- swi_d: build `sin_x96056-20261019-27`, boot image `flash:/x960-tb277.rel` **(file exists)**,
  boot config `flash:/default.cfg` (file exists), autoboot disabled, standalone Ready Active
  Master. **That is the baseline every reload must return to.**
- Host NICs `eth2` (`10.38.22.1/27`), `eth3` (`10.38.22.33/27`), `eth4` (`10.38.22.65/27`), all
  carrier=1, each with a ULA IPv6. **Box `eth2` is cabled to swi_d's out-of-band `eth0`
  management port**, not to a switchport.
- 🔴 **swi_d's `eth0` link-local CHANGES ACROSS A REBOOT** (measured 2026-10-22). Do not cache it.
- 🔴 **`/tmp` on tb277 is 96 % full** (93 MB free). **1.8 G is `wireshark_eth4*.pcapng` belonging
  to someone else — NOT ours to delete.** Bound and filter every capture; clean up your own.
- 🔴 **swi_d has TWO power supplies**, outlets **1 and 8** on `10.36.230.212`. **One outlet alone
  cannot power-cycle it** — the cycle completes, both PSU bays still read `Ok`, and only
  **uptime** tells you nothing happened. A real power cut needs **both outlets together**.

## 🔴 Method rules carried forward — each has already cost a session

- **A LOGIN PROMPT IS NOT READINESS.** After any reload, ping every leg to **4/4** before reading
  it. This nearly inverted a verdict on 2026-10-21.
- **A TIMEOUT IS NOT A MEASUREMENT.** If an earlier leg of the same case did it faster, the
  **inconsistency is the finding** — extend the window and decode what is on the wire before
  writing a defect against the product.
- **Never chain `| exclude` onto `| include`** — AW+ swallows it silently and the output *looks*
  filtered (`platforms/x960.md` §7G). Save the output and filter it box-side.
- **`show cpu` never prints an idle percentage** on this platform. Record what it does print.
- **Frame-level evidence or it did not happen** (STANDING-ORDERS §7). Every counted leg carries a
  **control that must NOT match**, sent in the same run. For 802.1X that means: a supplicant that
  should fail, in the same window as the one that should succeed.
- **A `% ` line can be informational**, not an error (`show trigger` with none defined). Gate on
  proven state, never on the absence of `% `.
- **Two console calls in one tool block run sequentially** — start a capture with
  `run_in_background` FIRST, or drive both ends from one process.
- 🔴 **Prove an ABSENCE with `grep -c` in a `start-shell`, never with `| include`** — on this
  platform `show log permanent | include <pattern>` **never returns a prompt when nothing
  matches** (measured 2026-10-22, `platforms/x960.md` §7J.4).

## ✅ TRIAGE ANSWER, 2026-10-23 13:21 NZDT — 10 runnable, 0 blocked by topology, 1 blocked

Measured on swi_d through u2. No device state changed, no case run. **No case needs u3 or u5**,
so the credential gate binds nothing — it is open anyway.

### 🔴 TPS: all eleven read `Yes`. There is NO desk UNSUPPORTED in this campaign.

Read **by feature name, not by the bracketed number** — and the dispatch's warning proved
necessary: **the offset is not a stable +2.** Supplicant MAC and Re-authentication sit at **+1**,
Tri-Authentication at **+2**. By-number lookup would have mis-read three cases.

| case | TPS feature | row | supported |
| --- | --- | --- | --- |
| T33354 EAP-Notification | under IEEE 802.1X | 189 | **Yes** |
| T9032 EAP-TLS | | 192 | **Yes** |
| T44270 EAP-PEAP | | 194 | **Yes** |
| T33360 Multiple Authentication | | 197 | **Yes** |
| T33362 Multiple Dynamic VLAN(Un-tag) | | 199 | **Yes** |
| T33368 SMTP Server Authentication | Mail based | 207 | **Yes** |
| T33369 Mac-based (1st) then 802.1x (2nd) | | 208 | **Yes** |
| T44277 Supplicant MAC | | 213 | **Yes** |
| T33374 Re-authentication option | | 215 | **Yes** |
| T44279 Tri-Authentication | | 216 | **Yes** |
| T44287 Crypt Secure-mode | | 226 | **Yes** |

🔴 **T33354 — this queue's hypothesis was WRONG.** Its authored objective says `Not Support`, but
**TPS row 189 says `Yes` with no caveat**, and `show auth` / `show dot1x` / the local RADIUS
server all exist. There is no grounds for a desk UNSUPPORTED. **Measure it, and report the
authored-vs-TPS discrepancy whichever way it grades.**

🔴 **Do NOT grade T44287 off TPS row 129.** Row 129 is a different feature, plain "Secure Mode",
marked `No / Not required`. T44287's row is **226, "Crypt Secure-mode"**, matching the case title
word for word, and it reads **Yes**.

### The rig — measured

- **The DUT can be its own RADIUS server.** `radius-server local` exists; `show radius
  local-server` offers `nas | user | group | statistics | **trustpoint** | auth-mac-promiscuous`
  (trustpoint is the EAP-TLS hook). Current state `% Local RADIUS server not initialized` — a
  clean baseline. `platforms/x960.md` §7E.5 already records its methods: **eapmd5 | eaptls | mac
  | peap**, so EAP-TLS and PEAP are served natively. **T9032's authored precondition is the
  correct recipe** and was not re-derived.
- **Supplicant:** `/sbin/wpa_supplicant` **v2.6** + `wpa_cli` on tb277. No `eapol_test` (source
  builds only), which is fine — `wpa_supplicant -D wired -i ethN` is the right driver. scapy
  2.4.4 imports `EAPOL / EAP / EAP_TLS / EAP_MD5`; openssl 1.1.1; `sudo -n` available.
- **Certificates:** `crypto pki trustpoint`, `crypto key generate|destroy|pubkey-chain` all
  present. Triage deliberately did **not** enter `crypto pki trustpoint local` — per §7E.8,
  entering a named sub-mode **creates** the object, which is not read-only.
- 🔴 **Put the supplicant leg on eth4 ↔ port1.0.48, NOT eth3 ↔ port1.0.10.** Enabling dot1x
  blocks a port until authentication succeeds; on port1.0.10 that would **cut the vlan10 L3
  underlay mid-campaign**. vlan48/port1.0.48 keeps the box's path to the DUT intact.
- 🔴 **Use `/tftproot` (1.7 G free), not `/tmp` (91 MB)**, for certificates and pcaps.

### The four questions, settled

- **T44277 Supplicant MAC needs NO partner switch.** `auth supplicant-mac <MAC>` is an
  **authenticator-side** command in config-if: the DUT pre-authorises a named client MAC on its
  own port. The DUT is not the supplicant. This queue's note said the opposite; it was wrong.
- **T33362 Multiple Dynamic VLAN** — `auth dynamic-vlan-creation type **multi**` + `rule
  permit|deny`, plus `auth multi-vlan-session`. `type multi` means **two supplicants on the SAME
  port getting different RADIUS-assigned VLANs**, so it needs **two source MACs on one wire**,
  not two ports. Recommended: a scapy EAP-MD5 multi-supplicant helper (`tools/eapol.py`) driven
  through `tools/tb sudotool`, which also serves T33360, T33369, T33374, T44277 and every
  negative control. `wpa_supplicant` only where real crypto is needed (T9032, T44270).
- **T33368 SMTP is runnable with NO root change**, and this queue was wrong twice. tb277 *does*
  run Postfix on `0.0.0.0:25` (reachable at `10.38.22.33:25`) — but its EHLO advertises **no
  `AUTH`**, so as-is it cannot exercise the feature, and adding SASL to it *would* be root. It
  does not have to be Postfix: `mail smtpserver <ip> **port** <1-65535>` and `mail smtpserver
  authentication crammd5|login|oauth2|plain` exist, so run **our own Python listener on an
  unprivileged port** advertising `250-AUTH PLAIN LOGIN CRAM-MD5`, trigger with `log email`, and
  grade the `AUTH` verb and the server's reply **on the wire**. Postfix on 25 is a free negative
  control: a server offering no AUTH. New helper `tools/smtpsrv.py`.
- **T44287 — see the BLOCKED section below.**

### No forwarding loop — re-measured today, two instruments

`show spanning-tree brief` converged: root `8000:0000cd423029`, **one** root port (port1.0.2
Forwarding), redundant legs port1.0.4 / 1.0.14 / 1.0.16 Alternate/Discarding; port1.0.8, 1.0.10,
1.0.48 Designated/Forwarding. `show loop-protection`: 57 instances, every port `Normal`, none
loop-disabled.

⚠️ **Carry into every run: that loop-protection LDF stream is 1 packet/s across 57 instances.**
Any EAPOL capture **must** be filtered on `ether proto 0x888e` or it drowns.

### Probe

Exit 1 MISMATCH, 11 lines, **all artefact**: the deployed `/home/st-art/configs/tb277.setup` is
stale and still describes an older topology (`swi_a` on `/dev/u3`, a stack `stk_a`,
`swi_a`-to-`swi_a` portlinks). The three `CHECK_CABLE` NEEDS-CHECKs are a `--read-only` artefact
— the probe may not ping, so the box's MACs had aged out of the DUT's FDB. Both legs were
independently confirmed up, in their VLANs, Designated/Forwarding. **Nothing moved.** Cutting the
DUT-only run `.setup` makes all 11 lines disappear. `bench-state.md` was restored with
`git checkout --`; nothing committed.

### 🔴 T44287 — BLOCKED for this unattended window; the SAFE HALF runs last as PARTIAL

`show secure-mode` → **"Secure mode is disabled"** (clean baseline). `crypto secure-mode` and
`no crypto secure-mode` both exist on this build.

**The finding that turns the Test Engineer's ordering instruction into a product fact rather
than a precaution** — from the wiki's *Secure-mode Differences*:

> **"Radius — Normal: `radius-server local` is supported. secure-mode: `radius-server local` is
> NOT supported in secure mode."**

**Enabling secure mode removes the local RADIUS server that groups A and B are built on.** So
T44287 running last is **mandatory**, not merely prudent.

Enabling also: forbids telnet (and CR-84010 disables the telnet client); SNMPv3 only, no MD5 or
DES; privilege levels **1 and 15 only**, `enable password` then ≥8 characters; `show run
unencrypted` cannot run; NVS unreachable from IMISH; **PKI keys and certificates move
`/flash/.certs → /nvs/.certs`**; `rsa1` and `dsa` unsupported; SSH ciphers fixed except CBC;
TACACS+ groups disallowed; licence activation disallowed; FIPS becomes the default provider; NTP
MD5 unsupported; a `security_banner` is configured on first enable.

**Four things could not be established read-only, and the documentation is exhausted** (no AW+
command-reference page for `crypto secure-mode`; none of the nine `Feature Overview Guides/`
PDFs covers AAA, Port Authentication or Secure Mode):

1. whether enabling needs a reboot, and whether it reboots automatically or prompts;
2. whether enabling rewrites or discards startup-config, and whether `no crypto secure-mode`
   restores it;
3. whether group A's EAP-TLS trustpoint and keys survive the `/flash/.certs → /nvs/.certs` move
   and the move back;
4. 🔴 **whether console login still works afterwards.** If any login method list points at a
   local RADIUS server that secure mode has just withdrawn, that is `platforms/x960.md` §7E.1 —
   which has already cost a console on this exact unit. **No amount of PDU cycling fixes a login
   method list.**

**Decision (sentinel, under the Test Engineer's own instruction that an unattended window
reports BLOCKED rather than risking an unrecoverable unit):**

- **Run the safe half LAST and grade PARTIAL**: `show secure-mode` (disabled), the full CLI
  surface, `show post`, and the documented differences quoted — with the enable step recorded
  under `NOT RUN:` and the four unknowns above under `UNBLOCK:`. That banks real evidence and
  risks nothing. **Do NOT run `crypto secure-mode-selftest` unless it is first proven read-only**
  — the name is not proof.
- **The enable limb needs an ATTENDED window.** De-risking steps, short: `copy running-config
  flash:/pre-securemode.cfg`; confirm `aaa authentication login` is **local-only with a
  known-good local account**; confirm **both** PSU outlets 1 and 8 on `10.36.230.212` respond
  (one outlet alone cannot cut this unit); enable, and **read the device's own prompt verbatim
  before answering**; `show secure-mode` + `show boot` after. Recovery in order: `no crypto
  secure-mode` → reboot → `show secure-mode`; then `boot config-file
  flash:/pre-securemode.cfg`; last resort a **both-outlet** power cut.

### MANUAL-ONLY

Nothing in `MANUAL-ONLY.md` touched any of the eleven. **A step-level row was added for T9032**
(2026-10-23): the manual part is the authored IE certificate-import GUI steps; the automatable
part is **the whole objective** via the approved `wpa_supplicant` redesign. The file explicitly
supports step-level rows and says the agent still runs the automatable part, so this records the
gap **without** blocking the run the Test Engineer asked for.

### 🔴 For the Test Engineer — a permission rule, not a bench problem

`tools/tb precheck tb277 u2,u3,u5` was **denied by the permission classifier** ("Sensitive Remote
Exec"); the single-console form `tools/tb precheck tb277 u2` was allowed. Not load-bearing —
no case here needs u3 or u5 — but **a future campaign wanting a partner switch will need that
rule widened.** Nothing was worked around.

### vlan 60 — leave it

Under the new standing order it may be removed if a case needs it gone. **No case in this
campaign does.** It is tagged on port1.0.2, the RSTP root port, and the supplicant leg is
port1.0.48; removing it would re-converge the tree through the root port for no gain.


## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |

## Issues

### 🔴🔥 UNATTRIBUTED: snmpd SIGSEGV + an Unexpected System reboot on swi_d, 2026-10-23 12:49–12:55 NZDT

**Found by group A's `before` health read at 13:29 NZDT, the first thing it did. It pre-dates
this campaign and was caused by nothing we ran.**

```
2026 Oct 22 23:49:18 local7.debug awplus corehandler : Process snmpd (PID:1841) signal 11,
    core dumped to /flash/snmpd-swmrvl_armv8-sin_x96056-20261019-27-1-1792712958-1841.tgz

show reboot history:
    2026-10-22 23:55:56   Unexpected   System reboot      <-- 12:55 NZDT
    2026-10-22 23:53:17   Unexpected   System reboot      <-- 12:53 NZDT
    2026-10-22 01:10:14   Expected     CLI(user request)  <-- the last one of OURS, yesterday
```

🔴 **CORRECTED 13:30 NZDT: there are TWO unexpected reboots, not one.** The tester's
`NEEDS TEST ENGINEER:` line reported only the newest. The sentinel read the tester's own health
sample (`/tmp/dot1x1304/health-u2-20261023T132928.out`) after the narrator said "two", and the
second entry is there. **The sequence is: core at 12:49 -> unexpected reboot at 12:53 ->
unexpected reboot again at 12:55.**

**Two restarts two minutes apart is a different and worse signal than one.** One restart after a
segfault reads as a crash-and-recover; two in two minutes reads as a repeated fault or a short
boot-loop that settled. The unit has been stable for the ~37 minutes since.

Device times are **UTC, 13 h behind the box**: 23:49:18 UTC = **12:49 NZDT**, 23:55:56 UTC =
**12:55 NZDT**, both on 2026-10-23.

**The control that makes this new, not inherited:** the `/wrap-dt` of the previous campaign read
`show reboot history` at **10:11 NZDT today** and its newest entry was
`2026-10-22 01:10:14 **Expected** CLI(user request)`, with `show exception log` **None**. So both
events happened **after 10:11 and before triage at 13:21**, and neither appears in
`SESSION-HANDOVER-2026-10-23.md` or anywhere in this queue.

**Nothing of ours was on the box in that window.** This session did nothing between the wrap and
13:04, and that was a no-console `precheck`. A user was logged in on `pts/1`.

**Not established, deliberately:**
- **whether the crash CAUSED the reboot.** Seven minutes apart, snmpd segfaulting, then a
  restart — plausible, not proven. `show log` between 23:49 and 23:56 UTC would say more.
- what snmpd was doing. The 2026-10-20 campaign exercised SNMP heavily (T44308 RMON, T33413
  traps, T44309 sFlow), but that was three days earlier and the unit has rebooted since.

**Handling, agreed with no one because the window is unattended:**
- **Not blocking.** The tester recorded it as the **baseline** in every group A working log, so
  per-case health verdicts are **diffs against this state** — a NEW core or a NEW unexpected
  reboot is still caught.
- 🔴 **The core file stays on flash.** It is the only evidence and it must not be deleted until
  the Test Engineer has decided. It also consumes flash on a unit this campaign reloads.
- **For the Test Engineer:** whether this warrants its own investigation, whether the core should
  be pulled off the unit for a developer, and whether anyone was on the DUT at 12:49 NZDT.


