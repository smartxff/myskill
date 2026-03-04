#!/usr/bin/env python3 -u
import argparse
import json
import re
import sys
import time
import urllib.parse
from pathlib import Path

import requests
from bs4 import BeautifulSoup

CONFIG_FILE = Path(__file__).resolve().parent.parent.parent / "configs" / "article-list-tracker.json"
OUTPUT_FILE = Path("article_lists.txt")
FAILED_URLS_FILE = Path("failed_url_list.txt")
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

def resolve_redirect_url(url: str, max_redirects: int = 5) -> str:
    try:
        for _ in range(max_redirects):
            r = requests.head(url, allow_redirects=False, timeout=10)
            if r.status_code in (301, 302, 303, 307, 308):
                location = r.headers.get('Location')
                if location:
                    if location.startswith('http'):
                        url = location
                    else:
                        url = urllib.parse.urljoin(url, location)
                else:
                    break
            else:
                break
        return url
    except Exception:
        return url

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

def find_list_urls_batch(article_urls: list, api_key: str) -> dict:
    if not article_urls:
        return {}
    
    urls_text = "\n".join([f"{i+1}. {url}" for i, url in enumerate(article_urls)])
    
    system_prompt = f"""你是一个URL分析助手。根据用户提供的多个文章URL，找出每个文章所属的**网站首页或分类列表页**URL。

文章URL列表：
{urls_text}

要求：
1. 只返回网站的主页或分类列表页URL（如 /category/ai, /tag/tech, /blog, /news 等）
2. 不要返回包含日期路径的URL（如 /2026/03/02, /2025/12/ 等）
3. 不要返回文章详情页URL（如 /article/xxx, /post/xxx）
4. 优先返回网站的根URL或主要分类页
5. 格式：每行一个结果，格式为 "原文章URL -> 列表URL"
6. 如果无法确定，返回 "原文章URL -> NONE"
7. 列表页示例：
   - https://example.com/ (网站首页)
   - https://example.com/blog (博客列表)
   - https://example.com/category/tech (技术分类)
   - https://example.com/tag/ai (AI标签页)
8. 非列表页示例（不要返回这些）：
   - https://example.com/article/123 (文章详情)
   - https://example.com/2026/03/02/post-name (日期路径)
   - https://example.com/blog/post-name (博客详情页)"""

    result = call_minimax("", system_prompt, api_key)
    
    article_url_bases = {}
    for url in article_urls:
        if '?' in url:
            base = url.split('?')[0]
            article_url_bases[base] = url
            article_url_bases[url] = url
        else:
            article_url_bases[url] = url
    
    list_urls = {}
    for line in result.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        
        if "->" not in line:
            continue
        
        line = line.lstrip('0123456789. ')
        
        if "->" not in line:
            continue
        
        parts = line.split("->", 1)
        if len(parts) == 2:
            original_url = parts[0].strip()
            list_url = parts[1].strip()
            
            if not list_url or list_url.upper() == "NONE":
                continue
            
            matched_article = article_url_bases.get(original_url)
            
            if not matched_article:
                for base, full in article_url_bases.items():
                    if original_url.startswith(base) or base.startswith(original_url.rstrip('/')):
                        matched_article = full
                        break
            
            if matched_article:
                list_urls[matched_article] = list_url
    
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

def load_failed_urls(file_path: Path) -> set:
    if not file_path.exists():
        return set()
    
    urls = set()
    with open(file_path) as f:
        for line in f:
            line = line.strip()
            if line:
                urls.add(line)
    return urls

def save_failed_urls(urls: set, file_path: Path):
    with open(file_path, "w") as f:
        for url in sorted(urls):
            f.write(url + "\n")

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

def check_url_accessible(url: str, timeout: int = 10) -> tuple:
    try:
        r = requests.head(url, allow_redirects=True, timeout=timeout)
        if r.status_code == 200:
            return True, None
        elif r.status_code == 405:
            r = requests.get(url, allow_redirects=True, timeout=timeout)
            if r.status_code == 200:
                return True, None
            return False, f"HTTP {r.status_code}"
        else:
            return False, f"HTTP {r.status_code}"
    except requests.exceptions.Timeout:
        return False, "Timeout"
    except requests.exceptions.RequestException as e:
        return False, str(e)

