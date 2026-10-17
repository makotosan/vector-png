# OSS and license review

Checked 2026-10-17 against upstream documentation and license files. This is a
focused comparison, not a claim that no other similar project exists.

| Project | Existing capability / role | Upstream license |
| --- | --- | --- |
| [draw.io](https://github.com/jgraph/drawio) | Editable PNG with embedded draw.io XML, rather than this SVG/iTXt convention. [Format](https://github.com/jgraph/drawio/wiki/File-Format) | [Apache-2.0](https://github.com/jgraph/drawio/blob/dev/LICENSE) |
| [CairoSVG](https://cairosvg.org/documentation/) | SVG rendering engine used here; not itself an editable-PNG container | [LGPL-3.0-or-later](https://github.com/Kozea/CairoSVG/blob/main/setup.cfg) |
| [Pillow](https://pillow.readthedocs.io/en/stable/PIL.html) | PNG encoding/decoding and compressed iTXt writing used here | [MIT-CMU](https://github.com/python-pillow/Pillow/blob/main/LICENSE) |
| [defusedxml](https://github.com/tiran/defusedxml) | Restricts unsafe XML parsing, used here | [PSF](https://github.com/tiran/defusedxml/blob/main/LICENSE) |

No compared project code was copied. The original application and skill are MIT.
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
