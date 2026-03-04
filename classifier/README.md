# Classifier Skill

邮件分类：AI相关英文邮件 / AI相关中文邮件 / 其他

## 安装依赖

```bash
pip install -r scripts/requirements.txt
```

## 配置

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

## 使用

```bash
# 分类文本
python scripts/classify.py --text "This is about AI and machine learning"

# 分类文件
python scripts/classify.py --file email.txt
```
