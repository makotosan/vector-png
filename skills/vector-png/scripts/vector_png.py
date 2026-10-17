"""Create, extract, update and inspect PNGs with compressed SVG and pixel verification."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import zlib

from defusedxml import ElementTree as ET
from PIL import Image
from PIL.PngImagePlugin import PngInfo

KEY = "vector-png.svg"
SIGNATURE = b"\x89PNG\r\n\x1a\n"
SVG_NS = "http://www.w3.org/2000/svg"
MAX_SVG = 1_000_000
MAX_PNG = 32_000_000
MAX_PIXELS = 4_000_000
MAX_SIDE = 4096
TAGS = set("svg g defs title desc path rect circle ellipse line polyline polygon text tspan linearGradient radialGradient stop clipPath".split())
ATTRS = set("id x y x1 y1 x2 y2 cx cy r rx ry width height viewBox preserveAspectRatio d points transform fill fill-opacity fill-rule stroke stroke-width stroke-opacity stroke-linecap stroke-linejoin stroke-miterlimit stroke-dasharray stroke-dashoffset opacity font-family font-size font-weight font-style text-anchor dominant-baseline dx dy rotate offset stop-color stop-opacity gradientUnits gradientTransform spreadMethod fx fy fr clip-path clipPathUnits".split())
FRAGMENT = re.compile(r"url\(#[A-Za-z_][A-Za-z0-9_.-]*\)")


class VectorPNGError(ValueError):
    """Invalid, unsupported or excessive input."""


def bounded_read(path, limit):
    with open(path, "rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise VectorPNGError("Input exceeds size limit")
    return data


def validate_svg(svg: str):
    if len(svg.encode("utf-8")) > MAX_SVG:
        raise VectorPNGError("SVG exceeds 1 MB")
    without_declaration = re.sub(r'^\s*<\?xml\s+[^?]*\?>', '', svg, count=1)
    if '<?' in without_declaration:
        raise VectorPNGError("XML processing instructions are unsupported")
    try:
        root = ET.fromstring(svg, forbid_dtd=True, forbid_entities=True, forbid_external=True)
    except Exception as exc:
        raise VectorPNGError("Invalid or unsafe XML") from exc
    if root.tag != f"{{{SVG_NS}}}svg":
        raise VectorPNGError("Root must be SVG in the SVG namespace")
    ids = {}
    refs = []
    stack = [(root, 0)]
    count = 0
    while stack:
        node, depth = stack.pop()
        count += 1
        if count > 5000 or depth > 32:
            raise VectorPNGError("SVG complexity limit exceeded")
        if not node.tag.startswith(f"{{{SVG_NS}}}") or node.tag.split("}")[-1] not in TAGS:
            raise VectorPNGError(f"Unsupported SVG element: {node.tag}")
        tag = node.tag.split("}")[-1]
        for name, value in node.attrib.items():
            if name not in ATTRS or len(value) > 100_000:
                raise VectorPNGError(f"Unsupported SVG attribute: {name}")
            # CSS escapes, declarations and non-ASCII controls cannot hide resource URLs.
            if any(c in value for c in "\\@{};<>\x00") or any(ord(c) < 32 and c not in "\t\n\r" for c in value):
                raise VectorPNGError("Unsupported attribute syntax")
            if "url" in value.lower():
                if name not in {"fill", "stroke", "clip-path"} or not FRAGMENT.fullmatch(value):
                    raise VectorPNGError("Only local paint/clip URLs are supported")
                refs.append((name, value[5:-1]))
            if name == "id":
                if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]*", value) or value in ids:
                    raise VectorPNGError("Invalid or duplicate SVG id")
                ids[value] = tag
        stack.extend((child, depth + 1) for child in node)
    for name, ref in refs:
        expected = {"clipPath"} if name == "clip-path" else {"linearGradient", "radialGradient"}
        if ids.get(ref) not in expected:
            raise VectorPNGError("Invalid local resource reference")
    # Disallow references from definitions, preventing recursive clips/paint servers.
    for node in root.iter():
        if node.tag.split("}")[-1] in {"clipPath", "linearGradient", "radialGradient"}:
            if any("url" in v.lower() for child in node.iter() for v in child.attrib.values()):
                raise VectorPNGError("References inside resource definitions are unsupported")
    return root


def _deny_fetch(*args, **kwargs):
    raise VectorPNGError("External SVG resources are disabled")


def _render_worker(svg, width, height):
    try:
        # Windows Cairo DLL directory can be supplied without modifying global PATH.
        dll_dir = os.environ.get("VECTOR_PNG_CAIRO_DIR")
        config = Path(__file__).resolve().parent.parent / 'cairo-path.txt'
        if not dll_dir and os.name == 'nt' and config.is_file():
            dll_dir = config.read_text(encoding='utf-8-sig').strip()
        handle = os.add_dll_directory(dll_dir) if os.name == "nt" and dll_dir else None
        if os.name == "nt" and dll_dir:
            # ctypes.find_library and CFFI's legacy loader also need PATH.
            # This changes only the disposable worker's environment.
            os.environ["PATH"] = dll_dir + os.pathsep + os.environ.get("PATH", "")
        from cairosvg.surface import PNGSurface
        png = PNGSurface.convert(bytestring=svg.encode("utf-8"), unsafe=False,
                                 output_width=width, output_height=height,
                                 url_fetcher=_deny_fetch)
        if handle:
            handle.close()
        return png
    except Exception as exc:
        raise VectorPNGError(f"SVG renderer failed: {type(exc).__name__}: {exc}") from exc


def render(svg, width, height, timeout=20):
    validate_svg(svg)
    if (not isinstance(width, int) or not isinstance(height, int)
            or min(width, height) < 1 or max(width, height) > MAX_SIDE
            or width * height > MAX_PIXELS):
        raise VectorPNGError("Invalid dimensions (max side 4096; max 4 million pixels)")
    try:
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), '--render-worker'],
            input=json.dumps([svg, width, height]).encode('utf-8'),
            capture_output=True, timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
        )
    except subprocess.TimeoutExpired as exc:
        raise VectorPNGError("SVG rendering timed out") from exc
    if result.returncode:
        raise VectorPNGError(result.stderr.decode('utf-8', errors='replace')[:2000])
    if len(result.stdout) > MAX_PNG or not result.stdout.startswith(SIGNATURE):
        raise VectorPNGError("SVG renderer returned invalid or excessive PNG")
    return result.stdout


def atomic_write(path, data, force=False):
    target = Path(path)
    fd, temp = tempfile.mkstemp(prefix=".vector-png-", dir=target.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if force:
            os.replace(temp, target)
        else:
            # Atomic no-clobber publish on Windows, macOS and Linux.
            os.link(temp, target)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def create(svg, output, width=512, height=512, force=False):
    png = render(svg, width, height)
    info = PngInfo()
    info.add_itxt(KEY, svg, zip=True)
    with Image.open(io.BytesIO(png)) as image:
        result = io.BytesIO()
        image.save(result, format="PNG", pnginfo=info)
    data = result.getvalue()
    if not _matches(svg, (width, height), data):
        raise VectorPNGError("Saved PNG pixels do not match embedded SVG")
    atomic_write(output, data, force)


def _chunks(data):
    if not data.startswith(SIGNATURE):
        raise VectorPNGError("Not a PNG")
    pos = 8
    count = 0
    while pos + 12 <= len(data):
        count += 1
        if count > 10000:
            raise VectorPNGError("Too many PNG chunks")
        size, = struct.unpack_from(">I", data, pos)
        kind = data[pos + 4:pos + 8]
        end = pos + 8 + size
        if end + 4 > len(data):
            raise VectorPNGError("Truncated PNG chunk")
        payload = data[pos + 8:end]
        crc, = struct.unpack_from(">I", data, end)
        if zlib.crc32(kind + payload) & 0xffffffff != crc:
            raise VectorPNGError("Invalid PNG CRC")
        yield kind, payload
        pos = end + 4
        if kind == b"IEND":
            if size or pos != len(data):
                raise VectorPNGError("Invalid PNG ending")
            return
    raise VectorPNGError("Missing PNG IEND")


def _read_document(path):
    data = bounded_read(path, MAX_PNG)
    found = []
    chunks = list(_chunks(data))
    if not chunks or chunks[0][0] != b"IHDR" or len(chunks[0][1]) != 13:
        raise VectorPNGError("Missing PNG IHDR")
    width, height = struct.unpack(">II", chunks[0][1][:8])
    if min(width, height) < 1 or max(width, height) > MAX_SIDE or width * height > MAX_PIXELS:
        raise VectorPNGError("PNG dimensions exceed limits")
    for kind, payload in chunks:
        keyword = payload.split(b"\0", 1)[0]
        if kind in {b"iTXt", b"tEXt", b"zTXt"} and keyword == KEY.encode():
            if kind != b"iTXt":
                raise VectorPNGError("SVG must use compressed iTXt")
            try:
                rest = payload[len(keyword) + 1:]
                if rest[:2] != b"\x01\x00":
                    raise ValueError("Expected zlib-compressed iTXt")
                language, translated, compressed = rest[2:].split(b"\0", 2)
                language.decode("ascii")
                translated.decode("utf-8")
                dec = zlib.decompressobj()
                raw = dec.decompress(compressed, MAX_SVG + 1)
                if len(raw) > MAX_SVG or not dec.eof or dec.unused_data:
                    raise ValueError("Oversized or invalid compressed SVG")
                found.append(raw.decode("utf-8"))
            except (ValueError, zlib.error, UnicodeError) as exc:
                raise VectorPNGError("Invalid SVG iTXt") from exc
    if len(found) != 1:
        raise VectorPNGError("Expected exactly one embedded SVG")
    validate_svg(found[0])
    try:
        with Image.open(io.BytesIO(data)) as image:
            image.verify()
        with Image.open(io.BytesIO(data)) as image:
            if image.format != "PNG" or getattr(image, "n_frames", 1) != 1:
                raise VectorPNGError("Only single-frame PNG is supported")
            image.load()
    except Exception as exc:
        raise VectorPNGError("Invalid PNG raster or metadata") from exc
    return found[0], (width, height), data


def _matches(svg, size, data):
    rendered = render(svg, *size)
    with Image.open(io.BytesIO(data)) as actual, Image.open(io.BytesIO(rendered)) as expected:
        return actual.convert("RGBA").tobytes() == expected.convert("RGBA").tobytes()


def read(path):
    svg, size, data = _read_document(path)
    if not _matches(svg, size, data):
        raise VectorPNGError("PNG pixels do not match embedded SVG in this rendering environment")
    return svg, size


def inspect(path):
    svg, (width, height), data = _read_document(path)
    return {"format": "vector-png/1", "keyword": KEY, "width": width, "height": height,
            "svg_bytes": len(svg.encode("utf-8")),
            "svg_sha256": hashlib.sha256(svg.encode("utf-8")).hexdigest(),
            "raster_matches_svg": _matches(svg, (width, height), data)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for cmd in ("create", "update"):
        p = sub.add_parser(cmd)
        if cmd == "update":
            p.add_argument("png", type=Path)
        p.add_argument("svg", type=Path)
        p.add_argument("output", type=Path)
        p.add_argument("--width", type=int, default=None)
        p.add_argument("--height", type=int, default=None)
        p.add_argument("--force", action="store_true")
    p = sub.add_parser("extract")
    p.add_argument("png", type=Path)
    p.add_argument("output", type=Path)
    p.add_argument("--force", action="store_true")
    p = sub.add_parser("inspect")
    p.add_argument("png", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "inspect":
            report = inspect(args.png)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            if not report["raster_matches_svg"]:
                parser.exit(2, "vector-png: PNG pixels do not match embedded SVG\n")
        elif args.command == "extract":
            svg, _ = read(args.png)
            atomic_write(args.output, svg.encode("utf-8"), args.force)
        else:
            size = read(args.png)[1] if args.command == "update" else (512, 512)
            svg = bounded_read(args.svg, MAX_SVG).decode("utf-8")
            create(svg, args.output, args.width if args.width is not None else size[0],
                   args.height if args.height is not None else size[1], args.force)
    except (VectorPNGError, OSError, UnicodeError) as exc:
        parser.exit(2, f"vector-png: {exc}\n")


if __name__ == "__main__":
    if sys.argv[1:] == ['--render-worker']:
        try:
            payload = sys.stdin.buffer.read(MAX_SVG * 12 + 1000)
            svg, width, height = json.loads(payload)
            validate_svg(svg)
            if (not isinstance(width, int) or not isinstance(height, int)
                    or min(width, height) < 1 or max(width, height) > MAX_SIDE
                    or width * height > MAX_PIXELS):
                raise VectorPNGError('Invalid dimensions')
            sys.stdout.buffer.write(_render_worker(svg, width, height))
        except Exception as exc:
            sys.stderr.buffer.write(str(exc).encode('utf-8', errors='replace'))
            sys.exit(2)
    else:
        main()
