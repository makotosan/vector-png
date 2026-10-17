# Development rules for vector-png

These rules apply throughout this repository.

## Specification first

- Use the application-independent vector-png-spec repository as the authority
  for file-format requirements. Read spec-reference.json for the exact pinned
  repository, revision and document paths before changing PNG/SVG reading,
  writing, extraction, validation, limits or interoperability behavior.
- Read the pinned English SPEC.md, the relevant safe-svg-v1 profile sections
  and IMPLEMENTATIONS.md. SPEC.ja.md is a full informative translation; it does
  not supersede the English normative text.
- Follow CONTRIBUTING.md / CONTRIBUTING.ja.md. Map behavior changes to spec
  sections and relevant fixtures, add implementation tests, and record gaps in
  SPEC_COMPATIBILITY.md / SPEC_COMPATIBILITY.ja.md.
- Separate container validity, SVG safety/profile support and renderer-specific
  preview comparison. Do not make CairoSVG pixel equality a universal format rule.
- Do not silently redefine vector-png.svg or add mandatory on-wire fields.
  Propose format changes upstream first and describe compatibility impact.
- The pin is a development baseline, not a declaration of complete conformance.
  Review upstream changes deliberately; do not automatically track main. Update
  the pin, compatibility records, affected bilingual docs and tests together.
  If the pinned specification cannot be retrieved, report the evidence gap
  instead of inventing requirements or claiming conformance.

## English/Japanese documentation parity

- Existing language pairs must convey identical complete content, not summaries.
  Update both languages in the same change, preserving sections, requirement
  strength, conditions, exceptions, numbers, identifiers, tables, examples,
  commands, references, warnings, limits, status and compatibility claims.
- Every public Japanese document needs an English counterpart and mutual links.
  English-only documents do not all require a Japanese translation.
- Compare affected pairs section by section for meaning before completion;
  structural checks alone are insufficient. Report the parity review result.
- This AGENTS.md is agent guidance and does not require a translated counterpart.

## Verification and scope

- Keep vector_png.py and skills/vector-png/scripts/vector_png.py byte-identical
  when changing the helper. Run relevant pytest and standalone roundtrip checks.
- The specification-reference CI job checks pinned fixture consistency only.
  It does not certify this implementation's conformance. Report its result
  separately from implementation tests and raster/source verification.
