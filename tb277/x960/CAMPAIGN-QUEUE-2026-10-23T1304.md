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
| A | T33354 EAP-Notification; T44270 EAP-PEAP; T33360 Multiple Authentication; T9032 EAP-TLS | `dot1x-2026-10-23T1304` | **DONE — 3 PASS, 1 PARTIAL** | The EAP / encryption-type family. **Build the local RADIUS server + supplicant rig ONCE as group setup** and let all four inherit it. T33354 is likely a desk UNSUPPORTED (`Not Support`) — confirm against the TPS, do not assume. T9032 is the redesign; use its authored precondition for the RADIUS and certificate recipe |
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


## 🔴 GROUP A RIG — the bench setup all four cases inherit, and its EXACT restore recipe

Written by the group A tester (bench-runner) **before the first case**, per the dispatch, so a
fresh tester can restore the bench if this one dies mid-group. Group B inherits this rig.

### What the rig is

The DUT (`swi_d`, u2) is **both the authenticator and the RADIUS server**. The **supplicant is
the testbox**, on **eth4 ↔ port1.0.48** (never eth3/port1.0.10 — dot1x blocks a port until
authentication succeeds, and port1.0.10 carries the vlan10 L3 underlay).

The recipe is **T9032's authored precondition**, which is the gold source. 🔴 **The queue's own
short form in "The rig — measured" is INCOMPLETE: it omits `radius-server host 127.0.0.1`.**
The authored precondition has it, and it is load-bearing — `aaa authentication dot1x default
group radius` sends the NAS to the *RADIUS client* configuration, and with no `radius-server
host` there is no server for `group radius` to reach, local server or not. Both keys must match.

```
! --- the DUT as RADIUS CLIENT (what `group radius` dials) ---
radius-server host 127.0.0.1 key awplus-local-radius-server
aaa authentication dot1x default group radius
! --- the DUT as RADIUS SERVER ---
radius-server local
 server enable
 nas 127.0.0.1 key awplus-local-radius-server
 user <user> password <password>
 exit
! --- the authenticator port ---
interface port1.0.48
 dot1x port-control auto
 dot1x control-direction both
 exit
```

### 🔴 The trustpoint `local` ALREADY EXISTS — do NOT remove it in teardown

The dispatch warned that `crypto pki trustpoint local` **creates** the object on entry
(`platforms/x960.md` §7E.8) and said to remove it in teardown. **Measured on this unit, that
would have destroyed pre-existing device state.** Before this group touched anything:

```
awplus#show crypto pki trustpoint
Trustpoint "local"
   Type                 : Self-signed certificate authority (RSA + ECDSA)
   Root Certificate     : RSA:  C29CD492 253DF5BD F849819E F12866D8 792C90BE
                        : ECDSA: 906D4096 FB243C13 F727C758 7F41DF0D CBCF1FB5
   Local Server (RSA)   : Enrolled with this trustpoint.
   Local Server (ECDSA) : Enrolled with this trustpoint.
   Server Key           : RSA: server-default
                        : ECDSA: server-default-ecdsa
```

and `show crypto key mypubkey rsa` already lists the RSA key pair `server-default` bound to
trustpoint `local`. **Yet `show running-config | include crypto` returns NOTHING** — the
trustpoint and its keys are persistent PKI state on flash, *not* configuration. So:

- entering `crypto pki trustpoint local` on THIS unit **does not create** anything;
- `no crypto pki trustpoint local` would **delete a pre-existing CA and its key pair**, which no
  case here asked for. **It is NOT in the restore recipe.** T9032 enrolls a *user* under the
  existing trustpoint and removes only that user's artefacts.

### The exact restore recipe

🔴 **Nothing in this group runs `write`.** `startup-config` stays `flash:/default.cfg` untouched
throughout, so **a reload or a (both-outlet) power cut is itself a complete restore**. That is
the backstop; the CLI recipe below is the normal path.

```
configure terminal
 interface port1.0.48
  no dot1x port-control
  no dot1x control-direction
  no auth host-mode
  no auth max-supplicant
  no auth dynamic-vlan-creation
  no auth multi-vlan-session
  no auth supplicant-mac
  no auth reauthentication
  no auth two-step
  exit
 no aaa authentication dot1x default
 no radius-server local
 no radius-server host 127.0.0.1
 end
! certificate artefacts T9032 exports (ONLY these; never the trustpoint itself):
delete force flash:/localca.cer
delete force flash:/<user>.p12
! and on the DUT, if T9032 enrolled a PKI user:
configure terminal
 crypto pki trustpoint local
  no crypto pki enroll local user <user>     ! see T9032's log for the exact negation measured
  end
```

