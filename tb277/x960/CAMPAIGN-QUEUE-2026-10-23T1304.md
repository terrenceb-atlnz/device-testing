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
| A | T33354 EAP-Notification; T44270 EAP-PEAP; T33360 Multiple Authentication; T9032 EAP-TLS | `dot1x-2026-10-23T1304` | TRIAGE | The EAP / encryption-type family. **Build the local RADIUS server + supplicant rig ONCE as group setup** and let all four inherit it. T33354 is likely a desk UNSUPPORTED (`Not Support`) — confirm against the TPS, do not assume. T9032 is the redesign; use its authored precondition for the RADIUS and certificate recipe |
| B | T33369 Two-step (MAC then 802.1X); T44279 Tri-Authentication; T44277 Supplicant MAC; T33374 Re-authentication option; T33362 Multiple Dynamic VLAN (un-tag) | `authmodes-2026-10-23T1304` | TRIAGE | Authentication modes and dynamic VLAN. Inherits group A's rig. 🔴 **T44277 "Supplicant MAC" may need the DUT to act as SUPPLICANT toward an authenticator** — that is the one case here most likely to need a partner switch, so it is the one most likely to hit the credential gate. Decide that at triage and say so. T33362 needs **two** dynamic VLANs assigned from RADIUS to different supplicants, untagged |
| C | T33368 SMTP server authentication | `smtp-2026-10-23T1304` | TRIAGE | A different subsystem: the DUT authenticating to an **SMTP server**, not 802.1X. Needs an SMTP listener that requires AUTH. **tb277 almost certainly does not run one** — establish at triage what exists before designing, and grade on the SMTP dialogue on the wire (the `AUTH` verb and the server's reply), never on `show`. Starting a service on the box is a root change (STANDING-ORDERS §4) |
| D | T44287 CryptSecureMode | `securemode-2026-10-23T1304` | TRIAGE — **RUNS LAST** | 🔴 **Test Engineer's decision: this case runs after every other row is DONE or BLOCKED**, so a DUT that comes back awkward costs nothing already measured. On AW+ secure mode disables telnet, SNMPv1/v2, most privilege levels and weak crypto, **needs a reboot, and can drop configuration**. **Before enabling anything, write the exact recovery steps into this file.** If recovery cannot be stated with confidence, report **BLOCKED** rather than risk an unrecoverable unit — the window is unattended |

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

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |

## Issues
