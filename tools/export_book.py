#!/usr/bin/env python3
"""Export the maintained Markdown guide as EPUB, PDF, standalone HTML or UTF-8 TXT."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from reading.book import ROOT, TITLE, load_book, source_hashes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--format', nargs='+', choices=['all', 'epub', 'pdf', 'html', 'txt'], default=['all'])
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'dist')
    parser.add_argument('--font', help='PDF Chinese TrueType font (.ttf or TrueType .ttc); also SAVE_MONEY_PDF_FONT')
    args = parser.parse_args()
    formats = ['epub', 'pdf', 'html', 'txt'] if 'all' in args.format else list(dict.fromkeys(args.format))
    manifest, pages, sources = load_book()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    info = {'title': TITLE, 'author': manifest['author'], 'source_version': manifest['source_version'],
            'built_at_utc': datetime.now(timezone.utc).isoformat(), 'sources': source_hashes(sources), 'outputs': {}}
    for fmt in formats:
        path = output / ('HowToSaveMoney.' + fmt)
        if fmt == 'epub':
            from reading.epub import build
            build(path, manifest, pages)
        elif fmt == 'pdf':
            from reading.pdf import build
            info['pdf_font'] = Path(build(path, manifest, pages, args.font)).name
        elif fmt == 'html':
            from reading.offline import build_html
            build_html(path, manifest, pages)
        else:
            from reading.offline import build_txt
            build_txt(path, manifest, pages)
        info['outputs'][fmt] = {'file': path.name, 'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        print(f'已生成 {path} ({path.stat().st_size / 1024:.1f} KiB)')
    # One manifest describes this invocation only. Separate invocations should use separate folders.
    (output / 'build-info.json').write_text(json.dumps(info, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
