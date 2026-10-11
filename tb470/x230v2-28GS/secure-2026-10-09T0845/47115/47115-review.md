# T47115 process review -- secure-2026-10-09T0845
Reviewed 2026-10-12 by /create-logs from `agent-aace2d4eb36f55205.jsonl` (the bench-runner transcript) and the working files.
Group-wide findings: [../REVIEW.md](../REVIEW.md). Call numbers (#n) are this case's segment, in call order
(07:18:43-07:33:07 UTC = 20:18:43-20:33:07 NZDT).

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 36 | 72 | 51,254 | 6,259,219 | 347 * | 36 | 864 s | 28,023 chars |

\* As measured by `tools/case_tokens.py`. It cannot be right: #33 alone wrote an 18 kB working log (~5k output tokens).
The transcript's usage records for this span look incomplete. Treat the output column as unreliable.

**Only about a third of this segment is the case.** By call: the case (precondition, setup, steps 1-3, case teardown) is
#1-#2, #7-#9 and #12-#13 (7 calls, ~4 min). T47114's log correction is #3-#6 (4 calls). The group restore, post-run probe
and wrap-up are #14-#35 (22 tool calls, ~10 min; with the RESULT call, 23 API calls carrying 4,193,620 of the
6,259,219 cache read, i.e. 67%, measured from the transcript's usage records for 07:22:41-07:33:07 UTC). The restore belongs to the group,
not to this case.

## Process taken
1. #1 precondition capture (`show secure-mode`, running-config, `show security-password configuration` / `user`).
2. #2 setup: `security-password minimum-length 12`, `minimum-categories 3`, running-config, `rc2cfg.py` -> `swi_f.cfg`.
3. #3-#6 T47114 correction: re-read `stepD-u0.out` lines 213-220, the wiki `crypto-verify.md` (3,257 chars), a read-only
   `show log` / `show log permanent` capture, and the correction appended to T47114's working log.
4. #7 steps 1 and 2 plus two step-3 attempts in one `ckcon` call (1,626 chars).
5. #8 "recovery path": re-sent manager's own `password 8 <hash>` line, then checked it was unchanged.
6. #9 step 3 proper (7 attempts) + `show running-config | include username`.
7. #10-#11 read `tools/tb` and the console modules for `CK_USER`/`CK_PASSWORD` (2.6k chars), to log in as a new user.
   It was not possible, so it was not done.
8. #12-#13 case teardown: `no username ckpw1/ckpw15`, `no security-password minimum-categories` (rejected), then
   `minimum-categories 1` / `minimum-length 8`, rcdiff empty.
9. #14-#30 group restore: `no crypto secure-mode`; five refused routes to put `default.cfg` back (copy, copy to startup,
   copy via a .cfg name, boot pointer moved, delete); wiki `boot-config-file.md`; `bench-setup/restore_cfg.py` read
   (2,651); `no boot config-file`, isolation removed, `write`, reload (165 s), isolation re-applied, delete backups.
10. #31-#32 post-run precheck/probe (MATCH) and peek; #33 the WHOLE working log written in one call; #34-#35 queue; #36 RESULT.

## Wasted input
- #10-#11 (2.6k chars): reading tool source to find out how to log in as another user. The answer, "tools/tb does not pass
  the environment over ssh", belongs in tools/README.md's `tb` entry, so the next tester reads one line (scripts, below).
- #22 `restore_cfg.py` (2,651 chars) and #19 wiki `boot-config-file.md` (1,136): restore research. It cost time because
  the restore plan had not been checked before T47114's write (../REVIEW.md).
- #4 wiki `crypto-verify.md` (3,257): needed once. It is now summarised in platforms/x230v2-28GS.md §2.

## Repetition
- Step 3's first two attempts (#7: `abc`, `friend`) were under the default 8-character minimum and answered
  `% password too short`. That is a different check, which proves nothing about the 12/3 rule, so #9 had to re-test.
  Choose the test data from the rule (9 characters = above 8, below 12; 16 characters of one category) and it takes one
  call. See the expected outputs below.
