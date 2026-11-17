"""Capture final admin screenshots after cleanup and a clean retrain."""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "reports" / "assets" / "screenshots"
BASE = "http://127.0.0.1:8000"


def settle(page, selector: str | None = None) -> None:
    page.wait_for_load_state("networkidle")
    if selector:
        page.wait_for_selector(selector)
    page.wait_for_timeout(700)


def shot(page, name: str) -> None:
    total = page.evaluate("document.body.scrollHeight")
    page.evaluate("window.scrollTo(0, 0)")
    for y in range(0, int(total), 700):
        page.evaluate("(y) => window.scrollTo(0, y)", y)
        page.wait_for_timeout(70)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(350)
    page.screenshot(path=str(SHOTS / name), full_page=True, animations="disabled")
    print("shot", name)


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        page = context.new_page()
        errors: list[str] = []
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))

        page.goto(BASE + "/login", wait_until="networkidle")
        page.locator("input[autocomplete=email]").fill("admin@shopwise.com")
        page.locator("input[autocomplete=current-password]").fill("admin1234")
        page.get_by_role("button", name="Sign in").click()
        page.wait_for_url("**/admin", timeout=15000)
        page.wait_for_selector(".admin-page")
        settle(page)
        page.wait_for_timeout(1200)
        shot(page, "20-admin-dashboard.png")

        page.goto(BASE + "/admin/products", wait_until="networkidle")
        settle(page, ".admin-table")
        page.locator(".admin-search input").fill("")
        settle(page, ".admin-table")
        shot(page, "21-admin-products.png")

        page.goto(BASE + "/admin/orders", wait_until="networkidle")
        settle(page, ".admin-table--orders")
        page.locator(".table-expand").first.click()
        page.wait_for_timeout(500)
        shot(page, "26-admin-orders.png")

        page.goto(BASE + "/admin/model", wait_until="networkidle")
        settle(page, ".admin-page")
        page.wait_for_timeout(900)
        shot(page, "27-admin-model.png")

        context.close()
        browser.close()
        bad = [e for e in errors if "ERR_SOCKET_NOT_CONNECTED" not in e and "ERR_ABORTED" not in e]
        if bad:
            raise AssertionError("Console errors: " + " | ".join(bad))
        print("final admin screenshots captured")


if __name__ == "__main__":
    main()
