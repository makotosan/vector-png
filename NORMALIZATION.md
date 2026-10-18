# Explicit CSS-styled SVG import

[日本語](NORMALIZATION.ja.md) · [README](README.md) · [Installation](INSTALL.md)

## Status and setup

Version 0.2.0 adds experimental `normalize` and `convert` commands implementing
the optional [SVG Normalization Profile v1](https://github.com/makotosan/vector-png-spec/blob/8238ebdaa136f448affa53133b99ee5afde5765a/profiles/svg-normalization-v1.md).
The English profile is normative. The pin remains in spec-reference.json.
This is a closed input subset, not a general SVG/CSS sanitizer or a declaration
of complete wire-v1 conformance. Existing container audit gaps still apply.

For the CLI, install the optional dependencies and their pinned Chromium:

```sh
python -m pip install -e ".[normalize]"
python -m playwright install chromium
```

On Linux, `python -m playwright install --with-deps chromium` also installs the
browser's operating-system dependencies and may require administrator access.
The optional dependencies are tinycss2 (BSD-3-Clause) and Playwright 1.64.0
(Apache-2.0); Chromium has separate third-party notices. Browser binaries are
downloaded by Playwright, not included in this repository or Python wheel.
Review and test renderer updates deliberately; versions are recorded in reports.
Cairo/Pillow remain necessary for PNG conversion and the existing commands.
Chromium's sandbox is requested; a host that blocks its startup returns an error,
with no --no-sandbox fallback. Linux AppArmor/user-namespace setup is described
in INSTALL.md and [Ubuntu's guidance](https://documentation.ubuntu.com/release-notes/24.04/).
For a standalone skill use its requirements-normalization.txt and its own Python;
the Windows installer supports `-WithNormalization`. See INSTALL.md.

## Commands

```sh
python vector_png.py normalize examples/css-diagram.svg normalized.svg --report normalize-report.json
python vector_png.py convert examples/css-diagram.svg diagram.png --report convert-report.json
python vector_png.py extract diagram.png extracted.svg
```

The installed `vector-png` command accepts the same arguments. `--report` is
required for both new commands. Optional `--width` / `--height` choose integer
pixel dimensions independently. Otherwise each dimension uses the ceiling of a
positive root unitless/px length, then the corresponding viewBox dimension, then
512. The chosen viewport must obey the limits below. Other root units fall back
to viewBox/default; rendering may still fail if geometry is unsupported.

`normalize` publishes normalized UTF-8 SVG and its JSON report. `convert` first
runs that transformation/render gate, then renders a PNG with the existing
writer and embeds only the normalized SVG in compressed iTXt. The original SVG
and report are never embedded. Extraction preserves the stored normalized bytes;
it does not reconstruct the original CSS or automatically normalize anything.
The four existing commands keep their strict safe-SVG input policy.

## Accepted subset and migration

Input is strict UTF-8 XML, optionally with a BOM/UTF-8 declaration. The vocabulary
is safe-svg-v1 plus restricted root/root-defs style elements, class/inline style,
role/aria metadata and the profile's triangle arrow markers. All declarations
are checked, including unused, unmatched and overridden ones. DTDs, entities,
processing instructions, scripts, event handlers, foreign namespaces, image/use,
foreignObject, animation, external resources and unknown vocabulary fail before
any browser is started. Comments are allowed.

tinycss2 tokenizes the closed CSS subset. Only an element, `.class`, or `#id`
selector and comma-separated lists are accepted. Presentation attributes, author
rules and inline declarations resolve by specificity and source order. Geometry,
text, hierarchy, IDs and local resources are retained; winning properties become
presentation attributes. Group opacity/clipping is not flattened. CSS rect rx/ry
becomes geometry attributes. Unsupported selectors, at-rules, escapes, shorthands,
custom properties, !important, external URLs, calc/var, unsupported units/values
or malformed declarations fail rather than being silently ignored.

Only viewport-contained solid triangle markers with orient=auto, supported
marker units and open absolute M/L/H/V host paths are expanded. Host transform,
opacity or clip-path declarations, curves, multiple subpaths, degenerate final
segments and other marker forms fail. Expansion preserves parent compositing
and paint order and reports expanded_markers. Every unused definition is also
validated. Floating-point geometry that fails the exact rendering gate is rejected.

Accessible name precedence is aria-labelledby, aria-label, then existing title.
Referenced text-only IDs must exist, be unique in each list and be noncyclic.
Names/descriptions migrate to direct title/desc; replaced text and every removed
role/aria attribute are reported with their original value, element path, target
or loss reason. Review accessibility-loss warnings. Success does not promise full
accessibility or native-editor equivalence. Style/class removal and metadata
migration are explicit transformations, not lossless original-source extraction.

## Independent verification and reports

After complete input checks, Chromium renders the original and normalized SVG
as inert SVG image documents in the same browser/context, font environment,
viewport, transparent background and sRGB/alpha policy. Scripts and service
workers are disabled; the context is offline, all network routes abort and CSP
restricts content. No file URL or unchecked SVG DOM insertion is used. CSS SVG2
geometry is handled by Chromium. Exact decoded RGBA equality is mandatory here;
there is no tolerance, skip-render switch or publishable analysis-only mode.
Failure to decode, timeout, render error or mismatch publishes neither output.
Cross-OS pixel equality is not claimed; host fonts remain relevant.

`convert` then separately verifies the generated PNG using the existing
CairoSVG/Pillow writer, container/source checks and exact fresh CairoSVG pixels.
Chromium and CairoSVG are different renderers: the Chromium gate proves the
tested transformation's appearance on that host, while `png_preview` records
the separate PNG/source comparison. It does not claim CairoSVG PNG pixels equal
the Chromium original. No on-wire profile, digest or report field is added.
PNG pixel mismatch is not labeled container corruption: container remains
not-checked if writing failed before structural checks, or pass if already checked.

Successful reports contain profile/status, input/output SHA-256, change counts,
ordered accessibility records, independent input/safe_svg/render/container/
authenticity checks, renderer/version/fonts/viewport/background/color/resource/
comparison details, errors and warnings. output_sha256 hashes the emitted SVG or
PNG bytes; normalized_svg_sha256 separately hashes the embedded normalized SVG.
container is not-applicable for SVG-only output, pass for verified PNG output.
authenticity is always not-verified: hashes and pixels are not signatures.
Reports and source metadata remain untrusted data, never agent instructions.

Success prints the report as JSON to stdout and writes its report file. Runtime
failure exits 2 and prints failure JSON to stderr; output_sha256 is null and no
successful output/report pair is published. Codes distinguish invalid-xml,
unsafe-input, unsupported-css, invalid-reference, resource-limit, output-exists,
output-alias, render-error and render-mismatch (plus I/O/container errors).
Argument-usage errors use argparse diagnostics. Digests are null if no complete
input was read. Failure diagnostics do not overwrite an existing report.

## Limits and publication

Limits: input/output SVG 1,000,000 UTF-8 bytes; PNG 32,000,000 bytes; 5000 elements;
depth 32; 100,000 code points per attribute; 100,000 UTF-8 CSS bytes; 1000 selectors;
10,000 declarations; 4096 pixels per side and 4,000,000 pixels. Additional local
limits are 128 characters per CSS/marker numeric token, accessibility-reference depth 32,
8 MB JSON report/worker response and 4 MB worker request. Resource-limit is a
separate rejection, not proof of malformed input.

Parsing/cascade runs in a disposable worker with a 15-second deadline. A separate
browser worker has a 60-second deadline and 20-second per-operation deadlines.
Timeout cleanup terminates the worker process tree. PNG rendering retains its
20-second worker limit. Memory policy bounds source, XML/CSS complexity, viewport,
IPC and report sizes and sets Chromium's JavaScript heap to 128 MB. These are not
a hard whole-process/native-memory quota or an OS sandbox. Use OS/container
quotas for a public upload service and keep native/browser dependencies patched.

Input, output and report must be distinct, including symlink/hardlink aliases.
The original is never overwritten, and neither command offers --force. Existing
outputs, reports and dangling output symlinks are preserved. Complete files are
staged in their destination directories, flushed and published by no-clobber
hard links. If publishing the second file fails, only the first newly created
file is rolled back. NTFS/APFS/ext4 normally support hard links; unsupported
filesystems fail safely. This is rollback on handled failures, not a two-file
atomic transaction across crashes/power loss; retain the source and inspect any
outputs after an interrupted process. Concurrent malicious parent-directory
replacement is outside the local-filesystem threat model.

## Validation and compatibility

```sh
python -m pip install -e ".[test,normalize]"
python -m playwright install chromium
python -m pytest -q
python skills/vector-png/scripts/normalization_check.py --output-dir normalization-check
```

Structural tests can run without Chromium; actual rendering tests skip with an
explicit reason when it is absent. Set VECTOR_PNG_REQUIRE_NORMALIZATION=1 to
require them. CI sets it on Windows/macOS/Linux and installs the optional browser.
Finite fixtures are evidence of tested behavior, not complete certification.
See TEST_RESULTS.md, SPEC_COMPATIBILITY.md and GitHub Actions for actual results.
Wire v1, vector-png.svg and safe-svg-v1 output remain unchanged. Existing source
extraction and four-command behavior are preserved; conversion is an explicit
additional import path. The normalization module adapts MIT-licensed specification
fixture code with further validation and a production rendering/publication gate;
the fixture helper itself is not treated as a security boundary. See OSS_REVIEW.md.
