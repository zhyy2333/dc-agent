"""Playwright browser automation tools for BOSS直聘.

All browser operations run in a dedicated background thread with its own asyncio
event loop. This isolates Playwright from any asyncio loops created by the
Anthropic SDK or the host environment (VSCode, Jupyter, etc.).
"""

import asyncio
import threading
from pathlib import Path

from hirehive.config import config


# ── Dedicated browser thread with its own asyncio event loop ────────────────

_browser_loop: asyncio.AbstractEventLoop | None = None
_browser_loop_ready = threading.Event()
_loop_lock = threading.Lock()
_playwright = None
_browser = None
_context = None
_page = None


def _start_browser_loop():
    """Start the persistent browser event loop in a background thread."""
    global _browser_loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    _browser_loop = loop
    _browser_loop_ready.set()
    loop.run_forever()


def _get_loop() -> asyncio.AbstractEventLoop:
    """Get or create the browser event loop (starts thread on first call)."""
    global _browser_loop
    if _browser_loop is None:
        with _loop_lock:
            if _browser_loop is None:
                t = threading.Thread(target=_start_browser_loop, daemon=True)
                t.start()
                _browser_loop_ready.wait(timeout=10)
                if _browser_loop is None:
                    raise RuntimeError("Browser event loop failed to start")
    return _browser_loop


def _run_async(coro):
    """Run a coroutine on the browser thread and return its result synchronously."""
    loop = _get_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result(timeout=120)


# ── Internal async browser management ───────────────────────────────────────

async def _get_page_async():
    global _playwright, _browser, _context, _page
    if _page is not None:
        try:
            if not _page.is_closed():
                return _page
        except Exception:
            pass
        _page = None

    from playwright.async_api import async_playwright
    _playwright = await async_playwright().start()

    # ── Strategy 1: connect to user's existing Chrome via CDP ──
    cdp_url = config.browser_cdp_url
    if cdp_url:
        _browser = await _playwright.chromium.connect_over_cdp(cdp_url)
        contexts = _browser.contexts
        if contexts:
            _context = contexts[0]
            pages = _context.pages
            if pages:
                _page = pages[0]
            else:
                _page = await _context.new_page()
        else:
            _context = await _browser.new_context()
            _page = await _context.new_page()
        return _page

    # ── Strategy 2: launch local Chromium with anti-detection ──
    launch_args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-features=IsolateOrigins,site-per-process",
        "--no-sandbox",
        "--disable-infobars",
        "--disable-dev-shm-usage",
    ]
    user_data_dir = str(config.browser_user_data_dir) if config.browser_user_data_dir else None
    if user_data_dir:
        _context = await _playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=config.browser_headless,
            args=launch_args,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            locale="zh-CN",
            ignore_default_args=["--enable-automation"],
        )
        _page = _context.pages[0] if _context.pages else await _context.new_page()
    else:
        _browser = await _playwright.chromium.launch(
            headless=config.browser_headless,
            args=launch_args,
            ignore_default_args=["--enable-automation"],
        )
        _context = await _browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            locale="zh-CN",
            bypass_csp=True,
        )
        _page = await _context.new_page()
    return _page


# ── Public tool functions (sync wrappers around async implementations) ─────

def boss_navigate(url: str) -> dict:
    """Navigate to a URL. Returns page title and URL after navigation."""

    async def _impl():
        try:
            page = await _get_page_async()
            await _random_delay()
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            return {"url": page.url, "title": await page.title()}
        except Exception as e:
            return {"error": str(e), "url": url}

    return _run_async(_impl())


