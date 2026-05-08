# 设计规范

## 代码风格

### 命名规范

| 类型 | 规范 | 示例 |
|---|---|---|
| 模块/文件 | snake_case | `interview_coach.py` |
| 类 | PascalCase | `CoordinatorAgent` |
| 函数/方法 | snake_case | `boss_search_jobs` |
| 变量 | snake_case | `tool_registry` |
| 常量 | UPPER_SNAKE_CASE | `PROMPT_FILE` |
| 私有方法 | _leading_underscore | `_collect_stream` |

### 类型注解

所有函数签名必须包含类型注解：

```python
def search(self, keyword: str, city: str, salary_min: int = 0) -> str:
```

### Docstring

每个模块有模块级 docstring，每个公开类/函数有简短 docstring。一行即可，不写多段注释。

## Agent 规范

### 必须继承 BaseAgent

```python
class MyAgent(BaseAgent):
    name = "my_agent"

    def __init__(self, registry: ToolRegistry):
        super().__init__(registry)
        self.system_prompt = PROMPT_FILE.read_text(encoding="utf-8")
```

### System Prompt 规则

1. 存放在 `prompts/<agent_name>.system.md`
2. 用中文编写
3. 包含：职责、工作流程、可用工具列表、输出格式
4. 不加 Python 代码片段，只描述行为

### 工具调用

- 不在 Agent 内部直接调用工具函数，通过 `self.tool_registry.execute()` 调用
- 工具函数放在 `tools/` 目录，按类别分文件

## 数据模型规范

### Pydantic 模型

- 所有数据模型继承 `pydantic.BaseModel`
- 使用 `Field(default_factory=...)` 处理可变默认值
- Optional 字段显式标注 `Optional[Type]`
- 存储到 SQLite 时，复杂类型序列化为 JSON string

### 数据库规范

- SQLite，不依赖外部数据库
- schema 定义在 `storage/schema.sql`
- 每个表对应一个 Repository 类
- Repository 负责获取/释放连接，不保持长连接

## CLI 规范

### 命令结构

```
hirehive <group> <command> [options]
```

- 顶层 8 个 group：resume, search, match, apply, interview, offer, dashboard, interactive
- 每个 group 对应一个 `@cli.group()` 装饰器函数
- 命令选项用 `--kebab-case`

### 输出规范

- 表格用 `rich.Table`
- 提示信息用 `[color]text[/color]` 标签
- 错误用 `[red]`，成功用 `[green]`，警告用 `[yellow]`
- 长操作使用 `rich.Progress` 显示 spinner

## Prompt 调优规范

- System Prompt 存放在 `prompts/` 目录
- 每个 Agent 一个独立 `.md` 文件
- 可被非技术人员直接编辑
- 修改后不需要重启即可生效（每次运行重新读取）

## 浏览器自动化规范

- 使用 Playwright sync API
- 全局单例 browser instance（`_get_page()`）
- 语义选择器优先：`text=`, `role=` > CSS class
- 每次操作间隔随机延迟（`random_delay(1, 3)`）
- 默认 headful 模式，支持 `--headless` flag
