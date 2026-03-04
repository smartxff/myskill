#!/usr/bin/env python3 -u
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from translate import translate, load_config

OUTPUT_DIR = Path("/root/myskills/article-reader/outputs")

def translate_md_file(filepath: Path, output_dir: Path) -> Path:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    translated = translate(content)
    
    date_dir = filepath.parent.name
    output_subdir = output_dir / date_dir
    output_subdir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_subdir / filepath.name.replace('.md', '_zh.md')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(translated)
    
    return output_file

def main():
    parser = argparse.ArgumentParser(description="Batch translate articles")
    parser.add_argument("--input", type=Path, help="Input directory (default: outputs)")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of files")
    
    args = parser.parse_args()
    
    input_dir = args.input if args.input else OUTPUT_DIR
    
    md_files = []
    for date_dir in sorted(input_dir.iterdir()):
        if date_dir.is_dir():
            for md_file in date_dir.glob("*.md"):
                if "_zh.md" not in md_file.name:
                    md_files.append(md_file)
    
    md_files = sorted(md_files)
    if args.limit > 0:
        md_files = md_files[:args.limit]
    
    print(f"[*] Found {len(md_files)} files to translate")
    
    config = load_config()
    if not config.get('api_key'):
        print("[-] API key not configured. Run: python scripts/translate.py --config --api-key YOUR_API_KEY")
        sys.exit(1)
    
    translated_count = 0
    for i, filepath in enumerate(md_files, 1):
        print(f"[*] Translating {i}/{len(md_files)}: {filepath.name}")
        try:
            output_file = translate_md_file(filepath, input_dir.parent)
            print(f"    [+] Saved: {output_file.name}")
            translated_count += 1
        except Exception as e:
            print(f"    [-] Failed: {e}")
    
    print(f"\n[✓] Done! Translated {translated_count} files")

if __name__ == "__main__":
    main()