def check_is_list_page(url: str, api_key: str) -> tuple:
    system_prompt = f"""你是一个网页分析助手。判断给定的URL是否是文章列表/分类页。
    
URL: {url}

要求：
1. 分析这个页面是什么类型的页面
2. 文章列表页特征：包含多篇文章的列表、分类页、标签页、博客首页、新闻频道首页等
3. 非列表页：单篇文章详情页、项目主页、文档页面、个人简介页等
4. 返回格式：
   - 如果是列表页，返回 "YES"
   - 如果不是列表页，返回 "NO:原因"
5. 不要添加任何解释"""

    result = call_minimax("", system_prompt, api_key)
    result = result.strip().upper()
    
    if result.startswith("YES"):
        return True, None
    elif result.startswith("NO:"):
        reason = result[3:].strip()
        return False, reason
    else:
        return False, "Unknown"

def check_is_list_page_batch(urls: list, api_key: str) -> dict:
    if not urls:
        return {}
    
    urls_text = "\n".join([f"{i+1}. {url}" for i, url in enumerate(urls)])
    
    system_prompt = f"""你是一个网页分析助手。批量判断多个URL是否是文章列表/分类页。

URL列表：
{urls_text}

要求：
1. 对每个URL，判断其页面是什么类型
2. 文章列表页特征：包含多篇文章的列表、分类页、标签页、博客首页、新闻频道首页等
3. 非列表页：单篇文章详情页、项目主页、文档页面、个人简介页、单篇论文页面等
4. 返回格式：每行一个结果，格式为 "原URL -> YES" 或 "原URL -> NO:原因"
5. 不要添加任何解释"""

    result = call_minimax("", system_prompt, api_key)
    
    url_base_map = {}
    for url in urls:
        if '?' in url:
            base = url.split('?')[0]
            url_base_map[base] = url
            url_base_map[url] = url
        else:
            url_base_map[url] = url
    
    url_results = {}
    for line in result.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        
        if "->" not in line:
            continue
        
        line = line.lstrip('0123456789. ')
        
        if "->" not in line:
            continue
        
        parts = line.split("->", 1)
        if len(parts) == 2:
            url = parts[0].strip()
            status = parts[1].strip().upper()
            
            matched = url_base_map.get(url)
            if not matched:
                for base, full in url_base_map.items():
                    if url.startswith(base) or base.startswith(url.rstrip('/')):
                        matched = full
                        break
            
            if matched:
                if status.startswith("YES"):
                    url_results[matched] = (True, None)
                elif status.startswith("NO:"):
                    reason = status[3:].strip()
                    url_results[matched] = (False, reason)
                else:
                    url_results[matched] = (False, "Unknown")
    
    return url_results
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
        resolved_urls = []
        for i, (title, url) in enumerate(articles, 1):
            print(f"    {i}. {title}")
            print(f"       Original: {url}")
            resolved = resolve_redirect_url(url)
            print(f"       Resolved: {resolved}")
            resolved_urls.append(resolved)
        return resolved_urls
    
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
    
    start_time = time.time()
    fallback_ai_extract = False
    article_urls = None
    
    print("[*] Step 1: Extracting and resolving article links from email...")
    if args.mail:
        article_urls = process_email_file(Path(args.mail), api_key)
        if article_urls is None:
            fallback_ai_extract = True
    elif args.file:
        with open(args.file) as f:
            content = f.read()
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
        text = args.text if args.text else ""
        fallback_ai_extract = True
    
    if fallback_ai_extract and not article_urls:
        if not text:
            print("Error: No text provided. Use --text, --file, --mail, or --stdin")
            sys.exit(1)
        
        article_urls = extract_article_urls(text, api_key)
    
    step1_time = time.time() - start_time
    print(f"[✓] Step 1 completed in {step1_time:.2f}s - Found {len(article_urls) if article_urls else 0} article URLs")
    
    if not article_urls:
        print("[-] No article URLs found")
        sys.exit(0)
    
    for url in article_urls:
        print(f"    - {url[:80]}...")
    
    print(f"\n[*] Step 2: Finding list URLs for each article (batch mode)...")
    step2_start = time.time()
    list_url_map = find_list_urls_batch(article_urls, api_key)
    step2_time = time.time() - step2_start
    
    list_urls = []
    for article_url in article_urls:
        list_url = list_url_map.get(article_url)
        if list_url:
            list_urls.append(list_url)
            print(f"    {article_url[:50]}... -> {list_url}")
        else:
            print(f"    {article_url[:50]}... -> No list URL found")
    
    print(f"[✓] Step 2 completed in {step2_time:.2f}s - Found {len(list_urls)} list URLs")
    
    if not list_urls:
        print("[-] No list URLs found")
        sys.exit(0)
    
    print(f"\n[*] Step 3: Validating URLs...")
    step3_start = time.time()
    failed_urls = load_failed_urls(FAILED_URLS_FILE)
    print(f"    Loaded {len(failed_urls)} failed URLs from previous runs")
    
    urls_to_validate = [url for url in list_urls if url not in failed_urls]
    print(f"    {len(urls_to_validate)} URLs to validate (skipping {len(list_urls) - len(urls_to_validate)} previously failed)")
    
    if not urls_to_validate:
        print("[-] No URLs to validate")
        sys.exit(0)
    
    print(f"    [*] Checking URL accessibility...")
    accessible_urls = []
    failed_this_run = set()
    
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    def check_single_url(url):
        accessible, error = check_url_accessible(url)
        return url, accessible, error
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(check_single_url, url): url for url in urls_to_validate}
        for future in as_completed(futures):
            url, accessible, error = future.result()
            if accessible:
                accessible_urls.append(url)
            else:
                print(f"        [-] Not accessible: {url} ({error})")
                failed_this_run.add(url)
    
    print(f"    [*] {len(accessible_urls)} URLs accessible, checking if list pages (batch)...")
    
    if not accessible_urls:
        print("[-] No accessible URLs")
    else:
        list_check_results = check_is_list_page_batch(accessible_urls, api_key)
        
        validated_urls = []
        for url in accessible_urls:
            is_list, reason = list_check_results.get(url, (False, "No response"))
            if is_list:
                print(f"        [+] Validated: {url}")
                validated_urls.append(url)
            else:
                print(f"        [-] Not a list page: {url} ({reason})")
                failed_this_run.add(url)
    
    if failed_this_run:
        failed_urls.update(failed_this_run)
        save_failed_urls(failed_urls, FAILED_URLS_FILE)
        print(f"    [*] Updated failed URLs file ({len(failed_urls)} total)")
    
    step3_time = time.time() - step3_start
    print(f"[✓] Step 3 completed in {step3_time:.2f}s - {len(validated_urls) if 'validated_urls' in dir() else 0} validated, {len(failed_this_run)} failed")
    
    if not validated_urls:
        print("[-] No valid list URLs found after validation")
        sys.exit(0)
    
    print(f"\n[*] Step 4: Saving validated URLs...")
    step4_start = time.time()
    output_file = Path(args.output) if args.output else OUTPUT_FILE
    existing_urls = load_existing_urls(output_file)
    added = save_urls(validated_urls, output_file, existing_urls)
    step4_time = time.time() - step4_start
    
    total_time = step1_time + step2_time + step3_time + step4_time
    print(f"[✓] Step 4 completed in {step4_time:.2f}s")
    print(f"\n{'='*50}")
    print(f"[✓] Total time: {total_time:.2f}s")
    print(f"    - Step 1 (Extract): {step1_time:.2f}s")
    print(f"    - Step 2 (Find lists): {step2_time:.2f}s")
    print(f"    - Step 3 (Validate): {step3_time:.2f}s")
    print(f"    - Step 4 (Save): {step4_time:.2f}s")
    print(f"[/=] Added {added} new list URLs, skipped {len(validated_urls) - added} duplicates, {len(failed_this_run)} failed")

if __name__ == "__main__":
    main()
