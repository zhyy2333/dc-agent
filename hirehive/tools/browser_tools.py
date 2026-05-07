"""Playwright browser automation tools for BOSS直聘.

These tools are fully implemented in Phase 2. They use playwright.sync_api
to automate BOSS直聘 job search, detail scraping, and application submission.
"""

from pathlib import Path
from hirehive.config import config
from hirehive.utils.text import random_delay


_browser = None
_page = None


def _get_page():
    global _browser, _page
    if _page is not None:
        return _page
    from playwright.sync_api import sync_playwright
    p = sync_playwright().start()
    _browser = p.chromium.launch(
        headless=config.browser_headless,
        user_data_dir=str(config.browser_user_data_dir) if config.browser_user_data_dir else None,
    )
    ctx = _browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        viewport={"width": 1440, "height": 900},
        locale="zh-CN",
    )
    _page = ctx.new_page()
    return _page


def boss_navigate(url: str) -> dict:
    """Navigate to a URL. Returns page title and URL after navigation."""
    try:
        page = _get_page()
        random_delay(config.action_delay_min, config.action_delay_max)
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        return {"url": page.url, "title": page.title()}
    except Exception as e:
        return {"error": str(e), "url": url}


def boss_search_jobs(keyword: str, city: str, salary_min: int = 0, salary_max: int = 0, page_num: int = 1) -> dict:
    """Search BOSS直聘 for jobs. Returns list of job cards found."""
    try:
        page = _get_page()
        search_url = f"https://www.zhipin.com/web/geek/job?query={keyword}&city={city}"
        if page_num > 1:
            search_url += f"&page={page_num}"
        random_delay(config.action_delay_min, config.action_delay_max)
        page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_selector(".job-list-box", timeout=10000)

        # Let the page render
        random_delay(2, 3)

        job_cards = page.query_selector_all(".job-card-wrapper")
        results = []
        for card in job_cards[:20]:
            try:
                title_el = card.query_selector(".job-name")
                company_el = card.query_selector(".company-name")
                salary_el = card.query_selector(".salary")
                tags_els = card.query_selector_all(".tag-item")
                link_el = card.query_selector("a")

                title = title_el.inner_text() if title_el else ""
                company = company_el.inner_text() if company_el else ""
                salary_text = salary_el.inner_text() if salary_el else ""
                tags = [t.inner_text() for t in tags_els[:5]]
                href = link_el.get_attribute("href") if link_el else ""

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


def boss_get_job_detail(job_url: str) -> dict:
    """Scrape a BOSS直聘 job detail page."""
    try:
        page = _get_page()
        random_delay(config.action_delay_min, config.action_delay_max)
        page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_selector(".job-detail", timeout=10000)

        random_delay(1, 2)

        title = page.query_selector(".name")
        company = page.query_selector(".company-name")
        salary = page.query_selector(".salary")
        desc = page.query_selector(".job-detail .text")

        return {
            "url": job_url,
            "title": title.inner_text().strip() if title else "",
            "company": company.inner_text().strip() if company else "",
            "salary_text": salary.inner_text().strip() if salary else "",
            "description": desc.inner_text().strip() if desc else "",
        }
    except Exception as e:
        return {"error": str(e), "url": job_url}


def boss_click_apply(job_url: str) -> dict:
    """Click the '立即沟通' button on a job detail page."""
    try:
        page = _get_page()
        if page.url != job_url:
            page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
        random_delay(config.action_delay_min, config.action_delay_max)
        btn = page.query_selector('text=立即沟通')
        if not btn:
            btn = page.query_selector('.btn-apply')
        if btn:
            btn.click()
            random_delay(1, 2)
            return {"status": "clicked", "url": job_url}
        return {"status": "button_not_found", "url": job_url}
    except Exception as e:
        return {"error": str(e), "url": job_url}


def boss_send_greeting(message: str) -> dict:
    """Send a greeting message in the BOSS直聘 chat popup."""
    try:
        page = _get_page()
        random_delay(0.5, 1.0)
        textarea = page.query_selector(".chat-input textarea, .message-input textarea")
        if not textarea:
            textarea = page.query_selector('[placeholder*="请输入"]')
        if textarea:
            textarea.fill(message)
            random_delay(0.5, 1.0)
            send_btn = page.query_selector('text=发送')
            if send_btn:
                send_btn.click()
                return {"status": "sent", "message": message[:80]}
        return {"status": "input_not_found"}
    except Exception as e:
        return {"error": str(e)}


def boss_fill_application(fields: list[dict]) -> dict:
    """Fill application form fields on BOSS直聘."""
    try:
        page = _get_page()
        for field in fields:
            el = page.query_selector(field.get("selector", ""))
            if el:
                el.fill(field.get("value", ""))
                random_delay(0.3, 0.8)
        return {"status": "filled", "field_count": len(fields)}
    except Exception as e:
        return {"error": str(e)}


def boss_upload_attachment(selector: str, file_path: str) -> dict:
    """Upload a file (resume) via file input."""
    try:
        page = _get_page()
        file_input = page.query_selector(selector)
        if file_input:
            file_input.set_input_files(file_path)
            return {"status": "uploaded", "file": file_path}
        return {"status": "selector_not_found", "selector": selector}
    except Exception as e:
        return {"error": str(e)}


def boss_check_message_response(job_url: str) -> dict:
    """Check for employer response in BOSS直聘 chat."""
    try:
        page = _get_page()
        messages = page.query_selector_all(".chat-message, .message-item")
        responses = []
        for msg in messages[-5:]:
            text = msg.inner_text()
            if text.strip():
                responses.append(text.strip())
        return {"has_response": len(responses) > 0, "messages": responses}
    except Exception as e:
        return {"error": str(e)}


def boss_scroll_page(times: int = 3) -> dict:
    """Scroll to load more listings (infinite scroll)."""
    try:
        page = _get_page()
        for _ in range(times):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            random_delay(1.5, 2.5)
        return {"status": "scrolled", "times": times}
    except Exception as e:
        return {"error": str(e)}


def boss_take_screenshot(label: str) -> dict:
    """Take a debug screenshot."""
    try:
        page = _get_page()
        screenshot_dir = config.data_dir / "screenshots"
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        path = screenshot_dir / f"{label}.png"
        page.screenshot(path=str(path), full_page=False)
        return {"path": str(path), "label": label}
    except Exception as e:
        return {"error": str(e)}


def boss_wait_for(selector: str, timeout_ms: int = 5000) -> dict:
    """Wait for an element to appear."""
    try:
        page = _get_page()
        page.wait_for_selector(selector, timeout=timeout_ms)
        return {"status": "found", "selector": selector}
    except Exception as e:
        return {"error": str(e), "selector": selector}
