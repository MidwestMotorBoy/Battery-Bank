---
name: kicad-tools-and-mcp
description: Run KiCad from an agent - kicad-cli for netlists, ERC, DRC and exports, a local KiCad MCP server on the user's PC, and what to do when no KiCad is available - including the fix for a KiCad MCP that stops after a KiCad reinstall. Use when you need ERC/DRC/exports, when KiCad tools fail, or when deciding whether to work in the cloud or on the user's machine.
---

# KiCad tooling for agents

## Where KiCad runs

- **Cloud containers usually have no KiCad.** On this project an apt PPA was blocked, and pulling the official Docker image was refused. Work on the files as text (`kicad-schematic-scripting`, `pcb-copper-resistance`), and get real ERC/DRC from the user's machine.
- **The user's PC.** Either use `kicad-cli` through a remote session, or use a KiCad MCP server running there (`mixelpixx/KiCAD-MCP-Server` on this project, tools `kicad__*`).
- **Heavy batches** (thermal sweeps, many solver runs) go to the user's machine too if it's set up for them.

## kicad-cli (KiCad 8–10)

```
kicad-cli sch export netlist --format kicadxml -o net.xml root.kicad_sch
kicad-cli sch erc --format json -o erc.json root.kicad_sch
kicad-cli pcb drc --format json --severity-all -o drc.json board.kicad_pcb     # add --schematic-parity / --refill-zones if your version has them
kicad-cli pcb export step|gerbers|drill|pos ...
```
On Windows the path is `C:\Program Files\KiCad\<ver>\bin\kicad-cli.exe`. KiCad's bundled Python (`...\bin\python.exe`) has pcbnew available, and is the interpreter to use for scripts that import it.

## Working with a local KiCad MCP

- **Read tools are safe** (`get_*`, `list_*`, `run_drc`, `run_erc`, `export_*`) and work with KiCad open.
- **`open_board`, `refill_zones` and `save_board` rewrite the file** in pcbnew's normalised form. That trips KiCad's "file changed on disk" guard and can fight the person's unsaved work. Run them on a copy (`review/revN-drc/`) unless the person asked for the edit.
- **Live board edits** (only when the board owner asks): have them save, write with KiCad closed or with a modification-time check, then `refill_zones` / `save_board(force)`, then they reopen or revert. Keep a backup in `review-backups/<what>/`.
- The server may have no tool for some edits (for example lines or polygons on silkscreen). Fall back to a text edit of a closed file.
- Some servers keep the open board's state in a Python process. If results look stale, reload the board.

## Fix: every call returns "Python process for KiCAD scripting is not running"

Seen 2026-10-30 after a clean reinstall of KiCad 10, while the MCP server still showed as connected.
1. Look in the server's log (`~\.kicad-mcp\logs\kicad-mcp-<date>.log` for this server). The helper process had crashed with `ModuleNotFoundError: sexpdata`.
2. Cause: the server's Python dependencies had been installed into KiCad's bundled site-packages, which the reinstall wiped. The config paths in `claude_desktop_config.json` were still fine.
3. Fix: install the requirements into the per-user KiCad Python folder, which survives reinstalls:
   ```
   "C:\Program Files\KiCad\10.0\bin\python.exe" -m pip install --target "%USERPROFILE%\Documents\KiCad\10.0\3rdparty\Python311\site-packages" -r <server>\requirements.txt
   ```
   `cairosvg` fails to load on Windows (no Cairo DLL). That's expected; the server renders with pymupdf instead.
4. Fully quit the Claude desktop app (from the tray) and reopen it, so the MCP server restarts.

Diagnose from a remote session on the PC. Folder access to dot-folders such as `~/.kicad-mcp` may be refused.

## When nothing can run

Say so in the report ("DRC not run: KiCad server down"), do the script-only checks you can (clearances, Kelvin taps, netlist from text), and list the ERC/DRC run as an open item for the person.
