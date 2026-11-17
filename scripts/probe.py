from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from playwright.async_api import Page, async_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "assets" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:8000"


async def snap(page: Page, name: str, full: bool = True) -> None:
    await page.wait_for_timeout(350)
    await page.screenshot(path=str(OUT / f"{name}.png"), full_page=full)
    print(f"snap {name}: {page.url}")


async def main() -> int:
    errors: list[str] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        page = await context.new_page()
        page.on("console", lambda msg: errors.append(f"console {msg.type}: {msg.text}") if msg.type == "error" else None)
        page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
        page.on("requestfailed", lambda request: errors.append(f"requestfailed: {request.url} {request.failure}"))

        await page.goto(f"{BASE}/shop", wait_until="networkidle")
        await snap(page, "probe-shop")
        await page.goto(f"{BASE}/product/291", wait_until="networkidle")
        await snap(page, "probe-product")
        await page.goto(f"{BASE}/login", wait_until="networkidle")
        await snap(page, "probe-login")
        await page.goto(f"{BASE}/register", wait_until="networkidle")
        await snap(page, "probe-register")
        await page.goto(f"{BASE}/this-does-not-exist", wait_until="networkidle")
        await snap(page, "probe-404")

        await page.goto(f"{BASE}/login", wait_until="networkidle")
        await page.locator('input[type="email"]').fill("admin@shopwise.com")
        await page.locator('input[type="password"]').fill("admin1234")
        await page.locator('button[type="submit"]').click()
        await page.wait_for_url(f"{BASE}/admin", timeout=10000)
        await page.goto(f"{BASE}/admin", wait_until="networkidle")
        await snap(page, "probe-admin-dashboard")
        await page.goto(f"{BASE}/admin/products", wait_until="networkidle")
        await snap(page, "probe-admin-products")
        await page.goto(f"{BASE}/admin/orders", wait_until="networkidle")
        await snap(page, "probe-admin-orders")
        await page.goto(f"{BASE}/admin/model", wait_until="networkidle")
        await snap(page, "probe-admin-model")

        print("URL:", page.url)
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
