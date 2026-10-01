---
verified: 2026-10-02
---
# Logged output — what a campaign leaves behind (any testbox, any product)

**What this is.** The single home for how test results are logged:
- the verdicts and what each one means;
- the tester's working files, written as a campaign runs;
- the **final logged output** of each case: one `.log` plus one `.cfg` per device.

The Test Engineer reviews it and attaches it to the case in Zephyr (Jira) themselves. No tool
here uploads anything.

Everything else (STANDING-ORDERS, `bench-runner`, `/test-mode`, `/wrap-dt`, the memories) points
here and does not restate it. Change the rules here and nowhere else.

**The final `.log` is never created automatically.** Only `/create-logs` creates it, and only
when the Test Engineer runs it after reviewing the campaign's results (§3).

**Each run stands alone.** A final log describes one run: this bench, this build, these
results. It never refers to an earlier run of the case or to another campaign. History is for
the agent (memories, handovers, git), not for the output.

Placeholders:
- `<TB>` is the testbox, for example `tb470`.
- `<FAMILY>` is the DUT's product family, for example `IE520`.
- `<group>` is the queue group, for example `routing`.
- `<STAMP>` is the group's start, `YYYY-MM-DDTHHMM` local.
- `<id>` is the case id without its prefix, for example `38472` for AWPTCM-T38472.
- `<dev>` is a device's name in the box's `.setup`, for example `stk_a` or `swi_b`.

## 1. Verdicts

Every case gets exactly one verdict. The bench owner's definition (2026-09-30), verbatim:

> If a platform doesnt support something, that test case is UNSUPPORTED. the Overall test set
> is a PASS even if it has UNSUPPORTED test cases within. FAIL means the test was run
> unsuccessfully, the platform prevented it from running, etc. PARTIAL means that the test was
> *unable* to be run, likely due to a misconfiguration physically or otherwise, a script error,
> etc., but not resulting from a FAIL condition being set. otherwise it would be NOT TESTED.

| verdict | when | final log |
| --- | --- | --- |
| **PASS** | It ran, and every step the platform supports passed. UNSUPPORTED steps or TestCases inside it do not stop a PASS | `<id>.log` |
| **FAIL** | It ran unsuccessfully: a check failed, or the platform prevented it from running | `<id>-fail.log` |
| **PARTIAL** | It was *unable* to run fully, because of a physical or other misconfiguration, a script error, etc. No FAIL condition was met | `<id>-partial.log` |
| **UNSUPPORTED** | The platform does not support what the case tests | `<id>-unsupported.log` |
| **NOT TESTED** | It was never attempted | no folder and no log. The results list carries the reason |

- **A plain `<id>.log` means the case explicitly PASSED.** Nothing else may use that name.
- A platform gap is UNSUPPORTED, a bench or script gap is PARTIAL, and a case nobody attempted
  is NOT TESTED. The pre-2026-09-30 `-skip.log` is retired.
- **The tester grades.** The tester that ran the case decides its verdict and reports it (§2).
  The Test Engineer may re-grade during review. `/create-logs` writes the verdict the results
  list holds when it runs, and the log's `Graded:` line says who graded it.

## 2. While the campaign runs

### Where each case's files live

Every case that is attempted gets its own folder:

```
<TB>/<FAMILY>/<group>-<STAMP>/
  README.md              the group's verdict table (§3), written by /create-logs
  <id>/
    <id><suffix>.log     the final log (§4), written by /create-logs only
    <dev>.cfg            one per device, the config after setup (below); a deliverable
    work/                the tester's working files; /create-logs deletes it (§3)
      run<N>.log         the working log of run N of this case
      ...                case-specific step scripts, pre/post configs, small captures
```

Raw console transcripts stay on the box (`/tmp/<campaign>/console-<uN>.log`) and are never
committed.

### Helper tools live in the repo-root `tools/`, not in a case

A helper that another case could use belongs in **`tools/`** at the repo root, catalogued in
`tools/README.md`. That covers a console driver, a CLI answerer, a config differ, a traffic
sender, a frame counter, a responder or a reload helper. It is never left inside a case's
`work/`, where `/create-logs` would delete it.

1. **Look in `tools/README.md` first.** Use or extend the tool that is already there. Do not
   write a second one that does the same job.
2. **Write it generic.** The testbox, consoles, NICs, ports, VLANs and addresses are arguments,
   never constants. It must not assume one product's prompts. Where a tool only works on one
   platform, say so in its README entry.
3. **Commit it with its README entry**, in the same commit as the case that first needed it.
4. **The working log names the tool and the exact arguments used**, so the run can be repeated.

Only a script that is genuinely this case's own (its step, config or teardown sequence, with the
case's ports and VLANs written in) stays in `work/`.

### The per-device `.cfg` files

