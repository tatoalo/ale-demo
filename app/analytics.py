"""PostHog server-side client and the feature flags that plant faults.

Every fault in this app sits behind a flag so it can be switched on from PostHog during
a demo and off again afterwards, without a deploy.
"""

from posthog import Posthog

from app.config import settings

posthog = Posthog(
    settings.posthog_api_key or "phc_missing",
    host=settings.posthog_host,
    enable_exception_autocapture=True,
    disabled=not settings.posthog_api_key,
)

FAULT_CHECKOUT_500 = "fault-checkout-500"
FAULT_ASSISTANT_BAD_MODEL = "fault-assistant-bad-model"
FAULT_SLOW_CATALOG = "fault-slow-catalog"
FAULT_CART_JS_ERROR = "fault-cart-js-error"
ASSISTANT_ENABLED = "assistant-enabled"

ALL_FLAGS = [FAULT_CHECKOUT_500, FAULT_ASSISTANT_BAD_MODEL, FAULT_SLOW_CATALOG, FAULT_CART_JS_ERROR, ASSISTANT_ENABLED]


def flag_on(key: str, distinct_id: str, default: bool = False) -> bool:
    if not settings.posthog_api_key:
        return default
    try:
        value = posthog.feature_enabled(key, distinct_id)
    except Exception:
        return default
    return default if value is None else bool(value)


def flags_for_client(distinct_id: str) -> dict[str, bool]:
    """All demo flags in one round trip, so a page render costs one flags request, not five."""
    defaults = {key: key == ASSISTANT_ENABLED for key in ALL_FLAGS}
    if not settings.posthog_api_key:
        return defaults
    try:
        remote = posthog.get_all_flags(distinct_id) or {}
    except Exception:
        return defaults
    return {key: bool(remote.get(key, defaults[key])) for key in ALL_FLAGS}
