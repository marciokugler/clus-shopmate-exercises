#!/usr/bin/env python3
"""ShopMate Sports standalone retail/chat app."""

from __future__ import annotations

import json
import math
import os
import time
import traceback
import asyncio
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

try:
    from openai import AsyncOpenAI
    from agents import Agent, OpenAIChatCompletionsModel, Runner, function_tool, set_tracing_disabled
except ImportError:  # pragma: no cover - optional runtime dependency
    AsyncOpenAI = None
    Agent = None
    OpenAIChatCompletionsModel = None
    Runner = None
    function_tool = None
    set_tracing_disabled = None


APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"
CATALOG_PATH = APP_DIR / "data" / "catalog.json"
HOST = os.environ.get("SHOPMATE_HOST", "0.0.0.0")
PORT = int(os.environ.get("SHOPMATE_PORT", "8080"))

NIM_BASE_URL = os.environ.get("NIM_BASE_URL", "").strip()
NIM_API_KEY = os.environ.get("NIM_API_KEY", "").strip()
NIM_MODEL = os.environ.get("NIM_MODEL", "nim-retail-assistant").strip()
SHOPMATE_AGENT_MAX_TURNS = int(os.environ.get("SHOPMATE_AGENT_MAX_TURNS", "6"))
SHOPMATE_DISABLE_OPENAI_AGENT_TRACING = (
    os.environ.get("SHOPMATE_DISABLE_OPENAI_AGENT_TRACING", "true").strip().lower() != "false"
)

SYSTEM_PROMPT = """You are ShopMate, a helpful assistant for a fictional athletic retail store.
Help shoppers choose products from the provided catalog. Be concise, ask a follow-up
question when needed, and avoid medical claims. If a shopper mentions pain or injury,
suggest comfort/stability considerations and recommend they consult a professional
for medical advice. Do not invent products outside the catalog."""


def load_catalog() -> list[dict[str, Any]]:
    with CATALOG_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


CATALOG = load_catalog()


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, math.ceil(len(text) / 4))


def catalog_context() -> str:
    rows = []
    for item in CATALOG:
        rows.append(
            f"- {item['name']} ({item['category']}, {item['audience']}): "
            f"${item['price']:.2f}; stock {item['stock']}; tags {', '.join(item['tags'])}; "
            f"{item['description']}"
        )
    return "\n".join(rows)


def nim_base_url() -> str:
    return NIM_BASE_URL.rstrip("/")


