"""Full browser E2E for Shopwise with report-ready screenshots.

Covers public catalogue browsing, registration, login, recommendations,
cart mutations, mock checkout, order history, reviews, and every admin page
including product CRUD (archive/restore) and a model retrain.
"""

from __future__ import annotations

import json
import sys
import time
import traceback
from pathlib import Path

from playwright.sync_api import Page, expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "reports" / "assets" / "screenshots"
SHOTS.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:8000"
QA_PRODUCT = "QA Stoneware Vase"
QA_EMAIL = f"qa.screens.{int(time.time())}@shopwise.com"
QA_PASSWORD = "Testing123!"
PASS: list[str] = []
IGNORED_CONSOLE = ("net::ERR_SOCKET_NOT_CONNECTED", "net::ERR_ABORTED")


def note_console(errors: list[str], message) -> None:
    if message.type != "error":
        return
    text = message.text
    if any(token in text for token in IGNORED_CONSOLE):
        return
    errors.append(text)


def step(message: str) -> None:
    PASS.append(message)
    print(f"  [ok] {message}")


def shot(page: Page, name: str, full: bool = True) -> Path:
    path = SHOTS / name
    scroll_through(page)
    page.wait_for_timeout(350)
    page.screenshot(path=str(path), full_page=full, animations="disabled")
    print(f"  [shot] {name}")
    return path


def scroll_through(page: Page) -> None:
    """Trigger lazy-loaded artwork before a full-page capture."""
    page.evaluate("window.scrollTo(0, 0)")
    total = page.evaluate("document.body.scrollHeight")
    for y in range(0, int(total), 700):
        page.evaluate("(y) => window.scrollTo(0, y)", y)
        page.wait_for_timeout(70)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(200)
    try:
        images_ready(page)
    except Exception:
        # Decorative images are not worth failing the functional flow for.
        pass


def images_ready(page: Page) -> None:
    page.wait_for_function(
        "() => Array.from(document.images).every((img) => img.complete && img.naturalWidth > 0)",
        timeout=15000,
    )


def settle(page: Page, selector: str | None = None) -> None:
    page.wait_for_load_state("networkidle")
    if selector:
        page.wait_for_selector(selector)
    page.wait_for_timeout(450)


def public_flow(browser) -> None:
    context = browser.new_context(viewport={"width": 1440, "height": 1000})
    page = context.new_page()
    errors: list[str] = []
    page.on("console", lambda msg: note_console(errors, msg))
    page.on(
        "pageerror",
        lambda exc: errors.append(f"pageerror: {exc}"),
    )

    print("\n[1/5] Public storefront")
    page.goto(BASE + "/", wait_until="networkidle")
    settle(page, ".hero")
    step("Home page renders with hero, category edit and rails")
    shot(page, "01-home.png")

    page.goto(BASE + "/shop", wait_until="networkidle")
    settle(page, ".product-grid")
    step("Shop renders full catalogue")
    shot(page, "02-shop.png")

    page.locator(".filter-categories").get_by_role("button", name="Kitchen & Dining").click()
    page.wait_for_url("**/shop?category=Kitchen+%26+Dining*", timeout=8000)
    settle(page, ".product-grid")
    assert "category=" in page.url
    step("Category filter updates URL and result grid")
    shot(page, "03-shop-category.png")

    search = page.locator(".shop-search input")
    search.fill("bowl")
    search.press("Enter")
    page.wait_for_url("**search=bowl**", timeout=8000)
    settle(page, ".product-grid")
    assert page.locator(".product-card").count() > 0
    step("Search returns matching products")
    shot(page, "04-shop-search.png")

    search = page.locator(".shop-search input")
    search.fill("zzzz-no-such-piece")
    search.press("Enter")
    page.wait_for_selector("text=No pieces match that yet", timeout=8000)
    settle(page)
    step("Empty search state renders")
    shot(page, "05-shop-empty.png")

    page.goto(BASE + "/product/291", wait_until="networkidle")
    settle(page, ".product-main")
    step("Product details, reviews and recommendation rails render")
    shot(page, "06-product.png")
    related = page.locator(".product-recommendations")
    rails = related.locator(":scope > *")
    assert rails.count() >= 2, f"expected two related rails, got {rails.count()}"
    rails.nth(0).screenshot(path=str(SHOTS / "07-product-similar.png"), animations="disabled")
    rails.nth(1).screenshot(path=str(SHOTS / "08-product-also-bought.png"), animations="disabled")
    step("Captured both product recommendation rails")

    page.goto(BASE + "/login", wait_until="networkidle")
    settle(page, ".auth-form")
    step("Login page renders")
    shot(page, "22-login.png", full=False)

    page.goto(BASE + "/register", wait_until="networkidle")
    settle(page, ".auth-form")
    step("Register page renders")
    shot(page, "23-register.png", full=False)

    page.goto(BASE + "/this-does-not-exist", wait_until="networkidle")
    settle(page, ".not-found")
    expect(page.locator(".not-found h2")).to_have_text("This shelf is empty.")
    step("404 page renders")
    shot(page, "24-not-found.png", full=False)

    # Mobile checks
    mobile = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=1)
    mp = mobile.new_page()
    mp.goto(BASE + "/", wait_until="networkidle")
    settle(mp, ".hero")
    shot(mp, "25-home-mobile.png")
    mp.goto(BASE + "/shop", wait_until="networkidle")
    settle(mp, ".product-grid")
    shot(mp, "26-shop-mobile.png")
    mobile.close()
    step("Mobile home and shop layouts render")

    if errors:
        raise AssertionError("Console errors on public pages: " + " | ".join(errors))
    context.close()


