# 斯坦星球知识库萃取协议库

> 本目录包含从《知识库萃取标准与执行规则.md》中拆分出的独立协议文件。
> 按需加载，减少Token消耗。

## 协议索引

| 编号 | 协议名称 | 文件名 | 使用场景 | 状态 |
|------|---------|--------|---------|------|
| 7.1 | 分批萃取协议 | batch-processing.md | 每次萃取必读 | ✅ 已创建 |
| 7.4 | 动态补漏指令 | gap-filling.md | 识别知识缺口时 | ✅ 已创建 |
| 7.5 | 逻辑冲突审计 | conflict-audit.md | 发现内容冲突时 | ✅ 已创建 |
| 7.6 | 负面案例萃取 | negative-case.md | 萃取教学内容时 | ✅ 已创建 |
| 7.7 | 创始人访谈提纲 | founder-interview.md | 需要人工补充时 | ✅ 已创建 |
| 7.8 | 双向校验机制 | bidirectional-verify.md | 校验一致性时 | ✅ 已创建 |
| 7.9 | 高价值信息提纯 | upward-distillation.md | 提炼决策层内容时 | ✅ 已创建 |
| 7.10 | 管理工具解耦 | tool-decoupling.md | 萃取管理工具时 | ✅ 已创建 |
| 7.11 | 动态题库生成 | quiz-generation.md | 生成考核题时 | ✅ 已创建 |
| 7.12 | 沟通心理学标签 | psychology-tagging.md | 萃取话术时 | ✅ 已创建 |
| 7.13 | 物料自动化关联 | material-linking.md | 关联物料时 | ✅ 已创建 |
| 7.14 | 数据驱动决策触发器 | data-trigger.md | 萃取数据内容时 | ✅ 已创建 |
| 7.15 | 互动反馈循环打标 | ifc-tagging.md | 萃取教学互动时 | ✅ 已创建 |
| 7.16 | 认知负荷标签 | cognitive-load.md | 萃取教学内容时 | ✅ 已创建 |
| 7.17 | 全局关联基准 | global-reference.md | 建立跨文档关联时 | ✅ 已创建 |
| 7.18 | 管理场景模拟 | scenario-simulation.md | 萃取管理内容时 | ✅ 已创建 |
| 7.19 | 考核题关联话术索引 | quiz-script-linking.md | 建立题目与话术关联时 | ✅ 已创建 |
| 7.20 | 知识点反向索引 | reverse-indexing.md | 建立反向索引时 | ✅ 已创建 |
| 7.21 | 闯关式学习路径 | gamified-learning.md | 设计学习路径时 | ✅ 已创建 |
| 7.22 | 实战演练脚本 | role-play-script.md | 萃取演练内容时 | ✅ 已创建 |
| 7.23 | 多模态素材需求标注 | multimodal-tagging.md | 标注素材需求时 | ✅ 已创建 |
| 7.24 | 体系兼容性处理 | legacy-compatibility.md | 处理新旧体系时 | ✅ 已创建 |
| - | 素材预处理协议 | material-preprocessing.md | 素材预处理时 | ✅ 已创建 |
| - | 深度萃取执行协议 | deep-extraction.md | 执行深度萃取时 | ✅ 已创建 |
| - | 工作流命令参考 | workflow-commands.md | 命令格式参考 | ✅ 已创建 |

---

## 协议分类

### 核心协议（每次萃取必读）
1. **batch-processing.md** - 分批萃取协议（5-5循环原则）
2. **deep-extraction.md** - 深度萃取执行协议（NotebookLM调用流程）

### 话术萃取协议
3. **psychology-tagging.md** - 沟通心理学标签（12种心理学标签）
4. **quiz-script-linking.md** - 考核题关联话术索引（考评练一体化）

### 教学内容萃取协议
5. **cognitive-load.md** - 认知负荷标签（游戏活动分级）
6. **ifc-tagging.md** - 互动反馈循环打标（预防/即时/复盘）
7. **multimodal-tagging.md** - 多模态素材需求标注
8. **negative-case.md** - 负面案例萃取

### 管理内容萃取协议
9. **tool-decoupling.md** - 管理工具解耦（Checklist化）
10. **scenario-simulation.md** - 管理场景模拟（挑战案例）
11. **data-trigger.md** - 数据驱动决策触发器

### 培训体系协议
12. **quiz-generation.md** - 动态题库生成
13. **reverse-indexing.md** - 知识点反向索引
14. **gamified-learning.md** - 闯关式学习路径
15. **role-play-script.md** - 实战演练脚本

### 质量保障协议
16. **gap-filling.md** - 动态补漏指令
17. **conflict-audit.md** - 逻辑冲突审计
18. **bidirectional-verify.md** - 双向校验机制
19. **upward-distillation.md** - 高价值信息提纯

### 体系与关联协议
20. **global-reference.md** - 全局关联基准
21. **legacy-compatibility.md** - 体系兼容性处理
22. **material-linking.md** - 物料自动化关联

### 辅助协议
23. **founder-interview.md** - 创始人访谈提纲
24. **material-preprocessing.md** - 素材预处理协议
25. **workflow-commands.md** - 工作流命令参考

---

## 使用说明

### 按需加载原则
1. **每次萃取必读**：batch-processing.md + deep-extraction.md
2. **萃取话术时**：+ psychology-tagging.md
3. **萃取教学内容时**：+ cognitive-load.md / ifc-tagging.md
4. **生成考核题时**：+ quiz-generation.md + reverse-indexing.md
5. **处理旧体系内容时**：+ legacy-compatibility.md

### 协议调用示例

```markdown
# 深度萃取话术内容
1. 加载 batch-processing.md（5-5循环）
2. 加载 deep-extraction.md（NotebookLM调用）
3. 加载 psychology-tagging.md（心理学标签）
4. 加载 quiz-script-linking.md（题目关联）

# 深度萃取教学内容
1. 加载 batch-processing.md
2. 加载 deep-extraction.md
3. 加载 cognitive-load.md（认知负荷）
4. 加载 ifc-tagging.md（IFC分类）
5. 加载 multimodal-tagging.md（素材需求）
```

---

## 版本信息

- 创建日期：2026-01-23
- 更新日期：2026-01-24
- 基于文档：知识库萃取标准与执行规则.md V4.1
- **已创建协议：25个（全部完成）**
- 待创建协议：0个

---

*协议库版本：V2.0 | 更新日期：2026-01-24*
