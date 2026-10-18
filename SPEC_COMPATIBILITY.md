# Specification compatibility record

[日本語](SPEC_COMPATIBILITY.ja.md)

## Baseline and status

Development targets [vector-png-spec at `8238ebdaa136f448affa53133b99ee5afde5765a`](https://github.com/makotosan/vector-png-spec/tree/8238ebdaa136f448affa53133b99ee5afde5765a),
wire v1 / draft 0.1, as recorded in [spec-reference.json](spec-reference.json).
English SPEC.md is normative; SPEC.ja.md is a full informative translation.
The shared source keyword is `vector-png.svg` in compressed iTXt.
This record tracks the development reference, tested scope and outstanding audits;
it does not declare complete conformance.

## Verification and outstanding audit

| Area | Current status / development requirement |
| --- | --- |
| Container, SPEC sections 2–3 | Compressed iTXt support exists. Full PNG ordering, unknown critical chunks and rejection of every APNG marker still need a requirement-by-requirement audit. |
| UTF-8/XML, SPEC section 3 | Exact extraction including BOM and conflicting declared XML encoding need dedicated conformance checks. Do not infer compliance from ordinary UTF-8 roundtrips. |
| Limits and outcomes, SPEC section 4 | The CLI has finite byte/pixel/complexity limits. Audit limits and distinctions between malformed, unsupported and resource-limited inputs against the pinned requirements. |
| SVG profile, SPEC section 5 | The CLI uses an allowlist and denies external resource fetching. Check safe-svg-v1 and test profile acceptance separately from container validity. |
| Editing/preview, SPEC sections 6–7 | The CLI regenerates source/raster together and requires exact CairoSVG/RGBA equality. This is stricter local policy, not a universal format requirement or author authentication. |
| Identification/claims, SPEC section 8 | Do not add mandatory fields or silently change the existing keyword. Describe tested scope and unresolved requirements rather than claiming complete conformance. |

These are audit areas, not a finding that every listed case currently fails.
Track individual requirements and evidence as behavior is audited or changed.
Keep renderer, fonts, color/alpha policy and comparison method explicit when
reporting preview verification. An unchecked preview must not be called verified.

The pinned specification's 21-case fixture catalog includes container-valid
unsafe SVG and differing-preview samples. The production CLI may reject those
under its safety/preview policy; do not treat every container-positive fixture as
a successful production import. The catalog checker covers a tiny raster subset
and is not a full PNG decoder, security sanitizer or certification suite.

## Reviewed specification update: 2026-10-19

The baseline advances from `491ba1783ca0819fa557aa34f9a4d89365f1e465` to `8238ebdaa136f448affa53133b99ee5afde5765a`.
SPEC section 5 and IMPLEMENTATIONS add the optional
[SVG Normalization Profile v1](https://github.com/makotosan/vector-png-spec/blob/8238ebdaa136f448affa53133b99ee5afde5765a/profiles/svg-normalization-v1.md).
Wire v1, `vector-png.svg`, safe-svg-v1 and the original 21 container cases are unchanged.
Existing files require no migration.

Normalization sections 2–7 are implemented experimentally in version 0.2.0:
bounded/tokenized CSS, cascade/inheritance, restricted arrows, metadata migration,
independent safe output validation, controlled Chromium before/after RGBA
comparison, reports and no-clobber pair publication with rollback on handled failure.
The original four commands retain their strict input policy and exact CairoSVG
comparison. Convert additionally runs the existing writer/reader checks; its
CairoSVG PNG comparison is separate from the Chromium normalization gate.

Tests adapt the pinned 24-case normalization catalog plus synthetic nameplate
goldens and new regressions for overridden references, malformed CSS, metadata
cycles, unused markers, resource bounds, output aliases, mismatch and publication
rollback. Real CLI tests cover CSS cascade/group opacity, CSS rounded boxes,
horizontal/returning arrows, accessibility loss and the nameplate PNG/extract
roundtrip. See TEST_RESULTS.md for executed results; upstream structural fixture
CI remains separate and cannot certify this implementation.

Optional dependencies are tinycss2 and Playwright 1.64.0 with its Chromium.
Additional local limits include 128-character CSS/marker numeric tokens, accessibility
reference depth 32, 15-second transformation and 60-second browser deadlines,
bounded IPC/report sizes and a 128 MB JavaScript heap. There is no hard native
memory quota, public-upload sandbox, crash-atomic two-file commit or guarantee
against malicious concurrent parent-directory replacement. No permissive CSS,
render bypass, automatic extraction normalization or overwrite mode is provided.
Exact mismatch (including floating-point/font differences) fails without output.
Metadata losses are reported, not claimed equivalent. The Chromium transform
gate does not assert that CairoSVG PNG pixels match Chromium. See the full scope,
policies and report schema in [NORMALIZATION.md](NORMALIZATION.md).
The outstanding container audits above remain open. Wire/output vocabulary and
extraction are unchanged; optional importing and dependencies are added.

## Updating this record

For each relevant change, record the pinned revision, specification section,
expected behavior, implementation test/fixture evidence and remaining deviations
in this document or a linked issue/PR. Update both language versions together.
Existing implementation test results remain recorded in [TEST_RESULTS.md](TEST_RESULTS.md).
The specification-reference CI job checks upstream fixture consistency only;
implementation tests and preview verification are separate evidence.
Follow [CONTRIBUTING.md](CONTRIBUTING.md) when changing the pin or behavior.

Text rendering uses grayscale antialiasing with hint style and hint metrics
disabled inside each worker, avoiding display-dependent LCD color fringes.
Font selection remains host-dependent; this is not cross-OS pixel equivalence.
Older PNGs rendered with the previous system-default text policy may fail exact
verification. Keep the original and recreate from a trusted SVG into a new file;
do not bypass mismatch rejection or automatically rewrite the original.