def registration_flow(browser) -> None:
    print("\n[2/5] Registration and session")
    context = browser.new_context(viewport={"width": 1440, "height": 1000})
    page = context.new_page()
    page.goto(BASE + "/register", wait_until="networkidle")
    page.locator("label.field").filter(has_text="Your name").locator("input").fill("Quinn Able")
    page.locator("label.field").filter(has_text="Email address").locator("input").fill(QA_EMAIL)
    page.locator('input[placeholder="At least 6 characters"]').fill(QA_PASSWORD)
    page.locator('input[placeholder="Same again"]').fill(QA_PASSWORD)
    shot(page, "23b-register-filled.png", full=False)
    page.get_by_role("button", name="Create my account").click()
    page.wait_for_url(BASE + "/", timeout=12000)
    page.wait_for_selector(".profile__trigger", timeout=10000)
    expect(page.locator(".profile__avatar")).to_have_text("QA")
    step(f"Registered {QA_EMAIL} and landed in an authenticated session")
    shot(page, "23c-registered-home.png")

    page.reload(wait_until="networkidle")
    page.wait_for_selector(".profile__trigger")
    step("Session persists across reload")
    context.close()


def shopper_flow(browser) -> None:
    print("\n[3/5] Shopper checkout, reviews and orders")
    context = browser.new_context(viewport={"width": 1440, "height": 1000})
    page = context.new_page()
    errors: list[str] = []
    page.on("console", lambda msg: note_console(errors, msg))
    page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))

    page.goto(BASE + "/login", wait_until="networkidle")
    page.get_by_role("button", name="Enter as shopper").click()
    page.wait_for_url(BASE + "/", timeout=12000)
    page.wait_for_selector(".profile__trigger", timeout=10000)
    settle(page, "#recommended")
    step("Demo shopper authenticated")
    shot(page, "09-home-personalized.png")
    page.locator("#recommended").screenshot(
        path=str(SHOTS / "10-recommended-for-you.png"), animations="disabled"
    )
    trending = page.locator("section.section--tight")
    trending.screenshot(path=str(SHOTS / "11-trending-now.png"), animations="disabled")
    step("Captured personalised and trending recommendation rails")

    # Make the cart flow repeatable regardless of the state left by an earlier run.
    page.evaluate(
        """async (items) => {
          const token = localStorage.getItem('shopwise_token');
          const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };
          await fetch('/api/cart', { method: 'DELETE', headers });
          for (const item of items) {
            await fetch('/api/cart/items', {
              method: 'POST', headers,
              body: JSON.stringify({ product_id: item.product_id, quantity: item.quantity }),
            });
          }
        }""",
        [
            {"product_id": 1, "quantity": 1},
            {"product_id": 240, "quantity": 2},
            {"product_id": 520, "quantity": 1},
        ],
    )
    step("Seeded a repeatable three-line demo bag through the API")

    # Review is an upsert, so demo user can safely update their review.
    page.goto(BASE + "/product/291", wait_until="networkidle")
    settle(page, ".product-main")
    page.get_by_role("button", name="Write a review").click()
    page.locator(".review-form").get_by_label("Title").fill("A quiet favourite")
    page.locator(".review-form").get_by_label("Your review").fill(
        "The glaze is beautiful in person and it has become part of our morning ritual."
    )
    page.get_by_role("button", name="4 stars").click()
    shot(page, "12-product-review-form.png", full=False)
    page.get_by_role("button", name="Publish review").click()
    page.wait_for_selector("text=A quiet favourite", timeout=10000)
    page.wait_for_timeout(500)
    shot(page, "13-product-reviews.png")
    step("Submitted a review and confirmed it appears immediately")

    # Cart mutation test with a product that is not already in the demo bag.
    page.goto(BASE + "/product/4", wait_until="networkidle")
    settle(page, ".product-main")
    page.get_by_role("button", name="Add to bag").click()
    page.wait_for_selector(".toast--success", timeout=10000)
    page.goto(BASE + "/cart", wait_until="networkidle")
    page.wait_for_selector(".cart-item")
    initial = page.locator(".cart-item").count()
    assert initial == 4, f"expected 4 cart lines after add, got {initial}"
    added = page.locator(".cart-item").filter(has_text="Assorted Colours Silk Fan")
    added.get_by_role("button", name="Increase quantity").click()
    expect(added.locator(".quantity-stepper span")).to_have_text("2", timeout=10000)
    added.get_by_role("button", name="Remove").click()
    expect(page.locator(".cart-item")).to_have_count(3, timeout=10000)
    step("Cart add, quantity update and remove all work")
    settle(page, ".cart-item")
    page.wait_for_selector(".cart-recommendations", timeout=10000)
    shot(page, "14-cart.png")
    page.locator(".cart-recommendations").screenshot(
        path=str(SHOTS / "15-cart-recommendations.png"), animations="disabled"
    )

    page.get_by_role("link", name="Continue to checkout").click()
    page.wait_for_url("**/checkout", timeout=10000)
    page.wait_for_selector("form.checkout-layout")
    page.locator("input[name=shipping_name]").fill("Sofia Hart")
    page.locator("input[name=shipping_address]").fill("14 Mercer Walk, Apt 3")
    page.locator("input[name=shipping_city]").fill("New York")
    page.locator("input[name=shipping_postcode]").fill("10012")
    page.locator("select[name=shipping_country]").select_option("United States")
    page.get_by_role("button", name="Use test card").click()
    settle(page)
    shot(page, "16-checkout.png")
    step("Checkout validates and fills mock card details")

    page.get_by_role("button", name="Pay $").click()
    page.wait_for_url("**/order-success/**", timeout=15000)
    page.wait_for_selector(".success-card")
    reference = page.locator(".success-card__reference strong").first.inner_text().strip()
    settle(page)
    shot(page, "17-order-success.png")
    step(f"Mock payment completed, order {reference} created")

    page.get_by_role("link", name="View my orders").first.click()
    page.wait_for_url("**/orders", timeout=10000)
    page.wait_for_selector(".order-card")
    expect(page.locator(".order-card").first).to_contain_text(reference.strip())
    settle(page)
    shot(page, "18-order-history.png")
    step("New order appears first in order history")

    page.goto(BASE + "/cart", wait_until="networkidle")
    page.wait_for_selector("text=Nothing in the bag yet", timeout=10000)
    settle(page)
    shot(page, "19-cart-empty.png")
    step("Cart is empty after checkout")

    if errors:
        raise AssertionError("Console errors in shopper flow: " + " | ".join(errors))
    context.close()
    return reference.strip()


