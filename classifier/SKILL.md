---
name: classifier
description: 邮件分类器 - 将邮件分类为: AI相关英文邮件、AI相关中文邮件、其他。使用场景：(1) 对邮件进行自动分类 (2) 筛选特定类型邮件
---

# Classifier

## 功能说明

使用 MiniMax LLM 对邮件进行智能分类。

## 分类类别

1. **AI相关英文邮件** - 与 AI 相关的英文邮件
2. **AI相关中文邮件** - 与 AI 相关的中文邮件
3. **其他** - 不属于上述类别的邮件

## 使用方法

### 基本使用

```bash
# 分类文本
python scripts/classify.py --text "邮件内容..."

# 分类文件
python scripts/classify.py --file email.txt

# 指定类别列表
python scripts/classify.py --text "邮件内容" --categories "AI英文,AI中文,其他"
```

### 配置 API

```bash
# 配置 MiniMax API
python scripts/classify.py --config --api-key YOUR_API_KEY
```

## 输出格式

```
分类结果: AI相关英文邮件
置信度: 0.95
```

## 依赖

- langdetect
- requests
