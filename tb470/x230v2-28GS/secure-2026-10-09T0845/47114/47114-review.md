# T47114 process review -- secure-2026-10-09T0845
Reviewed 2026-10-12 by /create-logs from `agent-aace2d4eb36f55205.jsonl` (the bench-runner transcript) and the working files.
Group-wide findings: [../REVIEW.md](../REVIEW.md). Call numbers (#n) are this case's segment, in call order
(07:07:50-07:18:37 UTC = 20:07:50-20:18:37 NZDT).

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 29 | 58 | 37,990 | 3,806,463 | 4,277 | 31 | 648 s | 24,975 chars |

About 270 s of the wall time is the reload wait (#21, 20:12:21-20:16:49). Cache read averages ~131k tokens per call.

## Process taken
1. #1 pre-run capture (`ckcon`: show secure-mode, running/startup-config, boot, system, clock, telnet, ssh server, user, exception log) to `prerun-u0.out`.
2. #2 read the capture's running-config back (2,774 chars); #3 counted `security-password` lines across 12 probe captures (why they are running-only).
3. #4 `qmark` of the CLI to be used (`crypto secure-mode ?`, `security-password ?`, ...); #5 tail of the console transcript.
4. #6 ck.db titles of the three NOT TESTED rows; #7 wiki `crypto-secure-mode-delete-hostkey` (116 chars, nothing useful).
5. #8-#11 queue: read, edit (restore recipe + NOT TESTED rows), commit.
6. #12-#14 backup `copy flash:/default.cfg flash:/default.cfg.pre-secure` + `show file` of both, saved as text (group restore preparation).
7. #15 second read of `prerun-u0.out` (4,239 chars: system, clock, ssh server, user, exception log) for the working log.
8. #16 working log started; #17 `rc2cfg.py` -> `swi_f.cfg`.
9. #18 step A+B (`ckyn`, exit 2 on the advisory `% ` line); #19 proof of B (`ckcon` running-config, show secure-mode, startup-config).
10. #20 step C `write`; #21 `ckreload` (265 s).
11. #22, #23 two `tools/tb grep` calls on the console transcript, returning 30 and 31 chars (nothing usable); #24 `tools/tb tail` of 400 lines to the scratchpad + grep (2,802); #25 a `sed` slice of it (1,592). Four calls for the boot excerpt.
12. #26 step D capture (`ckcon`, 13 commands) to `stepD-u0.out`; #27 a line-range read of it (`sed -n '28,32p;44,48p;73,77p;154,172p;182,212p'`, 4,024 chars) + `rcdiff.py`.
13. #28 working log steps appended; #29 commit; #30-#31 RESULT.

## Wasted input
- #2 + #15: `prerun-u0.out` read twice (2,774 + 4,239 chars), the second time for fields (uptime, serial, clock, SSH lists) that one `grep -A` per command would give in ~1k. The running-config read in #2 was not needed at all: `rc2cfg.py` writes it to `swi_f.cfg`, and `rcdiff.py` compares it.
- #22-#25: four calls (4.4k chars) to pull the boot excerpt from the console transcript, two of which returned nothing. One call, `tools/tb tail tb470 <transcript> 400 | grep -a -n -E '<pattern>'`, or a reload helper that saves the boot text itself (scripts, below), would do.
- #7: a wiki page that the case did not use (small).

## Repetition
- The boot excerpt (#22-#25) and the after-boot read (#27) are the same work T47115's group restore repeated for the second reload (T47115 #26-#27). See ../REVIEW.md.

## Accuracy risks
- **The release-verification warning was missed at grading time, because of a line-range read.** #27 read `stepD-u0.out` up to line 212. The `show log | include -i secure|crypto|FIPS|verify` output is at lines 213-216, and its second line is `user.warning ... Verification of the release file has failed, please verify it.`. The working log first quoted only the `crypto secure-mode enabled` line. The tester corrected it at 20:20, after the sentinel pointed it out (4 calls in T47115's segment). Lesson: read a capture by command marker (`sed -n '/>>> show log/,/>>>/p'`), not by guessed line numbers. The final log now quotes both lines, with the CAVEAT that release verification is not part of the case.
- **Step B's own pass criterion was not met literally.** The procedure says "accepted, no `% ` line", and the device printed `% Save the config and restart the system for this change to take effect.`. The tester read it as an advisory (the running-config and `show secure-mode` both show the command took). The final log keeps the step text verbatim and says why the `% ` line is not a rejection. Next time, write the advisory into the expected result.
- **`show secure-mode` is not proof of the boot.** It read "enabled" after step B, before the reload. The T47115 working log (R3) also shows that the "Secure mode setup" / "FIPS Provider Install" / "Secure mode enable" boot jobs run on a NON-secure boot too. So the proof of booting into secure mode rests on "Creating secure mode hostkey", the 20:16:04 `crypto secure-mode enabled` log line, and the SSH algorithm change. The final log grades on those. The SSH algorithm lists were not read between step B and the reload, so it is not shown whether they changed at config time or at boot. Close it next run with one `show ssh server` after step B.
- **Calling the post-boot SSH set "FIPS"** is the tester's label. The device shows only the lists. The final log says "narrowed" and quotes the lists.
- **Claims left out of the final log for lack of a source in the working files:**
  - "Login as manager succeeded with no forced password change". No login capture is in `work/`. The final log uses `show user` (manager on con 0) instead.
  - "No error, failure or exception line in the boot transcript". The boot transcript is not in `work/` (only the quoted lines in run1.log), and #22/#23's greps returned nothing usable.
- Left out as out-of-scope, not unsourced: "265 s, against 163-168 s for the five plain reloads in run 1 tonight" (other runs; the comparison is in platforms/x230v2-28GS.md §1).
- The backup of `default.cfg` (#12-#14) assumed it could be copied back. It could not (T47115 review, ../REVIEW.md).

## Next run: expected outputs (this bench, x230v2-28GS, awplus_main-20261008-57)
| step | command | expected |
| --- | --- | --- |
| A | `show secure-mode` | `Secure mode is disabled` |
| B | `crypto secure-mode` (config) | no (y/n); `% Save the config and restart the system for this change to take effect.` (an advisory: `ckyn`/`ckcon --stop-on-error` stop on it, exit 2). Then `show secure-mode` = `Secure mode is enabled` at once; rcdiff `+crypto secure-mode` after `security-password history 1` |
| C | `write`, `reload` | `[OK]`; login in ~265 s. Boot: `Creating secure mode hostkey`, `Please verify release with the 'crypto verify' command`, a `W A R N I N G` banner before `awplus login:` |
| D | `show log \| include -i secure\|crypto\|verify` | `user.notice ... IMI[...]: crypto secure-mode enabled` and `user.warning ... Verification of the release file has failed, please verify it.` |
| D | `show ssh server` | Ciphers `aes128-cbc,aes256-cbc,aes128-ctr,aes192-ctr,aes256-ctr`; KEX `ecdh-sha2-nistp256,ecdh-sha2-nistp384`; MAC `hmac-sha2-256`; hostkeys `ecdsa-sha2-nistp256,ecdsa-sha2-nistp384` (before: chacha20/gcm/ctr, mlkem/sntrup/curve25519/ecdh, umac/hmac-etm, ed25519/ecdsa/rsa + certs) |
| D | `show exception log`, `show boot` | `None`; `Current boot config: flash:/default.cfg (file exists)` |

## Next run: scripts
- `tools/tb ckcon` without `--stop-on-error` (or `ckyn` with an "expected `% `" allow-list) for step B, so the advisory does not end the call with exit 2 and a cleanup.
- **Proposed:** `ckreload ... --boot-log <file>`, which saves the console text from `reload` to the login prompt. It replaces #22-#25 here and T47115 #26.
- **Proposed:** `tools/capcmd.py <capture> "<command>"`, which prints one command's output from a ckcon/ckyn capture by its `>>>` marker. It replaces line-range `sed` (the cause of the missed warning).

## Next run: references
- `platforms/x230v2-28GS.md` §1 (secure-mode boot ≈ 265 s; the default.cfg restore rule) and §2 (the `crypto secure-mode` advisory, the release-verification warning, `crypto verify` not applicable to dev builds).
- AW+ wiki on the share: `crypto-secure-mode.md`, `show-secure-mode.md`, `crypto-verify.md` (x230 sections).
- Memory `awplus-default-cfg-cannot-be-overwritten` before planning any startup-config backup.
