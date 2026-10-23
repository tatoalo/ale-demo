import time
import uuid
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import assistant, catalog, store
from app.analytics import FAULT_CHECKOUT_500, FAULT_SLOW_CATALOG, flag_on, flags_for_client, posthog
from app.config import settings

BASE = Path(__file__).parent
app = FastAPI(title=settings.app_name)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")
templates.env.filters["price"] = catalog.format_price

CART_COOKIE = "cart_id"


@app.on_event("startup")
def startup() -> None:
    store.init()


def cart_id_of(request: Request) -> str:
    return request.cookies.get(CART_COOKIE) or uuid.uuid4().hex


def distinct_id_of(request: Request) -> str:
    # posthog-js sends its distinct id on every request so server events join the same person.
    return request.headers.get("x-posthog-distinct-id") or request.cookies.get(CART_COOKIE) or "anonymous"


def session_id_of(request: Request) -> str | None:
    return request.headers.get("x-posthog-session-id")


def capture(request: Request, event: str, **properties) -> None:
    """Server event stamped with the browser's session id, so it shows up inside the session replay."""
    session_id = session_id_of(request)
    if session_id:
        properties["$session_id"] = session_id
    posthog.capture(event, distinct_id=distinct_id_of(request), properties=properties)


def render(request: Request, name: str, **ctx) -> HTMLResponse:
    cart_id = cart_id_of(request)
    distinct_id = distinct_id_of(request)
    response = templates.TemplateResponse(
        request,
        name,
        {
            "settings": settings,
            "cart_count": sum(q for _, q in store.items(cart_id)),
            "flags": flags_for_client(distinct_id),
            **ctx,
        },
    )
    response.set_cookie(CART_COOKIE, cart_id, max_age=60 * 60 * 24 * 30, samesite="lax")
    return response


@app.get("/", response_class=HTMLResponse)
def home(request: Request, q: str = ""):
    if flag_on(FAULT_SLOW_CATALOG, distinct_id_of(request)):
        time.sleep(4)  # a planted latency regression for the web vitals and APM scouts
    return render(request, "index.html", products=catalog.search(q), query=q)


@app.get("/p/{slug}", response_class=HTMLResponse)
def product(request: Request, slug: str):
    item = catalog.BY_SLUG.get(slug)
    if item is None:
        return render(request, "404.html", slug=slug)
    capture(request, "product_viewed", slug=slug, price=item.price_cents / 100)
    return render(request, "product.html", product=item)


@app.post("/cart/add", response_class=HTMLResponse)
def cart_add(request: Request, slug: str = Form(...)):
    cart_id = cart_id_of(request)
    store.add(cart_id, slug)
    capture(request, "product_added_to_cart", slug=slug)
    response = render(request, "partials/cart_button.html")
    response.headers["HX-Trigger"] = "cart-updated"
    return response


@app.get("/cart/button", response_class=HTMLResponse)
def cart_button(request: Request):
    return render(request, "partials/cart_button.html")


@app.get("/cart", response_class=HTMLResponse)
def cart(request: Request):
    cart_id = cart_id_of(request)
    return render(request, "cart.html", items=store.items(cart_id), total=store.total_cents(cart_id))


@app.post("/cart/remove")
def cart_remove(request: Request, slug: str = Form(...)):
    store.remove(cart_id_of(request), slug)
    return RedirectResponse("/cart", status_code=303)


@app.get("/checkout", response_class=HTMLResponse)
def checkout(request: Request):
    cart_id = cart_id_of(request)
    capture(request, "checkout_started", total=store.total_cents(cart_id) / 100)
    return render(request, "checkout.html", items=store.items(cart_id), total=store.total_cents(cart_id))


@app.post("/checkout", response_class=HTMLResponse)
def checkout_submit(request: Request, email: str = Form(...)):
    cart_id = cart_id_of(request)
    distinct_id = distinct_id_of(request)
    if flag_on(FAULT_CHECKOUT_500, distinct_id):
        # Planted fault: the payment step dies for everyone in the flag's rollout.
        raise RuntimeError("Payment provider timed out after 30s (gateway=hogpay, step=authorize)")
    order_id, total = store.place_order(cart_id, email)
    capture(
        request, "order_completed", order_id=order_id, revenue=total / 100, currency="USD", email_domain=email.split("@")[-1]
    )
    return render(request, "thanks.html", order_id=order_id, total=total)


@app.post("/assistant", response_class=HTMLResponse)
def assistant_reply(request: Request, message: str = Form(...)):
    distinct_id = distinct_id_of(request)
    capture(request, "assistant_asked", length=len(message))
    try:
        answer = assistant.reply(message, distinct_id, session_id_of(request))
        error = None
    except Exception as exc:  # the provider error is the point: it is captured, then shown
        posthog.capture_exception(exc, distinct_id=distinct_id, properties={"feature": "shop_assistant"})
        answer, error = None, "The assistant is unavailable right now. Try again in a moment."
    return templates.TemplateResponse(request, "partials/assistant_reply.html", {"question": message, "answer": answer, "error": error})


@app.get("/healthz")
def healthz():
    return {"ok": True}
