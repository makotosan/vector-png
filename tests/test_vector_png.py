import io
import struct
import zlib

import pytest
from PIL import Image
from PIL.PngImagePlugin import PngInfo

import vector_png as v

SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="24"><title>花火 🎆</title><rect width="16" height="24" fill="red"/></svg>'


def chunk(kind, payload):
    return struct.pack('>I', len(payload)) + kind + payload + struct.pack('>I', zlib.crc32(kind + payload) & 0xffffffff)


def png_with(payload):
    buf = io.BytesIO()
    Image.new('RGBA', (32, 24)).save(buf, format='PNG')
    data = buf.getvalue()
    return data[:-12] + chunk(b'iTXt', payload) + data[-12:]


def test_roundtrip_pixels_and_compression(tmp_path):
    png = tmp_path / '花火.png'
    v.create(SVG, png, 32, 24)
    assert v.read(png) == (SVG, (32, 24))
    assert v.inspect(png)['svg_bytes'] == len(SVG.encode())
    chunks = list(v._chunks(png.read_bytes()))
    itxt = [p for k, p in chunks if k == b'iTXt']
    assert itxt[0].startswith(v.KEY.encode() + b'\0\x01\0\0\0')
    with Image.open(png) as im:
        assert im.getpixel((8, 12)) == (255, 0, 0, 255)
        assert im.getpixel((24, 12))[3] == 0


def test_cli_update_extract_inspect_and_no_clobber(tmp_path, capsys):
    svg = tmp_path / 'source.svg'
    svg.write_text(SVG, encoding='utf-8')
    png = tmp_path / 'out.png'
    v.main(['create', str(svg), str(png), '--width', '32', '--height', '24'])
    original = png.read_bytes()
    with pytest.raises(SystemExit):
        v.main(['create', str(svg), str(png)])
    assert png.read_bytes() == original
    svg.write_text(SVG.replace('red', 'blue'), encoding='utf-8')
    v.main(['update', str(png), str(svg), str(png), '--force'])
    assert v.read(png)[1] == (32, 24)
    with Image.open(png) as im:
        assert im.getpixel((8, 12)) == (0, 0, 255, 255)
    extracted = tmp_path / 'read.svg'
    v.main(['extract', str(png), str(extracted)])
    assert extracted.read_text(encoding='utf-8') == svg.read_text(encoding='utf-8')
    v.main(['inspect', str(png)])
    assert 'not checked' in capsys.readouterr().out


@pytest.mark.parametrize('body', [
    '<script>alert(1)</script>', '<image href="file:///etc/passwd"/>',
    '<use href="#a"/>', '<foreignObject/>', '<style>@import "https://example.com";</style>',
    '<rect style="fill:red"/>', '<rect onload="alert(1)"/>',
    '<rect fill="url(https://example.com/a)"/>', '<rect fill="url(file:///etc/passwd)"/>',
    '<rect fill="url(data:image/svg+xml,abc)"/>', '<rect fill="u\\72l(#a)"/>',
    '<rect xml:base="https://example.com"/>', '<a href="https://example.com"/>',
    '<rect id="a"/><rect id="a"/>', '<rect clip-path="url(#missing)"/>',
    '<defs><clipPath id="a"><rect clip-path="url(#a)"/></clipPath></defs>',
])
def test_reject_unsafe_or_unsupported_svg(body):
    with pytest.raises(v.VectorPNGError):
        v.validate_svg('<svg xmlns="http://www.w3.org/2000/svg">' + body + '</svg>')


@pytest.mark.parametrize('svg', [
    '<!DOCTYPE svg [<!ENTITY x "boom">]><svg xmlns="http://www.w3.org/2000/svg">&x;</svg>',
    '<!DOCTYPE svg SYSTEM "https://example.com/a"><svg/>', '<svg>', '<svg/>',
    '<svg xmlns="http://www.w3.org/2000/svg">' + '<g>' * 40 + '</g>' * 40 + '</svg>',
    '<svg xmlns="http://www.w3.org/2000/svg">' + '<rect/>' * 5001 + '</svg>',
    ' ' * (v.MAX_SVG + 1),
], ids=lambda value: str(len(value)) + '-bytes')
def test_xml_limits(svg):
    with pytest.raises(v.VectorPNGError):
        v.validate_svg(svg)


def test_gradient(tmp_path):
    svg = '<svg xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="a"><stop offset="0" stop-color="red"/><stop offset="1" stop-color="blue"/></linearGradient></defs><rect width="32" height="24" fill="url(#a)"/></svg>'
    v.create(svg, tmp_path / 'gradient.png', 32, 24)
    assert v.read(tmp_path / 'gradient.png')[0] == svg


@pytest.mark.parametrize('size', [(0, 10), (-1, 2), (4097, 1), (3000, 3000)])
def test_dimension_limits(size):
    with pytest.raises(v.VectorPNGError):
        v.render(SVG, *size)


@pytest.mark.parametrize('payload', [
    v.KEY.encode() + b'\0\0\0\0\0' + SVG.encode(),
    v.KEY.encode() + b'\0\1\0\0\0' + zlib.compress(b'a' * (v.MAX_SVG + 1)),
    v.KEY.encode() + b'\0\1\0\0\0' + zlib.compress(SVG.encode()) + b'trailing',
    v.KEY.encode() + b'\0\1\0\0\0broken',
])
def test_bad_itxt(tmp_path, payload):
    p = tmp_path / 'bad.png'
    p.write_bytes(png_with(payload))
    with pytest.raises(v.VectorPNGError):
        v.read(p)


def test_corrupt_missing_duplicate_and_ordinary_png(tmp_path):
    p = tmp_path / 'bad.png'
    payload = v.KEY.encode() + b'\0\1\0\0\0' + zlib.compress(SVG.encode())
    valid = png_with(payload)
    for data in [b'bad', valid[:-1], valid + b'trailing',
                 valid[:-12] + chunk(b'iTXt', payload) + valid[-12:],
                 valid[:40] + bytes([valid[40] ^ 1]) + valid[41:]]:
        p.write_bytes(data)
        with pytest.raises(v.VectorPNGError):
            v.read(p)
    Image.new('RGBA', (4, 4)).save(p)
    with pytest.raises(v.VectorPNGError):
        v.read(p)


def test_atomic_failure_preserves_target(tmp_path):
    p = tmp_path / 'keep.png'
    p.write_bytes(b'original')
    with pytest.raises(v.VectorPNGError):
        v.create('<bad/>', p, force=True)
    assert p.read_bytes() == b'original'
    assert not list(tmp_path.glob('.vector-png-*'))


def test_no_fetch():
    with pytest.raises(v.VectorPNGError):
        v._deny_fetch('https://example.com', 'image/svg+xml')


def test_processing_instruction_rejected():
    with pytest.raises(v.VectorPNGError):
        v.validate_svg('<?xml-stylesheet href="https://example.com/a"?>' + SVG)
    assert v.validate_svg('<?xml version="1.0"?>' + SVG) is not None


def test_render_timeout():
    with pytest.raises(v.VectorPNGError, match='timed out'):
        v.render(SVG, 32, 24, timeout=0)