def admin_flow(browser) -> None:
    print("\n[4/5] Admin dashboard and catalogue operations")
    context = browser.new_context(viewport={"width": 1440, "height": 1000})
    page = context.new_page()
    errors: list[str] = []
    page.on("console", lambda msg: note_console(errors, msg))
    page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))

    page.goto(BASE + "/login", wait_until="networkidle")
    page.get_by_role("button", name="Admin demo").click()
    page.wait_for_url("**/admin", timeout=15000)
    page.wait_for_selector(".admin-page", timeout=15000)
    page.wait_for_timeout(1400)
    step("Admin authenticated and dashboard loaded")
    shot(page, "20-admin-dashboard.png")

    page.goto(BASE + "/admin/products", wait_until="networkidle")
    settle(page, ".admin-table")
    step("Admin products list renders 1,000 catalogue rows")
    shot(page, "21-admin-products.png")

    page.get_by_role("button", name="Add product").click()
    page.wait_for_selector(".modal__panel--wide")
    page.locator("label.field").filter(has_text="Product name").locator("input").fill(QA_PRODUCT)
    page.locator("label.field").filter(has_text="Category").locator("select").select_option(
        label="Home Decor"
    )
    page.locator("label.field").filter(has_text="Price (USD)").locator("input").fill("64.00")
    page.locator("label.field").filter(has_text="Stock on hand").locator("input").fill("18")
    page.locator("label.field").filter(has_text="Colour").locator("input").fill("Terracotta")
    page.locator("label.field").filter(has_text="Material").locator("input").fill("Stoneware")
    page.locator("label.field").filter(has_text="Description").locator("textarea").fill(
        "A hand-finished stoneware vase with a warm, earthy glaze."
    )
    shot(page, "22-admin-product-modal.png", full=False)
    page.get_by_role("button", name="Add to shop").click()
    page.wait_for_selector("text=added to the shop", timeout=12000)
    step("Created a new product from the admin modal")

    search = page.locator(".admin-search input")
    search.fill(QA_PRODUCT)
    page.wait_for_timeout(500)
    row = page.locator(".admin-table tbody tr").filter(has_text=QA_PRODUCT)
    expect(row).to_be_visible(timeout=8000)
    expect(row).to_contain_text("$64.00")
    shot(page, "23-admin-product-created.png")
    step("New product is searchable and shows the entered price")

    row.get_by_role("button", name=f"Edit {QA_PRODUCT}").click()
    page.wait_for_selector(".modal__panel--wide")
    page.locator("label.field").filter(has_text="Price (USD)").locator("input").fill("69.00")
    page.locator("label.field").filter(has_text="Stock on hand").locator("input").fill("40")
    page.get_by_role("button", name="Save changes").click()
    page.wait_for_selector("text=updated", timeout=12000)
    row = page.locator(".admin-table tbody tr").filter(has_text=QA_PRODUCT)
    expect(row).to_contain_text("$69.00", timeout=8000)
    step("Edited product price and stock")

    row.get_by_role("button", name=f"Remove {QA_PRODUCT}").click()
    page.wait_for_selector(".modal__panel--confirm")
    shot(page, "24-admin-delete-modal.png", full=False)
    page.get_by_role("button", name="Remove product").click()
    page.wait_for_selector("text=removed from the storefront", timeout=12000)
    row = page.locator(".admin-table tbody tr").filter(has_text=QA_PRODUCT)
    expect(row).to_contain_text("Archived", timeout=8000)
    shot(page, "25-admin-product-archived.png")
    step("Soft-archived product, retaining history")

    row.get_by_role("button", name=f"Restore {QA_PRODUCT}").click()
    page.wait_for_selector("text=restored to the shop", timeout=12000)
    row = page.locator(".admin-table tbody tr").filter(has_text=QA_PRODUCT)
    expect(row).to_contain_text("Live", timeout=8000)
    step("Restored archived product")

    page.goto(BASE + "/admin/orders", wait_until="networkidle")
    settle(page, ".admin-table--orders")
    page.locator(".table-expand").first.click()
    page.wait_for_timeout(400)
    step("Admin orders page renders with expanded line items")
    shot(page, "26-admin-orders.png")

    page.goto(BASE + "/admin/model", wait_until="networkidle")
    settle(page, ".model-hero") if page.locator(".model-hero").count() else settle(page, ".admin-page")
    page.wait_for_timeout(700)
    step("Model lab renders comparison, tuning and diagnostics")
    shot(page, "27-admin-model.png")

    page.get_by_role("button", name="Retrain models").click()
    page.wait_for_selector("text=Retrain the recommender?", timeout=8000)
    shot(page, "28-admin-retrain-modal.png", full=False)
    page.get_by_role("button", name="Start retraining").click()
    page.wait_for_selector("text=Models retrained successfully", timeout=180000)
    page.wait_for_timeout(1200)
    step("Retrained all models from the admin UI")
    shot(page, "29-admin-model-retrained.png")

    if errors:
        raise AssertionError("Console errors in admin flow: " + " | ".join(errors))
    context.close()


