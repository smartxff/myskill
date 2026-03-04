#!/usr/bin/env python3 -u
import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md

DEFAULT_INPUT_FILE = Path("/root/myskills/article-list-tracker/article_lists.txt")
OUTPUT_DIR = Path("/root/myskills/article-reader/outputs")
READ_RECORD_FILE = Path("/root/myskills/article-reader/read_articles.json")

AD_SELECTORS = [
    'script', 'style', 'nav', 'footer', 'header', 'aside',
    '.ad', '.ads', '.advertisement', '.sponsored',
    '[class*="ad-"]', '[class*="Ad-"]', '[class*="advertisement"]',
    '[id*="ad-"]', '[id*="Ad-"]', '[id*="advertisement"]',
    '.sidebar', '.related', '.recommended', '.promo',
    '.newsletter', '.subscribe', '.popup', '.modal',
    '[class*="social"]', '[class*="share"]', '.comments'
]

def load_read_record(record_file: Path) -> dict:
    if not record_file.exists():
        return {}
    with open(record_file) as f:
        return json.load(f)

def save_read_record(record: dict, record_file: Path):
    record_file.parent.mkdir(parents=True, exist_ok=True)
    with open(record_file, "w") as f:
        json.dump(record, f, indent=2)

def load_urls_from_file(input_file: Path) -> list:
    if not input_file.exists():
        print(f"[-] URL file not found: {input_file}")
        sys.exit(1)
    urls = []
    with open(input_file) as f:
        for line in f:
            line = line.strip()
            if line and line.startswith("http"):
                urls.append(line)
    return urls

def get_page(url: str, timeout: int = 30) -> str:
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"    [!] Failed to fetch {url}: {e}")
        return ""

def extract_article_links_from_list(url: str, limit: int = 5) -> list:
    html = get_page(url)
    if not html:
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    articles = []
    
    for a in soup.find_all('a', href=True):
        href = a.get('href', '')
        text = a.get_text(strip=True)
        
        if not text or len(text) < 10:
            continue
        
        full_url = urljoin(url, href)
        parsed = urlparse(full_url)
        
        if any(x in parsed.path for x in ['/article/', '/post/', '/news/', '/blog/']) or \
           any(x in parsed.path for x in ['/p/', '.html', '.htm']) or \
           re.search(r'/\d{4}/', parsed.path):
            if full_url not in [a['url'] for a in articles]:
                articles.append({'url': full_url, 'title': text})
        
        if len(articles) >= limit:
            break
    
    return articles

def clean_content(soup: BeautifulSoup) -> str:
    for selector in AD_SELECTORS:
        for elem in soup.select(selector):
            elem.decompose()
    
    for elem in soup.find_all(['script', 'style', 'iframe', 'noscript']):
        elem.decompose()
    
    article = soup.find('article') or soup.find('main') or soup.find('div', class_=re.compile(r'content|article|post|body', re.I))
    
    if article:
        for ad in article.find_all(['aside', 'div', 'section'], class_=re.compile(r'ad|sponsor|promo|related|social|share|comment|event|register|newsletter|subscribe|footer|sidebar', re.I)):
            ad.decompose()
        
        for ad in article.find_all(['div', 'p'], class_=re.compile(r'advertisement|promo|register|signup', re.I)):
            ad.decompose()
        
        return str(article)
    
    return str(soup.body) if soup.body else ""

def extract_article_content(url: str) -> dict:
    html = get_page(url)
    if not html:
        return {'title': '', 'content': '', 'url': url}
    
    soup = BeautifulSoup(html, 'html.parser')
    
    title = ''
    for tag in soup.find_all(['h1', 'h2', 'title']):
        text = tag.get_text(strip=True)
        if text and len(text) > 5:
            title = text
            break
    
    cleaned_html = clean_content(soup)
    content_md = md(cleaned_html, heading_style="ATX")
    
    content_md = re.sub(r'\n{3,}', '\n', content_md)
    content_md = re.sub(r'!\[.*?\]\(.*?\)', '', content_md)
    content_md = re.sub(r'\n---\n', '\n', content_md)
    content_md = re.sub(r'\[([^\]]+)\]\(/blog[^\)]*\)', r'\1', content_md)
    
    lines = content_md.split('\n')
    new_lines = []
    prev_empty = False
    skip_patterns = ['blog', '/', '←', '→', '→']
    
    for line in lines:
        line = line.strip()
        
        if not line:
            if not prev_empty:
                new_lines.append('')
                prev_empty = True
            continue
        
        if line.startswith('[') and '](/' in line:
            continue
        
        if any(line == p or line.startswith(p) for p in skip_patterns):
            if not line.startswith('#'):
                continue
        
        new_lines.append(line)
        prev_empty = False
    
    content_md = '\n\n'.join(new_lines)
    content_md = content_md[:15000]
    content_md = re.sub(r'<img.*?>', '', content_md)
    content_md = content_md[:15000]
    
    content_md = clean_markdown(content_md)
    
    return {'title': title, 'content': content_md, 'url': url}


