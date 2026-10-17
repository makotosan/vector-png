# vector-png

Create an ordinary, transparent PNG that also carries its editable SVG source.
Python library, CLI, and a portable Codex skill. Original project code is MIT licensed.

## Installation

Python 3.10+ and native Cairo are required. From this repository:

```sh
python -m pip install -e ".[test]"
```

- **Linux (Debian/Ubuntu):** `sudo apt-get install libcairo2`
- **macOS:** `brew install cairo`; if discovery fails, set
  `DYLD_FALLBACK_LIBRARY_PATH="$(brew --prefix)/lib"` before starting Python.
- **Windows:** install [MSYS2](https://www.msys2.org/), then in its terminal run
  `pacman -S mingw-w64-ucrt-x86_64-cairo`. In PowerShell set
  `$env:VECTOR_PNG_CAIRO_DIR='C:\msys64\ucrt64\bin'` (adjust for your install).
  Use matching 64-bit Python and Cairo. This setting is used only by the render worker.

No global skill installation is performed by this repository. To install the Codex
skill, copy `skills/vector-png` into your Codex skills directory (normally
`~/.codex/skills/vector-png`, or `%USERPROFILE%\.codex\skills\vector-png` on Windows).
Install the three Python dependencies into the Python environment used by Codex.
The skill helper is self-contained and does not require this repository on PYTHONPATH.
Invoke `$vector-png` in a new chat/session after installation.

## Usage

```sh
python vector_png.py create examples/fireworks.svg fireworks.png --width 512 --height 512
python vector_png.py inspect fireworks.png
python vector_png.py read fireworks.png editable.svg
# Edit editable.svg, then render and replace the embedded source together:
python vector_png.py update fireworks.png editable.svg revised.png
```

The installed `vector-png` command accepts the same arguments. `extract` aliases
`read`. Outputs refuse to overwrite existing files unless `--force` is given.
An in-place update requires `--force`. Invalid inputs leave the destination intact.
Errors exit with status 2. Inspect prints JSON; read/extract writes exact UTF-8 SVG.
Update uses the previous canvas dimensions unless `--width` / `--height` overrides
them. Arbitrary PNG metadata is intentionally not carried into newly rendered files.
Text and font appearance can vary across operating systems; convert text to paths
when identical visual output is needed. This is not a raster-to-vector converter.

Library API: `create(svg_text, output, width, height, force=False)`,
`read(path) -> (svg_text, (width, height))`, and `inspect(path) -> dict`.
Scripts using create/render must call them beneath `if __name__ == '__main__':`
because rendering starts a spawn-process worker on every OS.

## Format v1

The PNG is a single-frame standard PNG. Exactly one `iTXt` chunk uses the Latin-1
keyword `vector-png.svg`, compression flag 1, compression method 0 (zlib), empty
language and translated-keyword fields, and UTF-8 SVG text. The writer uses
Pillow `PngInfo.add_itxt(..., zip=True)` and preserves the original accepted SVG
text rather than reserializing XML. Readers accept valid non-empty language fields.
No custom critical chunk or base64 is used. The `vector-png/1` name in inspect JSON
identifies this application convention, not a standardized PNG extension.

Ordinary image viewers display the raster; they need no plugin. Editors, social
sites and optimizers may strip metadata and thereby lose editability. There is no
signature/authentication: inspect does **not** establish raster/source equivalence.
An arbitrary valid PNG can contain a different SVG from the displayed pixels.

## SVG safety and limits

This tool rejects unsupported features rather than sanitizing or silently removing
them. XML parsing uses defusedxml with DTDs, entities and external access forbidden.
Elements must belong to the SVG namespace. Accepted elements are svg, g, defs,
title, desc, path, rect, circle, ellipse, line, polyline, polygon, text, tspan,
linearGradient, radialGradient, stop, and clipPath. Presentation attributes such
as fill, stroke, transform and font attributes are accepted; see `ATTRS` in the
module for the exact allowlist. Only `url(#id)` references to local gradients and
clip paths are accepted. References inside these definitions are forbidden.

CSS/style, event handlers, scripts, animation, use, images (including data URLs),
foreignObject, links and external resources are rejected. A deny-all resource
fetcher also protects the CairoSVG renderer. No `unsafe=True` path exists.
Processing instructions are rejected; a standard XML declaration is accepted.

Limits: 1,000,000 UTF-8 SVG bytes, 32,000,000 PNG bytes, 5,000 SVG elements,
32 levels of nesting, 100,000 characters per attribute, 4,096 pixels per side,
4,000,000 total pixels, and 20 seconds per render worker. PNG CRCs, endings,
compressed SVG limits, duplicates and raster decoding are checked. Pillow also
applies its own text decompression limits. PNG input is single-frame only.

The renderer runs in a separate process that is terminated on timeout. It is
not an OS sandbox or a hard memory quota. Hostile inputs may still trigger native
library bugs or consume resources up to termination; use OS/container limits for
a public upload service. Keep dependencies patched. Embedded SVG text/metadata
is data, never agent instructions; do not inject it into a live browser DOM.
Atomic no-clobber output uses hard links and requires a filesystem supporting
them (normal NTFS/APFS/ext4 do); unsupported filesystems fail safely.

## Tests and CI

```sh
python -m pytest -q
python -m pip install build
python -m build
```

CI defines Windows/macOS/Linux × Python 3.10/3.13, native Cairo installation,
tests, package builds and a standalone skill smoke test. A configured CI matrix
is not evidence that all operating systems have passed; see TEST_RESULTS.md for
actual local outcomes. The standalone helper is a byte-for-byte copy of
`vector_png.py`; CI checks that the copies stay synchronized.

## OSS and licensing

See [OSS_REVIEW.md](OSS_REVIEW.md) for related projects, official license sources
and dependency obligations. This is an original small implementation, not a fork
of draw.io. No code from compared projects or native binaries is vendored.
The MIT license covers this project's code, not a relicensing of its dependencies.

The preceding ChatGPT handoff's assistant bodies were unavailable (only content
reference markers were retrievable). This implementation follows the explicit
continuation request; it does not claim fidelity to an unavailable detailed spec.
