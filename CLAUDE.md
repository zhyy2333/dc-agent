# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Project — HireHive

A full-process AI job search assistant (求职助手) powered by multi-agent collaboration, targeting BOSS直聘 (zhipin.com). Covers: job discovery → resume matching → auto-apply → interview prep → offer comparison.

## Important: Always check docs first

Before starting any task, check the relevant docs:

| Document | Path | When to Read |
|---|---|---|
| 开发需求 | `docs/requirements.md` | New feature, scoping |
| 技术架构 | `docs/architecture.md` | Understanding project structure |
| 设计规范 | `docs/design-standards.md` | Coding style, conventions |
| 执行步骤 | `docs/implementation-steps.md` | How to implement new agents/tools |
| 开发日志 | `devlog/<YYYY-MM-DD>.md` | Today's progress, TODOs |

## Daily DevLog Protocol

**At the end of every coding session**, you MUST:
1. Read today's devlog if it exists, or create one at `devlog/YYYY-MM-DD.md` from `devlog/template.md`
2. Append a "今日完成" section listing what was done this session
3. Update the "待办事项" section with remaining/pending items
4. If relevant, add "遇到的问题" and "下一步计划"

## Tech Stack

- Python 3.11+, flat-layout package (`hirehive/`)
- LLM: DeepSeek V4 Pro via Anthropic SDK proxy (`base_url=https://api.deepseek.com/anthropic`)
- CLI: Click + Rich
- DB: SQLite (stdlib, no external service)
- Browser: Playwright (Chromium, sync API)
- Data: Pydantic v2

## Project Structure

```
hirehive/                    # Python package (flat layout)
├── main.py                  # CLI entry — Click groups (resume/search/match/apply/interview/offer)
├── config.py                # @dataclass Config loaded from env vars
├── llm.py                   # Anthropic client singleton
├── agents/
│   ├── base.py              # BaseAgent: stream + thinking + manual tool loop
│   ├── coordinator.py       # Planner/Orchestrator
│   ├── searcher.py          # BOSS job discovery
│   ├── matcher.py           # Resume-vs-job scoring
│   ├── applier.py           # Auto-apply on BOSS
│   ├── interview_coach.py   # Mock interview
│   └── offer_advisor.py     # Offer comparison
├── tools/
│   ├── registry.py          # ToolRegistry (name → schema + callable)
│   ├── browser_tools.py     # 12 Playwright tools for BOSS
│   ├── file_tools.py        # Resume parse, report export
│   └── state_tools.py       # DB read/write tools
├── models/                  # Pydantic: Job, Resume, Application, Offer
├── storage/                 # SQLite: schema.sql, engine, 4 repos
└── utils/                   # Logger, text utils
prompts/                     # 6 Agent system prompts (.md, editable by non-devs)
data/                        # Runtime: state.db, exports/, screenshots/ (gitignored)
docs/                        # Project docs: requirements, architecture, standards
devlog/                      # Daily development logs
```

## Key Conventions

### Imports
Always use absolute imports: `from hirehive.xxx import YYY`

### Agent Development
Every agent inherits `BaseAgent`:
```python
class XxxAgent(BaseAgent):
    name = "xxx"
    def __init__(self, registry: ToolRegistry):
        super().__init__(registry)
        self.system_prompt = PROMPT_FILE.read_text(encoding="utf-8")
```

### Tool Registration
Tools are registered per-agent-type in `main.py:build_registry()`. Add schema + callable for the relevant agent type.

### CLI Commands
1. Add to the relevant `@cli.group()` in `main.py`
2. Use `--kebab-case` for options
3. Use `console.print()` with Rich markup for output
4. Long operations use `Progress(spinner)`

### Testing
Always test CLI commands after changes:
```bash
hirehive --help
hirehive dashboard
hirehive <command> --help
```

### Before Commit
1. `hirehive dashboard` works
2. `hirehive --help` shows all commands
3. All imports resolve: `python -c "from hirehive.main import main"`
4. DB initializes cleanly (delete `data/state.db` and run dashboard)
5. Update `devlog/<date>.md` with today's work

## Common Tasks

### Add a new Agent
1. Create `hirehive/agents/new_agent.py` (copy existing agent as template)
2. Create `prompts/new_agent.system.md`
3. Register tools in `build_registry()` for the new agent type
4. Add CLI commands to `main.py`

### Add a new Tool
1. Add function to the appropriate `hirehive/tools/xxx_tools.py`
2. Register in `build_registry()` for the relevant agent type(s)
3. Function signature: `def tool_name(param: type) -> dict:`

### Fix LLM / Streaming issues
1. Check `BaseAgent._collect_stream()` — handles thinking/text/tool_use/content_block events
2. `src.config.anthropic_model` controls which model is used
3. DeepSeek proxy at `ANTHROPIC_BASE_URL` handles tool-use format differences

### Fix package install issues
If `hirehive` command fails on Windows:
```bash
# Reinstall
pip uninstall hirehive-jobsearchagent -y
pip install -e .
# Verify
hirehive --help
```
