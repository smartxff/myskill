---
name: article-list-tracker
description: 文章列表追踪器 - 从邮件中提取文章URL，分析并追踪其所属的文章列表/分类页URL，自动去重后保存到本地文件。使用场景：(1) 用户需要从包含文章链接的邮件中提取文章列表URL (2) 追踪文章来源，避免重复记录相同的文章列表
---

# Article List Tracker

## 功能说明

1. **自动提取文章链接**：从邮件 HTML 中自动提取带有 "minute read" 的文章标题和链接
2. **查找文章列表URL**：根据每个文章URL，分析其所属的文章列表/分类页URL
3. **去重保存**：将文章列表URL保存到本地文件，自动跳过已存在的URL

## 依赖

```bash
pip install requests beautifulsoup4
```

## 使用方法

### 推荐：从邮件 JSON 直接提取

```bash
# 先用 email-reader 读取邮件
python skills/email-reader/scripts/reader.py read --email-id 5506 --output mail.json

# 用 article-list-tracker 处理（自动提取文章链接）
python skills/article-list-tracker/scripts/track.py --mail mail.json
```

### 其他方式

```bash
# 指定输出文件
python skills/article-list-tracker/scripts/track.py --mail mail.json --output my_lists.txt

# 管道输入
cat mail.json | python skills/article-list-tracker/scripts/track.py --stdin
```

### 配置 API Key

```bash
python skills/article-list-tracker/scripts/track.py --config --api-key YOUR_MINIMAX_API_KEY
```

## 输出格式

纯文本文件，每行一个文章列表URL：

```
https://example.com/category/tech
https://example.com/category/ai
https://blog.site.com/column/python
```

## 工作流程

1. 读取邮件 JSON 文件（从 email-reader 获取）
2. 解析 HTML 提取文章链接（带有 "minute read" 标题）
3. 对每个文章URL，调用 MiniMax API 分析其所属的文章列表URL
4. 读取本地已保存的URL列表
5. 新URL追加到文件，已存在的URL跳过

## API 配置

MiniMax API key 获取地址: https://platform.minimax.io/