After the case's setup is applied, and before its first step, the tester saves each device's
running configuration to `<id>/<dev>.cfg`:
- **One file per device**, for every device the case uses (the DUT and each partner).
- **A stack is ONE device with ONE `.cfg`**: the master's `show running-config`, which covers
  every member. Never one file per member.
- **Content:** the `show running-config` output, with the prompt, pager and echoed command
  removed, so it loads back as a config. It starts with three AW+ comment lines:
  ```
  ! <dev>  <hostname>  <model>  S/N <serial(s)>  <software version>
  ! case <id>, run <N>, captured <date time tz> after setup, before step 1
  ! testbox <TB>, console <uN>
  ```
- **A re-run overwrites them**, so the folder always holds the latest run's configs. Git
  history keeps the earlier ones.
- **They are deliverables.** `/create-logs` never deletes them.
- **Configuration a step adds or removes mid-case** (a shutdown, a withdrawal) is not in the
  `.cfg`. It is quoted in that step of the log, with its prompt.

### The tester's working log

The tester writes `work/run<N>.log` **as it goes**, numbering each run of the case:
- every command it sends, with its device prompt, and every configuration line exactly as sent;
- the device output, and its measurements;
- the files it saved.

It ends with a `VERDICT:` line in the §1 vocabulary, plus one line of reason. This is what
`/create-logs` builds from, so it errs on the side of too much.

- **Commit it per case.** It is the resume point if the session dies.
- **A re-run starts `run<N+1>.log`.** It does not overwrite the earlier run.
- **Teardown.** The tester still restores the bench after every case and verifies that by
  diffing `show running-config` against the pre-case copy (STANDING-ORDERS §1). That proof stays
  in the working log and is not part of the final log.

### Reporting to the sentinel

At the end of each case, the tester sends the sentinel one line:

```
RESULT <id> <VERDICT> -- <one-line reason> -- <group>-<STAMP>/<id>/work/run<N>.log
```

### The results list

The sentinel keeps the **results list**, the `## Results` table in the campaign's queue file:
one row per case:

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |
| T<id> | <title> | <group>-<STAMP> | <VERDICT> | <one line> | <id>/work/run<N>.log | tester |

NOT TESTED rows carry the reason and no working log. `graded` is `tester`, or `Test Engineer,
re-graded from <VERDICT> on <date>`. The
sentinel updates it on every `RESULT` line and reports progress to the Test Engineer as the
campaign goes on.

When the queue is done, the sentinel shows the final results list and ends with this line,
exactly:

> please run /create-logs after reviewing the results for the final uploadable product.

## 3. `/create-logs` — the final logged output

The Test Engineer runs `/create-logs` in the sentinel session, after reviewing the results list
and re-grading anything they disagree with. For each attempted case in the list, it:

1. Reads the case's latest `work/run<N>.log` and the `work/` files it names.
2. Writes `<id>/<id><suffix>.log` from the §4 template. The suffix comes from the verdict in the
   results list. It uses the **latest run only**.
3. Checks that every device in the log's TOPOLOGY has its `<dev>.cfg` in the folder, and names
   any that are missing to the Test Engineer.
4. Checks that every tool the working log names is in `tools/`. If one is only in `work/`, it
   moves it to `tools/` with a README entry before cleaning up, and tells the Test Engineer.
5. Writes the group's `README.md`:
   - one line saying the testbox, the DUT and the date span;
   - a verdict table, one row per case in the results list, NOT TESTED included.

   | case | title | log | verdict |
   | --- | --- | --- | --- |
   | T<id> | <title> | [<id>/<id><suffix>.log](<id>/<id><suffix>.log) | **<VERDICT>**. <one line: what was proven or what failed> |
   | T<id> | <title> | — | **NOT TESTED**. <the reason from the results list> |

   It holds no other prose. The logs carry the detail.
6. **Cleans up:** deletes `<id>/work/`. That leaves each case folder holding exactly its one
   `.log` and its `.cfg` files.
7. Commits once per group. The working files remain in git history.

`/create-logs` adds nothing that is not in the working log. A claim it cannot source is left
out, and named to the Test Engineer instead.

## 4. The template

Structure from `IE520/atmf-2026-09-23/38472.log`: a header, the verdict up front, then one
block per step with its verdict on the heading line. Step contents and the topology block come
from `IE520/authentication/30142.log`: every command with its prompt, the raw output, the
reading of it, and a conclusion line per step.

The log is a plain-text attachment, so no outside format is imposed. Keep it readable in any
text viewer.

