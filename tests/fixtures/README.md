# Specification regression fixtures

These synthetic nameplate SVGs are copied byte-for-byte from
[vector-png-spec at 8238ebdaa136f448affa53133b99ee5afde5765a](https://github.com/makotosan/vector-png-spec/tree/8238ebdaa136f448affa53133b99ee5afde5765a/fixtures/normalization):
`nameplate.input.svg` → `normalization-input.svg`,
`nameplate.expected.svg` → `normalization-safe.svg`.
They contain original public test artwork, not customer material.
Copyright (c) 2026 makotosan. MIT licensed; see the distribution's LICENSE.
The expected SVG is a structural golden output, not a verified normalization report.
Tests here exercise this CLI's rejection and safe-source roundtrip only.

normalization-cases.json also copies the public cases.json catalog from that same
pinned upstream fixtures/normalization directory under its MIT license.
