"""CLI entry point for HireHive — Multi-Agent Job Search Pipeline."""

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from hirehive.config import config
from hirehive.storage import init_db
from hirehive.storage import job_repo, resume_repo, application_repo, offer_repo
from hirehive.tools.registry import ToolRegistry
from hirehive.tools import browser_tools, file_tools, state_tools

console = Console()


# ── Tool schema definitions ─────────────────────────────────────────────

def _make_tool(name: str, desc: str, properties: dict, required: list[str] | None = None) -> dict:
    return {
        "name": name,
        "description": desc,
        "input_schema": {
            "type": "object",
            "properties": properties,
            "required": required or [],
        },
    }


def build_registry(agent_type: str) -> ToolRegistry:
    """Build a ToolRegistry with schemas and callables for a given agent type."""
    r = ToolRegistry()

    # ── State tools (Coordinator) ──
    if agent_type in ("coordinator",):
        r.register("list_jobs", _make_tool("list_jobs", "List discovered jobs", {
            "stage": {"type": "string", "description": "Filter by pipeline stage"},
            "min_score": {"type": "number", "description": "Minimum match score"},
            "limit": {"type": "integer", "description": "Max results", "default": 100},
        }), state_tools.list_jobs)
        r.register("list_applications", _make_tool("list_applications", "List applications", {
            "stage": {"type": "string", "description": "Filter by stage"},
            "limit": {"type": "integer", "description": "Max results", "default": 100},
        }), state_tools.list_applications)
        r.register("update_application", _make_tool("update_application", "Update application status", {
            "job_id": {"type": "integer", "description": "Job ID"},
            "stage": {"type": "string", "description": "New pipeline stage"},
        }, ["job_id", "stage"]), state_tools.update_application)

    # ── Browser tools (Searcher, Applier) ──
    if agent_type in ("searcher", "applier", "coordinator"):
        r.register("boss_navigate", _make_tool("boss_navigate", "Navigate to URL", {
            "url": {"type": "string", "description": "Target URL"},
        }, ["url"]), browser_tools.boss_navigate)

    if agent_type in ("searcher",):
        r.register("boss_search_jobs", _make_tool("boss_search_jobs", "Search BOSS直聘 for jobs", {
            "keyword": {"type": "string", "description": "Job keyword"},
            "city": {"type": "string", "description": "City name in Chinese"},
            "salary_min": {"type": "integer", "description": "Minimum salary"},
            "salary_max": {"type": "integer", "description": "Maximum salary"},
            "page_num": {"type": "integer", "description": "Page number", "default": 1},
        }, ["keyword", "city"]), browser_tools.boss_search_jobs)
        r.register("boss_get_job_detail", _make_tool("boss_get_job_detail", "Get job detail page", {
            "job_url": {"type": "string", "description": "Job detail URL"},
        }, ["job_url"]), browser_tools.boss_get_job_detail)
        r.register("boss_scroll_page", _make_tool("boss_scroll_page", "Scroll to load more", {
            "times": {"type": "integer", "description": "Scroll times", "default": 3},
        }), browser_tools.boss_scroll_page)
        r.register("boss_take_screenshot", _make_tool("boss_take_screenshot", "Take screenshot", {
            "label": {"type": "string", "description": "Screenshot label"},
        }, ["label"]), browser_tools.boss_take_screenshot)
        r.register("boss_wait_for", _make_tool("boss_wait_for", "Wait for element", {
            "selector": {"type": "string", "description": "CSS selector"},
            "timeout_ms": {"type": "integer", "description": "Timeout milliseconds", "default": 5000},
        }, ["selector"]), browser_tools.boss_wait_for)

    if agent_type in ("applier",):
        r.register("boss_click_apply", _make_tool("boss_click_apply", "Click apply button", {
            "job_url": {"type": "string", "description": "Job URL"},
        }, ["job_url"]), browser_tools.boss_click_apply)
        r.register("boss_send_greeting", _make_tool("boss_send_greeting", "Send greeting message", {
            "message": {"type": "string", "description": "Greeting message text"},
        }, ["message"]), browser_tools.boss_send_greeting)
        r.register("boss_fill_application", _make_tool("boss_fill_application", "Fill application form", {
            "fields": {"type": "array", "description": "List of {selector, value} objects"},
        }, ["fields"]), browser_tools.boss_fill_application)
        r.register("boss_upload_attachment", _make_tool("boss_upload_attachment", "Upload file", {
            "selector": {"type": "string", "description": "File input selector"},
            "file_path": {"type": "string", "description": "Local file path"},
        }, ["selector", "file_path"]), browser_tools.boss_upload_attachment)
        r.register("boss_check_message_response", _make_tool("boss_check_message_response", "Check responses", {
            "job_url": {"type": "string", "description": "Job URL"},
        }, ["job_url"]), browser_tools.boss_check_message_response)
        r.register("boss_take_screenshot", _make_tool("boss_take_screenshot", "Take screenshot", {
            "label": {"type": "string", "description": "Screenshot label"},
        }, ["label"]), browser_tools.boss_take_screenshot)

    # ── File tools (Matcher, InterviewCoach, OfferAdvisor) ──
    if agent_type in ("matcher", "interview_coach", "offer_advisor"):
        r.register("read_user_resume", _make_tool("read_user_resume", "Get active resume", {}),
                   file_tools.read_user_resume)
        r.register("export_report_markdown", _make_tool("export_report_markdown", "Export markdown report", {
            "content": {"type": "string", "description": "Markdown content"},
            "filename": {"type": "string", "description": "Output filename"},
        }, ["content", "filename"]), file_tools.export_report_markdown)
        r.register("export_report_json", _make_tool("export_report_json", "Export JSON report", {
            "content": {"type": "object", "description": "JSON-serializable content"},
            "filename": {"type": "string", "description": "Output filename"},
        }, ["content", "filename"]), file_tools.export_report_json)

    if agent_type in ("matcher",):
        r.register("parse_resume_pdf", _make_tool("parse_resume_pdf", "Parse PDF resume", {
            "file_path": {"type": "string", "description": "Path to PDF file"},
        }, ["file_path"]), file_tools.parse_resume_pdf)
        r.register("parse_resume_docx", _make_tool("parse_resume_docx", "Parse DOCX resume", {
            "file_path": {"type": "string", "description": "Path to DOCX file"},
        }, ["file_path"]), file_tools.parse_resume_docx)

    # ── Offer tools ──
    if agent_type in ("offer_advisor", "coordinator"):
        r.register("save_offer", _make_tool("save_offer", "Save an offer", {
            "offer_data": {"type": "object", "description": "Offer data"},
        }, ["offer_data"]), state_tools.save_offer_state)
        r.register("get_offers", _make_tool("get_offers", "Get all offers", {
            "status": {"type": "string", "description": "Filter by status"},
        }), state_tools.get_offers)

    return r