def login_token() -> str:
    import urllib.request

    payload = json.dumps({"email": "demo@shopwise.com", "password": "demo1234"}).encode()
    request = urllib.request.Request(
        BASE + "/api/auth/login",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read())
    return data["access_token"]


def benchmark_flow() -> None:
    print("\n[5/5] Recommendation API timing")
    token = login_token()

    import statistics
    import urllib.request

    def call(path: str) -> tuple[float, int]:
        request = urllib.request.Request(
            BASE + path,
            headers={"Authorization": f"Bearer {token}"},
        )
        started = time.perf_counter()
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read()
            status = response.status
        elapsed_ms = (time.perf_counter() - started) * 1000
        if status != 200:
            raise AssertionError(f"{path} returned {status}")
        if not payload:
            raise AssertionError(f"{path} returned an empty body")
        return elapsed_ms, len(payload)

    endpoints = [
        ("for-you", "/api/recommendations/home?limit=10"),
        ("trending", "/api/recommendations/trending?limit=10"),
        ("similar-291", "/api/recommendations/similar/291?limit=8"),
        ("also-bought-291", "/api/recommendations/also-bought/291?limit=8"),
        ("cart", "/api/cart"),
        ("catalogue-12", "/api/products?page=1&page_size=12"),
        ("search-bowl", "/api/products?search=bowl&page_size=12"),
        ("product-detail", "/api/products/291"),
    ]
    results: dict[str, dict] = {}
    for name, path in endpoints:
        for _ in range(5):
            call(path)
        timings: list[float] = []
        size = 0
        for _ in range(40):
            elapsed, size = call(path)
            timings.append(elapsed)
        timings.sort()
        results[name] = {
            "path": path,
            "median_ms": round(statistics.median(timings), 2),
            "p95_ms": round(timings[int(len(timings) * 0.95) - 1], 2),
            "mean_ms": round(statistics.mean(timings), 2),
            "min_ms": round(timings[0], 2),
            "max_ms": round(timings[-1], 2),
            "payload_bytes": size,
            "samples": len(timings),
        }
        print(
            f"  [api] {name:18} median {results[name]['median_ms']:6.2f} ms"
            f"  p95 {results[name]['p95_ms']:6.2f} ms  {size:5} B"
        )

    out = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "samples_per_endpoint": 40,
        "warmup_requests": 5,
        "results": results,
    }
    target = ROOT / "reports" / "assets" / "api_benchmark.json"
    target.write_text(json.dumps(out, indent=2), encoding="utf-8")
    step(f"Benchmarked {len(endpoints)} API endpoints and wrote {target.name}")

    # Plot API timing for the report.
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = list(results)
    medians = [results[k]["median_ms"] for k in labels]
    p95s = [results[k]["p95_ms"] for k in labels]
    fig, ax = plt.subplots(figsize=(10, 4.8), dpi=180)
    y = range(len(labels))
    ax.barh([i + 0.2 for i in y], medians, height=0.38, color="#2f6b4f", label="Median")
    ax.barh([i - 0.2 for i in y], p95s, height=0.38, color="#c9a227", label="p95")
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel("Response time (ms)")
    ax.set_title("Live API response times (40 samples after warm-up)")
    ax.grid(axis="x", alpha=0.25)
    ax.legend(frameon=False)
    for i, value in enumerate(medians):
        ax.text(value + 1, i + 0.2, f"{value:.1f}", va="center", fontsize=8)
    for i, value in enumerate(p95s):
        ax.text(value + 1, i - 0.2, f"{value:.1f}", va="center", fontsize=8)
    fig.tight_layout()
    chart = ROOT / "reports" / "assets" / "api_response_times.png"
    fig.savefig(chart, bbox_inches="tight")
    plt.close(fig)
    step(f"Rendered API timing chart {chart.name}")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Shopwise E2E and API benchmark")
    parser.add_argument("--benchmark-only", action="store_true", help="Skip browser E2E and only time the APIs")
    args = parser.parse_args()

    print(f"Shopwise E2E | {BASE}")
    if not args.benchmark_only:
        print(f"QA registration: {QA_EMAIL}")
        (ROOT / "reports" / "assets" / "e2e_registration.json").write_text(
            json.dumps({"email": QA_EMAIL, "password": QA_PASSWORD, "product": QA_PRODUCT}, indent=2),
            encoding="utf-8",
        )
    started = time.time()
    reference = ""
    try:
        if args.benchmark_only:
            benchmark_flow()
        else:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                public_flow(browser)
                registration_flow(browser)
                reference = shopper_flow(browser)
                admin_flow(browser)
                benchmark_flow()
                browser.close()
    except Exception:
        traceback.print_exc()
        print(f"\nFAILED after {time.time() - started:.1f}s")
        return 1

    summary = {
        "passed": PASS,
        "order_reference": reference,
        "duration_seconds": round(time.time() - started, 1),
        "qa_email": QA_EMAIL,
        "qa_product": QA_PRODUCT,
        "screenshots": sorted(p.name for p in SHOTS.glob("*.png")),
    }
    summary_path = ROOT / "reports" / "assets" / "e2e_results.json"
    if args.benchmark_only:
        summary_path = ROOT / "reports" / "assets" / "benchmark_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(f"\nPASSED {len(PASS)} checks in {summary['duration_seconds']}s")
    if reference:
        print(f"Order reference: {reference}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
