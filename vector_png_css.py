"""Closed SVG normalization input profile, with no rendering or file publication.

Derived from vector-png-spec tools/normalization_fixture.py at
8238ebdaa136f448affa53133b99ee5afde5765a; Copyright (c) 2026 makotosan, MIT.
Production changes add independent output validation, early reference checking,
bounded parsing, stricter path parsing and metadata handling. See NORMALIZATION.md.
"""
import copy
import hashlib
import math
import re
import xml.etree.ElementTree as ET

import tinycss2
from decimal import Decimal
from defusedxml.ElementTree import DefusedXMLParser
from defusedxml.common import DefusedXmlException

from vector_png import validate_svg, VectorPNGError

NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)
TAGS = set('svg g defs title desc path rect circle ellipse line polyline polygon text tspan linearGradient radialGradient stop clipPath'.split())
ATTRS = set('id x y x1 y1 x2 y2 cx cy r rx ry width height viewBox preserveAspectRatio d points transform fill fill-opacity fill-rule stroke stroke-width stroke-opacity stroke-linecap stroke-linejoin stroke-miterlimit stroke-dasharray stroke-dashoffset opacity font-family font-size font-weight font-style text-anchor dominant-baseline dx dy rotate offset stop-color stop-opacity gradientUnits gradientTransform spreadMethod fx fy fr clip-path clipPathUnits'.split())
ENUMS = {'fill-rule': 'nonzero evenodd', 'stroke-linecap': 'butt round square',
         'stroke-linejoin': 'miter round bevel', 'font-weight': 'normal bold 100 200 300 400 500 600 700 800 900',
         'font-style': 'normal italic oblique', 'text-anchor': 'start middle end',
         'dominant-baseline': 'auto alphabetic middle central hanging text-before-edge text-after-edge'}
PROPS = set(ENUMS) | set('fill stroke stop-color opacity fill-opacity stroke-opacity stop-opacity stroke-width font-size stroke-miterlimit stroke-dashoffset stroke-dasharray font-family clip-path rx ry marker-end'.split())
INHERITED = PROPS - {'opacity', 'clip-path', 'stop-color', 'stop-opacity', 'rx', 'ry'}
NUMBER = r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)'
IDENT = r'[A-Za-z_][A-Za-z0-9_-]*'
COLORS = set('black silver gray white maroon red purple fuchsia green lime olive yellow navy blue teal aqua'.split())


class Rejected(ValueError):
    def __init__(self, code, detail=''):
        self.code = code
        super().__init__(detail or code)


def reject(code, detail=''):
    raise Rejected(code, detail)


def local(node):
    return node.tag.removeprefix('{' + NS + '}')


class BoundedXML(ET.TreeBuilder):
    def __init__(self):
        super().__init__()
        self.depth, self.count = -1, 0

    def start(self, tag, attrs):
        self.depth += 1
        self.count += 1
        if self.count > 5000 or self.depth > 32 or any(len(v) > 100_000 for v in attrs.values()):
            reject('resource-limit')
        return super().start(tag, attrs)

    def end(self, tag):
        node = super().end(tag)
        self.depth -= 1
        return node

    def doctype(self, *args):
        reject('unsafe-input', 'DTD forbidden')

    def pi(self, *args):
        reject('unsafe-input', 'Processing instruction forbidden')


def parse(raw):
    if not isinstance(raw, bytes):
        reject('invalid-xml', 'Expected UTF-8 bytes')
    if len(raw) > 1_000_000:
        reject('resource-limit')
    try:
        text = raw.decode('utf-8-sig')
        declaration = re.match(r'^<\?xml\s+([^?]*)\?>', text)
        if declaration:
            enc = re.search(r'encoding\s*=\s*[\'"]([^\'"]+)', declaration[1])
            if enc and enc[1].lower() != 'utf-8':
                reject('invalid-xml')
        root = ET.fromstring(text, parser=DefusedXMLParser(target=BoundedXML(),
                             forbid_dtd=True, forbid_entities=True, forbid_external=True))
    except DefusedXmlException as exc:
        reject('unsafe-input', str(exc))
    except (UnicodeError, ET.ParseError) as exc:
        reject('invalid-xml', str(exc))
    if root.tag != '{' + NS + '}svg':
        reject('unsafe-input')
    return root