# ── CLI group ──────────────────────────────────────────────────────────

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """HireHive — Multi-Agent Job Search Pipeline (Boss Zhipin)"""
    config.data_dir.mkdir(parents=True, exist_ok=True)
    init_db()


# ── resume ─────────────────────────────────────────────────────────────

@cli.group()
def resume():
    """简历管理"""


@resume.command("upload")
@click.argument("file_path", type=click.Path(exists=True))
def resume_upload(file_path: str):
    """上传并解析简历文件"""
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        result = file_tools.parse_resume_pdf(file_path)
    elif ext in (".docx", ".doc"):
        result = file_tools.parse_resume_docx(file_path)
    else:
        console.print(f"[red]不支持的文件格式: {ext}[/red]")
        return

    if "error" in result:
        console.print(f"[red]解析失败: {result['error']}[/red]")
        return

    from hirehive.models.resume import Resume
    resume_obj = Resume(
        file_path=file_path,
        raw_text=result["raw_text"],
        email=result.get("extracted_email"),
        phone=result.get("extracted_phone"),
    )
    resume_id = resume_repo.save_resume(resume_obj)
    console.print(f"[green]简历已上传 (ID: {resume_id})[/green]")
    console.print(f"  Email: {result.get('extracted_email', '未检测到')}")
    console.print(f"  Phone: {result.get('extracted_phone', '未检测到')}")
    console.print(f"  文本长度: {result['char_count']} 字符")


@resume.command("show")
def resume_show():
    """查看当前简历"""
    row = resume_repo.get_active_resume()
    if not row:
        console.print("[yellow]尚未上传简历。使用 resume upload <文件路径> 上传。[/yellow]")
        return
    console.print(Panel(f"[bold]简历 (ID: {row['id']})[/bold]\n"
                        f"文件: {row['file_path']}\n"
                        f"上传时间: {row['parsed_at']}"))


