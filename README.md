# vector-png — Codex Skill

[日本語 README](README.ja.md)

**vector-png is a user skill for OpenAI Codex.** Install it in
`~/.agents/skills/vector-png/` and invoke `$vector-png` in Codex to create,
extract, edit, save, and inspect PNG files containing editable SVG source in
compressed iTXt chunks. The skill is available across your projects.

The bundled Python CLI and library power the skill and can also be used directly.
They create ordinary, transparent PNGs that remain editable through their embedded
SVG source. The implementation uses Pillow, CairoSVG and defusedxml.
Original project code is MIT licensed.

## Installation

Python 3.10+ and native Cairo are required. For a user skill available across
projects, follow **[INSTALL.md](INSTALL.md)**. The destination is
`~/.agents/skills/vector-png/`
(`%USERPROFILE%\.agents\skills\vector-png` on Windows).

On Windows, run these commands in a normal PowerShell session:

```powershell
git clone https://github.com/makotosan/vector-png.git
Set-Location vector-png
./install-vector-png.ps1
```

The installer copies the skill, creates a dedicated `.venv`, installs
`requirements.txt`, and runs a sample create/extract/update/inspect roundtrip.
It refuses an existing destination. On failure, it leaves the copied folder for
diagnosis; inspect it and move or rename it before retrying.
The script does not change system-wide PATH or PowerShell execution policy.
Follow your organization's approved process if scripts are blocked.

Cairo is required separately. The installer searches `VECTOR_PNG_CAIRO_DIR`,
a standard MSYS2 UCRT64 installation and an existing bundled Codex runtime;
it does not download or copy Cairo DLLs. To specify an existing installation:

```powershell
./install-vector-png.ps1 -CairoDirectory 'C:\msys64\ucrt64\bin'
```

- **Linux (Debian/Ubuntu):** `sudo apt-get install libcairo2`.
- **macOS:** `brew install cairo`. If discovery fails, set
  `DYLD_FALLBACK_LIBRARY_PATH="$(brew --prefix)/lib"` before starting Python.