def scalar(value, minimum=None, maximum=None, px=False):
    pattern = NUMBER + ('(?:px)?' if px else '')
    if len(value) > 128:
        reject('resource-limit', 'Numeric token exceeds 128 characters')
    if not re.fullmatch(pattern, value):
        reject('unsupported-css', 'Unsupported numeric syntax')
    number = float(value.removesuffix('px'))
    if not math.isfinite(number) or (minimum is not None and number < minimum) or (maximum is not None and number > maximum):
        reject('unsupported-css', 'Numeric range')
    return number


def value(prop, raw):
    val = raw.strip()
    low = val.lower()
    if prop not in PROPS or any(c in val for c in '\\@{};<>\x00'):
        reject('unsupported-css', prop)
    if prop in {'fill', 'stroke', 'stop-color'}:
        if low in COLORS or re.fullmatch(r'#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?', val):
            return low
        if prop != 'stop-color' and (low == 'none' or re.fullmatch(r'url\(#[A-Za-z_][A-Za-z0-9_.-]*\)', val)):
            return val if val.startswith('url(') else low
        reject('unsupported-css', 'Paint')
    elif prop in {'clip-path', 'marker-end'}:
        if low == 'none' or re.fullmatch(r'url\(#[A-Za-z_][A-Za-z0-9_.-]*\)', val):
            return val if val.startswith('url(') else low
        reject('unsupported-css', 'Local reference only')
    elif prop in ENUMS:
        if low not in ENUMS[prop].split():
            reject('unsupported-css', prop)
        return low
    elif prop.endswith('opacity'):
        scalar(low, 0, 1)
    elif prop in {'stroke-width', 'font-size', 'rx', 'ry'}:
        scalar(low, 0, px=True)
    elif prop == 'stroke-miterlimit':
        scalar(low, 1)
    elif prop == 'stroke-dashoffset':
        scalar(low, px=True)
    elif prop == 'stroke-dasharray':
        if low != 'none':
            # Validate separators before tokenizing the numeric list.
            num = NUMBER + '(?:px)?'
            if not re.fullmatch(num + r'(?:(?:\s*,\s*|\s+)' + num + ')*', low):
                reject('unsupported-css', prop)
            if not any(scalar(t, 0, px=True) for t in re.split(r'[\s,]+', low)):
                reject('unsupported-css', 'Zero dash array')
    elif prop == 'font-family':
        name = r'(?:[A-Za-z][A-Za-z0-9_-]*(?: +[A-Za-z][A-Za-z0-9_-]*)*|"[A-Za-z][A-Za-z0-9_ -]*"|\'[A-Za-z][A-Za-z0-9_ -]*\')'
        if not re.fullmatch(name + r'(?:\s*,\s*' + name + ')*', val):
            reject('unsupported-css', prop)
        return val
    return low


def declarations(tokens, budget):
    result = []
    for item in tinycss2.parse_declaration_list(tokens, skip_comments=True, skip_whitespace=True):
        if item.type != 'declaration' or item.important:
            reject('unsupported-css', 'Declaration syntax or !important')
        budget[0] += 1
        if budget[0] > 10_000:
            reject('resource-limit')
        # CSS escapes are forbidden even if tokenization would unescape them.
        prop = item.lower_name
        result.append((prop, value(prop, tinycss2.serialize([t for t in item.value if t.type != 'comment']))))
    return result


def checked_css(text):
    """Reject tokenizer recovery of unclosed blocks, strings and comments."""
    stack, quote, index = [], None, 0
    while index < len(text):
        char = text[index]
        if char == '\\':
            reject('unsupported-css', 'CSS escapes')
        if quote:
            if char == quote:
                quote = None
        elif text[index:index+2] == '/*':
            end = text.find('*/', index+2)
            if end < 0:
                reject('unsupported-css', 'Unclosed comment')
            index = end + 1
        elif char in '\'"':
            quote = char
        elif char in '{([':
            stack.append(char)
        elif char in '})]':
            if not stack or stack.pop() != {'}':'{', ')':'(', ']':'['}[char]:
                reject('unsupported-css', 'Unbalanced CSS')
        index += 1
    if stack or quote:
        reject('unsupported-css', 'Unclosed CSS')
    return text


def matches(selector, node):
    if selector.startswith('.'):
        return selector[1:] in node.get('class', '').split()
    if selector.startswith('#'):
        return node.get('id') == selector[1:]
    return local(node) == selector


