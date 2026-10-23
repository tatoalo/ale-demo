"""Drive realistic shopper sessions through a real browser so replay, web vitals,
autocapture and the assistant all see traffic before a live audience arrives.

    pip install playwright && playwright install chromium
    python scripts/traffic.py --base-url https://ale-demo.fly.dev --sessions 20
"""

import argparse
import random
import time

from playwright.sync_api import sync_playwright

QUESTIONS = [
    "What goes well with cold brew?",
    "Do you have anything warm?",
    "Cheapest thing you sell?",
    "I need a gift for a data engineer",
    "Something for my desk",
]


def one_session(browser, base_url: str, rng: random.Random) -> None:
    context = browser.new_context(viewport={"width": rng.choice([1280, 1440, 390]), "height": 900})
    page = context.new_page()
    page.goto(base_url, wait_until="networkidle")
    time.sleep(rng.uniform(1, 3))
    if rng.random() < 0.7:
        page.click("article.card h3 a >> nth=%d" % rng.randrange(8))
        page.wait_for_load_state("networkidle")
        time.sleep(rng.uniform(1, 2))
        if rng.random() < 0.8:
            page.click("button[data-attr=add-to-cart]")
            time.sleep(1)
    if rng.random() < 0.5:
        page.fill("#assistant input[name=message]", rng.choice(QUESTIONS))
        page.click("#assistant button[type=submit]")
        time.sleep(rng.uniform(4, 8))
    if rng.random() < 0.5:
        page.goto(base_url + "/cart", wait_until="networkidle")
        if page.query_selector("a[data-attr=go-to-checkout]"):
            page.click("a[data-attr=go-to-checkout]")
            page.wait_for_load_state("networkidle")
            if rng.random() < 0.7:
                page.fill("input[name=email]", f"shopper{rng.randrange(10_000)}@example.com")
                page.click("button[data-attr=pay]")
                page.wait_for_load_state("networkidle")
    time.sleep(rng.uniform(1, 2))
    context.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--sessions", type=int, default=10)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()
    rng = random.Random(args.seed)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for i in range(args.sessions):
            try:
                one_session(browser, args.base_url.rstrip("/"), rng)
                print(f"session {i + 1}/{args.sessions} done")
            except Exception as exc:  # a planted fault is supposed to break some sessions
                print(f"session {i + 1} hit: {exc}")
        browser.close()


if __name__ == "__main__":
    main()
