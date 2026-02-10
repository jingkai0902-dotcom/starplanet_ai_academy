# 斯坦星球钉钉机器人

基于RAG+LLM的智能知识库问答机器人，为销售顾问和教师提供即时知识支持。

## 功能特性

- 📚 **知识库问答**：基于500+份知识文档的智能问答
- 🤖 **快捷命令**：`/stem`、`/code`、`/python`、`/价格` 快速获取常用信息
- 💬 **自然对话**：支持任意问题的智能回答
- 🔍 **智能搜索**：根据关键词匹配最相关的知识内容

## 快速开始

### 1. 配置

复制配置文件模板：
```bash
copy config.example.json config.json
```

编辑 `config.json` 填写以下信息：
```json
{
    "app_key": "钉钉应用AppKey",
    "app_secret": "钉钉应用AppSecret",
    "agent_id": "钉钉机器人AgentID",
    "claude_api_key": "Claude API Key",
    "claude_base_url": ""  // 可选，支持中转API
}
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动

**方式一：双击启动**
```
双击 启动机器人.bat
```

**方式二：命令行启动**
```bash
python bot.py
```

### 4. 配置钉钉

1. 登录 [钉钉开放平台](https://open.dingtalk.com/)
2. 创建企业内部应用 → 机器人
3. 配置消息接收地址：`http://你的服务器IP:8080/dingtalk/callback`
4. 开启机器人能力，发布应用

## 使用指南

### 帮助命令
发送 `帮助` 或 `help` 查看使用说明

### 快捷命令

| 命令 | 说明 |
|------|------|
| `/stem` | 查看STEM幼儿科创课程介绍 |
| `/code` | 查看CODE少儿编程课程介绍 |
| `/python` | 查看PythonAI课程介绍 |
| `/价格` | 查看价格异议处理话术 |

### 常见问题示例

- STEM小班学什么内容？
- CODE1和CODE2有什么区别？
- 孩子多大可以学编程？
- 家长说价格贵怎么处理？
- Python有什么用怎么回答家长？

## 知识库内容

已加载 **506份** 知识文档（V2.0 单节课拆分版），涵盖：

| 类别 | 数量 | 内容 |
|------|------|------|
| STEM课程 | 170+ | 小班/中班/大班单节课萃取（含5E流程） |
| CODE课程 | 170+ | CODE1/2/3单节课萃取（含七步教学法） |
| PythonAI课程 | 100+ | L1/L2/MP单节课萃取（含代码示例） |
| 品牌知识 | 8份 | 品牌定位、教育理念、销售话术 |
| 知识点数据库 | 37份 | 编程概念、硬件知识、AI知识、机械结构 |
| 教师培训手册 | 4份 | STEM/CODE/PythonAI/通用培训手册 |
| 素材资源 | 5份 | 各课程素材资源库 |

## 目录结构

```
dingtalk_bot/
├── bot.py              # 主程序
├── convert_kb.py       # 知识库转换工具
├── config.json         # 配置文件（需创建）
├── config.example.json # 配置文件模板
├── requirements.txt    # Python依赖
├── 启动机器人.bat       # Windows启动脚本
├── README.md           # 本文档
└── knowledge_base/     # 知识库JSON文件
    ├── _index.json     # 知识库索引
    └── *.json          # 各知识文档
```

## 更新知识库

当知识库有更新时，重新运行转换脚本：
```bash
python convert_kb.py
```

然后重启机器人。

## 生产部署

### 使用Gunicorn（推荐）

```bash
gunicorn -w 4 -b 0.0.0.0:8080 bot:app
```

### 使用Systemd服务（Linux）

```ini
[Unit]
Description=Starplanet Dingtalk Bot
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/dingtalk_bot
ExecStart=/usr/bin/gunicorn -w 4 -b 0.0.0.0:8080 bot:app
Restart=always

[Install]
WantedBy=multi-user.target
```

### 使用内网穿透（测试）

本地开发时可使用 ngrok 或 frp 进行内网穿透：
```bash
ngrok http 8080
```

## 注意事项

1. **API密钥安全**：`config.json` 包含敏感信息，请勿提交到版本控制
2. **网络访问**：需要能访问 Claude API（或中转地址）
3. **钉钉验签**：生产环境请确保 `app_secret` 已配置

## 技术支持

如有问题，请联系技术支持或查看日志：
- 日志输出在控制台
- 健康检查：`GET http://localhost:8080/`
