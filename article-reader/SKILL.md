---
name: article-reader
description: 文章阅读器 - 从文章列表URL文件中读取URL，访问每个列表页获取最新文章，保存为Markdown格式。使用场景：(1) 读取已追踪的文章列表URL (2) 获取每个列表的最新文章内容 (3) 自动去除广告和无关内容
---

# Article Reader

## 功能说明

1. **读取URL列表**：从文件读取文章列表URL
2. **获取最新文章**：访问每个列表URL，获取最新N篇文章
3. **智能清洗**：自动去除广告、推荐、社交按钮等无关内容
4. **保存为Markdown**：将文章保存为Markdown格式
5. **去重记录**：记录已读取的文章，避免重复读取

## 依赖

```bash
pip install requests beautifulsoup4 markdownify
```

## 使用方法

```bash
cd /root/myskills/article-reader
python3 scripts/read_articles.py

# 指定每个列表读取的文章数
python3 scripts/read_articles.py --limit 10
```

## 输出

文章保存到 `outputs/日期/` 目录下
