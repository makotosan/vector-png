"""Explicit normalized SVG import, controlled SVG2 rendering and pair publication.

The wire-v1 reader and writer remain in vector_png. Optional dependencies are
loaded only for these commands. All source is validated before browser launch.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile

import vector_png as v


class NormalizationError(v.VectorPNGError):
    def __init__(self, report):
        self.report = report
        error = report['errors'][-1]
        self.code = error['code']
        super().__init__(error['code'] + ': ' + error['explanation'])


def failure(code, stage, explanation, report=None, raw=None):
    if report is None:
        report = dict(profile='svg-normalization-v1', status='failure',
                      input_sha256=hashlib.sha256(raw).hexdigest() if raw is not None else None,
                      output_sha256=None, changes=dict(style_elements=0, class_attributes=0,
                      inline_styles=0, applied_declarations=0, expanded_markers=0),
                      accessibility=[], checks=dict(input='not-checked', safe_svg='not-checked',
                      render='not-checked', container='not-applicable', authenticity='not-verified'),
                      render=None, errors=[], warnings=[])
    report['status'] = 'failure'
    report['output_sha256'] = None
    report['errors'].append(dict(code=code, stage=stage, explanation=explanation))
    if stage == 'input':
        report['checks']['input'] = 'fail'
    elif stage == 'render':
        report['checks']['render'] = 'mismatch' if code == 'render-mismatch' else 'error'
    elif stage == 'container':
        report['checks']['container'] = 'fail'
    elif stage == 'safe_svg':
        report['checks']['input'] = 'pass'
        report['checks']['safe_svg'] = 'fail'
    elif stage == 'png_preview':
        report['png_preview'] = dict(renderer='CairoSVG', verified=False,
                                     result='mismatch' if code == 'render-mismatch' else 'error')
    raise NormalizationError(report)


def dimensions(root, width=None, height=None):
    """Explicit pixels, else ceil root px lengths, else viewBox, else 512."""
    from vector_png_css import NUMBER
    import re
    box = root.get('viewBox', '').replace(',', ' ').split()
    inferred = []
    for index, key in enumerate(['width', 'height']):
        override = width if index == 0 else height
        if override is not None:
            inferred.append(override)
            continue
        text = root.get(key, '')
        fallback = box[index + 2] if len(box) == 4 else '512'
        candidate = text if re.fullmatch(NUMBER + r'(?:px)?', text) else fallback
        try:
            value = float(candidate.removesuffix('px'))
            if not math.isfinite(value) or value <= 0 or value > v.MAX_SIDE:
                raise ValueError()
            inferred.append(math.ceil(value))
        except ValueError:
            failure('resource-limit', 'input', 'Invalid or excessive inferred viewport')
    result = (width if width is not None else inferred[0],
              height if height is not None else inferred[1])
    if any(type(x) is not int or x < 1 or x > v.MAX_SIDE for x in result) or result[0] * result[1] > v.MAX_PIXELS:
        failure('resource-limit', 'input', 'Viewport exceeds 4096 per side or 4000000 pixels')
    return result


def _stop_tree(process):
    """Timeout cleanup includes the browser and driver, not only Python."""
    if os.name == 'nt':
        subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def worker(kind, payload, timeout):
    flags = dict(creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP) if os.name == 'nt' else dict(start_new_session=True)
    # Stage bounded IPC in a private per-call directory. Worker never chooses paths.
    with tempfile.TemporaryDirectory(prefix='vector-png-normalize-') as folder:
        request, response = Path(folder) / 'request.json', Path(folder) / 'response.json'
        request.write_text(json.dumps(payload), encoding='utf-8')
        with (Path(folder) / 'stderr.txt').open('wb') as errors:
            process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--worker', kind,
                                        str(request), str(response)], stdin=subprocess.DEVNULL,
                                       stdout=subprocess.DEVNULL, stderr=errors, **flags)
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                _stop_tree(process)
                process.wait(timeout=10)
                failure('resource-limit', 'input' if kind == 'structure' else 'render',
                        kind + ' worker exceeded its finite time budget')
        if not response.exists():
            failure('render-error' if kind == 'render' else 'unsafe-input',
                    'render' if kind == 'render' else 'input', 'Worker failed without a result')
        result = json.loads(v.bounded_read(response, 8_000_000).decode('utf-8'))
        if not result['ok']:
            failure(result['code'], result.get('stage', 'input') if kind == 'structure' else 'render', result['explanation'])
        return result


def structure(raw, width=None, height=None):
    reply = worker('structure', dict(source=base64.b64encode(raw).decode('ascii'), width=width, height=height), 15)
    return base64.b64decode(reply['svg']), reply['report'], tuple(reply['viewport'])


def verify(raw, normalized, viewport):
    return worker('render', dict(source=base64.b64encode(raw).decode('ascii'),
                                svg=base64.b64encode(normalized).decode('ascii'),
                                width=viewport[0], height=viewport[1]), 60)


def check_paths(source, output, report_path):
    paths = [Path(p).absolute() for p in (source, output, report_path)]
    try:
        for i, path in enumerate(paths):
            for other in paths[:i]:
                if path.resolve() == other.resolve() or (path.exists() and other.exists() and os.path.samefile(path, other)):
                    failure('output-alias', 'publication', 'Input, output and report must be distinct, including aliases')
        for path in paths[1:]:
            if os.path.lexists(path):
                failure('output-exists', 'publication', 'Existing output/report is preserved: ' + str(path))
    except NormalizationError:
        raise
    except (OSError, RuntimeError, ValueError) as exc:
        failure('io-error', 'publication', 'Cannot safely resolve input/output paths: ' + str(exc))
    return paths


def publish_pair(paths, payloads):
    """Stage both complete files and roll back only our own newly linked files."""
    staged, published = [], []
    try:
        for path, payload in zip(paths, payloads):
            fd, name = tempfile.mkstemp(prefix='.vector-png-normalize-', dir=path.parent)
            staged.append(name)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
        for path, name in zip(paths, staged):
            os.link(name, path)
            published.append((path, name))
    except BaseException:
        for path, name in reversed(published):
            if path.exists() and os.path.samefile(path, name):
                path.unlink()
        raise
    finally:
        for name in staged:
            os.unlink(name)


def run(source, output, report_path, *, png=False, width=None, height=None):
    report, raw = None, None
    stage = 'publication'
    try:
        paths = check_paths(source, output, report_path)
        stage = 'input'
        raw = v.bounded_read(paths[0], v.MAX_SVG)
        normalized, report, viewport = structure(raw, width, height)
        if png:
            report['checks']['container'] = 'not-checked'
        stage = 'render'
        result = verify(raw, normalized, viewport)
        report['render'] = result['environment']
        if not result['match']:
            failure('render-mismatch', 'render', 'Before/after decoded RGBA pixels differ', report)
        report['checks']['render'] = 'pass'
        payload = normalized
        if png:
            stage = 'png_preview'
            # Existing writer regenerates and verifies PNG/SVG together using CairoSVG.
            with tempfile.TemporaryDirectory(prefix='vector-png-convert-') as folder:
                temp = Path(folder) / 'converted.png'
                v.create(normalized.decode('utf-8'), temp, *viewport)
                stage = 'container'
                restored, size, payload = v._read_document(temp)
                if restored.encode('utf-8') != normalized or size != viewport:
                    failure('invalid-container', stage, 'Written SVG or dimensions changed', report)
                report['checks']['container'] = 'pass'
                stage = 'png_preview'
                if not v._matches(restored, size, payload):
                    failure('render-mismatch', stage, 'PNG pixels differ from fresh CairoSVG rendering', report)
            from importlib.metadata import version
            report['png_preview'] = dict(renderer='CairoSVG', comparison='exact decoded RGBA',
                                         version=version('CairoSVG'), pillow=version('Pillow'),
                                         resource_policy='deny all fetching',
                                         fonts='host fonts; grayscale, hint style/metrics disabled',
                                         viewport=list(viewport), verified=True)
        report['status'] = 'success'
        report['output_sha256'] = hashlib.sha256(payload).hexdigest()
        report['normalized_svg_sha256'] = hashlib.sha256(normalized).hexdigest()
        report['output_kind'] = 'png' if png else 'svg'
        stage = 'publication'
        # Recheck after expensive work; no-clobber link handles concurrent creators.
        check_paths(*paths)
        encoded_report = (json.dumps(report, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
        if len(encoded_report) > 8_000_000:
            failure('resource-limit', stage, 'Report exceeds 8 MB', report)
        publish_pair(paths[1:], [payload, encoded_report])
        return report
    except NormalizationError as exc:
        if png and exc.report['checks']['container'] == 'not-applicable':
            exc.report['checks']['container'] = 'not-checked'
        if raw is not None and exc.report['input_sha256'] is None:
            exc.report['input_sha256'] = hashlib.sha256(raw).hexdigest()
        if report is not None and exc.report is not report:
            error = exc.report['errors'][-1]
            failure(error['code'], error['stage'], error['explanation'], report, raw)
        raise
    except (OSError, ValueError) as exc:
        code = ('output-exists' if isinstance(exc, FileExistsError) else
                'render-mismatch' if stage == 'png_preview' and 'do not match' in str(exc) else
                'render-error' if stage in {'render', 'png_preview'} else
                'invalid-container' if stage == 'container' else
                'resource-limit' if 'size limit' in str(exc) else 'io-error')
        failure(code, stage, str(exc), report, raw)


def _render_pair(raw, normalized, viewport):
    # Validate BOTH documents before starting Chromium or creating any image document.
    from vector_png_css import normalize_structure, validate_output
    checked, _ = normalize_structure(raw)
    if checked != normalized:
        raise ValueError('Normalized source differs from the validated transformation')
    validate_output(normalized)
    from playwright.sync_api import sync_playwright
    from importlib.metadata import version
    from PIL import Image
    families = sorted({n.get('font-family') for n in validate_output(normalized).iter() if n.get('font-family')})
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, chromium_sandbox=True,
                                            args=['--disable-background-networking', '--js-flags=--max-old-space-size=128'])
        try:
            context = browser.new_context(viewport=dict(width=viewport[0], height=viewport[1]),
                                          device_scale_factor=1, java_script_enabled=False,
                                          offline=True, color_scheme='light', service_workers='block')
            context.route('**/*', lambda route: route.abort())
            page = context.new_page()
            page.set_default_timeout(20_000)
            images = []
            for source in [raw, normalized]:
                encoded = base64.b64encode(source).decode('ascii')
                # Only validated bytes are loaded as an inert SVG image, never SVG DOM markup.
                page.set_content('<html><head><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src data:; style-src \'unsafe-inline\'; font-src \'none\'"></head><body style="margin:0;background:transparent"><img width="' + str(viewport[0]) + '" height="' + str(viewport[1]) + '" src="data:image/svg+xml;base64,' + encoded + '"></body></html>', wait_until='load')
                image = page.locator('img')
                # A broken image screenshot must not count as an equal SVG render.
                if not image.evaluate('(img) => img.complete && img.naturalWidth > 0 && img.naturalHeight > 0'):
                    raise ValueError('SVG image did not decode')
                png = image.screenshot(omit_background=True, timeout=20_000, animations='disabled')
                with Image.open(io.BytesIO(png)) as decoded:
                    if decoded.size != viewport:
                        raise ValueError('Unexpected screenshot dimensions')
                    images.append(decoded.convert('RGBA').tobytes())
            environment = dict(renderer='Chromium', version=browser.version,
                               playwright=version('playwright'), platform=sys.platform,
                               fonts=dict(policy='same browser/context and installed host fonts', requested_families=families),
                               viewport=list(viewport), background='transparent',
                               color_alpha='Chromium sRGB screenshot decoded to RGBA',
                               resource_policy='offline; abort every network route; CSP; script-disabled SVG image; no file URL',
                               mode='exact', tolerances=0)
            context.close()
            return dict(match=images[0] == images[1], environment=environment)
        finally:
            browser.close()


def worker_main(kind, request, response):
    try:
        payload = json.loads(v.bounded_read(request, 4_000_000).decode('utf-8'))
        raw = base64.b64decode(payload['source'], validate=True)
        from vector_png_css import normalize_structure, parse
        viewport = dimensions(parse(raw), payload.get('width'), payload.get('height'))
        if kind == 'structure':
            # Allocation policy: 1 MB input/output, depth/count/CSS bounds; 15 s outer deadline.
            # RLIMIT_AS is deliberately not imposed on Chromium; see NORMALIZATION.md.
            normalized, report = normalize_structure(raw)
            result = dict(svg=base64.b64encode(normalized).decode('ascii'), report=report, viewport=list(viewport))
        elif kind == 'render':
            normalized = base64.b64decode(payload['svg'], validate=True)
            result = _render_pair(raw, normalized, viewport)
        else:
            raise ValueError('Unknown worker kind')
        result['ok'] = True
    except Exception as exc:
        code = getattr(exc, 'code', 'render-error' if kind == 'render' else 'unsafe-input')
        explanation = str(exc)[:2000]
        if isinstance(exc, ModuleNotFoundError):
            explanation = 'Install normalization dependencies and Chromium: pip install -r requirements-normalization.txt; python -m playwright install chromium'
        result = dict(ok=False, code=code, stage=getattr(exc, 'stage', 'input'), explanation=explanation)
    Path(response).write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    if len(sys.argv) == 5 and sys.argv[1] == '--worker':
        worker_main(sys.argv[2], sys.argv[3], sys.argv[4])
