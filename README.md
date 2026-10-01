# device-testing — bench testing with Claude Code, on any testbox

This repo is how Test Engineers run AlliedWare Plus test campaigns on lab testbox hardware with
Claude Code. It is not tied to one box or one product. You bring the testbox, its consoles, its
PDU and your topology. The repo brings:
- the procedures, as skills;
- the tester agent;
- the reusable tools;
- the rules for logging results;
- what earlier sessions learned the hard way, as memories.

## One-time setup

1. **Clone it into your lab home**, so the testboxes see it at the same path over NFS:
   ```bash
   cd ~/claude && git clone <this repo's remote> device-testing
   ```
   The skills run tools ON the box from `~/claude/device-testing/`, so keep that path.
2. **Link the memories.** Claude Code finds a project's memories by its launch directory, under
   `~/.claude/projects/<slug>/memory`. The slug is the repo's absolute path with every
   non-alphanumeric character turned into `-`. From the repo root, on your dev host:
   ```bash
   slug=$(pwd | sed 's/[^A-Za-z0-9]/-/g')
   mkdir -p ~/.claude/projects/$slug
   ln -s "$(pwd)/.claude/memory" ~/.claude/projects/$slug/memory
   ```
   Without this link a session starts with none of the memories, and anything it learns is
   stranded outside the repo.
3. **Make SSH to the testboxes work non-interactively.** Run
   `ssh -o BatchMode=yes tb<NNN> hostname`. If that fails with `publickey`, see
   [TESTBOX-ACCESS.md](TESTBOX-ACCESS.md) §0 (the empty forwarded agent).
4. **Optional: give your dev host a default box.** Add one line, `<your-dev-hostname> <tbNNN>`,
   to [bench-setup/default-boxes](bench-setup/default-boxes). Without it, every session asks
   which box to use. Never edit another engineer's line.
5. **Check the box** has Python 3.7 or later with pyserial, and read access to the AT framework
   at `/home/st-art/framework`, which is read-only and never edited.

## Running a session

**Always start Claude Code in the repo root.** A session started anywhere else loads the wrong
memories, or none.

| command | what it does |
| --- | --- |
| `/orient-dt [tbNNN]` | Works out which bench this session is about, checks no one else is on its consoles, probes it, loads the traps, briefs you and waits. |
| `/test-mode <cases>` | Runs a campaign. It asks for the box, consoles, PDU and constraints, then triages the cases against the bench and runs the runnable ones. This session becomes the **sentinel**: your channel to the tester, and its rescuer. The `bench-runner` agent is the **tester**. `--resume` picks up after a cut. |
| `/create-logs` | **Only when you ask**, after reviewing the results list: builds the final per-case `.log` and `.cfg` files you attach to the case in Zephyr. |
| `/wrap-dt` | Closes the session: stops what it started, restores the bench, re-probes it, writes the handover and commits. |

**Claude commits but never pushes.** Company permissions deny `git push`, so you push.

## What lives where

| path | what |
| --- | --- |
| [STANDING-ORDERS.md](STANDING-ORDERS.md) | The standing answers for campaigns: what the tester may do to devices, the triage report shape, and what always stays the Test Engineer's. |
| [logged-output.md](logged-output.md) | Every logging rule: verdicts, working logs, the results list, the final log template, `/create-logs`. |
| [platforms/](platforms/README.md) | One file of platform facts per product family, e.g. `IE520.md`: hardware limits, boot traps, CLI differences. |
| [tools/](tools/README.md) | Reusable helpers: console drivers, CLI answerers, traffic senders and counters, protocol emulators. **Look here before writing a script.** |
| [TESTBOX-ACCESS.md](TESTBOX-ACCESS.md) | SSH to a testbox, driving its consoles, launching framework runs. |
| `bench-setup/` | `bench_probe.py` (the one bench-state tool), `default-boxes`, and per box `<TB>/`: the generated `bench-state.md`, `<TB>.static`, captures and backups. tb470 keeps the flat legacy files at the top of `bench-setup/`. |
| `<TB>/<FAMILY>/` | A campaign's queue file, handovers and case folders, for example `tb470/IE520/`. |
| `IE520/` | The current product's earlier campaigns. When a product's testing ends, its folder moves into `old test runs/`. |
| `old test runs/` | Archived history. Leave it as it is. |
| `.claude/skills/`, `.claude/agents/` | The skills above and the `bench-runner` tester. |
| `.claude/memory/` | Shared memories, indexed in `MEMORY.md`. |
| `docs/` | Wiki pages, including the `/test-mode` walkthrough. |

## Ground rules

- **Only touch your session's consoles.** Every other `/dev/uN` on a box is someone else's.
  `bench_probe.py precheck` checks for other holders without opening a console. Never displace
  anyone.
- **Bench facts are measured, never written by hand.** `bench_probe.py run` regenerates the
  box's `bench-state.md`. Never hand-edit it or the deployed `.setup`.
- **Write only inside the repo.** Scratch goes in the session scratchpad or the box's
  `/tmp/<scratch>/`. Don't leave stray scripts in the lab tree.
- **Product facts are per product.** `/orient-dt` holds what is true of any AW+ product. One
  product family's limits and boot traps live in `platforms/<FAMILY>.md`; there is one today,
  [platforms/IE520.md](platforms/IE520.md). Start your product's file the first time you measure
  something worth keeping ([platforms/README.md](platforms/README.md)).
