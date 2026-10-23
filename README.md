# Hog Supply Co.

A small merch shop with an AI assistant, built to demo PostHog's self-driving pipeline: signals from error tracking, session replay, LLM analytics and GitHub issues turn into inbox reports, research, and pull requests on this repository.

## Run it

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in the PostHog token and an LLM key
set -a; . ./.env; set +a
uvicorn app.main:app --reload
```

## What is instrumented

- `posthog-js` on every page: pageviews, autocapture, session replay, web vitals, exception autocapture.
- `posthog-python` on the server: `product_viewed`, `product_added_to_cart`, `checkout_started`, `order_completed` (with `revenue`), `assistant_asked`, and captured exceptions.
- The assistant's LLM calls go through the PostHog OpenAI wrapper, so each question is a trace with a tool-call span in LLM analytics.
- HTMX requests carry the browser's distinct id and session id, so server events join the same person and session.

## Planted faults

Each fault is a PostHog feature flag, off by default. Switch one on in PostHog, use the shop, switch it off.

| Flag | What breaks |
| --- | --- |
| `fault-checkout-500` | Paying throws a server error. Error tracking, replay vision. |
| `fault-assistant-bad-model` | The assistant asks the provider for a model that does not exist. LLM analytics error patterns. |
| `fault-slow-catalog` | The home page takes four extra seconds. Web vitals, latency scouts. |
| `fault-cart-js-error` | Add to cart throws in the browser. Exception autocapture with a replay. |
| `assistant-enabled` | Not a fault. Hides the assistant when off. |

## Access

Set `SHOP_PASSWORD` (and optionally `SHOP_USER`, default `hog`) to put the whole shop behind HTTP basic auth, so the assistant does not spend LLM credit between demos. Leave it unset to open the shop. `/healthz` is always open.

## Traffic

`scripts/traffic.py` drives shopper sessions through headless Chromium against any base URL.

## Deploy

`fly.toml` and the `Dockerfile` deploy to Fly.io. Set `POSTHOG_API_KEY`, `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` and `SHOP_PASSWORD` as Fly secrets.
