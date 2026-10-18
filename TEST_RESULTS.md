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

## Specification baseline review (2026-10-19)

- Reviewed specification commit `8238ebdaa136f448affa53133b99ee5afde5765a`,
  including SPEC section 5, IMPLEMENTATIONS and svg-normalization-v1 sections 1–8.
- Wire v1 and safe-svg-v1 are unchanged. Optional normalization remains unimplemented;
  production dependencies are unchanged. The local text policy is updated below.
- Local Python 3.13 implementation suite: **43 passed** (41 existing + 2 regressions).
  The pytest cache warning is an execution-environment permission issue, not a test failure.
- Pinned upstream structural suite: **10 passed** with tinycss2 installed.
  Both original and normalization catalog reproducibility checks passed.
  Temporary-directory permissions initially blocked an upstream transaction test;
  rerunning with approved normal permissions passed.
- The new nameplate tests cover early CSS rejection/output protection and the
  safe golden SVG's PNG roundtrip, exact extraction and CairoSVG raster verification.
  They do not establish normalization or before/after SVG2 appearance equivalence.
- README, CONTRIBUTING and SPEC_COMPATIBILITY English/Japanese pairs were reviewed
  section by section for equivalent requirements, status, links and limitations.
- Linux/macOS/Windows validation is configured in GitHub Actions; consult the
  workflow for this commit's actual outcome rather than treating configuration as a pass.

### Windows regression investigation

The new nameplate test exposed a real strict-comparison failure on both Windows
Python versions in [run 39152251592](https://github.com/makotosan/vector-png/actions/runs/39152251592).
Diagnostics in run 39152481159 confirmed identical embedded source bytes and
differences confined to the bold text area (53,50)-(230,70), with LCD color fringes.
The worker now explicitly selects grayscale antialiasing, no hint style and no
hint metrics. The regression also requires the black text region to remain
monochrome. Comparison is still exact; no tolerance or Windows skip is added.
Previously rendered text PNGs may mismatch; keep originals and use trusted SVG
to create a separate new file. New CI results must be checked independently.

## Explicit normalization implementation, version 0.2.0 (2026-10-19)

- Specification pin remains 8238ebdaa136f448affa53133b99ee5afde5765a.
  Implemented normalization sections 2–7 and the section-8 CLI proposals under
  the existing SPEC sections 5–7 import/writer policy. Wire v1 is unchanged.
- Production structure processing adapts the pinned MIT fixture transformer
  with defused bounded XML parsing, early validation of losing references,
  strict marker path parsing, accessibility cycles, complete safe-output checks
  and a separate no-clobber publication pipeline. The upstream helper alone
  is not presented as a production security boundary.
- Final local full suite before the last report distinction: **117 passed,
  1 skipped** on Windows / Python 3.13. The skip is symlink creation unavailable
  to this user; hardlink aliases, existing reports and rollback were tested.
  The earlier full run was 115 passed/1 skipped, before two additional cases.
- Optional-only suite after those cases: **74 passed, 1 skipped**. It used
  Playwright **1.64.0**, Chromium **156.0.8078.4**, CairoSVG 2.9.1, Pillow 13.0.0,
  tinycss2 1.5.1 and defusedxml 0.7.1. Real rendering tests were required.
- Final targeted checks: **4 passed**, covering the added PNG-preview-failure report distinction,
  real nameplate conversion, alias/no-clobber/rollback and render mismatch.
  A pixel mismatch is not mislabeled container corruption; independent Chromium
  normalization and CairoSVG PNG-preview outcomes remain separate.
- Actual Chromium tests cover cascade/group opacity, CSS rounded rectangles,
  two restricted triangle arrows, metadata migration/loss and the complete
  synthetic nameplate. Nameplate PNG extraction equals the normalized golden
  SVG bytes; source bytes remain unchanged. Unsafe samples are rejected before
  browser launch. These are finite fixture results, not complete certification.
- Standalone normalization_check.py passed normalize, convert and exact
  extraction using the distributed helper modules. Version 0.2.0 source archive
  and universal wheel built successfully, including the three CLI modules.
- README, INSTALL, CONTRIBUTING, SPEC_COMPATIBILITY and the new NORMALIZATION
  English/Japanese pairs were compared section by section for full semantic
  parity, commands, tables, references, limits and compatibility claims.
  The skill frontmatter validator also passed.
- Expanded CI requires optional dependencies/Chromium and real rendering on
  Windows/macOS/Linux × Python 3.10/3.13, tests the Windows installer with
  -WithNormalization and checks all three helper copies. Current remote results
  must be read from GitHub Actions; configuration alone is not a pass.