def choose_products(message: str) -> list[dict[str, Any]]:
    terms = {part.lower().strip(".,!?;:") for part in message.split() if len(part) > 2}
    scored: list[tuple[int, dict[str, Any]]] = []
    for product in CATALOG:
        haystack = " ".join(
            [
                product["name"],
                product["category"],
                product["audience"],
                product["description"],
                " ".join(product["tags"]),
                " ".join(product["colors"]),
            ]
        ).lower()
        score = sum(1 for term in terms if term in haystack)
        if "wide" in terms and "Wide" in product.get("widths", []):
            score += 3
        if "cheap" in terms or "under" in terms or "budget" in terms:
            score += max(0, 3 - int(product["price"] // 60))
        if score:
            scored.append((score, product))
    scored.sort(key=lambda pair: (-pair[0], pair[1]["price"]))
    return [product for _, product in scored[:3]] or CATALOG[:3]


def fallback_reply(message: str) -> tuple[str, list[dict[str, Any]]]:
    picks = choose_products(message)
    lines = ["I found a few good matches from the ShopMate Sports catalog:"]
    for product in picks:
        lines.append(
            f"- {product['name']}: {product['description']} "
            f"It is ${product['price']:.2f}, rated {product['rating']}/5, with {product['stock']} in stock."
        )
    lines.append("Tell me your size, preferred color, and whether this is for running, walking, training, or travel.")
    return "\n".join(lines), picks


if function_tool:

    @function_tool
    def search_catalog(query: str) -> str:
        """Search the ShopMate Sports catalog for products relevant to a shopper query."""
        products = choose_products(query)
        return json.dumps(
            [
                {
                    "id": product["id"],
                    "name": product["name"],
                    "category": product["category"],
                    "price": product["price"],
                    "stock": product["stock"],
                    "rating": product["rating"],
                    "description": product["description"],
                    "tags": product["tags"],
                    "widths": product["widths"],
                }
                for product in products
            ]
        )

    @function_tool
    def lookup_store_policy(topic: str) -> str:
        """Return fictional ShopMate Sports policy guidance for shipping, returns, and fit advice."""
        text = topic.lower()
        if "return" in text:
            return "Fictional policy: unused gear can be returned within 30 days with receipt. Worn performance gear can be exchanged within 14 days for fit issues."
        if "shipping" in text or "delivery" in text or "pickup" in text:
            return "Fictional policy: free pickup is available for lab orders over $75. Standard delivery takes 3 to 5 business days."
        if "wide" in text or "fit" in text or "size" in text:
            return "Fictional guidance: runners who need more toe-box room should filter for Wide sizes and compare return flexibility before checkout."
        return "Fictional policy: ask about returns, shipping, pickup, sizing, fit, or product compatibility."


def agents_available() -> bool:
    return all([AsyncOpenAI, Agent, OpenAIChatCompletionsModel, Runner, function_tool])


def build_model() -> Any:
    if not agents_available():
        raise RuntimeError("OpenAI Agents SDK dependencies are not installed")
    if not nim_base_url():
        raise RuntimeError("NIM_BASE_URL is not configured")
    if set_tracing_disabled:
        set_tracing_disabled(disabled=SHOPMATE_DISABLE_OPENAI_AGENT_TRACING)
    client = AsyncOpenAI(api_key=NIM_API_KEY or "nim-local-key", base_url=nim_base_url())
    return OpenAIChatCompletionsModel(model=NIM_MODEL, openai_client=client)


def build_agents() -> Any:
    model = build_model()
    catalog_agent = Agent(
        name="CatalogAgent",
        instructions=(
            "You are a retail catalog specialist. Use search_catalog to find relevant products. "
            "Return concise product recommendations with price, stock, and why each product fits."
        ),
        model=model,
        tools=[search_catalog],
    )
    policy_agent = Agent(
        name="PolicyAgent",
        instructions=(
            "You are a retail policy specialist. Use lookup_store_policy for returns, shipping, pickup, sizing, and fit questions. "
            "Keep answers short and practical."
        ),
        model=model,
        tools=[lookup_store_policy],
    )
    return Agent(
        name="ShoppingAssistantAgent",
        instructions=SYSTEM_PROMPT
        + "\n\nRoute product discovery to CatalogAgent and policy questions to PolicyAgent. "
        + "If a shopper asks a mixed question, use the best specialist and produce one final customer-facing answer.",
        model=model,
        handoffs=[catalog_agent, policy_agent],
        tools=[search_catalog, lookup_store_policy],
    )


def format_history(history: list[dict[str, str]]) -> str:
    if not history:
        return ""
    lines = ["Recent conversation:"]
    for item in history[-8:]:
        role = item.get("role", "unknown")
        content = item.get("content", "")
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


async def call_agents_sdk(message: str, history: list[dict[str, str]]) -> str:
    agent = build_agents()
    agent_input = "\n\n".join(part for part in [format_history(history), f"Current shopper request: {message}"] if part)
    result = await Runner.run(agent, agent_input, max_turns=SHOPMATE_AGENT_MAX_TURNS)
    return str(result.final_output)


def call_nim(message: str, history: list[dict[str, str]]) -> tuple[str, dict[str, int], bool, str | None]:
    if nim_base_url() and agents_available():
        try:
            reply = asyncio.run(call_agents_sdk(message, history))
            return reply, {
                "prompt_tokens": estimate_tokens(message),
                "completion_tokens": estimate_tokens(reply),
                "total_tokens": estimate_tokens(message) + estimate_tokens(reply),
            }, True, None
        except Exception as exc:  # pragma: no cover - fallback keeps lab usable
            reply, _ = fallback_reply(message)
            return reply, {
                "prompt_tokens": estimate_tokens(message),
                "completion_tokens": estimate_tokens(reply),
                "total_tokens": estimate_tokens(message) + estimate_tokens(reply),
            }, False, f"AgentsSDKFallback {type(exc).__name__}: {exc}"

    reply, _ = fallback_reply(message)
    return reply, {
        "prompt_tokens": estimate_tokens(message),
        "completion_tokens": estimate_tokens(reply),
        "total_tokens": estimate_tokens(message) + estimate_tokens(reply),
    }, False, None


class ShopMateHandler(SimpleHTTPRequestHandler):
    server_version = "ShopMateSports/0.1"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format % args}")

    def send_json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def do_GET(self) -> None:
        if self.path == "/api/products":
            self.send_json({"products": CATALOG})
            return
        if self.path == "/healthz":
            self.send_json({"ok": True, "nim_configured": bool(nim_base_url()), "agents_available": agents_available()})
            return
        super().do_GET()

    def do_POST(self) -> None:
        try:
            payload = self.read_json()
            if self.path == "/api/chat":
                started = time.perf_counter()
                message = str(payload.get("message", "")).strip()
                if not message:
                    self.send_json({"error": "message is required"}, HTTPStatus.BAD_REQUEST)
                    return
                history = payload.get("history") or []
                reply, usage, used_nim, error = call_nim(message, history)
                latency_ms = round((time.perf_counter() - started) * 1000)
                recommended = choose_products(message)
                self.send_json(
                    {
                        "reply": reply,
                        "usage": usage,
                        "latency_ms": latency_ms,
                        "nim_enabled": used_nim,
                        "nim_error": error,
                        "recommended_products": recommended,
                    }
                )
                return

            self.send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
        except Exception as exc:  # pragma: no cover - defensive server boundary
            traceback.print_exc()
            self.send_json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)


def main() -> None:
    display_host = "127.0.0.1" if HOST == "0.0.0.0" else HOST
    print(f"ShopMate Sports running at http://{display_host}:{PORT}/")
    print(f"NIM configured: {bool(nim_base_url())}")
    print(f"OpenAI Agents SDK available: {agents_available()}")
    ThreadingHTTPServer((HOST, PORT), ShopMateHandler).serve_forever()


if __name__ == "__main__":
    main()