def boss_search_jobs(keyword: str, city: str, salary_min: int = 0, salary_max: int = 0, page_num: int = 1) -> dict:
    """Search BOSS直聘 for jobs. Returns list of job cards found."""

    async def _impl():
        try:
            page = await _get_page_async()
            search_url = f"https://www.zhipin.com/web/geek/job?query={keyword}&city={city}"
            if page_num > 1:
                search_url += f"&page={page_num}"
            await _random_delay()
            await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_selector(".job-list-box", timeout=10000)
            await _random_delay(2, 3)

            job_cards = await page.query_selector_all(".job-card-wrapper")
            results = []
            for card in job_cards[:20]:
                try:
                    title_el = await card.query_selector(".job-name")
                    company_el = await card.query_selector(".company-name")
                    salary_el = await card.query_selector(".salary")
                    tags_els = await card.query_selector_all(".tag-item")
                    link_el = await card.query_selector("a")

                    title = (await title_el.inner_text()) if title_el else ""
                    company = (await company_el.inner_text()) if company_el else ""
                    salary_text = (await salary_el.inner_text()) if salary_el else ""
                    tags = [(await t.inner_text()) for t in tags_els[:5]]
                    href = (await link_el.get_attribute("href")) if link_el else ""

                    if title and company:
                        results.append({
                            "title": title.strip(),
                            "company": company.strip(),
                            "salary_text": salary_text.strip(),
                            "tags": tags,
                            "url": f"https://www.zhipin.com{href}" if href.startswith("/") else href,
                        })
                except Exception:
                    continue

            return {"total_found": len(results), "jobs": results}
        except Exception as e:
            return {"error": str(e), "total_found": 0, "jobs": []}

    return _run_async(_impl())


def boss_get_job_detail(job_url: str) -> dict:
    """Scrape a BOSS直聘 job detail page."""

    async def _impl():
        try:
            page = await _get_page_async()
            await _random_delay()
            await page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_selector(".job-detail", timeout=10000)
            await _random_delay(1, 2)

            title = await page.query_selector(".name")
            company = await page.query_selector(".company-name")
            salary = await page.query_selector(".salary")
            desc = await page.query_selector(".job-detail .text")

            return {
                "url": job_url,
                "title": (await title.inner_text()).strip() if title else "",
                "company": (await company.inner_text()).strip() if company else "",
                "salary_text": (await salary.inner_text()).strip() if salary else "",
                "description": (await desc.inner_text()).strip() if desc else "",
            }
        except Exception as e:
            return {"error": str(e), "url": job_url}

    return _run_async(_impl())


def boss_click_apply(job_url: str) -> dict:
    """Click the '立即沟通' button on a job detail page."""

    async def _impl():
        try:
            page = await _get_page_async()
            if page.url != job_url:
                await page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
            await _random_delay()
            btn = await page.query_selector('text=立即沟通')
            if not btn:
                btn = await page.query_selector('.btn-apply')
            if btn:
                await btn.click()
                await _random_delay(1, 2)
                return {"status": "clicked", "url": job_url}
            return {"status": "button_not_found", "url": job_url}
        except Exception as e:
            return {"error": str(e), "url": job_url}

    return _run_async(_impl())


def boss_send_greeting(message: str) -> dict:
    """Send a greeting message in the BOSS直聘 chat popup."""

    async def _impl():
        try:
            page = await _get_page_async()
            await _random_delay(0.5, 1.0)
            textarea = await page.query_selector(".chat-input textarea, .message-input textarea")
            if not textarea:
                textarea = await page.query_selector('[placeholder*="请输入"]')
            if textarea:
                await textarea.fill(message)
                await _random_delay(0.5, 1.0)
                send_btn = await page.query_selector('text=发送')
                if send_btn:
                    await send_btn.click()
                    return {"status": "sent", "message": message[:80]}
            return {"status": "input_not_found"}
        except Exception as e:
            return {"error": str(e)}

    return _run_async(_impl())


def boss_fill_application(fields: list[dict]) -> dict:
    """Fill application form fields on BOSS直聘."""

    async def _impl():
        try:
            page = await _get_page_async()
            for field in fields:
                el = await page.query_selector(field.get("selector", ""))
                if el:
                    await el.fill(field.get("value", ""))
                    await _random_delay(0.3, 0.8)
            return {"status": "filled", "field_count": len(fields)}
        except Exception as e:
            return {"error": str(e)}

    return _run_async(_impl())


def boss_upload_attachment(selector: str, file_path: str) -> dict:
    """Upload a file (resume) via file input."""

    async def _impl():
        try:
            page = await _get_page_async()
            file_input = await page.query_selector(selector)
            if file_input:
                await file_input.set_input_files(file_path)
                return {"status": "uploaded", "file": file_path}
            return {"status": "selector_not_found", "selector": selector}
        except Exception as e:
            return {"error": str(e)}

    return _run_async(_impl())


