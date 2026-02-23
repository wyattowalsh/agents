from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROUTES = [
    "/",
    "/skills/",
    "/skills/honest-review/",
    "/skills/wargame/",
    "/skills/orchestrator/",
    "/skills/mcp-creator/",
    "/skills/installed/",
    "/mcp/",
    "/cli/",
]

VIEWPORTS = {
    "desktop": {"width": 1440, "height": 900},
    "tablet": {"width": 1024, "height": 768},
    "mobile": {"width": 390, "height": 844},
}


def _slug(route: str) -> str:
    if route == "/":
        return "index"
    return route.strip("/").replace("/", "__")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Docs UI screenshot and keyboard smoke harness")
    parser.add_argument("--base-url", required=True, help="Base URL for the docs site (e.g. http://127.0.0.1:4321)")
    parser.add_argument(
        "--out-dir",
        default="artifacts/docs-ui-smoke",
        help="Directory for screenshots and smoke outputs",
    )
    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=45000,
        help="Navigation timeout in milliseconds",
    )
    parser.add_argument(
        "--max-full-page-height",
        type=int,
        default=8000,
        help="Use viewport screenshots when scroll height exceeds this threshold",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # pragma: no cover - helper script
        print("Playwright is not installed for Python in this environment.", file=sys.stderr)
        print("Install it with:", file=sys.stderr)
        print("  uv add --dev playwright", file=sys.stderr)
        print("  uv run playwright install chromium", file=sys.stderr)
        print(f"Import error: {exc}", file=sys.stderr)
        return 2

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            def capture_screenshot(page, path: Path) -> None:
                page_height = 0
                try:
                    page_height = int(page.evaluate("document.body?.scrollHeight || 0"))
                except Exception:
                    page_height = 0

                full_page = page_height <= args.max_full_page_height if page_height > 0 else True
                if not full_page:
                    print(
                        f"[screenshot-mode] {path.name} -> viewport (height={page_height}px exceeds {args.max_full_page_height}px)",
                        flush=True,
                    )

                try:
                    page.screenshot(
                        path=str(path),
                        full_page=full_page,
                        timeout=args.timeout_ms,
                    )
                except PlaywrightTimeoutError:
                    print(f"[screenshot-timeout] {path.name} -> retrying viewport capture", flush=True)
                    page.screenshot(
                        path=str(path),
                        full_page=False,
                        timeout=args.timeout_ms,
                    )

            for viewport_name, viewport in VIEWPORTS.items():
                context = browser.new_context(
                    viewport=viewport,
                    reduced_motion="no-preference",
                    color_scheme="dark",
                )
                reduced_context = browser.new_context(
                    viewport=viewport,
                    reduced_motion="reduce",
                    color_scheme="dark",
                )
                try:
                    page = context.new_page()
                    reduced_page = reduced_context.new_page()

                    for route in ROUTES:
                        url = args.base_url.rstrip("/") + route
                        file_stem = _slug(route)
                        print(f"[{viewport_name}] {route}", flush=True)

                        page.goto(url, wait_until="commit", timeout=args.timeout_ms)
                        page.wait_for_selector("body", state="visible", timeout=args.timeout_ms)
                        page.wait_for_timeout(250)
                        capture_screenshot(page, out_dir / f"{viewport_name}--{file_stem}.png")

                        # Keyboard smoke: page should handle a few tab presses without throwing.
                        page.keyboard.press("Tab")
                        page.keyboard.press("Tab")
                        page.keyboard.press("Tab")
                        page.keyboard.press("Escape")

                        print(f"[{viewport_name}] {route} (reduced-motion)", flush=True)
                        reduced_page.goto(url, wait_until="commit", timeout=args.timeout_ms)
                        reduced_page.wait_for_selector("body", state="visible", timeout=args.timeout_ms)
                        reduced_page.wait_for_timeout(250)
                        capture_screenshot(
                            reduced_page,
                            out_dir / f"{viewport_name}--{file_stem}--reduced-motion.png",
                        )
                finally:
                    context.close()
                    reduced_context.close()
        finally:
            browser.close()

    print(f"Wrote smoke screenshots to {out_dir}")
    return 0


if __name__ == "__main__":  # pragma: no cover - helper script
    raise SystemExit(main())
