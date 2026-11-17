"""Render a terminal-style screenshot from the live Shopwise API log."""

from __future__ import annotations

import html
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "reports" / "assets"
SERVER_LOG = Path(
    r"C:\Users\shlok\.local\share\opencode\shell\faa9cd1e410fcd1b25a2cbb08a04662af264e8ed\sh_1d0bf1731001qubrlDwXEVQxdA.out"
)
OUT = ASSETS / "terminal_log.png"


def select_lines(lines: list[str]) -> list[str]:
    """Use genuine backend log slices: startup, shopper journey, admin retrain."""
    selected: list[str] = []
    selected.extend(["Shopwise E2E session - live API log", ""])
    selected.extend(lines[2:3])
    selected.extend(lines[997:1009])
    selected.extend(["...", ""])
    selected.extend(lines[1099:1124])
    selected.extend(["...", ""])
    selected.extend(lines[1171:1177])
    selected.extend(lines[1242:1253])
    selected.extend(["...", ""])
    selected.extend(lines[2019:2021])
    selected.extend(lines[2029:2035])
    return selected


def main() -> None:
    lines = SERVER_LOG.read_text(encoding="utf-8", errors="replace").splitlines()
    content = select_lines(lines)
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "terminal_log.txt").write_text("\n".join(content) + "\n", encoding="utf-8")
    body = html.escape("\n".join(content))
    page_html = f"""<!doctype html>
    <html><body style="margin:0">
    <div id="terminal">
      <div class="bar"><span></span><span></span><span></span><em>Shopwise API - live request log</em></div>
      <pre>{body}</pre>
    </div>
    <style>
      * {{ box-sizing: border-box; }}
      body {{ font-family: "Cascadia Code", Consolas, monospace; }}
      #terminal {{ width: 1240px; background: #101614; color: #d9ece1; }}
      .bar {{ display:flex; align-items:center; gap:7px; padding:10px 14px; background:#1c2621; border-bottom:1px solid #2c3a33; }}
      .bar span {{ width:10px; height:10px; border-radius:50%; background:#4c5d54; }}
      .bar span:nth-child(1) {{ background:#e16a5b; }}
      .bar span:nth-child(2) {{ background:#e3b155; }}
      .bar span:nth-child(3) {{ background:#63c48d; }}
      .bar em {{ margin-left:14px; font-style:normal; color:#8fb2a0; font-size:12px; }}
      pre {{ margin:0; padding:16px 18px 20px; font-size:12px; line-height:1.45; white-space:pre-wrap; }}
    </style>
    </body></html>"""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1240, "height": 900})
        page.set_content(page_html)
        page.wait_for_timeout(250)
        page.locator("#terminal").screenshot(path=str(OUT), animations="disabled")
        browser.close()
    print("saved", OUT)


if __name__ == "__main__":
    main()