def boss_check_message_response(job_url: str) -> dict:
    """Check for employer response in BOSS直聘 chat."""

    async def _impl():
        try:
            page = await _get_page_async()
            messages = await page.query_selector_all(".chat-message, .message-item")
            responses = []
            for msg in messages[-5:]:
                text = await msg.inner_text()
                if text.strip():
                    responses.append(text.strip())
            return {"has_response": len(responses) > 0, "messages": responses}
        except Exception as e:
            return {"error": str(e)}

    return _run_async(_impl())


def boss_scroll_page(times: int = 3) -> dict:
    """Scroll to load more listings (infinite scroll)."""

    async def _impl():
        try:
            page = await _get_page_async()
            for _ in range(times):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await _random_delay(1.5, 2.5)
            return {"status": "scrolled", "times": times}
        except Exception as e:
            return {"error": str(e)}

    return _run_async(_impl())


def boss_take_screenshot(label: str) -> dict:
    """Take a debug screenshot."""

    async def _impl():
        try:
            page = await _get_page_async()
            screenshot_dir = config.data_dir / "screenshots"
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            path = screenshot_dir / f"{label}.png"
            await page.screenshot(path=str(path), full_page=False)
            return {"path": str(path), "label": label}
        except Exception as e:
            return {"error": str(e)}

    return _run_async(_impl())


def boss_wait_for(selector: str, timeout_ms: int = 5000) -> dict:
    """Wait for an element to appear."""

    async def _impl():
        try:
            page = await _get_page_async()
            await page.wait_for_selector(selector, timeout=timeout_ms)
            return {"status": "found", "selector": selector}
        except Exception as e:
            return {"error": str(e), "selector": selector}

    return _run_async(_impl())


def boss_login() -> dict:
    """Navigate to BOSS直聘 login page. The user must scan QR code to log in.
    After calling this, use boss_check_login to verify login was successful."""

    async def _impl():
        try:
            page = await _get_page_async()
            await page.goto("https://www.zhipin.com/web/user/?ka=header-login", wait_until="domcontentloaded", timeout=30000)
            await _random_delay(2, 3)
            return {"status": "ready", "url": page.url, "title": await page.title(),
                    "hint": "请在浏览器中扫码登录，完成后按 Enter"}
        except Exception as e:
            return {"error": str(e)}

    return _run_async(_impl())


def boss_check_login() -> dict:
    """Check if the user is logged in to BOSS直聘 (read-only, no navigation).
    Returns logged_in=true if the page shows a logged-in state."""

    async def _impl():
        try:
            page = await _get_page_async()
            current_url = page.url

            # If we're on the login page, definitely not logged in
            if "/web/user/" in current_url:
                return {"logged_in": False, "reason": "当前在登录页面", "url": current_url}

            # Check for logged-in indicators (read-only, no navigation)
            logged_in_indicators = [
                ".user-nav",
                ".header-avatar",
                ".avatar",
                ".user-name",
                ".navi-logo",
                ".header-login-user",
                ".shop-index",
            ]
            for selector in logged_in_indicators:
                el = await page.query_selector(selector)
                if el:
                    return {"logged_in": True, "url": current_url, "indicator": selector}

            # Check for visible login prompts → not logged in
            login_prompts = ["text=登录/注册", "text=登录", "a:has-text('登录')"]
            for selector in login_prompts:
                el = await page.query_selector(selector)
                if el:
                    try:
                        visible = await el.is_visible()
                        if visible:
                            return {"logged_in": False, "reason": f"页面显示登录入口", "url": current_url}
                    except Exception:
                        pass

            # Not on login page, no login prompts → assume logged in
            return {"logged_in": True, "url": current_url, "indicator": "implicit"}
        except Exception as e:
            return {"logged_in": False, "reason": str(e), "error": str(e)}

    return _run_async(_impl())


# ── Helpers ─────────────────────────────────────────────────────────────────

async def _random_delay(min_s: float = 1.0, max_s: float = 3.0):
    """Async random delay for anti-bot."""
    import random
    d = min_s + random.random() * (max_s - min_s)
    await asyncio.sleep(d)