**Proof of restore, in this order:** `show auth` must read all three of 802.1X / MAC-based /
WEB-based **Disabled**; `show radius` must read `No RADIUS servers currently defined`;
`show radius local-server nas` must be **empty**; `show running-config | include radius|dot1x|aaa`
must show only the two baseline lines `aaa authentication enable default local` and
`aaa authentication login default local`; and `show crypto pki trustpoint` must still list
**all three** trustpoints `default-selfsigned`, `default-system`, `local`.

### The bench baseline this group started from (2026-10-23 13:28–13:32 NZDT, u2)

| thing | value |
| --- | --- |
| build | `sin_x96056-20261019-27`, build date Sun Oct 18 23:18:21 UTC 2026 |
| boot image / config | `flash:/x960-tb277.rel` (exists) / `flash:/default.cfg` (exists), autoboot disabled |
| uptime at group start | 0 days 00:33:15 — i.e. booted 2026-10-22 23:55 UTC |
| DUT clock vs box clock | DUT `Fri, 23 Oct 2026 00:28:58 +0000` vs box `Fri 23 Oct 2026 00:29:12 UTC` — agree within the read latency, no offset to correct for |
| `show auth` / `show dot1x` | 802.1X, MAC-based and WEB-based all **Disabled** |
| `show radius` | `No RADIUS servers currently defined`; `show radius local-server nas` empty |
| `show running-config \| include crypto` | **empty** |
| `show running-config \| include aaa` | `aaa authentication enable default local` / `aaa authentication login default local` |
| port1.0.48 | `switchport mode access` / `switchport access vlan 48` (vlan48 `ckUNDERLAY-eth4`) |
| port1.0.10 | `switchport mode access` / `switchport access vlan 10` (vlan10 `ckUNDERLAY-eth3`) |
| both legs | ping 4/4 each: box eth4 → 10.38.22.66, box eth3 → 10.38.22.34 |
| spanning tree | root `8000:0000cd423029`, root port port1.0.2 Forwarding; port1.0.10 and port1.0.48 Designated/Forwarding |
| vlan 60 | present (`ckMGMT-A`, port1.0.2 tagged) — **left alone**, no case here needs it gone |

### Gate record (group A, 2026-10-23 13:27–13:32 NZDT)

