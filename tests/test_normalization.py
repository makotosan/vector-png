"""Profile regressions and real controlled-render CLI integrations."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

import vector_png as v
import vector_png_normalize as n

if os.environ.get('VECTOR_PNG_REQUIRE_NORMALIZATION') == '1':
    import vector_png_css as css
else:
    css = pytest.importorskip('vector_png_css', reason='Optional normalization needs tinycss2')
FIXTURES = Path(__file__).parent / 'fixtures'
CASES = json.loads((FIXTURES / 'normalization-cases.json').read_text(encoding='utf-8'))
NS = 'http://www.w3.org/2000/svg'


def svg(body, attrs=''):
    return f'<svg xmlns="{NS}" width="240" height="120" {attrs}>{body}</svg>'.encode()


def case(name):
    return next(c['input'].encode() for c in CASES if c['id'] == name)


@pytest.mark.parametrize('sample', CASES, ids=lambda c: c['id'])
def test_pinned_cases(sample):
    if sample['expect'] == 'accept':
        result, report = css.normalize_structure(sample['input'].encode())
        v.validate_svg(result.decode())
        assert report['status'] == 'failure'  # structure alone never claims success
        assert report['checks']['render'] == 'not-checked'
    else:
        with pytest.raises(css.Rejected) as exc:
            css.normalize_structure(sample['input'].encode())
        assert exc.value.code == sample['expect']


def test_golden_geometry_and_cascade():
    raw = (FIXTURES / 'normalization-input.svg').read_bytes()
    result, report = css.normalize_structure(raw)
    assert result == (FIXTURES / 'normalization-safe.svg').read_bytes()
    assert report['changes']['class_attributes'] == 26
    assert report['changes']['style_elements'] == 1
    before, after = css.parse(raw), css.parse(result)
    find_qr = lambda root: next(e.get('d') for e in root.iter() if e.get('id') == 'qr')
    assert find_qr(before) == find_qr(after)
    result, _ = css.normalize_structure(case('cascade'))
    group = list(css.parse(result))[0]
    assert group.get('opacity') == '0.5'
    assert list(group)[0].get('fill') == 'green'
    assert list(group)[1].get('fill') == 'navy'
    assert all(e.get('opacity') is None for e in group)


@pytest.mark.parametrize('body', [
    '<rect fill="url(#missing)" style="fill:red"/>',
    '<style>.unused {fill:url(#missing)}</style>',
    '<defs><clipPath id="c"><rect fill="url(#p)"/></clipPath><linearGradient id="p"/></defs>',
    '<style>.a {fill:var(--x)}</style>',
    '<style>rect {fill:red !important; fill:blue}</style>',
    '<style>rect > path {fill:red}</style>',
    '<style>rect.a {fill:red}</style>',
    '<style>rect {--x:red}</style>',
    '<rect style="fill:rgba(0,0,0,1)"/>',
    '<rect style="stroke-dasharray:0 0"/>',
    '<rect style="font-size:1e2px"/>',
    '<rect style="fill:currentColor"/>',
    '<rect style="fill:url(data:image/svg+xml,xxx)"/>',
    '<rect style="fill:url(file:///secret)"/>',
    '<rect style="fill:red; broken"/>',
    '<g><style>rect {fill:red}</style></g>',
    '<svg/>',
    '<text id="a" aria-labelledby="b">A</text><text id="b" aria-labelledby="a">B</text>',
    '<title>A</title><title>B</title>',
    '<text id="parent"><tspan aria-labelledby="parent">Cycle</tspan></text>',
    '<defs><marker id="m" markerWidth="12" markerHeight="12" orient="auto"><path d="M0,0 L12,6 L0,12 Z"><rect/></path></marker></defs>',
], ids=lambda text: 'body-' + hashlib.sha256(str(text).encode()).hexdigest()[:10])
def test_extra_rejections(body):
    with pytest.raises(css.Rejected):
        css.normalize_structure(svg(body))


@pytest.mark.parametrize('raw', [b'\xff', b'<svg>',
    b'<?xml version="1.0" encoding="ISO-8859-1"?><svg xmlns="http://www.w3.org/2000/svg"/>'], ids=lambda raw: 'bytes-' + str(len(raw)))
def test_strict_utf8_xml(raw):
    with pytest.raises(css.Rejected) as exc:
        css.normalize_structure(raw)
    assert exc.value.code == 'invalid-xml'


def test_bom_comments_and_accessibility_loss():
    raw = b'\xef\xbb\xbf<?xml version="1.0" encoding="UTF-8"?>' + svg('<!-- <? inert comment -->' +
        '<title id="t">Example</title><desc id="d">Description</desc>',
        'aria-labelledby="t" aria-label="fallback" aria-describedby="d" role="img" aria-unknown="inert"')
    result, report = css.normalize_structure(raw)
    records = {r['attribute']: r for r in report['accessibility']}
    assert records['aria-labelledby']['target'] == 'title'
    assert records['aria-label']['loss'] == 'lower-priority-label'
    assert records['aria-unknown']['loss'] == 'unsupported-semantics'
    assert report['warnings'][0]['code'] == 'accessibility-loss'
    assert b'aria-' not in result


@pytest.mark.parametrize('raw', [
    b' ' * 1_000_001,
    svg('<g>' * 33 + '</g>' * 33),
    svg('<rect/>' * 5000),
    svg('<rect id="' + 'x' * 100001 + '"/>'),
    svg('<style>' + ' ' * 100001 + '</style>'),
    svg('<style>' + ','.join('.c' + str(i) for i in range(1001)) + '{fill:red}</style>'),
    svg('<style>rect {' + 'fill:red;' * 10001 + '}</style>'),
], ids=lambda raw: 'bytes-' + str(len(raw)))
def test_resource_budgets(raw):
    with pytest.raises(css.Rejected) as exc:
        css.normalize_structure(raw)
    assert exc.value.code == 'resource-limit'


@pytest.mark.parametrize('attrs,child', [
    ('viewBox="0 0 12 12"', ''),
    ('markerWidth="12" markerHeight="12" orient="auto-start-reverse"', '<path d="M0,0 L12,6 L0,12 Z"/>'),
    ('markerWidth="0" markerHeight="12" orient="auto"', '<path/>'),
    ('markerWidth="12" markerHeight="12" orient="auto"', '<circle r="5"/>'),
])
def test_unused_marker_validation(attrs, child):
    with pytest.raises(css.Rejected):
        css.normalize_structure(svg(f'<defs><marker id="m" {attrs}>{child}</marker></defs>'))


def test_linear_path_parser_and_marker_counts():
    output, report = css.normalize_structure(case('rounded-diagram-arrows'))
    assert report['changes']['expanded_markers'] == 2
    assert b'<marker' not in output and b'marker-end=' not in output
    for path in ['L0 0 L1 1', 'M0,,0 L1 1', 'M0 0 L1 1,', 'M0 0 M1 1', 'M0 0 L0 0', 'M0 0 C1 2 3 4 5 6']:
        with pytest.raises(css.Rejected):
            css.path_points(path)
    assert css.path_points('M0 0 10 0 H20 V10')[-1] == (20, 10)


def stub_structure(raw, width, height):
    """Structural helper for transaction tests; rendering stub is labeled explicitly."""
    output, report = css.normalize_structure(raw)
    return output, report, (240, 120)


def test_aliases_no_clobber_and_pair_rollback(tmp_path, monkeypatch):
    source, output, report = [tmp_path / f for f in ['input.svg', 'output.svg', 'report.json']]
    raw = case('cascade')
    source.write_bytes(raw)
    alias = tmp_path / 'alias.svg'
    os.link(source, alias)
    for dst, rep in [(source, report), (alias, report), (output, output), (output, source), (output, alias)]:
        with pytest.raises(n.NormalizationError) as exc:
            n.run(source, dst, rep)
        assert exc.value.code == 'output-alias'
    output.write_bytes(b'keep')
    with pytest.raises(n.NormalizationError) as exc:
        n.run(source, output, report)
    assert exc.value.code == 'output-exists'
    assert output.read_bytes() == b'keep'
    output.unlink()
    monkeypatch.setattr(n, 'structure', stub_structure)
    # This stub exercises publication ONLY; integration tests use real Chromium.
    monkeypatch.setattr(n, 'verify', lambda *args: dict(match=True, environment={'test_stub': True}))
    original_link = os.link
    def fail_second(src, dst):
        if Path(dst) == report:
            raise OSError('simulated second publication failure')
        original_link(src, dst)
    monkeypatch.setattr(n.os, 'link', fail_second)
    with pytest.raises(n.NormalizationError):
        n.run(source, output, report)
    assert source.read_bytes() == raw
    assert not output.exists() and not report.exists()
    assert not list(tmp_path.glob('.vector-png-normalize-*'))


def test_render_mismatch_publishes_nothing(tmp_path, monkeypatch):
    source, output, report = [tmp_path / f for f in ['input.svg', 'output.svg', 'report.json']]
    source.write_bytes(case('cascade'))
    monkeypatch.setattr(n, 'structure', stub_structure)
    monkeypatch.setattr(n, 'verify', lambda *args: dict(match=False, environment={'test_stub': True}))
    with pytest.raises(n.NormalizationError) as exc:
        n.run(source, output, report)
    assert exc.value.report['checks']['render'] == 'mismatch'
    assert exc.value.report['output_sha256'] is None
    assert not output.exists() and not report.exists()


def test_existing_report_and_dangling_symlink_are_protected(tmp_path):
    source, output, report = [tmp_path / f for f in ['input.svg', 'output.svg', 'report.json']]
    source.write_bytes(case('cascade'))
    report.write_bytes(b'keep report')
    with pytest.raises(n.NormalizationError) as exc:
        n.run(source, output, report)
    assert exc.value.code == 'output-exists' and report.read_bytes() == b'keep report'
    report.unlink()
    try:
        output.symlink_to(tmp_path / 'missing.svg')
    except (OSError, NotImplementedError):
        pytest.skip('This host does not permit creating symlinks')
    with pytest.raises(n.NormalizationError) as exc:
        n.run(source, output, report)
    assert exc.value.code == 'output-exists' and output.is_symlink()


@pytest.mark.parametrize('size', [(0, 1), (4097, 1), (3000, 3000)])
def test_normalization_viewport_limits(size):
    with pytest.raises(n.NormalizationError) as exc:
        n.dimensions(css.parse(svg('')), *size)
    assert exc.value.code == 'resource-limit'


def test_safe_output_independent_validation():
    # Valid input font spelling conflicts with safe-svg-v1's intentionally narrow url rule.
    with pytest.raises(css.Rejected) as exc:
        css.normalize_structure(svg('<text font-family="urlfont">Text</text>'))
    assert exc.value.stage == 'safe_svg'


def test_png_preview_failure_is_not_container_corruption(tmp_path, monkeypatch):
    source, output, report = [tmp_path / f for f in ['input.svg', 'output.png', 'report.json']]
    source.write_bytes(case('cascade'))
    # Stubs isolate report/publication behavior; real conversion is tested below.
    monkeypatch.setattr(n, 'structure', stub_structure)
    monkeypatch.setattr(n, 'verify', lambda *args: dict(match=True, environment={'test_stub': True}))
    def mismatch(*args, **kwargs):
        raise v.VectorPNGError('Saved PNG pixels do not match embedded SVG')
    monkeypatch.setattr(n.v, 'create', mismatch)
    with pytest.raises(n.NormalizationError) as exc:
        n.run(source, output, report, png=True)
    data = exc.value.report
    assert data['checks']['render'] == 'pass'
    assert data['checks']['container'] == 'not-checked'
    assert data['png_preview']['result'] == 'mismatch' and not data['png_preview']['verified']
    assert exc.value.code == 'render-mismatch'
    assert not output.exists() and not report.exists()


def test_unsafe_source_never_launches_browser(tmp_path, monkeypatch):
    source = tmp_path / 'unsafe.svg'
    source.write_bytes(svg('<script/>'))
    def forbidden(*args):
        pytest.fail('Unchecked source reached browser')
    with pytest.raises(css.Rejected):
        n._render_pair(source.read_bytes(), svg(''), (240, 120))
    # Real worker path also refuses the input before the verify gate.
    monkeypatch.setattr(n, 'verify', forbidden)
    with pytest.raises(n.NormalizationError) as exc:
        n.run(source, tmp_path / 'out.svg', tmp_path / 'report.json')
    assert exc.value.code == 'unsafe-input'


@pytest.fixture
def browser_ready():
    reason = None
    if importlib.util.find_spec('playwright') is None:
        reason = 'Optional integration requires Playwright and its Chromium'
    else:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            if not Path(p.chromium.executable_path).exists():
                reason = 'Install the pinned Playwright Chromium before integration tests'
    if reason:
        if os.environ.get('VECTOR_PNG_REQUIRE_NORMALIZATION') == '1':
            pytest.fail(reason)
        pytest.skip(reason)


@pytest.mark.parametrize('name', ['cascade', 'rounded-diagram-arrows', 'accessibility'])
def test_real_normalize_cli(tmp_path, browser_ready, name):
    source, output, report = [tmp_path / f for f in ['input.svg', 'normalized.svg', 'report.json']]
    raw = case(name)
    source.write_bytes(raw)
    result = subprocess.run([sys.executable, v.__file__, 'normalize', str(source), str(output), '--report', str(report)],
                            capture_output=True, timeout=100)
    assert result.returncode == 0, result.stderr.decode('utf-8', errors='replace')
    data = json.loads(report.read_text(encoding='utf-8'))
    assert data['status'] == 'success'
    assert data['checks'] == dict(input='pass', safe_svg='pass', render='pass', container='not-applicable', authenticity='not-verified')
    assert data['render']['renderer'] == 'Chromium' and data['render']['mode'] == 'exact'
    assert data['output_sha256'] == hashlib.sha256(output.read_bytes()).hexdigest()
    assert source.read_bytes() == raw
    v.validate_svg(output.read_text(encoding='utf-8'))


def test_real_nameplate_convert_and_extract(tmp_path, browser_ready):
    source = FIXTURES / 'normalization-input.svg'
    original = source.read_bytes()
    output, report, extracted = [tmp_path / f for f in ['converted.png', 'report.json', 'extracted.svg']]
    data = n.run(source, output, report, png=True)
    assert data['status'] == 'success' and data['checks']['container'] == 'pass'
    assert data['checks']['render'] == 'pass' and data['png_preview']['verified'] is True
    assert data['render']['viewport'] == [660, 240]
    v.main(['extract', str(output), str(extracted)])
    assert extracted.read_bytes() == (FIXTURES / 'normalization-safe.svg').read_bytes()
    assert source.read_bytes() == original
    assert data['output_sha256'] == hashlib.sha256(output.read_bytes()).hexdigest()
    assert v.inspect(output)['raster_matches_svg'] is True


def test_cli_failure_json_has_no_outputs(tmp_path):
    source, output, report = [tmp_path / f for f in ['bad.svg', 'out.svg', 'report.json']]
    source.write_bytes(svg('<rect style="filter:blur(1px)"/>'))
    result = subprocess.run([sys.executable, v.__file__, 'normalize', str(source), str(output), '--report', str(report)],
                            capture_output=True, timeout=30)
    assert result.returncode == 2
    info = json.loads(result.stderr.decode('utf-8'))
    assert info['status'] == 'failure' and info['errors'][0]['code'] == 'unsupported-css'
    assert info['output_sha256'] is None
    assert not output.exists() and not report.exists()