```
================================================================================
TEST <id> -- <case title, as in the test-case database>
================================================================================
Run:      <date> <start>-<end> <tz> (device clocks <UTC / offset>, if they differ)
Bench:    <TB>, consoles <list>; Test Engineer <user@host>
Tester:   <bench-runner | <script> @ <commit> | by hand>
Graded:   <tester | Test Engineer, re-graded from <VERDICT> on <date>>
Case:     <source id>, objective "<objective>", <N> steps
Build:    <dev> <software version> (<release file>, build date <date>)
          <one line per device>
Configs:  <dev>.cfg, <dev>.cfg, ... (running-config after setup; saved to startup: no | yes)

VERDICT: <PASS | FAIL | PARTIAL | UNSUPPORTED> -- <one-line summary>
  <what was proven, as a dotted list when there are several things:>
      <thing checked> ............ <result>  (<the proof, in a few words>)
<verdict block -- see below>
CAVEAT:  <the scope limit of the proof, if any: what this run did NOT establish>

--------------------------------------------------------------------------------
TOPOLOGY AS TESTED
--------------------------------------------------------------------------------
  <role>  : <dev> (<model>) console <uN>, S/N <serial>, MAC <mac>
            <stack: members, IDs, master>
  <role>  : <dev> ...
  <link>  : <dev> <port> <-> <dev> <port>  (<media>, <vlan / aggregation>)
  <host>  : <TB> <nic> <mac> <address> -> <dev> <port>
  <tools> : <traffic or capture tools used, and where they ran>

STEP 0 -- baseline (feature OFF)                                          done
--------------------------------------------------------------------------------
<prompt># <command>
  <output, verbatim>

STEP 1 -- "<the case's step text, quoted>"                                PASS
--------------------------------------------------------------------------------
  Method: <how the step was exercised, when it is not obvious from the step text>
<prompt># <command>
  <output, verbatim>                       <-- <what this line shows>
<prompt>(config)# <a configuration line this step sends>
host# <a host-side command>  -> <its result line>
  => STEP 1 PASS: <what the outputs above prove, and why that is the feature working>

STEP 2 -- "<step text>"                                                   UNSUPPORTED
--------------------------------------------------------------------------------
<prompt># <the refused command>
  <the device's exact answer>
  => STEP 2 UNSUPPORTED: <what the platform lacks>
================================================================================
```

**Step verdicts:** `done` (setup or baseline), `PASS`, `FAIL`, `UNSUPPORTED`, `NOT RUN`.

**The verdict block** comes after the `VERDICT:` lines and before `CAVEAT:`. It depends on the
verdict:

| verdict | block |
| --- | --- |
| PASS | none. Each UNSUPPORTED step is named in its own STEP, with its proof |
| FAIL | `FAIL CONDITION:` which check failed, against which expected result, and why that is a product failure rather than the method. `TRIED:` each attempt and its outcome, when there was more than one |
| PARTIAL | `NOT RUN:` each step that could not run, with the reason. `UNBLOCK:` the exact change that would let it run, stated so someone at the bench can do it without asking a question (STANDING-ORDERS §3) |
| UNSUPPORTED | `NEEDS:` what the case requires. `ABSENT:` the proof the platform lacks it, verbatim (the refused command, the missing hardware or licence bit) |

### What goes in, and what stays out

**In: the evidence chain.** That means:
- the commands, with their prompts;
- the raw device output;
- each step's verdict and its conclusion line;
- the session facts (box, consoles, Test Engineer, devices, links).

In detail:
- **Every step quotes its own proof**: the command with its prompt, the output verbatim, short
  `<--` notes on the lines that matter, and a closing `=> STEP n <VERDICT>:` line. The
  conclusion says what the output proves, not merely that it was read.
- **Every pass has positive proof**: something that could only be seen if the feature worked,
  ideally with a control (30142's STEP 2 reverses the condition on identical cabling).
  Absence of an error is not proof.
- **Several readings become a table** rather than repeated blocks.
- **Times come from the device log** when they matter (convergence, rejoin, recovery), with
  the clock source named.
- **A baseline** (STEP 0, feature off) whenever the case changes behaviour. That baseline is
  what makes the later steps interpretable.
- **Every non-PASS holds as much evidence as possible**: everything tried, the raw output that
  shows the failure, and the reason.
- **TOPOLOGY AS TESTED is complete enough to rebuild the case**: devices, serials, consoles,
  links, host NICs and tools. With the `.cfg` files, a Test Engineer or an agent can set the
  case up again on the same bench, or map it onto another.

**Out: everything that is not this run's evidence.** That means:
- earlier runs and other campaigns (each run stands alone);
- setup detours and approaches that did not work;
- infrastructure findings;
- conversations with the sentinel or the Test Engineer;
- the teardown proof.

Those belong in the working log, the session handover or a memory. Raw console transcripts
never go in. They stay on the box.

### Existing logs

Logs written before 2026-10-02 (`IE520/<group>-<date>/`, flat, with no per-case folder) keep
their own structure and are not rewritten. A case re-run in a new campaign gets a new folder
and log from this template.
