# 执行步骤

## 开发流程

### 1. 新功能开发

```
1. 确定需求 → 更新 docs/requirements.md
2. 设计方案 → 更新 docs/architecture.md
3. 编写代码 → 遵循 docs/design-standards.md
4. 编写 Prompt → 更新 prompts/<agent>.system.md
5. 测试验证 → hirehive <command> 端到端测试
6. 记录日志 → 追加到 devlog/<YYYY-MM-DD>.md
```

### 2. Agent Pipeline 开发

新增 Agent 的步骤：

1. 在 `hirehive/agents/` 创建 `xxx.py`
2. 继承 `BaseAgent`，设置 `name` 和 `system_prompt`
3. 在 `prompts/` 创建对应的 `.system.md`
4. 将 Agent 需要的工具注册到 `ToolRegistry`
5. 在 `main.py` 中：
   - 添加相应的 CLI 命令组/命令
   - 在 `build_registry()` 中添加工具的 schema 和 callable
   - 实例化 Agent 并调用其方法

### 3. 新工具开发

新增工具的步骤：

1. 在 `hirehive/tools/` 添加函数（如 `browser_tools.py` 中追加）
2. 在 `build_registry(agent_type)` 中为相关 Agent 注册工具
3. 工具函数必须签名清晰，返回 dict 或 list
4. 错误时返回 `{"error": "message"}`

### 4. 数据模型变更

1. 修改或新增 `hirehive/models/` 中的 Pydantic 模型
2. 如需新表 → 更新 `hirehive/storage/schema.sql`
3. 新增 Repository 类（如已有 CRUD，追加方法即可）
4. 更新 `state_tools.py` 暴露给 Agent 的工具函数

## Phase 回顾

| Phase | 内容 | 状态 |
|---|---|---|
| 0 | 项目脚手架、配置、LLM 封装、BaseAgent、CLI 骨架、数据库 | ✅ |
| 1 | 简历模型、文件解析工具、upload/show/parse | ✅ |
| 2 | SearcherAgent、浏览器工具、BOSS 直聘集成、search 命令 | ✅ |
| 3 | MatcherAgent、五维度评分、match 命令 | ✅ |
| 4 | ApplierAgent、投递自动化、apply 命令 | ✅ |
| 5 | InterviewCoachAgent、题库生成、mock 面试 | ✅ |
| 6 | OfferAdvisorAgent、对比逻辑、offer 命令 | ✅ |
| 7 | Dashboard、交互 REPL、错误处理、反爬策略 | ✅ |

## 当前待办

- [ ] 支持猎聘 / 拉勾等更多招聘平台
- [ ] 定时搜索 + 新岗位通知
- [ ] Web UI (Gradio / Streamlit)
- [ ] 投递漏斗数据分析
- [ ] 面试录音转文字 + AI 实时提示
