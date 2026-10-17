# Specification compatibility record

[日本語](SPEC_COMPATIBILITY.ja.md)

## Baseline and status

Development targets [vector-png-spec at `491ba1783ca0819fa557aa34f9a4d89365f1e465`](https://github.com/makotosan/vector-png-spec/tree/491ba1783ca0819fa557aa34f9a4d89365f1e465),
wire v1 / draft 0.1, as recorded in [spec-reference.json](spec-reference.json).
English SPEC.md is normative; SPEC.ja.md is a full informative translation.
The shared source keyword is `vector-png.svg` in compressed iTXt.
This record establishes the reference for future development; it does not upgrade
runtime behavior or declare complete conformance.

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

## Updating this record

For each relevant change, record the pinned revision, specification section,
expected behavior, implementation test/fixture evidence and remaining deviations
in this document or a linked issue/PR. Update both language versions together.
Existing implementation test results remain recorded in [TEST_RESULTS.md](TEST_RESULTS.md).
The specification-reference CI job checks upstream fixture consistency only;
implementation tests and preview verification are separate evidence.
Follow [CONTRIBUTING.md](CONTRIBUTING.md) when changing the pin or behavior.
