"""Run the optional SVG2 normalize/convert pipeline from any project directory."""
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
    source = root / 'examples/css-diagram.svg'
    original = source.read_bytes()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    for command, name in [('normalize', 'normalized.svg'), ('convert', 'converted.png')]:
        subprocess.run([sys.executable, str(cli), command, str(source), str(out / name),
                        '--report', str(out / (command + '-report.json'))], check=True,
                       stdout=subprocess.DEVNULL, timeout=120)
    subprocess.run([sys.executable, str(cli), 'extract', str(out / 'converted.png'),
                    str(out / 'extracted.svg')], check=True, timeout=60)
    assert (out / 'normalized.svg').read_bytes() == (out / 'extracted.svg').read_bytes()
    assert source.read_bytes() == original
    reports = [json.loads((out / (cmd + '-report.json')).read_text(encoding='utf-8'))
               for cmd in ['normalize', 'convert']]
    assert all(r['status'] == 'success' and r['checks']['render'] == 'pass' for r in reports)
    assert reports[1]['checks']['container'] == 'pass'
    print(json.dumps({'normalization_roundtrip': 'passed', 'original_unchanged': True,
                      'normalized_extract_exact': True, 'output_dir': str(out)}, indent=2))


if __name__ == '__main__':
    main()
