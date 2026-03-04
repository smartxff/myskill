#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

try:
    from langdetect import detect, LangDetectException
except ImportError:
    print("Error: langdetect not installed. Run: pip install langdetect")
    sys.exit(1)

import requests

CONFIG_FILE = Path(__file__).resolve().parent.parent.parent / "configs" / "classifier.json"
MINIMAX_API_URL = "https://api.minimax.chat/v1/text/chatcompletion_v2"

DEFAULT_CATEGORIES = ["AI相关英文邮件", "AI相关中文邮件", "其他"]

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {"api_key": ""}

def detect_language(text: str) -> str:
    try:
        lang = detect(text)
        if lang in ["en"]:
            return "en"
        elif lang in ["zh-cn", "zh-tw", "zh"]:
            return "zh"
        return "other"
    except LangDetectException:
        return "unknown"

def classify_with_llm(text: str, categories: list, api_key: str) -> dict:
    if not api_key:
        return {"category": None, "error": "API key not configured"}
    
    categories_str = ", ".join(categories)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""请将以下邮件内容分类到指定类别之一: {categories_str}

邮件内容:
{text}

请直接返回类别名称，不要添加任何解释。"""
    
    payload = {
        "model": "MiniMax-M2.5",
        "messages": [
            {
                "role": "system",
                "content": "你是一个邮件分类助手。请根据邮件内容进行分类，只返回类别名称。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    try:
        response = requests.post(MINIMAX_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        category = result["choices"][0]["message"]["content"].strip()
        return {"category": category, "error": None}
    except Exception as e:
        return {"category": None, "error": str(e)}

def classify(text: str, categories: list = None, api_key: str = None) -> dict:
    if categories is None:
        categories = DEFAULT_CATEGORIES
    
    if api_key is None:
        config = load_config()
        api_key = config.get("api_key", "")
    
    lang = detect_language(text)
    
    if lang == "zh":
        relevant = check_ai_relevant(text, api_key)
        if relevant:
            return {"category": "AI相关中文邮件", "language": "zh", "ai_relevant": True}
        return {"category": "其他", "language": "zh", "ai_relevant": False}
    
    if lang == "en":
        relevant = check_ai_relevant(text, api_key)
        if relevant:
            return {"category": "AI相关英文邮件", "language": "en", "ai_relevant": True}
        return {"category": "其他", "language": "en", "ai_relevant": False}
    
    return {"category": "其他", "language": "unknown", "ai_relevant": False}

def check_ai_relevant(text: str, api_key: str) -> bool:
    if not api_key:
        return False
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""判断以下邮件内容是否与AI相关。只返回"是"或"否"，不要返回其他内容。

邮件内容:
{text}"""
    
    payload = {
        "model": "MiniMax-M2.5",
        "messages": [
            {
                "role": "system",
                "content": "判断内容是否与AI相关，只回答是或否。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    try:
        response = requests.post(MINIMAX_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        answer = result["choices"][0]["message"]["content"].strip()
        return "是" in answer or "yes" in answer.lower()
    except:
        return False

def main():
    parser = argparse.ArgumentParser(description="Classifier - 邮件分类器")
    parser.add_argument("--text", help="要分类的文本")
    parser.add_argument("--file", help="要分类的文件")
    parser.add_argument("--categories", help="类别列表，用逗号分隔")
    parser.add_argument("--output", help="输出文件")
    parser.add_argument("--config", action="store_true", help="配置 API key")
    parser.add_argument("--api-key", help="API key")
    
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
    
    categories = DEFAULT_CATEGORIES
    if args.categories:
        categories = [c.strip() for c in args.categories.split(",")]
    
    config = load_config()
    api_key = args.api_key or config.get("api_key", "")
    
    result = classify(text, categories, api_key)
    
    output = f"分类结果: {result['category']}"
    if "language" in result:
        output += f"\n语言: {result['language']}"
    if "ai_relevant" in result:
        output += f"\nAI相关: {result['ai_relevant']}"
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"结果已保存到 {args.output}")
    else:
        print(output)

if __name__ == "__main__":
    main()