@resume.command("parse")
def resume_parse():
    """用 LLM 深度解析当前简历"""
    row = resume_repo.get_active_resume()
    if not row:
        console.print("[yellow]No resume found.[/yellow]")
        return

    registry = build_registry("matcher")
    from hirehive.agents.matcher import MatcherAgent
    agent = MatcherAgent(registry)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task("LLM 解析简历中...", total=None)
        result = agent.run(
            f"请解析以下简历文本，提取姓名、邮箱、电话、技能列表、工作经历、教育背景。"
            f"用结构化 JSON 格式输出。\n\n{row['raw_text']}",
        )

    console.print(Panel(result, title="LLM 解析结果"))


# ── search ─────────────────────────────────────────────────────────────

@cli.group()
def search():
    """岗位搜索"""


@search.command("run")
@click.option("--role", required=True, help="岗位关键词，如 'Python开发'")
@click.option("--city", default=None, help="城市，如 '深圳'")
@click.option("--salary-min", type=int, default=0, help="最低薪资")
@click.option("--salary-max", type=int, default=0, help="最高薪资")
@click.option("--pages", type=int, default=3, help="搜索页数")
def search_run(role: str, city: str | None, salary_min: int, salary_max: int, pages: int):
    """在 BOSS 直聘搜索岗位"""
    city = city or config.default_city
    registry = build_registry("searcher")
    from hirehive.agents.searcher import SearcherAgent
    agent = SearcherAgent(registry)

    console.print(f"[bold]搜索条件[/bold]: {role} / {city} / {salary_min}-{salary_max}K")

    # ── Login / verification ──
    logged_in = False
    while not logged_in:
        nav = browser_tools.boss_navigate("https://www.zhipin.com/web/geek")
        current_url = nav.get("url", "")

        if "error" in nav:
            err = nav["error"]
            if "ECONNREFUSED" in err or "connect" in err.lower():
                console.print()
                console.print("[bold red]未检测到 Chrome 调试端口[/bold red]")
                console.print()
                console.print("[yellow]请按以下步骤操作：[/yellow]")
                console.print()
                console.print("  [bold]1.[/bold] 完全关闭所有 Chrome 窗口")
                console.print("  [bold]2.[/bold] 按 [bold]Win+R[/bold]，粘贴以下命令并回车：")
                console.print()
                console.print('    [bold green]"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222[/bold green]')
                console.print()
                console.print("  [bold]3.[/bold] 在打开的 Chrome 中访问 [bold]zhipin.com[/bold] 并扫码登录")
                console.print("  [bold]4.[/bold] 回到这里按 Enter")
                console.print()
                input()
                continue
            else:
                console.print(f"[red]浏览器错误: {err}[/red]")
                return

        if "/web/user/" in current_url or "/web/login" in current_url:
            console.print()
            console.print("[yellow]当前页面需要登录[/yellow]")
            console.print("[dim]请在 Chrome 浏览器中扫码登录 BOSS 直聘，完成后按 Enter...[/dim]")
            input()
        else:
            logged_in = True
            console.print(f"[green]已登录 BOSS 直聘[/green]")

    console.print("[dim]开始搜索...[/dim]")
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task("搜索中...", total=None)
        result = agent.search(role, city, salary_min, salary_max, pages)

    console.print(Panel(result, title="搜索结果"))


@search.command("list")
@click.option("--stage", default=None, help="按流水线阶段筛选")
@click.option("--min-score", type=float, default=None, help="最低匹配分")
@click.option("--limit", type=int, default=50, help="最大条数")
def search_list(stage: str | None, min_score: float | None, limit: int):
    """查看已发现的岗位"""
    jobs = job_repo.list_jobs(stage=stage, min_score=min_score, limit=limit)
    if not jobs:
        console.print("[yellow]没有找到岗位。先用 search run 搜索。[/yellow]")
        return

    table = Table(title=f"岗位列表 ({len(jobs)} 个)")
    table.add_column("ID", style="dim")
    table.add_column("标题")
    table.add_column("公司")
    table.add_column("城市")
    table.add_column("薪资")
    table.add_column("阶段")
    table.add_column("匹配分")

    for j in jobs:
        salary_text = f"{j.get('salary_min', '-')}~{j.get('salary_max', '-')}K" if j.get("salary_min") else "-"
        stage_val = j.get("pipeline_stage") or "discovered"
        score = j.get("match_score")
        score_text = f"{score:.1f}" if score else "-"
        table.add_row(
            str(j["id"]), str(j["title"])[:25], str(j["company"])[:15],
            str(j.get("city", ""))[:8], salary_text, stage_val, score_text,
        )

    console.print(table)


