import asyncio
from typing import Optional

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeout,
    async_playwright,
)

SEARCH_URL = "https://search.sunbiz.org/Inquiry/CorporationSearch/ByName"
ACTIVE_STATUSES = {"active"}
DEFAULT_TIMEOUT_MS = 20000


async def _search_one(page: Page, term: str) -> Optional[dict]:
    await page.goto(SEARCH_URL, timeout=DEFAULT_TIMEOUT_MS, wait_until="domcontentloaded")
    await page.fill("#SearchTerm", term)
    await page.click('input[type="submit"][value="Search Now"]')
    try:
        await page.wait_for_selector(
            "#search-results table tbody tr", timeout=DEFAULT_TIMEOUT_MS
        )
    except PlaywrightTimeout:
        return None

    rows = await page.query_selector_all("#search-results table tbody tr")
    for row in rows:
        cells = await row.query_selector_all("td")
        if len(cells) < 3:
            continue
        status = (await cells[2].inner_text()).strip().lower()
        if status in ACTIVE_STATUSES:
            return {
                "matched_corporate_name": (await cells[0].inner_text()).strip(),
                "document_number": (await cells[1].inner_text()).strip(),
                "status": (await cells[2].inner_text()).strip(),
            }
    return None


async def _worker(
    name: str,
    queue: asyncio.Queue,
    results: list,
    browser: Browser,
    progress: dict,
    retries: int,
):
    ctx: BrowserContext = await browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    )
    page = await ctx.new_page()
    while True:
        item = await queue.get()
        if item is None:
            queue.task_done()
            break

        idx, term = item
        result = None
        last_err = None
        for attempt in range(retries):
            try:
                result = await _search_one(page, term)
                break
            except Exception as e:
                last_err = e
                await asyncio.sleep(1 + attempt)

        if result is None and last_err is not None:
            results[idx] = {"error": str(last_err)}
        else:
            results[idx] = result

        progress["done"] += 1
        status = "ok" if result else "no-active"
        if result is None and last_err is not None:
            status = "error"
        print(
            f"[{progress['done']:>3}/{progress['total']}] "
            f"{name} {status:<9} {term!r} -> "
            f"{result.get('document_number') if result else '-'}"
        )
        queue.task_done()

    await ctx.close()


async def scrape_terms(
    terms: list, concurrency: int = 5, retries: int = 2, headless: bool = True
) -> list:
    queue: asyncio.Queue = asyncio.Queue()
    for i, t in enumerate(terms):
        queue.put_nowait((i, t))
    for _ in range(concurrency):
        queue.put_nowait(None)

    results = [None] * len(terms)
    progress = {"done": 0, "total": len(terms)}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        workers = [
            asyncio.create_task(
                _worker(f"w{i}", queue, results, browser, progress, retries)
            )
            for i in range(concurrency)
        ]
        await asyncio.gather(*workers)
        await browser.close()

    return results
