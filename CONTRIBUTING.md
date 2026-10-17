# Developing against vector-png-spec

[日本語](CONTRIBUTING.ja.md)

## Baseline and authority

The file-format authority is [vector-png-spec](https://github.com/makotosan/vector-png-spec).
[spec-reference.json](spec-reference.json) pins the development baseline to
commit `491ba1783ca0819fa557aa34f9a4d89365f1e465` (wire v1, draft 0.1).
This is a source-repository reference, not a new field embedded in PNG files.
The pin does not assert complete implementation conformance.

At that revision, read:

- [SPEC.md](https://github.com/makotosan/vector-png-spec/blob/491ba1783ca0819fa557aa34f9a4d89365f1e465/SPEC.md): normative English requirements.
- [SPEC.ja.md](https://github.com/makotosan/vector-png-spec/blob/491ba1783ca0819fa557aa34f9a4d89365f1e465/SPEC.ja.md): full informative Japanese translation.
- [safe-svg-v1](https://github.com/makotosan/vector-png-spec/blob/491ba1783ca0819fa557aa34f9a4d89365f1e465/profiles/safe-svg-v1.md): restricted SVG processing profile.
- [IMPLEMENTATIONS.md](https://github.com/makotosan/vector-png-spec/blob/491ba1783ca0819fa557aa34f9a4d89365f1e465/IMPLEMENTATIONS.md): implementation and migration guidance.
- [Fixture catalog](https://github.com/makotosan/vector-png-spec/blob/491ba1783ca0819fa557aa34f9a4d89365f1e465/fixtures/README.md): fixture usage and limitations.

## Before changing behavior

1. Identify the affected specification sections and whether the change concerns
   the container, SVG profile/security, preview verification or CLI behavior.
2. Check relevant pinned fixtures. A container-valid fixture can contain unsafe
   SVG or a different preview; it is not automatically acceptable to this CLI.
3. Describe intended behavior and known deviations in
   [SPEC_COMPATIBILITY.md](SPEC_COMPATIBILITY.md). Do not silently change the
   meaning of `vector-png.svg`, add mandatory wire fields or weaken SVG safety.
   Propose file-format changes in the specification repository first.
4. Add meaningful implementation tests for changed behavior, update both helper
   copies when applicable, and run relevant pytest and standalone roundtrip checks.
5. In the change description, record the spec revision/sections, affected
   fixtures, test outcomes, compatibility impact and English/Japanese parity review.

Keep container validity, safe SVG profile support and renderer-specific pixel
comparison separate. The CLI's exact CairoSVG/RGBA match is a local implementation
policy, not a requirement imposed on Illustrator/Inkscape or every format reader.

## Updating the specification baseline

Review upstream changes; do not automatically follow `main`. Replace the full
40-character revision in spec-reference.json and update this guide's pinned links
and revision in both languages. Update the compatibility record, relevant tests
and affected bilingual documentation in the same change. Identify any wire/profile
impact and any newly satisfied or unresolved requirements.
If the pinned source is unavailable, report that limitation; do not invent rules.

CI reads the pin, checks out that revision and runs its fixture checks.
Those checks validate the specification's finite test catalog; they do not
exercise this CLI against every fixture or certify complete conformance.
Implementation tests and pixel comparison remain separate checks.

## Documentation and contributions

Follow [AGENTS.md](AGENTS.md). Existing English/Japanese pairs are complete
translations, with equivalent section order, requirement strength, conditions,
exceptions, numbers, identifiers, tables, examples, commands, references,
warnings, limits, status and compatibility claims. Update both in the same change
and manually compare meaning; heading/code/link checks alone do not prove parity.
Each public Japanese document needs an English counterpart and navigation links.
English-only documents do not all require translation.
Contributions use this repository's MIT license; dependencies retain their licenses.