@search.command("refresh")
def search_refresh():
    """重新运行上次搜索（使用相同条件）"""
    console.print("[yellow]Refresh not yet implemented — re-run 'search run' manually.[/yellow]")


# ── match ──────────────────────────────────────────────────────────────

@cli.group()
def match():
    """简历匹配"""


@match.command("run")
@click.option("--job-ids", default=None, help="逗号分隔的岗位 ID，如 '1,3,5'")
@click.option("--all/--selected", default=True, help="匹配所有未匹配的岗位")
@click.option("--min-score", type=float, default=0.0, help="最低评分阈值")
def match_run(job_ids: str | None, all: bool, min_score: float):
    """匹配简历与岗位"""
    row = resume_repo.get_active_resume()
    if not row:
        console.print("[red]请先上传简历: resume upload <文件路径>[/red]")
        return

    registry = build_registry("matcher")
    from hirehive.agents.matcher import MatcherAgent
    agent = MatcherAgent(registry)

    ids_list = [int(x.strip()) for x in job_ids.split(",") if x.strip()] if job_ids else None

    console.print("[bold]开始匹配...[/bold]")
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task("LLM 分析匹配中...", total=None)
        result = agent.match(ids_list, min_score)

    console.print(Panel(result, title="匹配结果"))


@match.command("show")
@click.option("--job-id", type=int, required=True, help="岗位 ID")
def match_show(job_id: int):
    """查看指定岗位的详细匹配报告"""
    app = application_repo.get_application(job_id)
    if not app or not app.get("match_details"):
        console.print("[yellow]该岗位尚未匹配。先执行 match run。[/yellow]")
        return

    md = json.loads(app["match_details"]) if isinstance(app["match_details"], str) else app["match_details"]
    console.print(Panel(json.dumps(md, ensure_ascii=False, indent=2), title=f"匹配报告 (Job #{job_id})"))


# ── apply ──────────────────────────────────────────────────────────────

@cli.group()
def apply():
    """自动投递"""


@apply.command("go")
@click.option("--job-id", type=int, required=True, help="岗位 ID")
def apply_go(job_id: int):
    """投递指定岗位"""
    job = job_repo.get_job(job_id)
    if not job:
        console.print(f"[red]岗位 ID {job_id} 不存在[/red]")
        return

    row = resume_repo.get_active_resume()
    if not row:
        console.print("[red]请先上传简历[/red]")
        return

    if not click.confirm(f"确认投递 '{job['title']}' @ {job['company']}?"):
        console.print("[dim]已取消[/dim]")
        return

    registry = build_registry("applier")
    from hirehive.agents.applier import ApplierAgent
    agent = ApplierAgent(registry)

    console.print("[bold]执行投递...[/bold]")
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task("浏览器操作中...", total=None)
        result = agent.apply(job["url"], job["title"], job["company"])

    # Update application state
    from hirehive.models.application import Application, PipelineStage
    app = Application(job_id=job_id, resume_id=row["id"], pipeline_stage=PipelineStage.APPLIED)
    application_repo.save_application(app)

    console.print(Panel(result, title="投递结果"))


@apply.command("status")
def apply_status():
    """查看投递状态"""
    apps = application_repo.list_applications()
    if not apps:
        console.print("[yellow]暂无投递记录[/yellow]")
        return

    stage_colors = {
        "discovered": "white", "matched": "cyan", "applied": "yellow",
        "interviewing": "green", "offered": "magenta", "accepted": "bold green",
        "rejected": "red",
    }

    table = Table(title="投递状态")
    table.add_column("ID")
    table.add_column("岗位")
    table.add_column("公司")
    table.add_column("阶段")
    table.add_column("匹配分")
    table.add_column("投递时间")

    for a in apps:
        stage = a["pipeline_stage"]
        color = stage_colors.get(stage, "white")
        table.add_row(
            str(a["id"]), str(a.get("title", ""))[:25], str(a.get("company", ""))[:15],
            f"[{color}]{stage}[/{color}]",
            f"{a['match_score']:.1f}" if a.get("match_score") else "-",
            a.get("applied_at") or "-",
        )

    console.print(table)


