# 🤖 求职助手 (Job Search Assistant)

**全流程 AI 求职 Agent** — 从岗位发现、简历匹配、自动投递、面试准备到 Offer 对比，覆盖求职全生命周期。

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![DeepSeek](https://img.shields.io/badge/LLM-DeepSeek%20V4%20Pro-purple.svg)](https://deepseek.com)

---

## 核心功能

| 阶段 | 功能 | 说明 |
|---|---|---|
| 🔍 **岗位发现** | BOSS 直聘自动搜索 | 按关键词、城市、薪资范围搜索，自动翻页抓取详情 |
| 🎯 **简历匹配** | AI 智能评分 | 五个维度（技能/经验/学历/薪资/综合）打分，输出 S/A/B/C/D 评级 |
| 🚀 **自动投递** | 半自动申请 | 一键点击"立即沟通"，生成个性化打招呼消息，需人工确认 |
| 🎤 **面试准备** | 题库生成 + 模拟面试 | 根据 JD 生成个性化面试题，支持交互式 AI 模拟面试 |
| ⚖️ **Offer 对比** | 多维分析 | 薪资/发展/生活/公司/文化五维度加权对比，输出推荐排名 |

## 技术亮点

- **多 Agent 协作**: Coordinator → Searcher → Matcher → Applier → InterviewCoach → OfferAdvisor
- **浏览器自动化**: Playwright 驱动 BOSS 直聘，真实 UA、随机延迟、Session 持久化
- **工具调用**: 12 个浏览器工具 + 文件解析工具 + 数据库工具，Agent 自主选择调用
- **状态记忆**: SQLite 记录完整流水线（discovered → matched → applied → interviewing → offered → accepted/rejected）
- **流式响应**: 支持 DeepSeek V4 Pro Thinking/Reasoning 模式

## 架构

```
┌─────────────────────────────────────────────────┐
│                    CLI / REPL                     │
│    search | match | apply | interview | offer    │
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
                   │          OfferAdvisor Agent
                   ▼
┌─────────────────────────────────────────────────┐
│              Tool Registry + LLM                 │
│  Browser Tools │ File Tools │ State Tools       │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│               SQLite Persistence                 │
│  user_profile │ resume │ job │ application       │
│  offer │ message_log                             │
└─────────────────────────────────────────────────┘
```

## 项目结构

```
dc-agent/
├── src/
│   ├── main.py                    # CLI 入口 (Click, 8 个子命令组)
│   ├── config.py                  # 配置管理 (环境变量 + dataclass)
│   ├── llm.py                     # Anthropic SDK 封装 (DeepSeek proxy)
│   ├── agents/
│   │   ├── base.py                # BaseAgent: 流式 + 思维链 + 工具循环
│   │   ├── coordinator.py         # 规划/协调 Agent
│   │   ├── searcher.py            # 岗位搜索 Agent
│   │   ├── matcher.py             # 简历匹配 Agent
│   │   ├── applier.py             # 自动投递 Agent
│   │   ├── interview_coach.py     # 面试教练 Agent
│   │   └── offer_advisor.py       # Offer 顾问 Agent
│   ├── tools/
│   │   ├── registry.py            # 工具注册表 (name → schema + executor)
│   │   ├── browser_tools.py       # 12 个 Playwright 浏览器工具
│   │   ├── file_tools.py          # 简历解析 / 报告导出
│   │   └── state_tools.py         # 数据库 CRUD 工具
│   ├── models/                    # Pydantic 数据模型
│   │   ├── job.py                 # Job, SalaryRange
│   │   ├── resume.py              # Resume, Experience, Education
│   │   ├── application.py         # Application, PipelineStage
│   │   └── offer.py               # Offer
│   ├── storage/                   # SQLite 持久化层
│   │   ├── schema.sql             # 6 张表 DDL
│   │   ├── engine.py              # 连接管理
│   │   ├── job_repo.py            # 岗位 CRUD
│   │   ├── resume_repo.py         # 简历 CRUD
│   │   ├── application_repo.py    # 申请 CRUD
│   │   └── offer_repo.py          # Offer CRUD
│   └── utils/
│       ├── logger.py              # 结构化日志
│       └── text.py                # 文本提取 + 随机延迟
├── prompts/                       # System Prompts (Markdown)
│   ├── coordinator.system.md
│   ├── searcher.system.md
│   ├── matcher.system.md
│   ├── applier.system.md
│   ├── interview_coach.system.md
│   └── offer_advisor.system.md
├── data/                          # 运行时数据 (gitignored)
│   ├── state.db                   # SQLite 数据库
│   ├── exports/                   # 导出报告
│   └── screenshots/               # 浏览器截图
├── requirements.txt
├── pyproject.toml
├── .env.example
└── .gitignore
```

## 快速开始

### 前置要求

- Python 3.11+
- Windows / macOS / Linux

### 安装

```bash
# 1. 克隆项目
git clone <repo-url> && cd dc-agent

# 2. 安装依赖
pip install -e .

# 3. 安装 Playwright 浏览器
playwright install chromium

# 4. 配置 API Key
cp .env.example .env
# 编辑 .env，填入你的 DeepSeek API Key
```

### 配置

通过 `.env` 文件配置（也支持环境变量）：

```bash
ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
ANTHROPIC_AUTH_TOKEN=sk-your-key-here
ANTHROPIC_MODEL=deepseek-v4-pro
JOB_DEFAULT_CITY=深圳
JOB_DEFAULT_SALARY_MIN=15000
JOB_DEFAULT_SALARY_MAX=35000
BROWSER_HEADLESS=false
```

### 使用

```bash
# 查看所有命令
job-assistant --help

# 上传简历
job-assistant resume upload ~/my-resume.pdf

# 搜索岗位
job-assistant search run --role "Python开发" --city "深圳" --salary-min 20000

# 查看搜索到的岗位
job-assistant search list

# 简历匹配评分
job-assistant match --all --min-score 0.6

# 投递岗位
job-assistant apply go --job-id 3

# 查看投递状态
job-assistant apply status

# 面试准备
job-assistant interview prep --job-id 3

# 模拟面试
job-assistant interview mock --job-id 3

# 添加 Offer
job-assistant offer add --company "A公司" --position "高级Python" --salary 30000

# Offer 对比
job-assistant offer compare

# 流水线仪表盘
job-assistant dashboard

# 交互式 REPL 模式
job-assistant interactive
```

## 交互式模式

```bash
$ job-assistant interactive

╭──── 欢迎 ────╮
│ 求职助手      │
│ 命令: search / match / apply / interview / offer / dashboard / help / quit │
╰──────────────╯

job> dashboard
  已发现        [ 12]
  已匹配        [  8]
  已投递        [  3]
  面试中        [  2]

job> match --all --min-score 0.7
  [████████████] 匹配中... 8 个岗位评分 >= 0.7

job> apply 12
  确认投递 'Python高级开发' @ 示例科技? [Y/n] y
  投递完成 ✓

job> offer compare
  Offer 对比分析...（多维度加权评分表）
```

## 数据模型

### 流水线状态机

```
discovered → matched → applied → interviewing → offered → accepted
                                                          → rejected
```

### 数据库表

| 表名 | 说明 | 核心字段 |
|---|---|---|
| `user_profile` | 用户偏好 | city, salary_range, preferred_roles |
| `resume` | 简历 | file_path, raw_text, structured_data (JSON) |
| `job` | 岗位 | title, company, salary_range, description, tags |
| `application` | 申请 | pipeline_stage, match_score, match_details (JSON) |
| `offer` | Offer | base_salary, bonus, equity, benefits, work_mode |
| `message_log` | 对话记录 | role, content, metadata |

### 匹配评分维度

| 维度 | 权重 | 说明 |
|---|---|---|
| 技能匹配 | 20% | 编程语言、框架、工具栈重合度 |
| 经验匹配 | 20% | 工作年限、行业背景、项目经验 |
| 学历匹配 | 20% | 学历层次、专业对口程度 |
| 薪资匹配 | 20% | 期望与提供的重合度 |
| 综合印象 | 20% | 软性要求契合度 |

**评级**: S (>90) / A (80-90) / B (65-80) / C (50-65) / D (<50)

## Agent 详情

### 1. CoordinatorAgent (协调器)
- 理解用户意图，拆解为执行阶段
- 串行调度各专业 Agent
- 在关键节点（投递前）插入人工确认
- 汇总各阶段结果并呈现

### 2. SearcherAgent (搜索)
- 自动搜索 BOSS 直聘岗位列表
- 滚动加载更多、逐一抓取详情页
- 去重保存到本地数据库
- 工具: `boss_search_jobs`, `boss_get_job_detail`, `boss_scroll_page` 等

### 3. MatcherAgent (匹配)
- 读取简历原文，LLM 提取结构化信息
- 逐一分析岗位要求，五维度打分
- 输出评分理由、优势/风险点、投递建议
- 工具: `parse_resume_pdf`, `export_report_markdown`

### 4. ApplierAgent (投递)
- 打开岗位详情页，点击"立即沟通"
- 生成个性化打招呼消息（含技能亮点）
- 模拟人类操作节奏（随机延迟 1-5s）
- 必须先获得用户确认
- 工具: `boss_click_apply`, `boss_send_greeting`, `boss_upload_attachment`

### 5. InterviewCoachAgent (面试教练)
- 根据 JD 和简历生成 10-15 道个性化面试题
- 覆盖技术题、项目题、行为题三类
- 交互式模拟面试，逐题评分
- 工具: `read_user_resume`, `export_report_markdown`

### 6. OfferAdvisorAgent (Offer 顾问)
- 薪资/发展/生活/公司/文化五维度加权对比
- 排名 + 优劣势分析 + 风险提示
- 产出对比报告
- 工具: `save_offer`, `get_offers`, `export_report_markdown`

## 浏览器工具

| 工具 | 功能 |
|---|---|
| `boss_navigate` | 导航到指定 URL |
| `boss_search_jobs` | 按关键词/城市/薪资搜索 |
| `boss_get_job_detail` | 抓取岗位详情页 |
| `boss_scroll_page` | 滚动加载更多（无限滚动） |
| `boss_click_apply` | 点击"立即沟通"按钮 |
| `boss_send_greeting` | 发送打招呼消息 |
| `boss_fill_application` | 填充申请表单 |
| `boss_upload_attachment` | 上传简历附件 |
| `boss_check_message_response` | 检查雇主回复 |
| `boss_take_screenshot` | 截图记录 |
| `boss_wait_for` | 等待元素出现 |

### 反爬策略

- 真实 Chrome UA
- 操作间随机延迟 (1-5s)
- headful 模式（默认，方便过人机验证）
- Session Cookie 持久化到 `data/browser_profile/`
- 语义选择器 (`text=`, `role=`) 优先于脆弱的 CSS class

## 技术栈

| 组件 | 选型 | 用途 |
|---|---|---|
| 语言 | Python 3.11+ | — |
| LLM SDK | anthropic >= 0.45 | 通过 DeepSeek Proxy 调用 |
| 模型 | deepseek-v4-pro | 支持 Thinking/Reasoning |
| CLI | Click + Rich | 命令行 + 美化终端输出 |
| 浏览器 | Playwright (Chromium) | BOSS 直聘自动化 |
| 数据校验 | Pydantic v2 | 类型安全 + JSON Schema 生成 |
| 数据库 | SQLite (stdlib) | 零配置持久化 |
| PDF | pypdf | 简历 PDF 解析 |
| DOCX | python-docx | 简历 Word 解析 |
| HTTP | httpx | REST API 请求 |

## 贡献

欢迎提交 Issue 和 PR。

### 开发

```bash
pip install -e ".[dev]"
python -m src.main --help
```

### Prompt 调优

所有 Agent 的 System Prompt 存放在 `prompts/*.system.md`，可直接编辑调优，无需改动代码。

## 路线图

- [x] 项目脚手架 + 数据库
- [x] 简历上传 / 解析
- [x] BOSS 直聘搜索
- [x] 简历匹配评分
- [x] 半自动投递
- [x] 面试题库 / 模拟面试
- [x] Offer 对比
- [x] 仪表盘 / 交互 REPL
- [ ] 支持拉勾 / 猎聘
- [ ] 定时搜索 + 新岗位通知
- [ ] Web UI (Gradio / Streamlit)
- [ ] 投递漏斗数据分析
- [ ] 面试录音转文字 + AI 实时提示

## License

MIT
