---
name: translator
description: 翻译工具 - 支持直接翻译 HTML 内容。使用场景：(1) 用户需要将英文文章翻译成中文 (2) 支持直接传入 HTML 内容，会自动识别并解析，只翻译文本部分，保留 HTML 标签和结构 (3) 检测输入语言，如果是英文则翻译为中文，如果是中文则直接返回原文
---

# Translator

## 功能说明

1. **语言检测**: 使用 langdetect 库自动检测输入文章是中文还是英文
2. **智能翻译**: 
   - 如果输入是中文 → 直接返回原文
   - 如果输入是英文 → 调用 Minimax M2.5 API 翻译成中文
3. **HTML 支持（重点）**: 
   - 支持直接传入 HTML 内容，**无需用户自行解析**
   - 自动识别 HTML 格式，智能解析 HTML 结构
   - 保留所有 HTML 标签、链接、属性和结构
   - 只翻译标签内的文本内容
   - 例如：`<p>Hello</p>` → `<p>你好</p>`

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