- #8 re-sent manager's existing hash to "prove the recovery path" before trying weak passwords on manager. It wrote
  config on the DUT's only login account without any need: a rejected password changes nothing, and the earlier
  rejections had already shown that. The echo in `steps2a-u0.out` shows the line wrapped across the console
  (`...rJWi6S..L0u7` / `FYo4iPIgN0...`). A mangled paste here was the one way this case could have locked the console
  tools out. Drop the step, or keep the recovery hash in secrets.md and only use it if a weak password is ever accepted.

## Accuracy risks
- **"Applies to all users" was tested on passwords being SET, not on stored ones.** `setup-u0.out` shows each rule
  printing `The new '<rule>' security rule will apply to new passwords only`. The working log said only "(no `% ` line)"
  and did not record that message. The final log quotes it, and its CAVEAT says manager's stored password is not
  re-checked. Whether the case owner means "every user's new password" (what was tested) or "existing passwords are
  forced to change" (e.g. `security-password forced-change`) is for the Test Engineer. The verdict is unchanged.
- **No login as the new users.** The accepted passwords were never used to log in (#10-#11: the console tools take
  another login only from the environment). It is in the final log's CAVEAT.
- **ckpw15 as an existing user** was tried with a too-short password only, not a 1-category one (`steps2b-u0.out`).
  Minor. One more line closes it.
- **The working log was written once, at 20:32, after the 10-minute group restore** (#33), not as the case went. Had the
  session died in #14-#30, the case's record would have existed only in `work/*.out`. The rule is "write it as it goes,
  commit per case" (logged-output.md §2).
- No claim had to be left out of the final log for lack of a source. Everything in it is in `precase`, `verify-obs`,
  `setup`, `steps`, `steps2b-u0.out` or run1.log.

## Next run: expected outputs (this bench, x230v2-28GS in secure mode, awplus_main-20261008-57)
| step | command | expected |
| --- | --- | --- |
| setup | `security-password minimum-length 12` / `minimum-categories 3` | `The new 'minimum-length' security rule will apply to new passwords only` (same for minimum-categories); `show security-password configuration` 12 / 3 |
| 1-3 | password of 9 chars (e.g. `Ab1-shrt9`) | `% User password should have length of 12 or more characters.` |
| 1-3 | 14-16 chars, 1 category (e.g. `abcdefghijklmnop`) | `% Password does not match at least 3 character categories.` |
| 1-3 | under 8 chars | `% password too short` (the default check, NOT the configured rule: avoid as test data) |
| 1-2 | compliant (e.g. `Ck-Pw-Test-2026`) | no output; user listed in `show security-password user`; stored as `password 8 $5$...` |
| 3 | `username manager [privilege 15] password <bad>` | rejected as above; `show running-config \| include username` hashes unchanged |
| teardown | `no username ckpw1` | no prompt, user gone |
| teardown | `no security-password minimum-categories` | `% Invalid input detected at '^' marker.`; use `security-password minimum-categories 1` and `minimum-length 8` |

## Next run: scripts
- **Proposed:** `tools/tb` passes `CK_USER`/`CK_PASSWORD` over ssh (or `awlogin.py --user U --password-env VAR`), so a
  login as a test user can be checked and the case's "applies to all users" gets a login proof.
- **Proposed:** `ckcon --expect '<regex>'` per command (or a plan file `command<TAB>expected-regex`). Steps 1-3 then
  become one call that prints PASS/FAIL per line, instead of a reading of 15 rejections.
- Existing: `tools/rcdiff.py` for the teardown diff (used); `tools/rc2cfg.py` (used).

## Next run: references
- `platforms/x230v2-28GS.md` §2: no `no` form for minimum-categories; the secure-mode boot's release-verification warning.
- AW+ wiki on the share: `security-password-minimum-length.md`, `security-password-minimum-categories.md`,
  `security-password-forced-change.md` (if the case owner wants existing passwords forced to change), `show-security-password-user.md`.
- This review's expected-outputs table, for the test data.
