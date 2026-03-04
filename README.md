# My Skills

项目自定义 Skills 集合。

## Skills 列表

| Skill | 功能 | 模型/服务 |
|-------|------|----------|
| translator | 翻译：英文 → 中文 | MiniMax M2.5 |
| classifier | 分类：AI相关英文 / AI相关中文 / 其他 | MiniMax M2.5 |
| email-reader | 读取 QQ 邮箱邮件 | QQ邮箱 IMAP/SMTP |
| article-list-tracker | 从邮件中提取文章列表URL并去重 | MiniMax M2.5 |

## 快速开始

### 1. 安装依赖

```bash
pip install -r skills/*/scripts/requirements.txt
```

### 2. 配置

每个 skill 的配置位于 `configs/` 目录：

```
configs/
├── translator.json
├── classifier.json
├── email-reader.json
└── article-list-tracker.json
```

#### 配置方法

1. 复制示例配置：
```bash
# translator
cp skills/translator/config/example.json configs/translator.json

# classifier
cp skills/classifier/config/example.json configs/classifier.json

# email-reader
cp skills/email-reader/config/example.json configs/email-reader.json

# article-list-tracker
cp skills/article-list-tracker/config/example.json configs/article-list-tracker.json
```

2. 编辑 `configs/` 下的配置文件，填入真实配置

### 3. 使用

```bash
# 读取邮件详情
python skills/email-reader/scripts/reader.py read --latest

# 文章列表追踪（从邮件中提取文章列表URL）
python skills/article-list-tracker/scripts/track.py --stdin
```

## 项目结构

```
myskills/
├── .gitignore
├── README.md
├── AGENTS.md
├── configs/                    # 真实配置（git ignore）
│   ├── translator.json
│   ├── classifier.json
│   ├── email-reader.json
│   └── article-list-tracker.json
└── skills/                     # Skills 代码
    ├── translator/
    │   ├── SKILL.md
    │   ├── README.md
    │   ├── config/
    │   │   └── example.json
    │   └── scripts/
    ├── classifier/
    │   ├── SKILL.md
    │   ├── README.md
    │   ├── config/
    │   │   └── example.json
    │   └── scripts/
    ├── email-reader/
    │   ├── SKILL.md
    │   ├── README.md
    │   ├── config/
    │   │   └── example.json
    │   └── scripts/
    └── article-list-tracker/
        ├── SKILL.md
        ├── config/
        │   └── example.json
        └── scripts/
```
