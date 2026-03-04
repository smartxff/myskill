# Email Reader Skill

读取 QQ 邮箱邮件。

## 安装依赖

```bash
pip install -r scripts/requirements.txt
```

## 配置

**邮箱**：QQ 邮箱

1. 复制示例配置：
```bash
cp config/example.json ../../configs/email-reader.json
```

2. 编辑 `../../configs/email-reader.json`，填入 QQ 邮箱和授权码：
```json
{
  "email": "your_email@qq.com",
  "password": "your_auth_code"
}
```

**获取 QQ 邮箱授权码：**
1. 登录 QQ 邮箱
2. 设置 → 账户
3. 开启 IMAP/SMTP 服务
4. 生成授权码

## 使用

```bash
# 获取邮件列表（最新10封）
python scripts/reader.py list --limit 10

# 只获取未读邮件
python scripts/reader.py list --unread

# 读取最新一封邮件详情
python scripts/reader.py read --latest

# 根据 ID 读取邮件详情
python scripts/reader.py read --message-id "<xxx@qq.com>"
```

## 进度记录

已读邮件记录在 `../../configs/email-reader-history.json`
