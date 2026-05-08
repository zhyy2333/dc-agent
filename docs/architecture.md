# 技术架构文档

## 整体架构

```
┌─────────────────────────────────────────────────┐
│                    CLI / REPL                     │
│    Click (8 子命令组) + Rich (美化输出)           │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│              CoordinatorAgent (Planner)           │
│         理解意图 → 制定计划 → 调度执行            │
└───┬──────────┬──────────┬──────────┬────────────┘
    │          │          │          │
    ▼          ▼          ▼          ▼
┌────────┐┌────────┐┌────────┐┌──────────────┐
│Searcher││Matcher ││Applier ││InterviewCoach│
│  Agent ││ Agent  ││ Agent  ││    Agent     │
└───┬────┘└───┬────┘└───┬────┘└──────┬───────┘
    │         │         │           │
    └─────────┴────┬────┴───────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│                Tool Registry                      │
│  Browser Tools │ File Tools │ State Tools        │
│  (Playwright)  │ (pypdf/docx)│ (SQLite)          │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│              Data Layer                           │
│  SQLite + 4 Repository + 6 Tables                │
└─────────────────────────────────────────────────┘
```

## 技术栈

| 组件 | 选型 | 版本 |
|---|---|---|
| 语言 | Python | 3.11+ |
| LLM SDK | anthropic (DeepSeek proxy) | >=0.45 |
| CLI | Click | >=8.1 |
| 终端 UI | Rich | >=13.0 |
| 浏览器自动化 | Playwright (Chromium) | >=1.45 |
| 数据校验 | Pydantic | >=2.0 |
| 数据库 | SQLite (stdlib) | — |
| PDF 解析 | pypdf | >=4.0 |
| DOCX 解析 | python-docx | >=1.0 |
| HTTP | httpx | >=0.27 |
| 环境变量 | python-dotenv | >=1.0 |

## Agent 设计

### BaseAgent

所有 Agent 的基类，实现：
- 流式消息处理（支持 thinking/reasoning blocks）
- 手动工具循环（非 SDK tool_runner）
- 工具注册与执行

### 工具循环

```
User Message → LLM Call (stream) → Collect Blocks
  → Has tool_use? → Execute Tool → Append Result → LLM Call
  → No tool_use? → Extract Text → Return Result
```

### 工具注册

每个 Agent 通过 ToolRegistry 注册：
- `name` — 工具名
- `schema` — Anthropic SDK ToolParam JSON Schema
- `func` — Python callable

## 数据流

```
CLI Input → Context Dict → Agent.run() → LLM Response → Parsed Result → CLI Output
                              ↕
                         SQLite (Read/Write via tools)
```

## 目录结构

```
hirehive/                # Python 包 (flat layout)
├── main.py              # CLI 入口
├── config.py            # 配置 (dataclass + env)
├── llm.py               # LLM client 封装
├── agents/              # 6 个 Agent 模块
├── tools/               # 工具注册表 + 3 类工具
├── models/              # 4 个 Pydantic 模型
├── storage/             # DB schema + 4 个 Repository
└── utils/               # 日志 + 文本工具
prompts/                 # 6 个 System Prompt (.md)
data/                    # 运行时数据 (gitignored)
docs/                    # 开发文档
devlog/                  # 开发日志
```