- **Windows:** install [MSYS2](https://www.msys2.org/), then in its terminal run
  `pacman -S mingw-w64-ucrt-x86_64-cairo`. In PowerShell set
  `$env:VECTOR_PNG_CAIRO_DIR='C:\msys64\ucrt64\bin'`, adjusting for your install.
  Match the Python and Cairo architectures, for example 64-bit with 64-bit.
  The directory setting affects only the render worker's DLL search.

For macOS/Linux skill copying, virtual environment creation and dependency
installation, see [the installation guide](INSTALL.md).
Installing the Python package alone does not register the skill. For manual setup,
copy `skills/vector-png` to the user skill destination and install its dependencies
in the Python environment used by Codex. The helper is self-contained and does not
require this repository on PYTHONPATH. It uses the skill's `.venv` when present.

After installation and a successful roundtrip, invoke `$vector-png` in Codex.
Existing chats can use the skill once recognized; if it does not appear, restart
Codex and reopen the chat. Ask it to create and inspect a PNG and check for
`"raster_matches_svg": true`. CLI test success alone does not establish that an
already-open Codex session has refreshed its skill discovery.

## Usage

For CLI-only development, install dependencies from the repository:

```sh
python -m pip install -e ".[test]"
```

```sh
python vector_png.py create examples/fireworks.svg editable-art.png --width 512 --height 512
python vector_png.py extract editable-art.png editable.svg
# Edit editable.svg before running update.
python vector_png.py update editable-art.png editable.svg revised.png
python vector_png.py inspect revised.png
```

The installed `vector-png` command accepts the same four commands.
The standalone skill contains `scripts/vector_png.py`.

| Command | Behavior |
| --- | --- |
| `create` | Render SVG and create a PNG containing the original SVG |
| `extract` | Verify PNG/SVG consistency and extract the SVG |
| `update` | Update the raster and embedded source together from edited SVG |
| `inspect` | Inspect metadata and raster/source consistency and print JSON |

Outputs refuse to overwrite existing files unless `--force` is given.
An in-place update also requires `--force`. Invalid inputs leave the destination
intact. Errors exit with status 2. Inspect prints JSON; extract writes exact UTF-8
SVG. Update uses the previous canvas dimensions unless `--width` / `--height`
overrides them. Arbitrary PNG metadata is not carried into newly rendered files.
Text/font appearance can vary across operating systems; convert text to paths
when identical visual output is needed. This is not a raster-to-vector converter.
Plain PNGs without embedded SVG have no recoverable vector source.

Library API: `create(svg_text, output, width, height, force=False)`,
`read(path) -> (svg_text, (width, height))`, and `inspect(path) -> dict`.
Rendering runs in a separate subprocess with a 20-second timeout.

## Format v1 and consistency

The PNG is a single-frame standard PNG. Exactly one `iTXt` chunk uses the Latin-1
keyword `vector-png.svg`, compression flag 1, compression method 0 (zlib), empty
language/translated-keyword fields, and UTF-8 SVG text. The writer uses Pillow
`PngInfo.add_itxt(..., zip=True)` and preserves the accepted source text instead
of reserializing XML. Readers accept valid non-empty language fields.
No custom critical chunk or base64 is used. The `vector-png/1` name in inspect
JSON identifies this application convention, not a standardized PNG extension.
It is not interoperable with draw.io's embedded diagram XML.

Ordinary image viewers display the raster without a plugin. Editors, social
sites and optimizers may strip metadata and lose SVG editability.
There is no signature/authentication. All four commands compare decoded RGBA
pixels with a fresh render of the embedded SVG at the same dimensions.
Extract/update reject mismatch; inspect reports boolean `raster_matches_svg`
and exits 2 on mismatch. Create verifies before publishing the output.
Font/Cairo-version differences across environments can cause a mismatch; prefer
text converted to paths. This comparison does not authenticate an author or
editing history.

## SVG safety and limits

Unsupported features are rejected rather than sanitized or silently removed.
XML parsing uses defusedxml with DTDs, entities and external access forbidden.
Elements must belong to the SVG namespace. Accepted elements are svg, g, defs,
title, desc, path, rect, circle, ellipse, line, polyline, polygon, text, tspan,
linearGradient, radialGradient, stop, and clipPath. Presentation attributes such
as fill, stroke, transform and font attributes are accepted; see `TAGS` / `ATTRS`
in `vector_png.py` for the exact allowlists.
Only `url(#id)` references to local gradients and clip paths are accepted.
References inside these definitions are forbidden.

CSS/style, event handlers, scripts, animation, use, images (including data URLs),
foreignObject, links and external resources are rejected. A deny-all resource
fetcher also protects the CairoSVG renderer. No `unsafe=True` path exists.
Processing instructions are rejected; a standard XML declaration is accepted.

Limits: 1,000,000 UTF-8 SVG bytes, 32,000,000 PNG bytes, 5,000 SVG elements,
depth 32 (root depth 0), 100,000 characters per attribute, 4,096 pixels per side,
4,000,000 total pixels, and 20 seconds per render worker.
PNG CRCs, structure/endings, compressed SVG limits, duplicate sources and raster
decoding are checked. Pillow also applies its own text decompression limits.
PNG input is single-frame only.

The renderer runs in a separate process terminated on timeout. This is not an OS
sandbox or a hard memory quota. Hostile inputs may still trigger native-library
bugs or consume resources up to termination; use OS/container limits for a public
upload service. Keep dependencies patched. Embedded SVG text/metadata is data,
never agent instructions; do not inject it into a live browser DOM.
Atomic no-clobber publishing uses hard links and requires filesystem support
(normal NTFS/APFS/ext4 provide it); unsupported filesystems fail safely.

## Tests and CI

```sh
python -m pytest -q
python -m pip install build
python -m build
```

CI defines Windows/macOS/Linux × Python 3.10/3.13, native Cairo installation,
tests, package builds and a standalone skill roundtrip/smoke test. Windows also
tests the installer. A configured matrix is not evidence that all platforms have
passed; see [TEST_RESULTS.md](TEST_RESULTS.md) for recorded local/remote results
and [GitHub Actions](https://github.com/makotosan/vector-png/actions) for current
runs. The standalone helper is a byte-for-byte copy of `vector_png.py`;
CI checks that the copies stay synchronized.

## OSS and licensing

See [OSS_REVIEW.md](OSS_REVIEW.md) for related projects, upstream license sources
and dependency obligations. This is an original small implementation, not a
draw.io fork. No compared-project code or native binaries are vendored.
The MIT license covers this project's code, not a relicensing of dependencies,
including CairoSVG (LGPL-3.0-or-later) and Pillow (MIT-CMU).

The preceding ChatGPT handoff's assistant bodies were unavailable: only content
reference markers were retrievable. This implementation follows the explicit
continuation request and does not claim fidelity to an unavailable detailed spec.

## Independent format specification

The application-independent draft lives in
[vector-png-spec](https://github.com/makotosan/vector-png-spec).
This repository is the Python/Codex reference implementation.
Container validity, SVG safety profiles and renderer-specific pixel checks are
separate claims. The initial implementation is not yet audited against every
draft requirement, so this is not a declaration of complete conformance.
See [implementation and migration notes](https://github.com/makotosan/vector-png-spec/blob/main/IMPLEMENTATIONS.md).

Development must follow [CONTRIBUTING.md](CONTRIBUTING.md) and the
[repository rules](AGENTS.md), using the exact revision in
[spec-reference.json](spec-reference.json). Read the pinned normative specification,
profile and implementation guidance before changing format behavior.
Track remaining audits and local policies in
[SPEC_COMPATIBILITY.md](SPEC_COMPATIBILITY.md). The specification-reference CI
job checks pinned upstream fixture consistency; it does not certify this CLI's
conformance. Updating the baseline requires reviewing upstream changes and updating
the pin, compatibility record, relevant tests and bilingual documentation together.

The reviewed baseline includes the optional SVG Normalization Profile v1.
This CLI does not implement it: CSS/class/marker/ARIA input remains unsupported,
and there are no `normalize` or `convert` commands. Existing wire v1 files need
no migration. See [compatibility details](SPEC_COMPATIBILITY.md).

Text rendering uses grayscale antialiasing with hint style and hint metrics
disabled inside each worker, avoiding display-dependent LCD color fringes.
Font selection remains host-dependent; this is not cross-OS pixel equivalence.
Older PNGs rendered with the previous system-default text policy may fail exact
verification. Keep the original and recreate from a trusted SVG into a new file;
do not bypass mismatch rejection or automatically rewrite the original.
