"""The shop assistant: one LLM call, one product-search tool, traced into PostHog LLM analytics."""

import json
import uuid

from posthog.ai.openai import OpenAI

from app import catalog
from app.analytics import FAULT_ASSISTANT_BAD_MODEL, flag_on, posthog
from app.config import settings

SYSTEM_PROMPT = (
    "You are the shop assistant for Hog Supply Co., a small merch store. "
    "Answer in two or three short sentences. Use the search_products tool before you "
    "recommend anything, and only recommend products the tool returned. Prices are in USD."
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "Search the catalog by free text. Returns matching products with slug, name and price.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Words to match against name, blurb and category."}},
                "required": ["query"],
            },
        },
    }
]


def _client() -> OpenAI:
    return OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url, posthog_client=posthog)


def _run_tool(name: str, arguments: str) -> str:
    if name != "search_products":
        return json.dumps({"error": f"unknown tool {name}"})
    query = json.loads(arguments or "{}").get("query", "")
    hits = catalog.search(query)[:4]
    return json.dumps([{"slug": p.slug, "name": p.name, "price": catalog.format_price(p.price_cents)} for p in hits])


def reply(message: str, distinct_id: str, session_id: str | None) -> str:
    """Answer a shopper. Raises on provider errors so the route can report them."""
    model = settings.llm_model
    if flag_on(FAULT_ASSISTANT_BAD_MODEL, distinct_id):
        model = "gpt-5-turbo-ultra"  # does not exist: the provider answers 404 and the error lands in LLM analytics
    trace_id = str(uuid.uuid4())
    common = {
        "posthog_distinct_id": distinct_id,
        "posthog_trace_id": trace_id,
        "posthog_properties": {"$session_id": session_id, "feature": "shop_assistant"},
    }
    client = _client()
    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": message}]
    first = client.chat.completions.create(model=model, messages=messages, tools=TOOLS, tool_choice="auto", **common)
    choice = first.choices[0].message
    if not choice.tool_calls:
        return choice.content or "I could not find anything for that."
    messages.append(choice)
    for call in choice.tool_calls:
        messages.append(
            {"role": "tool", "tool_call_id": call.id, "content": _run_tool(call.function.name, call.function.arguments)}
        )
    second = client.chat.completions.create(model=model, messages=messages, **common)
    return second.choices[0].message.content or "I could not find anything for that."
