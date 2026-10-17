# Validation results

Local Windows x64 / Python 3.13, 2026-10-17 (Asia/Tokyo).

- **39 tests passed**, 3.72 seconds, using Pillow 13.0.0, CairoSVG 2.9.1,
  defusedxml 0.7.1 and pytest 9.1.1.
- Covered compressed iTXt roundtrip and Unicode, visible pixel changes after update,
  alpha transparency, gradients, CLI extraction/inspection, no-clobber writes,
  unsafe XML/SVG rejection, local resource reference restrictions, oversized inputs,
  corrupt CRC/truncation/duplicates, decompression bombs and rendering timeout.
- Standalone skill: created and inspected a 512×512 fireworks PNG successfully.
  Embedded SVG SHA-256:
  `4c01aa94aec8f2992bac3194f7c7cdfd48a410c577e7f43512f172b141192b94`.
- Skill creator's quick validator: **Skill is valid!**
- Source distribution and universal Python wheel: built successfully using
  setuptools 84.0.0. Native Cairo remains a separately installed prerequisite.
- This host used its preinstalled Cairo DLLs via VECTOR_PNG_CAIRO_DIR.

The restricted execution environment initially blocked temporary-directory access
and multiprocessing. Tests passed with normal approved execution permissions.
The first build attempt lacked setuptools; adding the build tools resolved it.

Windows/macOS/Linux CI is configured for Python 3.10 and 3.13. Remote results
must be checked in GitHub Actions; local success does not establish those results.
The optional skill is packaged in the source archive/repository, not in the CLI wheel.
No global Codex installation or machine-wide Python modification was performed.