# ── interview ──────────────────────────────────────────────────────────

@cli.group()
def interview():
    """面试准备"""


@interview.command("prep")
@click.option("--job-id", type=int, required=True, help="岗位 ID")
def interview_prep(job_id: int):
    """生成面试准备材料"""
    job = job_repo.get_job(job_id)
    if not job:
        console.print(f"[red]岗位 ID {job_id} 不存在[/red]")
        return

    registry = build_registry("interview_coach")
    from hirehive.agents.interview_coach import InterviewCoachAgent
    agent = InterviewCoachAgent(registry)

    console.print("[bold]生成面试准备材料...[/bold]")
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task("LLM 生成中...", total=None)
        result = agent.prepare(
            job_description=job.get("description", ""),
            job_title=job["title"],
            company=job["company"],
        )

    console.print(Panel(result, title=f"面试准备 — {job['title']} @ {job['company']}"))


@interview.command("mock")
@click.option("--job-id", type=int, default=None, help="岗位 ID (可选)")
def interview_mock(job_id: int | None):
    """启动模拟面试"""
    job_desc = ""
    if job_id:
        job = job_repo.get_job(job_id)
        if job:
            job_desc = job.get("description", "")

    registry = build_registry("interview_coach")
    from hirehive.agents.interview_coach import InterviewCoachAgent
    agent = InterviewCoachAgent(registry)

    console.print(Panel("[bold]模拟面试模式[/bold]\n输入你的回答，AI 面试官会追问。输入 /quit 退出。", title="面试开始"))

    history: list[dict] = []
    first = True
    while True:
        if first:
            response = agent.mock_interview("", [{"role": "system", "content": f"岗位描述：{job_desc}"}] if job_desc else None)
            first = False
        else:
            user_answer = click.prompt("\n[bold]你[/bold]", prompt_suffix="> ")
            if user_answer.strip() == "/quit":
                console.print("[dim]面试结束。[/dim]")
                break
            history.append({"role": "user", "content": user_answer})
            response = agent.mock_interview(user_answer, history)
            history.append({"role": "assistant", "content": response})

        console.print(f"\n[bold cyan]面试官[/bold cyan]: {response}")


# ── offer ──────────────────────────────────────────────────────────────

@cli.group()
def offer():
    """Offer 管理"""


@offer.command("add")
@click.option("--company", required=True, help="公司名")
@click.option("--position", required=True, help="岗位名称")
@click.option("--salary", type=int, required=True, help="月薪 (元)")
@click.option("--bonus", type=int, default=12, help="年终奖月数")
@click.option("--location", default="", help="工作地点")
@click.option("--work-mode", default="onsite", type=click.Choice(["onsite", "remote", "hybrid"]))
@click.option("--equity", default="", help="股票/期权描述")
@click.option("--commute", type=int, default=0, help="通勤时间 (分钟)")
def offer_add(company: str, position: str, salary: int, bonus: int, location: str, work_mode: str, equity: str, commute: int):
    """添加 Offer 记录"""
    from hirehive.models.offer import Offer
    o = Offer(
        company=company, position=position, base_salary=salary,
        bonus_months=bonus, location=location, work_mode=work_mode,
        equity=equity, commute_minutes=commute,
    )
    oid = offer_repo.save_offer(o)
    console.print(f"[green]Offer 已保存 (ID: {oid})[/green]")


@offer.command("compare")
def offer_compare():
    """对比所有待选 Offer"""
    offers = offer_repo.get_offers(status="pending")
    if not offers:
        console.print("[yellow]没有待选的 Offer。用 offer add 添加。[/yellow]")
        return

    registry = build_registry("offer_advisor")
    from hirehive.agents.offer_advisor import OfferAdvisorAgent
    agent = OfferAdvisorAgent(registry)

    console.print("[bold]分析对比中...[/bold]")
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task("LLM 分析中...", total=None)
        result = agent.compare()

    console.print(Panel(result, title="Offer 对比分析"))


