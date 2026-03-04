# Classifier Skill

邮件分类：AI相关英文邮件 / AI相关中文邮件 / 其他

## 安装依赖

```bash
pip install -r scripts/requirements.txt
```

## 配置

**模型**：MiniMax M2.5

1. 复制示例配置：
```bash
cp config/example.json ../../configs/classifier.json
```

2. 编辑 `../../configs/classifier.json`，填入 API key：
```json
{
  "api_key": "your_minimax_api_key"
}
```

获取 MiniMax API key: https://platform.minimax.io/

## 分类策略（撇脂法）

采用"撇脂"策略优化 API 调用：

1. **语言检测**：先用 langdetect 快速判断邮件语言（中文/英文/其他）
2. **AI 相关性判断**：仅对中文或英文邮件调用 LLM 判断是否与 AI 相关
3. **直接分类**：非中英文邮件直接归类为"其他"

这种策略可以：
- 减少 API 调用次数（非中英文内容无需调用 LLM）
- 提升分类效率
- 降低成本

## 使用

```bash
# 分类文本
python scripts/classify.py --text "This is about AI and machine learning"

# 分类文件
python scripts/classify.py --file email.txt
```
