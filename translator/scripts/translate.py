#!/usr/bin/env python3
import argparse
import json
import sys
import time
from pathlib import Path

try:
    from langdetect import detect, LangDetectException
except ImportError:
    print("Error: langdetect not installed. Run: pip install langdetect")
    sys.exit(1)

import requests
from bs4 import BeautifulSoup, NavigableString, Comment
from bs4 import MarkupResemblesLocatorWarning
from warnings import filterwarnings
filterwarnings("ignore", category=DeprecationWarning)
filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

STATS = {
    "api_calls": 0,
    "total_time": 0,
    "total_chars": 0,
}

CONFIG_FILE = Path(__file__).resolve().parent.parent.parent / "configs" / "translator.json"
MINIMAX_API_URL = "https://api.minimax.chat/v1/text/chatcompletion_v2"

SKIP_TAGS = {'script', 'style', 'noscript', 'meta', 'link', 'br', 'hr', 'img', 'input'}

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {"api_key": ""}

def is_html(text: str) -> bool:
    text = text.strip()
    return text.startswith('<') and '>' in text

def detect_language(text: str) -> str:
    try:
        lang = detect(text)
        return lang
    except LangDetectException:
        return "unknown"

def translate_batch(texts: list, api_key: str) -> dict:
    if not api_key:
        return {t: "Error: API key not configured" for t in texts}
    
    combined = "\n---\n".join(texts)
    print(f"[DEBUG] Batch translating {len(texts)} texts ({len(combined)} chars)...")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "MiniMax-M2.5",
        "messages": [
            {
                "role": "system",
                "content": "你是一个专业的翻译助手。请将用户提供的英文准确翻译成中文，只需要翻译结果，不需要任何解释。保持每行翻译对应原文本的顺序。"
            },
            {
                "role": "user", 
                "content": f"请逐行翻译以下内容，每行对应一个翻译结果：\n{combined}"
            }
        ]
    }
    
    start_time = time.time()
    try:
        response = requests.post(MINIMAX_API_URL, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        translated = result["choices"][0]["message"]["content"]
        
        elapsed = time.time() - start_time
        STATS["api_calls"] += 1
        STATS["total_time"] += elapsed
        STATS["total_chars"] += len(combined)
        
        lines = [l.strip() for l in translated.strip().split("---") if l.strip()]
        result_map = {}
        for i, text in enumerate(texts):
            if i < len(lines):
                result_map[text] = lines[i].strip()
            else:
                result_map[text] = text
        
        print(f"[DEBUG] Batch done: {elapsed:.2f}s")
        return result_map
    except requests.exceptions.RequestException as e:
        return {t: f"Error: {str(e)}" for t in texts}
    except (KeyError, IndexError) as e:
        return {t: f"Error: {str(e)}" for t in texts}

def translate_to_chinese(text: str, api_key: str) -> str:
    if not api_key:
        return "Error: Minimax API key not configured. Run: python scripts/translate.py --config"
    
    print(f"[DEBUG] Submitting for translation: {text[:100]}...")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "MiniMax-M2.5",
        "messages": [
            {
                "role": "system",
                "content": "你是一个专业的翻译助手。请将用户提供的英文准确翻译成中文，只需要翻译结果，不需要任何解释。"
            },
            {
                "role": "user", 
                "content": text
            }
        ]
    }
    
    start_time = time.time()
    try:
        response = requests.post(MINIMAX_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        translated = result["choices"][0]["message"]["content"]
        
        elapsed = time.time() - start_time
        STATS["api_calls"] += 1
        STATS["total_time"] += elapsed
        STATS["total_chars"] += len(text)
        
        print(f"[DEBUG] Translation result: {translated[:100]}... ({elapsed:.2f}s, {len(text)} chars)")
        return translated
    except requests.exceptions.RequestException as e:
        return f"Error: Translation failed - {str(e)}"
    except (KeyError, IndexError) as e:
        return f"Error: Invalid API response - {str(e)}"

def translate_html(html_text: str, api_key: str) -> str:
    soup = BeautifulSoup(html_text, 'html.parser')
    
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()
    
    def get_text_nodes(element):
        texts = []
        for node in element.descendants:
            if isinstance(node, NavigableString):
                text = str(node).strip()
                if text:
                    texts.append((node, text))
        return texts
    
    text_nodes = get_text_nodes(soup)
    
    def is_likely_english(text):
        ascii_count = sum(1 for c in text if c.isascii())
        return ascii_count / len(text) > 0.5 if text else False
    
    en_texts = []
    for node, text in text_nodes:
        parent = node.parent
        if parent and parent.name and parent.name.lower() in SKIP_TAGS:
            continue
        if len(text) > 1 and is_likely_english(text):
            en_texts.append((node, text))
    
    if not en_texts:
        return html_text
    
    unique_texts = []
    seen = set()
    for node, text in en_texts:
        if text not in seen:
            unique_texts.append(text)
            seen.add(text)
    
    translated_map = {}
    
    all_combined = "\n---\n".join(unique_texts)
    translated_map = translate_batch(unique_texts, api_key)
    
    for node, original_text in en_texts:
        if original_text in translated_map:
            new_text = translated_map[original_text]
            node.replace_with(BeautifulSoup(new_text, 'html.parser'))
    
    return str(soup)

def translate(text: str, api_key: str = None) -> str:
    global STATS
    STATS = {"api_calls": 0, "total_time": 0, "total_chars": 0}
    
    if api_key is None:
        config = load_config()
        api_key = config.get("api_key", "")
    
    if is_html(text):
        result = translate_html(text, api_key)
    else:
        lang = detect_language(text)
        
        if lang == "zh-cn" or lang == "zh-tw" or lang == "zh":
            return text
        
        if lang == "en":
            result = translate_to_chinese(text, api_key)
        else:
            result = translate_to_chinese(text, api_key)
    
    print_stats()
    return result

def print_stats():
    if STATS["api_calls"] > 0:
        avg_time = STATS["total_time"] / STATS["api_calls"]
        avg_chars = STATS["total_chars"] / STATS["api_calls"]
        print(f"\n{'='*50}")
        print(f"[STATS] API调用次数: {STATS['api_calls']}")
        print(f"[STATS] 总耗时: {STATS['total_time']:.2f}s")
        print(f"[STATS] 平均耗时: {avg_time:.2f}s/次")
        print(f"[STATS] 平均字数: {avg_chars:.1f} 字/次")
        print(f"{'='*50}")

def main():
    parser = argparse.ArgumentParser(description="Translator CLI - English to Chinese")
    parser.add_argument("--text", help="Text to translate")
    parser.add_argument("--file", help="File to translate")
    parser.add_argument("--output", help="Output file")
    parser.add_argument("--config", action="store_true", help="Configure API key")
    parser.add_argument("--api-key", help="API key for Minimax")
    
    args = parser.parse_args()
    
    if args.config:
        config = load_config()
        if args.api_key:
            config["api_key"] = args.api_key
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
        print(f"Configuration saved to {CONFIG_FILE}")
        return
    
    text = args.text
    if args.file:
        with open(args.file) as f:
            text = f.read()
    
    if not text:
        print("Error: No text provided", file=sys.stderr)
        sys.exit(1)
    
    config = load_config()
    api_key = args.api_key or config.get("api_key", "")
    
    result = translate(text, api_key)
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(result)
        print(f"Translated to {args.output}")
    else:
        print(result)

if __name__ == "__main__":
    main()
