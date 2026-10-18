"""Regression boundary for the pinned optional normalization profile."""
from pathlib import Path

import pytest
import vector_png as v

FIXTURES = Path(__file__).parent / "fixtures"


def test_css_input_rejected_before_render_or_publication(tmp_path, monkeypatch):
    source = FIXTURES / "normalization-input.svg"
    original = source.read_bytes()
    target = tmp_path / "keep.png"
    target.write_bytes(b"keep")

    def unexpected_worker(*args, **kwargs):
        pytest.fail("Unsupported input reached the renderer")

    monkeypatch.setattr(v.subprocess, "run", unexpected_worker)
    with pytest.raises(v.VectorPNGError):
        v.create(original.decode("utf-8"), target, 660, 240, force=True)
    assert source.read_bytes() == original
    assert target.read_bytes() == b"keep"
    assert not list(tmp_path.glob(".vector-png-*"))


def test_normalized_golden_source_roundtrip(tmp_path):
    # This tests safe output consumption, NOT normalization or input/output appearance.
    data = (FIXTURES / "normalization-safe.svg").read_bytes()
    png = tmp_path / "nameplate.png"
    v.create(data.decode("utf-8"), png, 660, 240)
    embedded, dimensions, encoded = v._read_document(png)
    assert embedded.encode("utf-8") == data
    try:
        svg, dimensions = v.read(png)
    except v.VectorPNGError:
        import io
        from PIL import Image, ImageChops
        actual = Image.open(io.BytesIO(encoded)).convert("RGBA")
        diagnostics = []
        for _ in range(3):
            fresh = Image.open(io.BytesIO(v.render(embedded, *dimensions))).convert("RGBA")
            delta = ImageChops.difference(actual, fresh).convert("RGB")
            diagnostics.append({"bounds": delta.getbbox(),
                                "first": [(x, y, actual.getpixel((x, y)), fresh.getpixel((x, y)))
                                          for y in range(240) for x in range(660)
                                          if actual.getpixel((x, y)) != fresh.getpixel((x, y))][:5]})
        pytest.fail("Same-source render diagnostics: " + repr(diagnostics))
    assert svg.encode("utf-8") == data
    assert dimensions == (660, 240)
    assert v.inspect(png)["raster_matches_svg"] is True
    extracted = tmp_path / "extracted.svg"
    v.main(["extract", str(png), str(extracted)])
    assert extracted.read_bytes() == data