def clean_markdown(content: str) -> str:
    lines = content.split('\n')
    result = []
    in_code_block = False
    
    for line in lines:
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            result.append(line)
            continue
        
        if in_code_block:
            result.append(line)
            continue
        
        stripped = line.strip()
        
        if stripped.startswith('#'):
            if stripped.startswith('##'):
                result.append(stripped)
            else:
                result.append(stripped)
            continue
        
        if re.match(r'^[-*+]\s', stripped) or re.match(r'^\d+\.\s', stripped):
            result.append(stripped)
            continue
        
        if stripped.startswith('**') and stripped.endswith('**'):
            result.append(stripped)
            continue
        
        if len(stripped) > 0:
            cleaned_line = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', stripped)
            cleaned_line = re.sub(r'[*_`]+', '', cleaned_line)
            if cleaned_line.strip():
                result.append(cleaned_line)
    
    final_lines = []
    prev_empty = False
    for line in result:
        if not line.strip():
            if not prev_empty:
                final_lines.append('')
                prev_empty = True
        else:
            final_lines.append(line)
            prev_empty = False
    
    return '\n'.join(final_lines)

def sanitize_filename(url: str) -> str:
    parsed = urlparse(url)
    name = parsed.netloc + parsed.path
    name = re.sub(r'[^\w\-_.]', '_', name)
    name = re.sub(r'_+', '_', name)
    name = name.strip('_')
    return name[:100] + '.md'


def clean_markdown(content: str) -> str:
    lines = content.split('\n')
    result = []
    in_code_block = False
    
    for line in lines:
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            result.append(line)
            continue
        
        if in_code_block:
            result.append(line)
            continue
        
        stripped = line.strip()
        
        if stripped.startswith('#'):
            result.append(stripped)
            continue
        
        if re.match(r'^[-*+]\s', stripped) or re.match(r'^\d+\.\s', stripped):
            if len(stripped) > 10:
                result.append(stripped)
            continue
        
        if stripped.startswith('**') and stripped.endswith('**'):
            result.append(stripped)
            continue
        
        if len(stripped) > 20:
            cleaned_line = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', stripped)
            cleaned_line = re.sub(r'[*_`]+', '', cleaned_line)
            cleaned_line = re.sub(r'\s+', ' ', cleaned_line)
            if cleaned_line.strip():
                result.append(cleaned_line)
    
    final_lines = []
    prev_empty = False
    for line in result:
        if not line.strip():
            if not prev_empty:
                final_lines.append('')
                prev_empty = True
        else:
            final_lines.append(line)
            prev_empty = False
    
    return '\n'.join(final_lines)

def main():
    parser = argparse.ArgumentParser(description="Article Reader")
    parser.add_argument("--input", type=Path, help="Input URL list file")
    parser.add_argument("--output", type=Path, help="Output directory")
    parser.add_argument("--limit", type=int, default=5, help="Number of latest articles per list")
    
    args = parser.parse_args()
    
    input_file = args.input if args.input else DEFAULT_INPUT_FILE
    output_dir = args.output if args.output else OUTPUT_DIR
    limit = args.limit
    
    urls = load_urls_from_file(input_file)
    print(f"[*] Loaded {len(urls)} URLs from {input_file}")
    
    today = datetime.now().strftime("%Y-%m-%d")
    output_subdir = output_dir / today
    output_subdir.mkdir(parents=True, exist_ok=True)
    print(f"[*] Output directory: {output_subdir}")
    
    record_file = output_dir.parent / READ_RECORD_FILE
    read_record = load_read_record(record_file)
    
    total_articles = 0
    skipped_articles = 0
    
    for list_url in urls:
        print(f"\n[*] Processing: {list_url}")
        
        article_links = extract_article_links_from_list(list_url, limit)
        print(f"    Found {len(article_links)} article links")
        
        if not article_links:
            continue
        
        list_key = urlparse(list_url).netloc
        if list_key not in read_record:
            read_record[list_key] = {'list_url': list_url, 'articles': []}
        
        list_record = read_record[list_key]
        
        for article in article_links:
            article_url = article['url']
            article_title = article['title']
            
            if any(a['url'] == article_url for a in list_record['articles']):
                print(f"    [-] Skipped (already read): {article_title[:50]}...")
                skipped_articles += 1
                continue
            
            print(f"    [*] Reading: {article_title[:50]}...")
            
            content = extract_article_content(article_url)
            
            if not content['title']:
                content['title'] = article_title
            
            filename = sanitize_filename(article_url)
            filepath = output_subdir / filename
            
            cleaned_content = clean_markdown(content['content'])
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# {content['title']}\n\n")
                f.write(f"**Source**: {article_url}\n\n")
                f.write("---\n\n")
                f.write(cleaned_content)
            
            list_record['articles'].append({
                'url': article_url,
                'title': content['title'],
                'date': today,
                'saved_file': str(filepath)
            })
            
            total_articles += 1
            time.sleep(1)
        
        read_record[list_key]['last_updated'] = today
    
    save_read_record(read_record, record_file)
    
    print(f"\n[✓] Done!")
    print(f"    - Total articles read: {total_articles}")
    print(f"    - Skipped (already read): {skipped_articles}")
    print(f"    - Output: {output_subdir}")

if __name__ == "__main__":
    main()
