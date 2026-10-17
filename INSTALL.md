# Install vector-png as a user skill

[日本語インストール手順](INSTALL.ja.md)

Destination: **`~/.agents/skills/vector-png/`**, discoverable across projects.
Python 3.10+ and native Cairo are required. Existing skills are never overwritten.

## Windows (PowerShell)

Run in a normal PowerShell session:

```powershell
git clone https://github.com/makotosan/vector-png.git
Set-Location vector-png
./install-vector-png.ps1
```

The installer copies `skills/vector-png` into your user skill directory, creates
an isolated `.venv`, installs `requirements.txt`, and runs all four CLI commands
in a roundtrip check. It does not change system-wide PATH. On failure it leaves
the copied folder for diagnosis, and a retry refuses that existing folder.
Move/rename an existing installation yourself before retrying.

Cairo is located from `VECTOR_PNG_CAIRO_DIR`, a standard MSYS2 UCRT64 installation,
or an existing bundled Codex runtime. No Cairo DLL is downloaded or copied by
this installer. You can specify an existing library directory:

```powershell
./install-vector-png.ps1 -CairoDirectory 'C:\msys64\ucrt64\bin'
```

To obtain Cairo, install [MSYS2](https://www.msys2.org/) and run
`pacman -S mingw-w64-ucrt-x86_64-cairo` in its terminal. Match 64-bit Python and
Cairo. The installer records the directory in `cairo-path.txt` for the worker.
It does not change PowerShell execution policy; follow your organization's
approved process if scripts are blocked.

## macOS / Linux

Install Cairo (`brew install cairo` on macOS, or
`sudo apt-get install libcairo2` on Debian/Ubuntu), clone this repository, then:

```sh
python - <<'PY'
from pathlib import Path
import shutil
target = Path.home() / '.agents/skills/vector-png'
if target.exists():
    raise SystemExit(f'Existing skill was not overwritten: {target}')
target.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree('skills/vector-png', target)
print(target)
PY
python -m venv "$HOME/.agents/skills/vector-png/.venv"
"$HOME/.agents/skills/vector-png/.venv/bin/python" -m pip install -r "$HOME/.agents/skills/vector-png/requirements.txt"
"$HOME/.agents/skills/vector-png/.venv/bin/python" "$HOME/.agents/skills/vector-png/scripts/roundtrip_check.py" --output-dir "$(mktemp -d)"
```

Run from the repository root. Use `python3` instead of `python` where required.
Stop if copying or dependency installation fails; do not continue with a refused
destination. If macOS cannot find Cairo, export
`DYLD_FALLBACK_LIBRARY_PATH="$(brew --prefix)/lib"` before invoking Python.

## Verify discovery and use

1. Confirm that the roundtrip check reports success. It verifies generation,
   exact SVG extraction, editing, resaving and pixel/source comparison.
2. Invoke `$vector-png` in Codex. Existing chats can use it once the skill is
   recognized. If it does not appear, restart Codex and reopen the chat.
3. Ask it to create and inspect a PNG. Expected JSON: `"raster_matches_svg": true`.

The skill instructs Codex to use its local `.venv`. The helper also works from
any project using its absolute path. Syntax checks and CLI tests do not prove
that an already-open Codex session has refreshed its skill discovery.

## Tests

From the repository: `python -m pip install -e ".[test]"`, then
`python -m pytest -q`. From an installed skill, run its `.venv` Python with
`-m pytest -q` in the skill directory. `VECTOR_PNG_TEST_TMP_ROOT` optionally
places test artifacts in a writable workspace folder.
