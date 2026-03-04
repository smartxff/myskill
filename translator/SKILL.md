---
name: translator
description: 翻译工具 - 将英文文章翻译成中文。使用场景：(1) 用户需要将英文文章翻译成中文 (2) 检测输入语言，如果是英文则翻译为中文，如果是中文则直接返回原文
---

# Translator

## 功能说明

1. **语言检测**: 使用 langdetect 库自动检测输入文章是中文还是英文
2. **智能翻译**: 
   - 如果输入是中文 → 直接返回原文
   - 如果输入是英文 → 调用 Minimax M2.5 API 翻译成中文
3. **HTML支持**: 自动识别HTML格式，保留HTML标签和链接，只翻译文本内容

## 依赖

```bash
pip install beautifulsoup4
```

## 使用方法

### 基本翻译

```bash
# 翻译文本
python scripts/translate.py --text "Hello world"

# 翻译文件
python scripts/translate.py --file article.txt
```

### 配置 API Key

```bash
# 配置 Minimax API key
python scripts/translate.py --config --api-key YOUR_MINIMAX_API_KEY
```

### 输出到文件

```bash
python scripts/translate.py --file article.txt --output translated.txt
```

## API 配置

Minimax API key 获取地址: https://platform.minimax.io/

详细配置说明见 [api-options.md](references/api-options.md)

## 语言检测

- 使用 `langdetect` 库检测语言
- 支持: 中文 (zh-cn, zh-tw, zh)、英文 (en) 等
- 非英文文章也会翻译成中文
