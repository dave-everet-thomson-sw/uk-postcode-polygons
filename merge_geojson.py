#!/usr/bin/env python3
"""
Merge multiple GeoJSON files into a single FeatureCollection.

Usage:
  merge_geojson.py [-o OUTPUT] INPUT [INPUT ...]

Inputs may be files, directories, or glob patterns. The output defaults to
`uk.geojson` in the current working directory if not specified.
"""
import argparse
import glob
import json
import sys
from pathlib import Path


def iter_input_paths(items):
    seen = set()
    for it in items:
        p = Path(it)
        if p.exists():
            if p.is_dir():
                for f in sorted(p.glob('*.geojson')):
                    if f not in seen:
                        seen.add(f)
                        yield f
            else:
                if p not in seen:
                    seen.add(p)
                    yield p
        else:
            # treat as glob
            for m in sorted(glob.glob(it, recursive=True)):
                fp = Path(m)
                if fp not in seen:
                    seen.add(fp)
                    yield fp


def load_json(path: Path):
    with path.open('r', encoding='utf-8') as fh:
        return json.load(fh)


def main():
    p = argparse.ArgumentParser(description='Merge GeoJSON files into one FeatureCollection')
    p.add_argument('inputs', nargs='+', help='Input files, directories, or glob patterns')
    p.add_argument('-o', '--output', default='uk.geojson', help='Output GeoJSON file (default: uk.geojson)')
    args = p.parse_args()

    files = [f for inp in args.inputs for f in iter_input_paths([inp]) if f.is_file() and f.suffix.lower() in ('.geojson', '.json')]
    if not files:
        print('No input GeoJSON files found for: {}'.format(args.inputs), file=sys.stderr)
        sys.exit(2)

    merged = {'type': 'FeatureCollection', 'features': []}
    for fp in files:
        try:
            data = load_json(fp)
        except Exception as exc:
            print(f'Warning: failed to load {fp}: {exc}', file=sys.stderr)
            continue

        t = data.get('type') if isinstance(data, dict) else None
        if t == 'FeatureCollection' and 'features' in data:
            merged['features'].extend(data['features'])
        elif t == 'Feature':
            merged['features'].append(data)
        elif isinstance(data, list):
            merged['features'].extend(data)
        else:
            print(f'Warning: {fp} has unrecognized GeoJSON structure; skipping', file=sys.stderr)

    out_path = Path(args.output).expanduser().resolve()
    out_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Wrote {out_path} with {len(merged["features"])} features')


if __name__ == '__main__':
    main()
