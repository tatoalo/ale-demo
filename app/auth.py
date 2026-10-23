"""HTTP basic auth in front of the whole shop.

The assistant spends LLM credit on every question, so outside of a demo the shop is closed to
everyone but the presenter. Set SHOP_PASSWORD to lock it; leave it empty to open the shop.
The Fly health check stays open either way.
"""

import base64
import secrets

from starlette.types import ASGIApp, Receive, Scope, Send

from app.config import settings

OPEN_PATHS = {"/healthz"}


class BasicAuthMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not settings.shop_password or scope["path"] in OPEN_PATHS:
            await self.app(scope, receive, send)
            return
        if self.authorized(dict(scope["headers"]).get(b"authorization", b"")):
            await self.app(scope, receive, send)
            return
        await send(
            {
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    (b"www-authenticate", b'Basic realm="Hog Supply Co."'),
                    (b"content-type", b"text/plain; charset=utf-8"),
                ],
            }
        )
        await send({"type": "http.response.body", "body": b"The shop is closed. Sign in to browse."})

    @staticmethod
    def authorized(header: bytes) -> bool:
        scheme, _, encoded = header.partition(b" ")
        if scheme.lower() != b"basic":
            return False
        try:
            user, _, password = base64.b64decode(encoded, validate=True).decode().partition(":")
        except (ValueError, UnicodeDecodeError):
            return False
        return secrets.compare_digest(user, settings.shop_user) and secrets.compare_digest(password, settings.shop_password)