@offer.command("list")
def offer_list():
    """查看所有 Offer"""
    offers = offer_repo.get_offers()
    if not offers:
        console.print("[yellow]暂无 Offer 记录[/yellow]")
        return

    table = Table(title="Offer 列表")
    table.add_column("ID", style="dim")
    table.add_column("公司")
    table.add_column("岗位")
    table.add_column("月薪")
    table.add_column("年终")
    table.add_column("地点")
    table.add_column("模式")
    table.add_column("状态")

    for o in offers:
        table.add_row(
            str(o["id"]), o["company"], o["position"],
            f"{o['base_salary']:,}" if o.get("base_salary") else "-",
            f"{o.get('bonus_months', 12)}个月",
            o.get("location", ""), o.get("work_mode", ""),
            o.get("status", "pending"),
        )
    console.print(table)


@offer.command("decide")
@click.option("--offer-id", type=int, required=True, help="Offer ID")
@click.option("--accept/--decline", default=True, help="接受或拒绝")
def offer_decide(offer_id: int, accept: bool):
    """接受或拒绝一个 Offer"""
    status = "accepted" if accept else "declined"
    offer_repo.update_offer_status(offer_id, status)
    action = "已接受" if accept else "已拒绝"
    console.print(f"[green]Offer {offer_id} {action}[/green]")


# ── dashboard ──────────────────────────────────────────────────────────

@cli.command()
def dashboard():
    """流水线概览仪表盘"""
    stats = application_repo.get_pipeline_stats()
    jobs_total = job_repo.job_count()

    console.print(Panel.fit(
        f"[bold]HireHive Dashboard[/bold]\n\n"
        f"  总岗位数: {jobs_total}\n",
        title="Dashboard"
    ))

    stages = ["discovered", "matched", "applied", "interviewing", "offered", "accepted", "rejected"]
    labels = {
        "discovered": "已发现", "matched": "已匹配", "applied": "已投递",
        "interviewing": "面试中", "offered": "已获 Offer", "accepted": "已接受",
        "rejected": "已拒绝",
    }

    for stage in stages:
        count = stats.get(stage, 0)
        bar = "█" * min(count, 30)
        console.print(f"  {labels.get(stage, stage):10s} [{count:3d}] {bar}")

    # Active offers
    offers = offer_repo.get_offers(status="pending")
    if offers:
        console.print(f"\n[bold]待选 Offer: {len(offers)} 个[/bold] — 使用 'offer compare' 对比")


# ── interactive ────────────────────────────────────────────────────────

@cli.command()
def interactive():
    """交互式 REPL 模式"""
    console.print(Panel.fit(
        "[bold]HireHive — Job Search Agent[/bold]\n\n"
        "Commands: search / match / apply / interview / offer / dashboard / help / quit",
        title="Welcome"
    ))

    # Build coordinator registry with all tools
    registry = build_registry("coordinator")
    from hirehive.agents.coordinator import CoordinatorAgent
    coordinator = CoordinatorAgent(registry)

    while True:
        try:
            cmd = click.prompt("\n[bold cyan]hirehive[/bold cyan]", prompt_suffix="> ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]再见！[/dim]")
            break

        if not cmd:
            continue
        if cmd in ("quit", "exit", "q"):
            console.print("[dim]再见！[/dim]")
            break
        if cmd == "help":
            console.print("""
  search <关键词> [in <城市>]             — 搜索岗位
  match [<ids>] [min <score>]           — 匹配简历
  apply <id>                            — 投递岗位
  interview prep <id>                   — 面试准备
  interview mock [<id>]                 — 模拟面试
  offer add                             — 添加 Offer
  offer compare                         — 对比 Offer
  dashboard                             — 流水线概览
  quit                                  — 退出
""")
            continue
        if cmd == "dashboard":
            dashboard.callback()
            continue
        if cmd.startswith("offer compare"):
            offer_compare.callback()
            continue
        if cmd.startswith("offer list"):
            offer_list.callback()
            continue

        # For anything else, delegate to the coordinator agent
        context = {
            "pipeline_stats": application_repo.get_pipeline_stats(),
            "total_jobs": job_repo.job_count(),
        }
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            progress.add_task("思考中...", total=None)
            response = coordinator.run(cmd, context=context)

        console.print(f"\n{response}")


# ── entry ──────────────────────────────────────────────────────────────

def main():
    """Entry point with UTF-8 encoding for Windows."""
    import sys
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    cli()


if __name__ == "__main__":
    main()
