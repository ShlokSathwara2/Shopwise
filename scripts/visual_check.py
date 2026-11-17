from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "assets" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)


async def main() -> int:
    errors: list[str] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        page.on("console", lambda msg: errors.append(f"console {msg.type}: {msg.text}") if msg.type == "error" else None)
        page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
        page.on("requestfailed", lambda request: errors.append(f"requestfailed: {request.url} {request.failure}"))
        await page.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        await page.wait_for_timeout(800)
        await page.screenshot(path=str(OUT / "00-home.png"), full_page=True)
        print("TITLE:", await page.title())
        print("H1:", await page.locator("h1").first.text_content())
        print("PRODUCT CARDS:", await page.locator(".product-card").count())
        print("SIZE:", await page.evaluate("({w: document.documentElement.scrollWidth, h: document.documentElement.scrollHeight})"))
        if errors:
            print("ERRORS:")
            for error in errors:
                print(" -", error)
        else:
            print("NO BROWSER ERRORS")
        await browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
