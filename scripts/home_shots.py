"""Refresh public and personalised home screenshots after de-duplicating rails."""

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
    page.wait_for_timeout(600)


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


def rail(page, selector: str, name: str) -> None:
    page.wait_for_selector(selector)
    page.locator(selector).screenshot(path=str(SHOTS / name), animations="disabled")
    print("rail", name)


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        public = browser.new_context(viewport={"width": 1440, "height": 1000})
        page = public.new_page()
        page.goto(BASE + "/", wait_until="networkidle")
        settle(page, ".hero")
        shot(page, "01-home.png")
        public.close()

        shopper = browser.new_context(viewport={"width": 1440, "height": 1000})
        page = shopper.new_page()
        page.goto(BASE + "/login", wait_until="networkidle")
        page.get_by_role("button", name="Enter as shopper").click()
        page.wait_for_url(BASE + "/", timeout=15000)
        settle(page, "#recommended")
        shot(page, "09-home-personalized.png")
        rail(page, "#recommended", "10-recommended-for-you.png")
        rail(page, "section.section--tight", "11-trending-now.png")
        shopper.close()
        browser.close()


if __name__ == "__main__":
    main()
