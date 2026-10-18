# OSS and license review

Checked 2026-10-17 against upstream documentation and license files. This is a
focused comparison, not a claim that no other similar project exists.

| Project | Existing capability / role | Upstream license |
| --- | --- | --- |
| [draw.io](https://github.com/jgraph/drawio) | Editable PNG with embedded draw.io XML, rather than this SVG/iTXt convention. [Format](https://github.com/jgraph/drawio/wiki/File-Format) | [Apache-2.0](https://github.com/jgraph/drawio/blob/dev/LICENSE) |
| [CairoSVG](https://cairosvg.org/documentation/) | SVG rendering engine used here; not itself an editable-PNG container | [LGPL-3.0-or-later](https://github.com/Kozea/CairoSVG/blob/main/setup.cfg) |
| [Pillow](https://pillow.readthedocs.io/en/stable/PIL.html) | PNG encoding/decoding and compressed iTXt writing used here | [MIT-CMU](https://github.com/python-pillow/Pillow/blob/main/LICENSE) |
| [defusedxml](https://github.com/tiran/defusedxml) | Restricts unsafe XML parsing, used here | [PSF](https://github.com/tiran/defusedxml/blob/main/LICENSE) |

No code from the compared projects in the table was copied. The original application and skill are MIT.
Dependencies retain their own licenses. CairoSVG is LGPL, so distributing it or a
bundled application requires preserving applicable notices, source availability
and replacement/relinking rights; the MIT label does not remove those obligations.
This repository declares dependencies rather than redistributing their sources
or binaries. Downstream distributors must review the exact versions they ship,
including transitive dependencies and native libraries.

Native [Cairo](https://www.cairographics.org/) uses LGPL-2.1/MPL-1.1 dual licensing;
its compiled dependency stack may have additional notices. We install it through
OS package managers; no native DLLs are included in this repository.
Other runtime dependencies include cairocffi (BSD), cffi (MIT), cssselect2
(BSD), tinycss2 (BSD), webencodings (BSD), and pycparser (BSD). Consult installed
distribution metadata/license files for exact versions and full notices.
Build/test dependencies are development tools and are not bundled in the wheel.

There is no verified interoperability with draw.io PNG files; vector-png rejects
plain PNG or other embedded document formats without its own keyword. The
convention is documented in README so other tools can implement it independently.


## Normalization additions (2026-10-19)

vector_png_css.py adapts tools/normalization_fixture.py from
[vector-png-spec at 8238ebdaa136f448affa53133b99ee5afde5765a](https://github.com/makotosan/vector-png-spec/blob/8238ebdaa136f448affa53133b99ee5afde5765a/tools/normalization_fixture.py),
Copyright (c) 2026 makotosan, MIT. The source-file attribution and repository/skill
MIT license are retained. Production changes include defused bounded parsing,
early reference checks, strict path lexing, metadata cycle handling, independent
safe-output validation and separate controlled rendering/publication. The fixture
helper alone is not presented as an audited sanitizer.

Optional direct dependencies: tinycss2 (BSD-3-Clause, checked in installed
1.5.1 license) and Playwright 1.64.0 (Apache-2.0; installed distribution LICENSE
and NOTICE). Playwright's Chromium and its third-party components have separate
notices; browser installation downloads them rather than embedding them in the
repository or wheel. Review notices and exact transitive/native versions if
redistributing an application or browser. No dependency is relicensed to MIT.
The browser/driver and Python dependencies must be kept patched and retested;
pinning for reproducibility is not a security guarantee.
