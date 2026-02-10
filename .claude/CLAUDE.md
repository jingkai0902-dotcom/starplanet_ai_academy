# 斯坦星球知识库项目

## 新会话入口

**首先阅读**：`.claude/WORKFLOW.md`（工作进度和待办任务）

> 如需查看课程文档标准和详细课程体系，阅读 `.claude/COURSE_INTEGRATION_PLAN.md`

## 钉钉机器人（已完成）

```
dingtalk_bot/
├── bot.py            # 主程序
├── config.json       # 配置文件（需填写钉钉AppKey等）
├── knowledge_base/   # 已转换121个JSON文档
└── 启动机器人.bat     # Windows启动
```

**启动**：`python dingtalk_bot/bot.py` 或双击 `启动机器人.bat`

## 项目文档

| 文档 | 用途 |
|------|------|
| `.claude/WORKFLOW.md` | 工作进度、待办任务 |
| `.claude/COURSE_INTEGRATION_PLAN.md` | 课程文档标准、4文档体系、课程体系总览 |
| `.claude/PROJECT_INDEX.md` | 项目总索引、文件统计 |
| `.claude/BUILD_PLAN.md` | 建设计划、里程碑 |
| `dingtalk_bot/README.md` | 钉钉机器人部署文档 |

## 按需加载

| 需求 | 加载文件 |
|------|---------|
| 查待办任务 | `.claude/WORKFLOW.md` |
| 查课程标准/体系 | `.claude/COURSE_INTEGRATION_PLAN.md` |
| 查文件位置 | `.claude/PROJECT_INDEX.md` |
| 查萃取报告 | `知识库/萃取报告/_总索引.md` |
| 查萃取规则 | `知识库/协议库/萃取标准/_索引.md` |
| 查NotebookLM | `知识库/NotebookLM笔记本索引.md` |
| 查课程内容 | 使用 `/notebooklm` 查询 |
| 钉钉机器人开发 | `dingtalk_bot/README.md` |

## 可用命令

- `/notebooklm` - 查询NotebookLM（不占用上下文）
- `/context-dump` - 保存当前进度
- `/context-reload` - 恢复上次进度

## 项目状态速览（2026-02-06）

| 维度 | 当前 | 目标 |
|------|------|------|
| STEM课程 | ✅ 147节全部完成 | - |
| CODE课程 | ✅ 94节格式升级完成 | 待内容深度萃取 |
| PythonAI | ⏳ 83节进行中 | 待内容深度萃取 |
| 协议文件 | 18个 | 20个 |
| NotebookLM | 9个 | 32个 |

## 注意事项

- `docs/` 目录是 AI 学院系统的技术文档，不要修改
- 知识库建好后将为 AI 学院系统服务
- 参考项目：`C:\Users\Frank.J\libu_knowledge`（励步知识库）