def specificity(selector):
    return (int(selector.startswith('#')), int(selector.startswith('.')), int(selector[0] not in '.#'))


def inspect(root, input_mode=True):
    ids, locations, parent = {}, {}, {}
    css_bytes = 0

    def visit(node, path):
        nonlocal css_bytes
        locations[node] = path
        tag = local(node)
        if not node.tag.startswith('{' + NS + '}') or tag not in TAGS | ({'style', 'marker'} if input_mode else set()):
            reject('unsafe-input', 'Unsupported element')
        if tag == 'svg' and node is not root:
            reject('unsafe-input', 'Nested SVG')
        if tag == 'style':
            owner = parent.get(node)
            if not (owner is root or (owner is not None and local(owner) == 'defs' and parent.get(owner) is root)) or list(node):
                reject('unsupported-css', 'Style location/content')
            if set(node.attrib) - {'type'} or node.get('type', 'text/css') != 'text/css':
                reject('unsupported-css', 'Style attributes')
            css_bytes += len((node.text or '').encode())
        else:
            extra = {'class', 'style', 'role', 'marker-end'} if input_mode else set()
            if input_mode and tag == 'marker':
                extra |= {'markerWidth', 'markerHeight', 'refX', 'refY', 'orient', 'markerUnits'}
            for key, val in node.attrib.items():
                if key not in ATTRS | extra and not (input_mode and re.fullmatch(r'aria-[a-z][a-z-]*', key)):
                    reject('unsafe-input', 'Unsupported attribute ' + key)
                if key == 'style':
                    css_bytes += len(val.encode())
                elif key == 'class':
                    if any(not re.fullmatch(IDENT, t) for t in re.findall(r'[^ \t\r\n]+', val)):
                        reject('unsupported-css', 'Class token')
                elif key not in {'role'} and not key.startswith('aria-'):
                    if any(c in val for c in '\\@{};<>\x00') or any(ord(c) < 32 and c not in '\t\n\r' for c in val):
                        reject('unsafe-input', 'Attribute syntax')
                    if key in PROPS:
                        value(key, val)
                    elif 'url' in val.lower():
                        reject('unsafe-input', 'Resource syntax')
                if key == 'id':
                    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.-]*', val) or val in ids:
                        reject('invalid-reference', 'Duplicate/invalid ID')
                    ids[val] = node
        counts = {}
        for child in node:
            name = local(child)
            counts[name] = counts.get(name, 0) + 1
            parent[child] = node
            visit(child, path + '/' + name + '[' + str(counts[name]) + ']')
    visit(root, '/svg[1]')
    if css_bytes > 100_000:
        reject('resource-limit')
    for node in root.iter():
        for prop, val in node.attrib.items():
            if prop in PROPS:
                check_ref(prop, value(prop, val), ids, node, parent)
    return ids, locations, parent


def check_ref(prop, val, ids, node, parent):
    if not val.startswith('url('):
        return
    kinds = {'marker-end': {'marker'}, 'clip-path': {'clipPath'}}.get(prop, {'linearGradient', 'radialGradient'})
    if val[5:-1] not in ids or local(ids[val[5:-1]]) not in kinds:
        reject('invalid-reference')
    cur = node
    while cur is not None:
        if local(cur) in {'linearGradient', 'radialGradient', 'clipPath', 'marker'}:
            reject('invalid-reference', 'Reference within definition')
        cur = parent.get(cur)