| gate | result |
| --- | --- |
| 1 occupancy | `tools/tb precheck tb277 u2` → `/dev/u2` **free**; exit 5 for one FOUND item, `ser2net` pid 744 (root, up 42 d) — **the standing adjudication** (maps only ttyS0/ttyS1, holds no USB console; the 2026-10-23 handover lists it as expected). Not touched |
| 2 console state | probe opened u2 at 115200, banner `awplus`, hostname `awplus`, exec prompt. Not parked in config mode, not at a shell |
| 3 template path | `tools/tb template tb277` → `/nfsHome not mounted`, **no deployed `tb277.setup`** — expected and correct for this box; never bind one |
| 4 probe | `--read-only`, run `.setup`, exit **2 NEEDS-CHECK**: 2 × `CHECK_CABLE` on eth3 and eth4. **Both are the known `--read-only` artefact** (the probe may not ping, so the box's MACs had aged out of the DUT's FDB) and **both were disproved immediately**: ping 4/4 on each leg. Nothing moved. `bench-setup/tb277/bench-state.md` was regenerated by the probe and restored with `git checkout --`; **not committed** |
| 5 run `.setup` | `tb277/x960/dot1x-2026-10-23T1304/tb277-u2.setup`, swi_d only |
| 6 preflight | **N/A — no framework script in this group.** All four cases are console + host-traffic cases driven through `tools/tb`; `pt_preflight.py` has nothing to check |
| 7 boot baseline | `flash:/x960-tb277.rel` + `flash:/default.cfg`, autoboot disabled — recorded, to be re-read after the group |
| 8 Ask-CK server path | not used |
| 9 sentinel | `sentinel: parent` — nothing to arm |
| 10 CLI defaulting | N/A (no framework defaulting step). The config-if surface was still probed read-only with `qmark`: `dot1x port-control {auto\|force-authorized\|force-unauthorized}` and `auth host-mode {single-host\|multi-host\|multi-supplicant\|host-plus-voice}` all confirmed present before any of it was sent |

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |
| AWPTCM-T44270 | (177) Authentication&Security_IEEE 802.1XEncryptionType - EAP-PEAP | dot1x-2026-10-23T1304 | **PASS** | EAP-PEAP authenticates a valid supplicant on port1.0.48 against the DUT's own local RADIUS server, graded on frames: **24 EAPOL frames ending in EAP-Success, port Unauthorized -> Authorized, dataplane 0/4 -> 4/4**. **Both controls in the same window are refused** -- wrong password 22 frames EAP-Failure 0/4, unknown identity 22 frames EAP-Failure 0/4 -- and S5 authenticates again afterwards, so the refusals are the feature working, not the rig breaking. Five legs, each matching its declared expectation, from an S0 feature-OFF baseline of 4/4. **Measured, not assumed:** the local server is freeradius and PEAP's inner method is **MSCHAPv2**, and the TLS tunnel is served by the unit's own `local` trustpoint (CA `/O=Allied Telesis, Inc./CN=AlliedWarePlusCAA2WQS700B`, this unit's serial in the CN). Two anomalies recorded rather than smoothed over, neither changing the verdict: (a) the session's FIRST PEAP attempt failed where five identical later ones did not -- the Access-Request never reached the server (statistics all zero), a NAS rejection of a response belonging to a superseded EAP session; it has not recurred since every leg was preceded by `dot1x initialize interface port1.0.48`, now the group's method. (b) 🔴 **A TOOL TRUST ISSUE, not graded on**: control B's first run printed 22 frames and `MATCH` exit 0 while the JSON beside it recorded `"verdict": "timeout"`, `"eapol_frames": 2`. Nothing in `wpasup.py` can produce that. The leg was re-run unchanged as S4b, whose stdout and JSON agree with each other and with S4's stdout, and **S4b is what was graded**; the inconsistent JSON is kept as the record and `tools/README.md` now warns to check wpasup.py's JSON against its printed RESULT. Counter note so nobody redoes it: the local server counts **twice per PEAP authentication** (outer + inner), so three successes read `Successes: 6`; an unknown identity never gets a user-table row, so its failures are in the global total but attributable to nobody. Health twice, after-diff **CLEAN**: no new reboot, exception log unchanged from the dirty baseline, 0 new non-echo log lines, memory +10.6 MB which is radiusd now running. Run labelled **clean**. Nothing written to startup-config; vlan 60 untouched; no PKI object created or removed. New helpers `tools/wpasup.py` and `tools/eapol.py`, both with README entries in the same commit (`639f33b`). | dot1x-2026-10-23T1304/T44270/work/run1.log | tester |
| AWPTCM-T33360 | (199) Authentication&Security_IEEE 802.1XEncryptionType - Multiple Authentication | dot1x-2026-10-23T1304 | **PASS** | `auth host-mode multi-supplicant` authenticates multiple supplicants **independently** on one port, proved by changing only the mode: **single-host admits 1 of 2** (the second gets **silence** — no challenge, no EAP-Failure, nothing in 40 s), **multi-supplicant admits 2 of 2, then 3 of 3** MACs Authenticated. Authorization is **per-MAC, not per-port**: the host's own unauthenticated MAC pinged **0/4** while crafted MACs were Authenticated on the same port at the same moment, then **4/4** once it authenticated. The bad-credential control shared a **single 1.04-second packet window** with the legs it controls for, and `show auth supplicant brief` showed all three at once: two `Authenticated`, one `Held`. Also measured: one RADIUS identity can hold several concurrent supplicant sessions on different MACs; the DUT does not keep a failed supplicant's identity in the table (its log does). 🔥 **PRODUCT FINDING the case did not ask for: `auth host-mode multi-supplicant` SILENTLY REWRITES `dot1x control-direction both` to `in`** — no warning, no `% ` line, no log entry — **and `no auth host-mode` restores single-host but does NOT restore `both`**, so the port stays ingress-only for good. Defensible (egress cannot be gated per-MAC on a shared port) but an operator who chose `both` for a security reason is never told it was weakened. Same shape as the known `spanning-tree mode` behaviour that silently drops `no spanning-tree <mode> enable`. `both` was restored explicitly and re-read. Health twice, **CLEAN**: no new reboot, exception log unchanged from the pre-existing dirty baseline, 0 new non-echo log lines, memory finished 348 kB MORE free than it started. | dot1x-2026-10-23T1304/T33360/work/run1.log | tester |
| AWPTCM-T9032 | EAP-TLS | dot1x-2026-10-23T1304 | **PARTIAL** | 🔴 **The 15 authored steps were NOT followed and the log says so in its first section**: they are a person clicking through Internet Explorer's certificate import wizard on a Windows PC (`Environment: Windows PC`), and there is none on tb277. Redesigned with `wpa_supplicant` at the Test Engineer's decision; a step-level MANUAL-ONLY row already exists. Graded on the authored **objective**, which is **MET on the wire**: EAP-TLS (method 13) negotiated after a Legacy-Nak from MD5-Challenge; the server's **2520-byte flight fragmented and reassembled exactly per RFC 5216** (flags `0xc0 LM msglen=2520` twice, then `0x80 L`, with correct 6-byte empty ACKs back); and the server chain **validated against a CA exported from this very unit** (CN carries the serial `A2WQS700B`). The whole provisioning path works end to end. 🔥 **Best measurement in the case: the DUT VALIDATES CLIENT CERTIFICATES.** A self-signed cert with the same identity but a different issuer is refused with an **EAP-Failure frame at 1.045 s**, confirmed in the DUT's own log — a positive decision on the wire, and it disposes of any idea the DUT cannot conclude an EAP-TLS exchange. **NOT concluded:** EAP-Success on a valid certificate. Diagnosed to the bottom and **it is the SUPPLICANT, not the DUT**: `wpa_supplicant` 2.6 predates TLS 1.3 and RFC 9190 while OpenSSL 1.1.1 beneath it negotiates TLS 1.3 (`ver=0x304` in its own log), so the client's handshake completes when it sends its Finished — `Handshake finished`, `EAP-TLS: Done`, keys derived — with 743 of 2141 bytes still unsent, and it then **DISCARDs the DUT's correct empty ACK**, twice. Every frame the DUT sent is correct, and it was confirmed responsive with a known-good PEAP authentication both mid-case and as the last act. Three workarounds recorded as negative results: `fragment_size` had no effect, an ECDSA credential gave `msglen=2141` unchanged to the byte, and the DUT exposes **no TLS-version control**. **UNBLOCK, cheapest first and needing no root:** the exported PKCS#12 carries **the CA as well as the leaf** (proved from the supplicant's log), which is what makes the flight two fragments — the control's single certificate was 1224 bytes, one fragment, and concluded fine, so **split the p12 and present a leaf-only credential**; failing that `wpa_supplicant` 2.10+ (root, the Test Engineer's); capping TLS at 1.2 is impossible on the DUT and root on the box. Three traps for anyone following the authored precondition, all measured: `crypto pki` is **EXEC-only** here (config mode offers only `trustpoint`); `crypto pki enroll` asks for an export passphrase **twice as free text**, which no console driver could answer — hence `ckcon.py`'s new `@ask` directive; and the export syntax has no `url` keyword, requires a key type for pkcs12, and adds **`pem terminal`**, which emits the CA to the console and removes the need for any file transfer. Health twice, **CLEAN**. No `write`. The pre-existing `local` trustpoint was **not** removed and is excluded from the restore recipe on purpose. (`de19a1f`) | dot1x-2026-10-23T1304/T9032/work/run1.log | tester |
| AWPTCM-T33354 | (191) Authentication&Security_IEEE 802.1X - EAP-Notification | dot1x-2026-10-23T1304 | **PASS** | 🔥 **The authored objective `Not Support` is WRONG; TPS row 189 (`Yes`) is right.** Had the objective been taken at face value this would have been graded UNSUPPORTED without a packet being sent. An **A/B pair differing in exactly ONE server flag** — same server, same user, same supplicant MAC, same port: **control (no `--notify`) 6 EAPOL frames, no notification anywhere** (the server's own counter reads `NOTIFICATIONS SENT=0`), EAP-Success 1.03 s; **`--notify` 8 frames**, the two extra being the Notification Request and its Response. Four things proved: the authenticator **relays** EAP-Request/Notification to the supplicant; the text survives **byte for byte** (50 bytes in, 50 bytes out, raw Type-Data decoding to the exact distinctive string given to the server); the supplicant's mandatory **empty** EAP-Response/Notification (RFC 3748 §5.2) is relayed **back** — the server logged `EAP code=2(Response) type=Notification len=0`, so the relay works in **both** directions; and it is informational, the exchange continuing to MD5 and EAP-Success in the same time as the control. Leg C put two supplicants in one invocation against the notifying server: **both** got the notification, the right password got EAP-Success at 1.05 s and the wrong one EAP-Failure at 0.05 s — a notification rescues nobody. ⚠️ **The DUT's own log shows NO trace of the notification** — not the text, not that one passed through — so only the wire and the RADIUS server can evidence this feature. 🔴 **The T33360 `control-direction` finding REPRODUCED independently here**, hours after `both` had been explicitly restored and verified: `auth host-mode multi-supplicant` (set for leg C) again silently rewrote it to `in`. Second clean observation, different case. New tool **`tools/radeap.py`** with its README entry — a RADIUS server speaking EAP-Identity, EAP-Notification and EAP-MD5 with Message-Authenticator (RFC 3579) and State on every reply, unprivileged on 11812 so **no root**; `radsrv.py` is PAP only and cannot carry an EAP-Message, and the DUT's own local server has no command that emits a notification. Health twice, **CLEAN**; memory finished 2712 kB MORE free. Fully restored and verified. The **login** method list was never touched (x960.md §7E.1). (`33de1ef`) | dot1x-2026-10-23T1304/T33354/work/run1.log | tester |


### 🔴 TOOLING DEFECT, found and FIXED 2026-10-23 — `tools/tb killmine` could not kill ANY root sudotool

Not a case result; it affects **every campaign on every box**, so it is recorded here.

**`killmine` could not kill any root `sudotool` run** — not only `eapol.py` but `linerate`,
`l2flows`, `vsend`, `igmp`, `dhcp4`, every member of `SUDO_TOOLS`. Two independent reasons:

1. a sudotool runs **as root**, so an unprivileged `readlink /proc/<pid>/cwd` returns empty and
   the cwd branch can never match;
2. the wrapper launches it as `cd /tmp/<x>/tools && sudo -n python3 <tool>.py` — a **relative**
   command line — so the absolute-path branch cannot match either.

Even past identification, the kill only allowed `sudo -n kill` for pytest-create paths. It was
hit live: a hung `eapol.py` holding eth4 promiscuous, which **closing the local ssh did not
kill**.

**Fixed in commit `788205b`**: a `sudo -n readlink` fallback for the cwd, acceptance of a
`sudo -n python3 <tool>.py` command line, and `sudo -n kill` for a **root** process that
identification has **already established is ours**. The refusals that matter are untouched —
minicom / screen / tmux, and any other user's process — which is the property that counts,
since every session here runs as the same Unix user. Verified live: `tb: 17344 stopped`.

### 🔧 Two `tools/eapol.py` bugs, found BEFORE any measurement, both now in `tools/README.md`

- 🔴 **Never read EAP Type-Data from scapy's `eap.payload`.** scapy dissects a MD5-Challenge into
  its own `EAP_MD5` class, so the challenge sits in a **field** and `eap.payload` holds only the
  **Ethernet padding** an EAPOL frame gets to reach 60 bytes — 37 bytes of it on a
  Request/Identity. The digest then hashes **no challenge at all**, the frame is perfectly well
  formed, and the server says only `Login incorrect`. **What settled whose fault it was in one
  step:** run the same credential through `wpa_supplicant --method md5`, whose EAP-MD5 is beyond
  doubt. It succeeded first time, so the server was fine and the tool was wrong. **A second
  instrument is the cheapest way to tell a tool defect from a product one.**
- A scapy `L2socket.recv()` **blocks on an idle wire**, so `--timeout` did nothing and a
  `--timeout 25` run was still alive 11 minutes later. Fixed with `select`.


### 🔧 Three traps for anyone following T9032's authored precondition on this build (measured 2026-10-23)

The authored precondition is from the legacy `xml` corpus and does not match this build:

- **`crypto pki` is EXEC-only.** Config mode offers only `trustpoint`. The authored text shows
  these commands in a config context.
- **`crypto pki enroll` asks for an export passphrase TWICE, as FREE TEXT.** No console driver
  could answer that — `ckcon.py` could handle `(y/n)` confirmations and nothing else. Hence its
  new **`@ask` directive**, which answers an arbitrary prompt. That is reusable for every future
  case with a free-text prompt.
- **The export syntax differs**: there is no `url` keyword, pkcs12 requires a key type, and
  there is **`pem terminal`**, which emits the CA straight to the console and **removes the need
  for any file transfer at all** — simpler than the authored `export ... url flash:` route.

### 📋 A SENTINEL ERROR worth recording, because the lesson is about reporting, not about EAP

Mid-case I directed the tester to stop debugging T9032 and grade it PARTIAL, on the grounds that
its observations of the same leg contradicted each other — a completed handshake at 14:41, then
"only EAPOL-Start, no server response" at 14:44 and 14:47.

**The captures were never inconsistent.** All five runs of that leg produced **exactly 17 EAPOL
frames with an identical shape, stalling at the identical point**. What reached the sentinel was
the tester's own `grep` of the tool's stdout, narrowed to a couple of lines — so the sentinel was
reading the filter, not the capture, and drew the obvious (wrong) conclusion from it.

The direction was stood down within a minute, before it was acted on, once the rogue-certificate
result showed the tester was a step ahead. **The rule both sides took from it: when a leg is in
dispute, send the frame table, not a grep of it.** A narrowed view of good evidence is
indistinguishable from bad evidence.
| AWPTCM-T33374 | (216) Authentication&Security - Re-authentication option | authmodes-2026-10-23T1304 | **PASS** | Re-authentication happens **on time at the configured period** and **stops when removed** — measured on the wire, never from `show`. The frame count is a straight function of the period: **OFF 6 frames / 1 authentication in 106 s; 15 s → 31 frames, six authentications at 15.03 s; 30 s → 26 frames, intervals 30.049 / 30.044 / 30.048 / 30.049 s; 60 s → 16 frames, intervals 60.070 / 60.068 s** — within 70 ms of the configured value. The authenticator **initiates each cycle unsolicited** and runs a **full EAP exchange with a fresh challenge and new EAP ids** every time, and the **session never drops** (port `Authorized`, supplicant `Authenticated` at four samples across the window). **Second witness:** the DUT's own RADIUS server counted **+6 Successes** for the six authentications seen on the wire, to the unit. **Removal limb:** `no auth reauthentication` returns the port to **6 frames in 76 s — identical to the OFF control — with `reauth-period` STILL configured**, so it is the enable that governs, not the period value. Restored field by field and verified; health twice, **CLEAN** against the pre-existing dirty baseline; no `write`. | authmodes-2026-10-23T1304/T33374/work/run1.log | tester |

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

### 🔴 PRODUCT FINDING: `auth host-mode multi-supplicant` silently rewrites `dot1x control-direction`

**Observed TWICE, in two different cases, hours apart — T33360 and again in T33354.**

`dot1x control-direction both` was configured on port1.0.48 in T44270 and verified in the
running-config. Setting `auth host-mode multi-supplicant` rewrote it to `dot1x control-direction
in` with **no warning, no `% ` line and no log entry**. `no auth host-mode` restores `hostMode:
single-host` but **does NOT restore `both`** — the port stays ingress-only control permanently.

It is technically defensible: egress on a shared port cannot be gated per supplicant MAC. **The
silence is the defect, and the non-restoration on removal more so** — an operator who chose
`both` for a security reason has had it weakened and is never told. Same shape as the known AW+
behaviour where a `spanning-tree mode` change silently drops `no spanning-tree <mode> enable`.

Restored explicitly both times. For `platforms/x960.md` and a memory at the wrap.

### ⚠️ EAP-TLS cannot be concluded from this bench until the supplicant is newer (T9032)

Not a DUT fault — every frame the DUT sent was correct, and it refused an untrusted client
certificate with an EAP-Failure in 1.045 s. `wpa_supplicant` on tb277 is
`2:2.6-15ubuntu2.8`, which predates TLS 1.3 and RFC 9190, while OpenSSL 1.1.1 beneath it
negotiates TLS 1.3. The supplicant therefore completes its handshake with a fragment still
unsent and discards the authenticator's correct request for it.

**Cheapest unblock needs no root and should be tried first:** the DUT's PKCS#12 export carries
the CA as well as the leaf, which is what makes the client flight need two fragments. Split it
and present a leaf-only credential. Otherwise `wpa_supplicant` 2.10+ (a root change on the box,
STANDING-ORDERS §4).

### ⚠️ `tools/tb killmine` could not kill ANY root `sudotool` run — FIXED in this group

A `sudotool` process is root, so an unprivileged `readlink /proc/<pid>/cwd` returned empty and
killmine's cwd branch never matched; and the wrapper launches it with a RELATIVE command line
(`cd /tmp/<x>/tools && sudo -n python3 <tool>.py`), so the absolute-path branch never matched
either. Even past identification, the kill only allowed `sudo -n kill` for `pytest-create`
paths. **This affected every root traffic tool** — `linerate`, `l2flows`, `vsend`, `igmp`,
`dhcp4` — not just the new ones. Hit for real with a hung `eapol.py` holding eth4 promiscuous;
closing the local ssh did not kill it.

Fixed (`788205b`): `sudo -n readlink` fallback for the cwd, accept a `sudo -n python3 <tool>.py`
command line, and `sudo -n kill` for a **root** process that identification has already
established is ours. The refusal for `minicom`/`screen`/`tmux` and for any other user's process
is untouched. Verified live on the stuck PID.

### ⚠️ One `wpasup.py` artefact inconsistency that was never explained (T44270)

Control B's first run printed 22 EAPOL frames and `got failure -- MATCH`, exit 0, while the JSON
it wrote alongside recorded `"verdict": "timeout"` and `"eapol_frames": 2`. Nothing in the code
can produce that — both are final before the JSON is built. **Not graded on**: the leg was
re-run unchanged, the re-run is internally consistent, and that is what was graded. The JSON is
kept on the box at `/tmp/dot1x1304/T44270-S4-peap-nouser.json` as the record, and
`tools/README.md` warns to check wpasup.py's JSON against its printed RESULT. If it recurs it
should be treated as a real tool defect. (The tool now writes its JSON exactly once, after the
verdict is final, which removes one possible mechanism.)

## 🔴 Bench state as group A hands over to group B

Group A deliberately leaves its rig in place — group B inherits it. The full restore recipe is
in **`## GROUP A RIG`** above and nothing in this group ran `write`, so `startup-config` is still
`flash:/default.cfg` and **a reload is itself a complete restore**.

Verified at 15:11 NZDT after the last case:

| thing | state |
| --- | --- |
| boot | `flash:/x960-tb277.rel` (exists) / `flash:/default.cfg` (exists), autoboot disabled — the baseline, unchanged |
| `show auth` | 802.1X **Enabled**, MAC-based Disabled, WEB-based Disabled |
| `show radius` | `127.0.0.1` only — T33354's testbox server entry and its `ckbox` group are gone |
| `show radius local-server user` | 4 users: `ckmulti1`, `ckmulti2`, `ckpeap`, `cktls` — **the rig, left for group B** |
| port1.0.48 | `dot1x port-control auto`, `dot1x control-direction both`, **no** `auth host-mode` line |
| trustpoints | all three present: `default-selfsigned`, `default-system`, `local` — the pre-existing `local` CA was **not** touched, and user `cktls` stays enrolled under it |
| vlan 60 | untouched (no case needed it gone) |
| vlan10/vlan48 L3 underlay | untouched |
| host NIC `eth3` → 10.38.22.34 | **ping 4/4** |
| host NIC `eth4` → 10.38.22.66 | **ping 0/4 — EXPECTED, not a fault** |
| probe | exit 2 NEEDS-CHECK, the same 2 `CHECK_CABLE` lines as before the group — **no change** |
| anything still running on the box | **nothing of ours.** The only `wpa_supplicant` is the system D-Bus daemon, pid 606, up since 11 Sep |

🔴 **Two things group B must not misread:**

1. **`eth4` pings 0/4 and port1.0.48 shows `Disabled / Discarding` in `show spanning-tree
   brief`. That is 802.1X doing its job, not a cable or a port fault.** The port is
   dot1x-controlled and no supplicant is currently authenticated. It goes to 4/4 and Forwarding
   the moment one authenticates, which every group B case does as its first act.
2. The probe's two `CHECK_CABLE` lines are therefore **expected** for eth4 now, and remain the
   known `--read-only` artefact for eth3 (the probe may not ping, so the box's MACs age out of
   the DUT's FDB). eth3 was confirmed at 4/4 by hand. Nothing moved.

## 🔴 GROUP B RIG — `authmodes-2026-10-23T1304`, written BEFORE the first case

Group B **inherits group A's rig unchanged** and adds nothing to it at group level. Everything
group B configures is **per case, on `interface port1.0.48` only**, and is removed at the end of
that case. Written here so a fresh tester can restore the bench if this one dies mid-group.

### The rig as group B found it (measured 2026-10-23 15:18 NZDT / 02:18 UTC, u2)

| thing | value |
| --- | --- |
| build / boot | `sin_x96056-20261019-27`; `flash:/x960-tb277.rel` (file exists) / `flash:/default.cfg` (file exists), autoboot disabled — **the baseline** |
| uptime | 0 days 02:22:57 — same boot as group A's, **no new reboot** |
| DUT clock vs box | DUT `Fri, 23 Oct 2026 02:18:43 +0000` vs box `Fri 23 Oct 2026 02:18:57 UTC` — agree within read latency |
| `show auth` | 802.1X **Enabled**, MAC-based Disabled, WEB-based Disabled; RADIUS auth server `127.0.0.1:1812` |
| `show radius` | one host `127.0.0.1` auth 1812 acct 1813 |
| `show radius local-server user` | 4 users: `ckmulti1`, `ckmulti2`, `ckpeap`, `cktls` — group A's, reused by group B |
| `show radius local-server nas` | one NAS `127.0.0.1` |
| `running-config \| include radius` | `radius-server host 127.0.0.1 key <enc> encrypted` / `aaa authentication dot1x default group radius` / `radius-server local` |
| `running-config \| include aaa` | the two baseline lines + `aaa authentication dot1x default group radius` |
| port1.0.48 | `switchport mode access` / `switchport access vlan 48` / `dot1x port-control auto` / `dot1x control-direction both` |
| `show auth interface port1.0.48` | portStatus **Unauthorized**; reAuthenticate **disabled**, reAuthPeriod 3600; hostMode **single-host**; CD adminControlledDirections **both**; dynamicVlanCreation / multiVlanSession / twoStepAuthentication / authMac / authWeb all **disabled**; supplicantMac **none** |
| vlan 60 / vlan10 / vlan48 | untouched |

### The one-line restore for group B

🔴 **Nothing in group B runs `write`.** `startup-config` stays `flash:/default.cfg`, so **a
reload (or a BOTH-outlet power cut, outlets 1 and 8 on 10.36.230.212) is itself a complete
restore** of the whole bench, group A's rig included. That is the backstop.

### The CLI restore recipe — group B's own additions, removed per case

Run at the end of EVERY case in this group, then verified with one
`show auth interface port1.0.48` (the single read that shows every knob below at once):

```
configure terminal
 interface port1.0.48
  no auth reauthentication           ! T33374
  no auth timeout reauth-period      ! T33374  (returns reAuthPeriod to 3600)
  no auth supplicant-mac             ! T44277
  no auth two-step                   ! T33369
  no auth dynamic-vlan-creation      ! T33362
  no auth multi-vlan-session         ! T33362
  no auth host-mode                  ! T33362 / T44279
  no auth-mac enable                 ! T33369 / T44279
  no auth-web enable                 ! T44279
  dot1x control-direction both       ! 🔴 ALWAYS, EXPLICITLY -- see below
  end
```

🔴 **`dot1x control-direction both` is re-sent explicitly at the end of every case that touches
`auth host-mode`,** because of the standing finding: `auth host-mode multi-supplicant` silently
rewrites it to `in` and `no auth host-mode` does not put it back. Verified by reading
`CD: adminControlledDirections: both` back out, not by assuming.

**Proof of restore for group B (after the LAST case):** `show auth interface port1.0.48` must
read exactly the baseline row above — reAuthenticate disabled / reAuthPeriod 3600 / hostMode
single-host / CD both / dynamicVlanCreation, multiVlanSession, twoStep, authMac, authWeb all
disabled / supplicantMac none — and `show running-config interface port1.0.48` must hold only
the four baseline lines. **Group A's rig (`radius-server local`, the four users, the NAS, the
`local` trustpoint, `aaa authentication dot1x default group radius`) is LEFT IN PLACE** for
group C/D; group A's own recipe above removes it when the campaign is done with it.

### Group B gate record (2026-10-23 15:17–15:19 NZDT)

| gate | result |
| --- | --- |
| 1 occupancy | `tools/tb precheck tb277 u2` → `/dev/u2` **free**; exit 5 for the one standing FOUND item, `ser2net` pid 744 (root, up 42 d) — the standing adjudication, not touched. `tools/tb scratch tb277 authm1304` → 79 files |
| 2 console state | `tools/tb peek` → `awplus#`, exec prompt. Not in config mode, not at a shell |
| 3 template path | `tools/tb template tb277` → `/nfsHome not mounted`, no deployed `tb277.setup` — expected for this box; none bound |
| 4 probe | `--read-only`, group B run `.setup`, exit **2 NEEDS-CHECK**: **one** `CHECK_CABLE`, on **eth4** only. 🔴 **Expected and predicted by group A's handover** — port1.0.48 is dot1x-controlled with no supplicant authenticated, so the box's MAC is not in the FDB. eth3's artefact of the morning is **gone** (its MAC is learned again). Nothing moved. `bench-setup/tb277/bench-state.md` regenerated **byte-identical** (`git status` clean) — nothing to restore, nothing committed |
| 5 run `.setup` | `tb277/x960/authmodes-2026-10-23T1304/tb277-u2.setup`, swi_d only, cut from group A's |
| 6 preflight | **N/A — no framework script.** All five cases are console + host-traffic cases driven through `tools/tb` |
| 7 boot baseline | `flash:/x960-tb277.rel` + `flash:/default.cfg`, autoboot disabled — re-read at the group's end |
| 8 Ask-CK server path | not used |
| 9 sentinel | `sentinel: parent` — nothing to arm |
| 10 CLI defaulting | N/A (no framework defaulting step). Each case probes its own commands with `qmark` read-only before sending them |
