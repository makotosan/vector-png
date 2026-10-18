# Install vector-png as a Codex user skill

[日本語インストール手順](INSTALL.ja.md) · [English README](README.md)

Destination: **`~/.agents/skills/vector-png/`**, available across projects.
Python 3.10+ and native Cairo are required. Existing skills are never overwritten.

## Windows (PowerShell)

Run these commands in a normal PowerShell session:

```powershell
git clone https://github.com/makotosan/vector-png.git
Set-Location vector-png
./install-vector-png.ps1
```

If you have already cloned the repository, update that checkout before running the script.

The installer performs these steps:

1. Copy `skills/vector-png` into your user skill directory.
2. Create a dedicated Python virtual environment, `.venv`, inside the skill.
3. Install dependencies from `requirements.txt`.
4. Run a roundtrip check using the four existing PNG commands: create/extract/update/inspect.

It does not change system-wide PATH. On failure it leaves the copied folder for
diagnosis. A retry refuses that existing folder; inspect it and, if needed, move
or rename it before retrying.

### Prepare Cairo

The installer searches `VECTOR_PNG_CAIRO_DIR`, a standard MSYS2 UCRT64 installation,
or an existing bundled Codex runtime. It does not download or copy Cairo DLLs.
You can specify an existing library directory:

```powershell
./install-vector-png.ps1 -CairoDirectory 'C:\msys64\ucrt64\bin'
```

If Cairo is not installed, install [MSYS2](https://www.msys2.org/) and run the
following in its terminal:

```sh
pacman -S mingw-w64-ucrt-x86_64-cairo
```

Match the Python and Cairo architectures, for example 64-bit with 64-bit.
The selected directory is recorded in the skill's `cairo-path.txt` and used by
the render worker. The script does not change PowerShell execution policy.
If your organization restricts scripts, follow its approved process.

## macOS / Linux

Install Cairo first:

- macOS: `brew install cairo`.
- Debian/Ubuntu: `sudo apt-get install libcairo2`.

Clone the repository and enter its root directory:

```sh
git clone https://github.com/makotosan/vector-png.git
cd vector-png
```

Run the copy step below. It stops if the destination already exists.

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
```

**Confirm that copying succeeded before** creating the virtual environment and
installing dependencies. If any step fails, do not execute subsequent commands.

```sh
python -m venv "$HOME/.agents/skills/vector-png/.venv"
"$HOME/.agents/skills/vector-png/.venv/bin/python" -m pip install -r "$HOME/.agents/skills/vector-png/requirements.txt"
"$HOME/.agents/skills/vector-png/.venv/bin/python" "$HOME/.agents/skills/vector-png/scripts/roundtrip_check.py" --output-dir "$(mktemp -d)"
```

Use `python3` instead of `python` where required. If macOS cannot locate Cairo,
set this before running Python:

```sh
export DYLD_FALLBACK_LIBRARY_PATH="$(brew --prefix)/lib"
```

## Optional normalization support

For a new Windows skill installation with normalize/convert enabled:

```powershell
./install-vector-png.ps1 -WithNormalization
```

This additionally installs requirements-normalization.txt, downloads the pinned
Playwright Chromium and runs normalization_check.py. It still refuses an existing
skill. Preserve/rename an existing skill after reviewing its local configuration,
then install the new copy; do not erase your only copy or mix helper versions.

For a copied macOS/Linux skill, install optional dependencies using its own Python:

```sh
"$HOME/.agents/skills/vector-png/.venv/bin/python" -m pip install -r "$HOME/.agents/skills/vector-png/requirements-normalization.txt"
"$HOME/.agents/skills/vector-png/.venv/bin/python" -m playwright install chromium
"$HOME/.agents/skills/vector-png/.venv/bin/python" "$HOME/.agents/skills/vector-png/scripts/normalization_check.py" --output-dir "$(mktemp -d)"
```

On Linux, --with-deps may be added to the browser install command when system
dependencies are missing; it may require administrator access. Keep each step's
success check. PLAYWRIGHT_BROWSERS_PATH can select a browser-cache location; use
the same setting when installing and invoking the skill. Without the optional
dependencies/browser, the four existing commands still work, while normalization
fails safely. See [NORMALIZATION.md](NORMALIZATION.md) for scope and reports.

The normalizer requests Chromium's sandbox and never retries with --no-sandbox.
On Linux, host policy must permit the browser's sandbox/user namespaces. If
AppArmor blocks it, configure an approved profile for the installed binary;
see [Ubuntu's user-namespace guidance](https://documentation.ubuntu.com/release-notes/24.04/).
CI permits userns for its exact downloaded Chromium binary using a dedicated
AppArmor profile, without disabling AppArmor or its system-wide restriction.

## Verify installation and use in Codex

1. Confirm the roundtrip output contains `"roundtrip": "passed"`. It checks PNG
   creation, extraction of exactly matching SVG bytes, editing, resaving and
   raster/source consistency.
2. Invoke `$vector-png` in Codex. Existing chats can use the skill once recognized.
   If it does not appear, restart Codex and reopen the chat.
3. Ask it to create a PNG from a simple SVG and inspect it.
   Successful JSON includes `"raster_matches_svg": true`.

The skill instructs Codex to use its dedicated `.venv` when present.
The helper also runs from any project when addressed by its absolute path.
Verify CLI operation and Codex skill discovery separately.

## Automated tests

From the development repository root:

```sh
python -m pip install -e ".[test]"
python -m pytest -q
```

For an installed skill, enter the skill directory and use that skill's `.venv`
Python to run `-m pytest -q`.

`VECTOR_PNG_TEST_TMP_ROOT` optionally places test artifacts in a writable
workspace directory.

[Return to the Japanese installation guide](INSTALL.ja.md)