def path_points(d):
    token = re.compile(r'[MLHV]|' + NUMBER)
    tokens, pos = [], 0
    while pos < len(d):
        gap = re.match(r'\s*(?:,\s*)?', d[pos:])[0]
        if ',' in gap and (not tokens or tokens[-1] in {'M', 'L', 'H', 'V'}):
            reject('unsupported-css', 'Path separator')
        pos += len(gap)
        if pos == len(d):
            if ',' in gap:
                reject('unsupported-css', 'Trailing comma')
            break
        match = token.match(d, pos)
        if match is None or (',' in gap and match[0] in {'M', 'L', 'H', 'V'}):
            reject('unsupported-css', 'Marker host path syntax')
        tokens.append(match[0])
        pos = match.end()
    if not tokens or tokens[0] != 'M':
        reject('unsupported-css', 'Marker host must start with M')
    points, index, command = [], 0, None
    while index < len(tokens):
        if tokens[index] in {'M', 'L', 'H', 'V'}:
            command = tokens[index]
            index += 1
        count = 2 if command in {'M', 'L'} else 1
        if command is None or index + count > len(tokens) or any(t in {'M', 'L', 'H', 'V'} for t in tokens[index:index+count]):
            reject('unsupported-css', 'Incomplete marker path')
        coords = [scalar(t) for t in tokens[index:index+count]]
        index += count
        if command in {'H', 'V'}:
            coords = [coords[0], points[-1][1]] if command == 'H' else [points[-1][0], coords[0]]
        elif command == 'M' and points:
            reject('unsupported-css', 'Multiple subpaths')
        points.append(tuple(coords))
        if command == 'M':
            command = 'L'
    if len(points) < 2 or points[-1] == points[-2]:
        reject('unsupported-css', 'Degenerate marker tangent')
    return points


def xml_space(text):
    return re.sub(r'[ \t\r\n]+', ' ', text).strip(' \t\r\n')


def validate_accessibility_graph(root, ids):
    visiting, done = set(), set()
    def visit(node):
        if node in visiting:
            reject('invalid-reference', 'Cyclic accessibility reference')
        if node in done:
            return
        if len(visiting) >= 32:
            reject('resource-limit', 'Accessibility reference depth exceeds 32')
        visiting.add(node)
        for key in ['aria-labelledby', 'aria-describedby']:
            if key not in node.attrib:
                continue
            refs = re.findall(r'[^ \t\r\n]+', node.get(key))
            if not refs or len(refs) != len(set(refs)):
                reject('invalid-reference', 'Accessibility ID list')
            for ref in refs:
                target = ids.get(ref)
                if target is None or node in set(target.iter()) or any(local(t) not in {'title', 'desc', 'text', 'tspan'} for t in target.iter()):
                    reject('invalid-reference', 'Accessibility target')
                visit(target)
        visiting.remove(node)
        done.add(node)
    for node in root.iter():
        visit(node)


def marker_definition(src, root, parent, computed):
    """Validate every definition, including definitions with no rendered uses."""
    owner = parent.get(src)
    if owner is None or local(owner) != 'defs' or parent.get(owner) is not root:
        reject('unsupported-css', 'Marker placement')
    allowed = {'id', 'markerWidth', 'markerHeight', 'refX', 'refY', 'orient', 'markerUnits'}
    if set(src.attrib) - allowed or src.get('orient') != 'auto' or len(src) != 1 or local(src[0]) != 'path':
        reject('unsupported-css', 'Marker definition')
    w, h = scalar(src.get('markerWidth', ''), 0), scalar(src.get('markerHeight', ''), 0)
    if w <= 0 or h <= 0:
        reject('unsupported-css')
    rx, ry = scalar(src.get('refX', '0'), 0, w), scalar(src.get('refY', '0'), 0, h)
    child = src[0]
    if set(child.attrib) - {'d', 'fill'} or list(child) or (child.text or '').strip() or (src.text or '').strip() or (child.tail or '').strip():
        reject('unsupported-css', 'Marker child attributes')
    triangle = re.fullmatch(r'\s*M\s*(' + NUMBER + r')[\s,]+(' + NUMBER + r')\s+L\s*(' + NUMBER + r')[\s,]+(' + NUMBER + r')\s+L\s*(' + NUMBER + r')[\s,]+(' + NUMBER + r')\s+Z\s*', child.get('d', ''))
    expected = (Decimal(0), Decimal(0), Decimal(src.get('markerWidth')),
                Decimal(src.get('markerHeight')) / 2, Decimal(0), Decimal(src.get('markerHeight')))
    if triangle is None or tuple(Decimal(t) for t in triangle.groups()) != expected:
        reject('unsupported-css', 'Only viewport-contained triangle markers')
    paint = computed.get(child, {}).get('fill', 'black')
    if paint.startswith('url(') or paint == 'none':
        reject('unsupported-css')
    unit = src.get('markerUnits', 'strokeWidth')
    if unit not in {'strokeWidth', 'userSpaceOnUse'}:
        reject('unsupported-css')
    return rx, ry, child, paint, unit


