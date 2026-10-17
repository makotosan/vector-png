# Validation results

## Integrity verification and user-skill installer (2026-10-18)

The updated user skill passed **41 local pytest tests**, including pixel and
embedded-source tampering rejection. The standalone create → extract → edit →
update → inspect check passed from outside the skill directory. Skill syntax
validation passed. The PowerShell installer passed syntax parsing. The local
user-skill destination is outside this session's permitted write roots, so local
installation/discovery has not been performed. INSTALL.md includes the exact
installation and fresh-session discovery steps. Updated CI also runs the complete
Windows installer on its disposable runners and a roundtrip on every platform.
The previous six-job success below applies to the preceding implementation.

Updated verification: **all six CI jobs passed**, including the full Windows
user-skill installation (copy, dedicated venv, dependency installation and CLI
roundtrip) on Python 3.10 and 3.13. Tested implementation commit:
`fe623995de3ee436f5fdfd5dfa2c9dd575206826`.
[Successful installer workflow](https://github.com/makotosan/vector-png/actions/runs/39043808350).
This verifies installation on disposable CI runners; the user's local installation
and discovery in a new Codex session remain separate steps.

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

Initial remote CI passed Linux/macOS on Python 3.10 and 3.13. Windows exposed
CFFI DLL discovery requiring PATH in addition to add_dll_directory; the render
worker now sets both within its own process. The corrected run's results are
available in GitHub Actions.

Final remote verification (2026-10-18 Asia/Tokyo): **all six jobs passed** for
Windows, macOS and Linux on Python 3.10 and 3.13, including pytest, package build
and the standalone skill smoke test. Tested implementation commit:
`a85cccff5172d23bf9d27ff3e695c2aedf8db46a`.
[Successful workflow run](https://github.com/makotosan/vector-png/actions/runs/39043089032).
The optional skill is packaged in the source archive/repository, not in the CLI wheel.
No global Codex installation or machine-wide Python modification was performed.
