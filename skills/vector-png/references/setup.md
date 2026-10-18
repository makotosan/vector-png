# Setup and verification

The intended user-skill location is `~/.agents/skills/vector-png/` on all operating
systems, independent of a project's current directory. The folder containing
SKILL.md is the skill root. Restart Codex or open a fresh session after installation.

Install Python dependencies with:

```sh
python -m pip install -r /absolute/path/to/vector-png/requirements.txt
```

Install native Cairo separately:

- Linux (Debian/Ubuntu): `sudo apt-get install libcairo2`
- macOS: `brew install cairo`; if needed export
  `DYLD_FALLBACK_LIBRARY_PATH="$(brew --prefix)/lib"` before running Python.
- Windows: install MSYS2 from its official site, then run
  `pacman -S mingw-w64-ucrt-x86_64-cairo` in its terminal. In PowerShell set
  `$env:VECTOR_PNG_CAIRO_DIR='C:\msys64\ucrt64\bin'`, adjusting for the actual
  install. Use matching 64-bit Python and native libraries. The variable affects
  only the worker's DLL search, not system-wide PATH.
  Alternatively, put the directory path in `cairo-path.txt` at the skill root.
  This is local configuration, never taken from SVG/PNG metadata.

Run `python -m pytest -q` from the skill root. Tests include create/extract/update/
inspect, Unicode compressed iTXt, transparency, unsafe SVG rejection, corrupt
PNG metadata, limits and raster/source tampering. Input SVG is stored as UTF-8
under the keyword `vector-png.svg`, iTXt flag 1/method 0 (zlib).

The source SVG limit is 1 MB; PNG limit 32 MB; maximum side 4096 and total pixels
4 million. SVG limits: 5000 elements and depth 32. The original four commands reject CSS; the optional explicit import path is
described in normalization.md. External resources and scripts are always rejected, and the renderer also has a deny-all resource fetcher.

