---
name: dev-host-vscode-update-process
description: VS Code on the dev host updates via ~/bin/update-vscode.sh (apt, Microsoft repo) with an "Update VS Code" desktop icon; built 2026-10-29
metadata:
  type: reference
---

**Dev host (Ubuntu 24.04 GNOME) VS Code update process, built 2026-10-29 at Terrence's request.**

- VS Code is the `code` .deb from Microsoft's apt repo (`/etc/apt/sources.list.d/vscode.sources`), not a snap or tarball.
- `~/bin/update-vscode.sh` refreshes ONLY that source, upgrades `code` with `apt-get install --only-upgrade`, logs to `~/.local/state/update-vscode.log`, and offers (default No) to relaunch VS Code. `--quiet` / no tty = no prompts. Passwordless sudo on this host.
- Launchers: `~/Desktop/update-vscode.desktop` (trusted, executable) and `~/.local/share/applications/update-vscode.desktop` ("Update VS Code" in the app grid, pinnable to the dock). `Terminal=true` so the run is visible.
- The `code` postinst asks a debconf question (`code/add-microsoft-repo`); it is preseeded `true` and the script exports `DEBIAN_FRONTEND=noninteractive`, so a button-click run never stalls.
- A running VS Code keeps the old binary until restarted; restarting it kills any Claude Code session inside it, so the script never restarts on its own.

**Why it lives on the dev host, not in a repo:** it is host tooling, not lab work; the share write boundary ([[tb470-root-changes-go-through-terrence]] is the testbox analogue) does not cover `~` on the dev host, and Terrence asked for the desktop button explicitly.
