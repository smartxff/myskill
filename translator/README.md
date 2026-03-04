# Translator Skill

英文邮件翻译为中文。

## 功能特点

- 支持纯文本和 HTML 翻译
- HTML 模式下保留所有标签、样式和链接
- 批量翻译优化：所有文本一次性提交，减少 API 调用
- 自动识别英文内容，只翻译需要翻译的部分

## 安装依赖

```bash
pip install -r scripts/requirements.txt
```

## 配置

**模型**：MiniMax M2.5

1. 复制示例配置：
```bash
cp config/example.json ../../configs/translator.json
```

2. 编辑 `../../configs/translator.json`，填入 API key：
```json
{
  "api_key": "your_minimax_api_key"
}
```

获取 MiniMax API key: https://platform.minimax.io/

## 使用

```bash
# 翻译文本
python scripts/translate.py --text "Hello world"

# 翻译文件
python scripts/translate.py --file article.txt --output translated.txt

# 翻译 HTML 邮件（推荐）
python scripts/translate.py --file email.html --output translated_email.html
```

## 性能

| 文件类型 | 文本节点 | API调用 | 耗时 |
|----------|----------|---------|------|
| 小型 HTML | 7 | 1 | ~8s |
| 邮件 (~40KB) | 82 | 1 | ~37s |

相比逐句翻译，速度提升 3-5 倍。
