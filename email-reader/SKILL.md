---
name: email-reader
description: QQ邮箱邮件读取器 - 读取QQ邮箱邮件，支持获取邮件列表和详情，自动记录已读进度。使用场景：(1) 获取最新N封邮件列表 (2) 根据邮件ID读取邮件详情
---

# Email Reader

## 功能说明

1. **读取邮件列表** - 获取最新 N 封邮件的基本信息
2. **读取邮件详情** - 根据邮件ID获取单封邮件完整内容
3. **进度记录** - 自动记录已读邮件 ID，避免重复读取

## 使用方法

### 配置 QQ 邮箱

1. 复制示例配置：
```bash
cp configs/email-reader.json configs/email-reader.json.bak
# 编辑 configs/email-reader.json 填入真实配置
```

2. QQ邮箱需要使用授权码登录：
   - 登录 QQ 邮箱 → 设置 → 账户 → 开启 IMAP/SMTP 服务 → 生成授权码

### 读取邮件列表

```bash
# 读取最新 10 封邮件
python email-reader/scripts/reader.py list --limit 10

# 只显示未读邮件
python email-reader/scripts/reader.py list --unread
```

### 读取邮件详情

```bash
# 根据 email_id 读取详情（快速，推荐）
python email-reader/scripts/reader.py read --email-id 5530

# 根据 message-id 读取详情（较慢，需遍历搜索）
python email-reader/scripts/reader.py read --message-id "<xxx@xxx.com>"
```

## 输出格式

### 邮件列表
```json
[
  {"email_id": "5531", "message_id": "xxx", "from": "发件人", "subject": "主题", "date": "日期", "unread": true}
]
```

> 注意：返回的 email_id 可用于快速读取邮件详情，避免遍历搜索

### 邮件详情
```json
{
  "message_id": "xxx",
  "from": "发件人",
  "to": "收件人", 
  "subject": "主题",
  "date": "日期",
  "body": "正文内容",
  "attachments": []
}
```

## 配置说明

配置文件: `configs/email-reader.json`

```json
{
  "email": "your_email@qq.com",
  "password": "your授权码"
}
```
