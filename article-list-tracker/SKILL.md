---
name: article-list-tracker
description: 文章列表追踪器 - 从邮件中提取文章URL，分析并追踪其所属的文章列表/分类页URL，自动去重后保存到本地文件。使用场景：(1) 用户需要从包含文章链接的邮件中提取文章列表URL (2) 追踪文章来源，避免重复记录相同的文章列表
---

# Article List Tracker

## 功能说明

1. **自动提取文章链接**：从邮件 HTML 中自动提取带有 "minute read" 的文章标题和链接
2. **查找文章列表URL**：根据每个文章URL，分析其所属的文章列表/分类页URL
3. **URL验证**：
   - 检查URL是否可访问（HTTP状态码检查）
   - 检查URL是否为文章列表页（AI分析页面类型）
   - 验证失败的URL记录到失败列表，下次跳过
4. **去重保存**：将验证通过的URL保存到本地文件，自动跳过已存在和验证失败的URL

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

### 成功列表 (article_lists.txt)

纯文本文件，每行一个文章列表URL：

```
https://example.com/category/tech
https://example.com/category/ai
https://blog.site.com/column/python
```

### 失败列表 (failed_url_list.txt)

验证失败的URL会被记录到这个文件，下次运行时自动跳过：

```
https://example.com/article/123
https://project.site.com
```

## 工作流程

1. 读取邮件 JSON 文件（从 email-reader 获取）
2. 解析 HTML 提取文章链接（带有 "minute read" 标题）
3. 对每个文章URL，调用 MiniMax API 分析其所属的文章列表URL
4. 加载已保存的URL列表和失败URL列表
5. 对每个候选URL进行验证：
   - 检查URL是否可访问
   - 检查URL是否为文章列表页
6. 验证通过且不在已有列表中的URL追加到文件

## 验证失败URL管理

- 失败URL保存在 `failed_url_list.txt`
- 再次运行时，已验证失败的URL会自动跳过
- 如需重新验证失败URL，可手动删除 `failed_url_list.txt` 文件

## API 配置

MiniMax API key 获取地址: https://platform.minimax.io/
