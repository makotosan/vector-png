# Specification compatibility record

[日本語](SPEC_COMPATIBILITY.ja.md)

## Baseline and status

Development targets [vector-png-spec at `8238ebdaa136f448affa53133b99ee5afde5765a`](https://github.com/makotosan/vector-png-spec/tree/8238ebdaa136f448affa53133b99ee5afde5765a),
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

## Reviewed specification update: 2026-10-19

The baseline advances from `491ba1783ca0819fa557aa34f9a4d89365f1e465` to `8238ebdaa136f448affa53133b99ee5afde5765a`.
SPEC section 5 and IMPLEMENTATIONS add the optional
[SVG Normalization Profile v1](https://github.com/makotosan/vector-png-spec/blob/8238ebdaa136f448affa53133b99ee5afde5765a/profiles/svg-normalization-v1.md).
Wire v1, `vector-png.svg`, safe-svg-v1 and the original 21 container cases are unchanged.
Existing files require no migration.

Normalization sections 2–7 require validated/tokenized CSS, cascade and inheritance,
restricted arrow expansion, accessibility migration, a controlled SVG2 before/after
rendering gate, separate reports and transactional no-clobber publication.
This implementation does **not** implement that optional profile: `normalize` and
`convert` are not commands. The four existing commands continue to reject CSS,
classes, markers and ARIA metadata rather than strip them. CairoSVG pixel checks
on an already-safe SVG do not establish SVG2 normalization equivalence.

Regression tests use the pinned synthetic nameplate input and expected normalized
SVG. They check rejection before rendering/publication, safe-output acceptance,
byte-preserving PNG extraction and source/raster verification. These do not
verify the upstream transformation or before/after appearance. Upstream
normalization structural/catalog tests run separately in specification-reference
CI with tinycss2; they do not certify this CLI as a normalizer.
No production dependency, output vocabulary or extraction behavior changes.
The outstanding audits above remain open.

## Updating this record

For each relevant change, record the pinned revision, specification section,
expected behavior, implementation test/fixture evidence and remaining deviations
in this document or a linked issue/PR. Update both language versions together.
Existing implementation test results remain recorded in [TEST_RESULTS.md](TEST_RESULTS.md).
The specification-reference CI job checks upstream fixture consistency only;
implementation tests and preview verification are separate evidence.
Follow [CONTRIBUTING.md](CONTRIBUTING.md) when changing the pin or behavior.