def normalize_structure(raw):
    """Validate and transform; success requires an independent rendering gate."""
    root = parse(raw)
    ids, loc, parent = inspect(root)
    original_text = {node: xml_space(''.join(node.itertext())) for node in root.iter()}
    validate_accessibility_graph(root, ids)
    rules, budget = [], [0]
    changes = dict(style_elements=0, class_attributes=0, inline_styles=0, applied_declarations=0, expanded_markers=0)
    for node in root.iter():
        if local(node) != 'style':
            continue
        css = checked_css(node.text or '')
        if '\\' in css:
            reject('unsupported-css', 'CSS escapes')
        for rule in tinycss2.parse_stylesheet(css, skip_whitespace=True, skip_comments=True):
            if rule.type != 'qualified-rule':
                reject('unsupported-css', 'Rule syntax/at-rule')
            selectors = [s.strip() for s in tinycss2.serialize([t for t in rule.prelude if t.type != 'comment']).split(',')]
            if any(not re.fullmatch(r'[.#]?' + IDENT, s) or (s[0] not in '.#' and s not in TAGS | {'marker'}) for s in selectors):
                reject('unsupported-css', 'Selector')
            if sum(len(r[0]) for r in rules) + len(selectors) > 1000:
                reject('resource-limit')
            rules.append((selectors, declarations(rule.content, budget)))
    computed = {}
    for node in list(root.iter()):
        if local(node) == 'style':
            continue
        chosen = {k: ((0, 0, 0, -1), value(k, v)) for k, v in node.attrib.items() if k in PROPS}
        for selectors, decls in rules:
            # Validate references even on unmatched/overridden declarations.
            for prop, val in decls:
                if val.startswith('url(') and (val[5:-1] not in ids or local(ids[val[5:-1]]) not in ({'marker'} if prop == 'marker-end' else {'clipPath'} if prop == 'clip-path' else {'linearGradient', 'radialGradient'})):
                    reject('invalid-reference')
            specs = [specificity(s) for s in selectors if matches(s, node)]
            if specs:
                for prop, val in decls:
                    check_ref(prop, val, ids, node, parent)
                    rank = (0,) + max(specs)
                    if prop not in chosen or rank >= chosen[prop][0]:
                        chosen[prop] = (rank, val)
        if 'style' in node.attrib:
            if '\\' in node.attrib['style']:
                reject('unsupported-css')
            for prop, val in declarations(checked_css(node.attrib['style']), budget):
                check_ref(prop, val, ids, node, parent)
                chosen[prop] = ((1, 0, 0, 0), val)
            changes['inline_styles'] += 1
        for prop, original in node.attrib.items():
            if prop in {'rx', 'ry'} and local(node) != 'rect':
                reject('unsupported-css', 'rx/ry require rect')
        for prop, (_, val) in chosen.items():
            check_ref(prop, val, ids, node, parent)
            if prop in {'rx', 'ry'} and local(node) != 'rect':
                reject('unsupported-css', 'CSS rx/ry require rect')
            node.set(prop, val)
        changes['applied_declarations'] += len(chosen)
        values = {k: v for k, v in computed.get(parent.get(node), {}).items() if k in INHERITED}
        values.update({k: v[1] for k, v in chosen.items()})
        computed[node] = values
        if 'class' in node.attrib:
            changes['class_attributes'] += 1
            del node.attrib['class']
        node.attrib.pop('style', None)
    markers = {node: marker_definition(node, root, parent, computed)
               for node in root.iter() if local(node) == 'marker'}
    accessibility = []
    for node in list(root.iter()):
        if local(node) == 'style':
            continue
        attrs = {k: v for k, v in node.attrib.items() if k == 'role' or k.startswith('aria-')}
        def resolve(text):
            values = []
            refs = re.findall(r'[^ \t\r\n]+', text)
            if not refs or len(refs) != len(set(refs)):
                reject('invalid-reference', 'Accessibility ID list')
            for ref in refs:
                target = ids.get(ref)
                if target is None or target is node or any(local(t) not in {'title', 'desc', 'text', 'tspan'} for t in target.iter()):
                    reject('invalid-reference', 'Accessibility target')
                values.append(original_text[target])
            return xml_space(' '.join(values))
        name = resolve(attrs['aria-labelledby']) if 'aria-labelledby' in attrs else xml_space(attrs['aria-label']) if 'aria-label' in attrs else None
        description = resolve(attrs['aria-describedby']) if 'aria-describedby' in attrs else None
        for tag, newtext in [('title', name), ('desc', description)]:
            old = [n for n in node if local(n) == tag]
            if len(old) > 1:
                reject('invalid-reference', 'Multiple metadata nodes')
            if newtext is not None:
                if old:
                    oldtext = ''.join(old[0].itertext())
                    if oldtext != newtext:
                        accessibility.append(dict(element=loc[node], attribute=tag, value=oldtext, loss='replaced-text'))
                    for child in list(old[0]):
                        old[0].remove(child)
                    old[0].text = newtext
                else:
                    new = ET.Element('{' + NS + '}' + tag)
                    new.text = newtext
                    node.insert(0 if tag == 'title' else 1, new)
        for key, val in sorted(attrs.items()):
            target = 'title' if key == 'aria-labelledby' or (key == 'aria-label' and 'aria-labelledby' not in attrs) else 'desc' if key == 'aria-describedby' else None
            accessibility.append(dict(element=loc[node], attribute=key, value=val, **({'target': target} if target else {'loss': 'lower-priority-label' if key == 'aria-label' else 'unsupported-semantics'})))
            del node.attrib[key]
    # Restricted triangle markers on open M/L/H/V paths are expanded explicitly.
    for node in list(root.iter()):
        marker = computed.get(node, {}).get('marker-end', 'none')
        node.attrib.pop('marker-end', None)
        if marker == 'none':
            continue
        if local(node) != 'path' or computed[node].get('fill', 'black') != 'none':
            reject('unsupported-css', 'Marker host')
        src = ids[marker[5:-1]]
        rx, ry, child, paint, unit = markers[src]
        scale = scalar(computed[node].get('stroke-width', '1'), 0, px=True) if unit == 'strokeWidth' else 1
        points = path_points(node.get('d', ''))
        (x0, y0), (x, y) = points[-2:]
        angle = math.degrees(math.atan2(y-y0, x-x0))
        container = parent[node]
        group = ET.Element('{' + NS + '}g', {'transform': f'translate({x:.17g} {y:.17g}) rotate({angle:.17g}) scale({scale:.17g}) translate({-rx:.17g} {-ry:.17g})', 'fill': paint, 'stroke': 'none'})
        # Host opacity/clip/transform would require wrapping: reject in this subset.
        if any(k in computed[node] for k in {'opacity', 'clip-path'}) or 'transform' in node.attrib:
            reject('unsupported-css', 'Marker host compositing')
        clone = copy.deepcopy(child)
        clone.attrib.pop('id', None)
        clone.set('fill', paint)
        clone.set('fill-opacity', computed[child].get('fill-opacity', '1'))
        group.append(clone)
        container.insert(list(container).index(node) + 1, group)
        changes['expanded_markers'] += 1
    for node in list(root.iter()):
        for child in list(node):
            if local(child) in {'style', 'marker'}:
                changes['style_elements'] += int(local(child) == 'style')
                index = list(node).index(child)
                if child.tail and child.tail.strip():
                    if index:
                        previous = node[index - 1]
                        previous.tail = (previous.tail or '') + child.tail
                    else:
                        node.text = (node.text or '') + child.tail
                node.remove(child)
    output = ET.tostring(root, encoding='utf-8')
    try:
        validate_output(output)
    except Rejected as exc:
        exc.stage = 'safe_svg'
        raise
    report = dict(profile='svg-normalization-v1', status='failure', input_sha256=hashlib.sha256(raw).hexdigest(),
                  output_sha256=None, changes=changes, accessibility=accessibility,
                  checks=dict(input='pass', safe_svg='pass', render='not-checked', container='not-applicable', authenticity='not-verified'),
                  render=None, errors=[], warnings=[dict(code='accessibility-loss', stage='accessibility', explanation='Review recorded semantic losses')] if any('loss' in a for a in accessibility) else [])
    return output, report


def validate_output(raw):
    root = parse(raw)
    try:
        validate_svg(raw.decode('utf-8'))
    except VectorPNGError as exc:
        reject('unsafe-input', 'Normalized output failed safe-svg-v1: ' + str(exc))
    ids, _, parent = inspect(root, input_mode=False)
    for node in root.iter():
        for prop, val in node.attrib.items():
            if prop in PROPS:
                check_ref(prop, val, ids, node, parent)
    return root

