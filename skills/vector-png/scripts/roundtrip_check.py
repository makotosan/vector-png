"""Exercise all four CLI commands from any current directory."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    cli = root / 'scripts/vector_png.py'
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    source = (root / 'examples/fireworks.svg').read_bytes()
    original = out / 'original.png'
    extracted = out / 'extracted.svg'
    edited = out / 'edited.svg'
    updated = out / 'updated.png'

    def run(*words):
        result = subprocess.run([sys.executable, str(cli), *map(str, words)],
                                capture_output=True, check=True)
        return result.stdout.decode('utf-8')

    run('create', root / 'examples/fireworks.svg', original)
    run('extract', original, extracted)
    assert extracted.read_bytes() == source
    edited.write_bytes(source.replace(b'#ffca63', b'#aabbff'))
    run('update', original, edited, updated)
    before = json.loads(run('inspect', original))
    after = json.loads(run('inspect', updated))
    assert before['raster_matches_svg'] is True and after['raster_matches_svg'] is True
    assert before['svg_sha256'] != after['svg_sha256']
    print(json.dumps({'roundtrip': 'passed', 'create_extract_exact': True,
                      'edited_source_verified': True, 'output_dir': str(out)}, indent=2))


if __name__ == '__main__':
    main()
