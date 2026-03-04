#!/usr/bin/env python3 -u
import argparse
import json
import re
import sys
import urllib.parse
from pathlib import Path

import requests
from bs4 import BeautifulSoup

CONFIG_FILE = Path(__file__).resolve().parent.parent.parent / "configs" / "article-list-tracker.json"
OUTPUT_FILE = Path("article_lists.txt")
MINIMAX_API_URL = "https://api.minimax.chat/v1/text/chatcompletion_v2"

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {"api_key": ""}

def save_config(api_key: str):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump({"api_key": api_key}, f, indent=2)
    print(f"Configuration saved to {CONFIG_FILE}")

def call_minimax(prompt: str, system_prompt: str = None, api_key: str = None) -> str:
    if not api_key:
        return "Error: API key not configured"
    
    if system_prompt is None:
        system_prompt = "你是一个专业的AI助手。请严格按照用户要求返回结果，不要添加任何解释或额外内容。"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "MiniMax-M2.5",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        response = requests.post(MINIMAX_API_URL, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {str(e)}"

def extract_article_links_from_html(html_content: str) -> list:
    soup = BeautifulSoup(html_content, 'html.parser')
    articles = []
    
    for strong in soup.find_all('strong'):
        text = strong.get_text(strip=True)
        if 'minute read' in text.lower():
            parent = strong.find_parent('a')
            if parent:
                href = parent.get('href', '')
                if 'tracking.tldrnewsletter.com' in href and '/CL0/' in href:
                    path = urllib.parse.urlparse(href).path
                    if '/CL0/' in path:
                        try:
                            encoded = path.split('/CL0/')[1].split('/')[0]
                            decoded_url = urllib.parse.unquote(encoded)
                            articles.append((text, decoded_url))
                        except:
                            pass
    
    return articles

def extract_article_urls(mail_text: str, api_key: str) -> list:
    system_prompt = """你是一个文章链接提取助手。从用户提供的邮件内容中提取所有文章的URL。
要求：
1. 只提取文章的具体URL（通常是文章的详情页）
2. 每行一个URL，不要有任何其他内容
3. 如果没有找到任何文章URL，返回"NONE"."""

    result = call_minimax(mail_text, system_prompt, api_key)
    
    if result == "NONE" or result.startswith("Error"):
        return []
    
    urls = []
    for line in result.strip().split("\n"):
        line = line.strip()
        if line.startswith("http://") or line.startswith("https://"):
            urls.append(line)
    
    return urls

def find_list_urls_batch(article_urls: list, api_key: str) -> list:
    if not article_urls:
        return []
    
    urls_text = "\n".join([f"{i+1}. {url}" for i, url in enumerate(article_urls)])
    
    system_prompt = f"""你是一个URL分析助手。根据用户提供的多个文章URL，分析并找出每个文章所属的文章列表/分类页URL。

文章URL列表：
{urls_text}

要求：
1. 对每个文章URL，分析其所属的列表/分类页URL
2. 格式：每行一个结果，格式为 "原文章URL -> 列表URL"
3. 如果某文章无法确定列表URL，格式为 "原文章URL -> NONE"
4. 不要添加任何解释"""
    
    result = call_minimax("", system_prompt, api_key)
    
    list_urls = {}
    for line in result.strip().split("\n"):
        if "->" in line:
            parts = line.split("->", 1)
            if len(parts) == 2:
                original_url = parts[0].strip()
                list_url = parts[1].strip()
                if list_url and list_url.upper() != "NONE":
                    list_urls[original_url] = list_url
    
    return list_urls

def find_list_url(article_url: str, api_key: str) -> str:
    system_prompt = f"""你是一个URL分析助手。根据给定的文章URL，分析并找出其所属的文章列表/分类页URL。

文章URL: {article_url}

要求：
1. 分析这个文章URL属于哪个网站
2. 找出该文章的列表/分类页URL（例如：/category/xxx, /tag/xxx, /column/xxx, /topic/xxx 等）
3. 只返回列表页的完整URL，不要返回文章详情页
4. 如果无法确定列表页，返回"NONE"
5. 不要添加任何解释，只返回URL或NONE"""

    result = call_minimax("", system_prompt, api_key)
    
    result = result.strip()
    if result == "NONE":
        return None
    
    for line in result.strip().split("\n"):
        line = line.strip()
        if line.startswith("http://") or line.startswith("https://"):
            return line
    
    return None

def load_existing_urls(output_file: Path) -> set:
    if not output_file.exists():
        return set()
    
    urls = set()
    with open(output_file) as f:
        for line in f:
            line = line.strip()
            if line:
                urls.add(line)
    return urls

def save_urls(new_urls: list, output_file: Path, existing_urls: set):
    added = 0
    with open(output_file, "a") as f:
        for url in new_urls:
            if url not in existing_urls:
                f.write(url + "\n")
                existing_urls.add(url)
                added += 1
                print(f"[+] Added: {url}")
            else:
                print(f"[-] Skipped (duplicate): {url}")
    
    return added

def process_email_file(email_file: Path, api_key: str) -> list:
    print(f"[*] Loading email from {email_file}...")
    with open(email_file) as f:
        email_data = json.load(f)
    
    body = email_data.get('body', '')
    if not body:
        print("[-] No email body found")
        return []
    
    print(f"[*] Extracting article links from email body ({len(body)} chars)...")
    articles = extract_article_links_from_html(body)
    
    if articles:
        print(f"[+] Found {len(articles)} articles")
        for i, (title, url) in enumerate(articles, 1):
            print(f"    {i}. {title}")
            print(f"       {url}")
        return [url for _, url in articles]
    
    print("[-] No articles found in email, falling back to AI extraction...")
    return None

def main():
    parser = argparse.ArgumentParser(description="Article List Tracker")
    parser.add_argument("--text", help="Mail text content")
    parser.add_argument("--file", help="File containing mail text (plain text or email JSON)")
    parser.add_argument("--mail", help="Email JSON file from email-reader")
    parser.add_argument("--stdin", action="store_true", help="Read from stdin")
    parser.add_argument("--output", help="Output file (default: article_lists.txt)")
    parser.add_argument("--config", action="store_true", help="Configure API key")
    parser.add_argument("--api-key", help="API key for Minimax")
    
    args = parser.parse_args()
    
    if args.config:
        api_key = args.api_key or input("Enter Minimax API key: ").strip()
        save_config(api_key)
        return
    
    config = load_config()
    api_key = args.api_key or config.get("api_key", "")
    
    if not api_key:
        print("Error: API key not configured. Run: python scripts/track.py --config")
        sys.exit(1)
    
    text = args.text
    fallback_ai_extract = False
    
    if args.mail:
        article_urls = process_email_file(Path(args.mail), api_key)
        if article_urls is None:
            fallback_ai_extract = True
    elif args.file:
        with open(args.file) as f:
            content = f.read()
        # Check if it's an email JSON file
        if content.strip().startswith('{') and '"body"' in content:
            try:
                email_data = json.loads(content)
                article_urls = process_email_file(Path(args.file), api_key)
                if article_urls is None:
                    fallback_ai_extract = True
            except:
                text = content
                fallback_ai_extract = True
        else:
            text = content
            fallback_ai_extract = True
    elif args.stdin:
        text = sys.stdin.read()
        fallback_ai_extract = True
    else:
        text = args.text
        fallback_ai_extract = True
    
    if fallback_ai_extract and not article_urls:
        if not text:
            print("Error: No text provided. Use --text, --file, --mail, or --stdin")
            sys.exit(1)
        
        print("[*] Step 1: Extracting article URLs from mail...")
        article_urls = extract_article_urls(text, api_key)
        print(f"[+] Found {len(article_urls)} article URLs")
    
    if not article_urls:
        print("[-] No article URLs found")
        sys.exit(0)
    
    output_file = Path(args.output) if args.output else OUTPUT_FILE
    
    for url in article_urls:
        print(f"    - {url}")
    
    print("\n[*] Step 2: Finding list URLs for each article (batch mode)...")
    print(f"    Processing {len(article_urls)} URLs in a single API call...")
    list_url_map = find_list_urls_batch(article_urls, api_key)
    
    list_urls = []
    for article_url in article_urls:
        list_url = list_url_map.get(article_url)
        if list_url:
            list_urls.append(list_url)
            print(f"    {article_url[:50]}... -> {list_url}")
        else:
            print(f"    {article_url[:50]}... -> No list URL found")
    
    if not list_urls:
        print("[-] No list URLs found")
        sys.exit(0)
    
    print(f"\n[*] Step 3: Saving to {output_file} (with deduplication)...")
    existing_urls = load_existing_urls(output_file)
    added = save_urls(list_urls, output_file, existing_urls)
    
    print(f"\n[✓] Done! Added {added} new list URLs, skipped {len(list_urls) - added} duplicates")

if __name__ == "__main__":
    main()
