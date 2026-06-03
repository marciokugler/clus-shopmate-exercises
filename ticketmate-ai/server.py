#!/usr/bin/env python3
"""TicketMate AI standalone concert ticket assistant."""

from __future__ import annotations

import asyncio
import json
import math
import os
import re
import time
import traceback
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    from openai import AsyncOpenAI
    from agents import Agent, ModelSettings, OpenAIChatCompletionsModel, Runner, function_tool, set_tracing_disabled
except ImportError:  # pragma: no cover - optional lab dependency
    AsyncOpenAI = None
    Agent = None
    ModelSettings = None
    OpenAIChatCompletionsModel = None
    Runner = None
    function_tool = None
    set_tracing_disabled = None


APP_DIR = Path(__file__).resolve().parent
REPO_DIR = APP_DIR.parent
STATIC_DIR = APP_DIR / "static"
EVENTS_PATH = APP_DIR / "data" / "events.json"
POLICIES_PATH = APP_DIR / "data" / "policies.json"

SHOPMATE_NIM_BASE_URL = "http://nim-service.nim-system.svc.cluster.local:8000/v1"
SHOPMATE_NIM_API_KEY = "nim-local-key"
SHOPMATE_NIM_MODEL = "meta/llama-3.2-1b-instruct"


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


for env_path in [
    REPO_DIR / ".env",
    REPO_DIR / ".env.local",
    APP_DIR / ".env",
    APP_DIR / ".env.local",
    REPO_DIR / "shopmate-sports" / ".env",
    REPO_DIR / "shopmate-sports" / ".env.local",
]:
    load_env_file(env_path)

HOST = os.environ.get("TICKETMATE_HOST", "0.0.0.0")
PORT = int(os.environ.get("TICKETMATE_PORT", "8080"))
NIM_BASE_URL = os.environ.get("NIM_BASE_URL", SHOPMATE_NIM_BASE_URL).strip()
NIM_API_KEY = os.environ.get("NIM_API_KEY", SHOPMATE_NIM_API_KEY).strip()
NIM_MODEL = os.environ.get("NIM_MODEL", SHOPMATE_NIM_MODEL).strip()
TICKETMATE_AGENT_MAX_TURNS = int(os.environ.get("TICKETMATE_AGENT_MAX_TURNS", "4"))
TICKETMATE_DISABLE_OPENAI_AGENT_TRACING = (
    os.environ.get("TICKETMATE_DISABLE_OPENAI_AGENT_TRACING", "false").strip().lower() == "true"
)
TICKETMATE_NIM_HEALTH_TIMEOUT = float(os.environ.get("TICKETMATE_NIM_HEALTH_TIMEOUT", "1.5"))

SYSTEM_PROMPT = """You are TicketMate, a workshop assistant for a fictional concert ticket site.
Use only the provided tool results and event context. Do not invent events, prices,
refund rules, payment actions, or real ticket inventory. Keep responses practical
and concise. Never ask for real payment, identity, or private customer information."""


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


EVENT_DATA = load_json(EVENTS_PATH)
POLICY_DATA = load_json(POLICIES_PATH)
EVENTS = EVENT_DATA["events"]
POLICIES = POLICY_DATA["venues"]


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, math.ceil(len(text) / 4))


def tokenize(text: str) -> set[str]:
    return {token.lower() for token in re.findall(r"[a-zA-Z0-9]+", text)}


def event_by_id(event_id: str) -> dict[str, Any] | None:
    for event in EVENTS:
        if event["id"] == event_id:
            return event
    return None


def best_event_for_query(query: str) -> dict[str, Any]:
    terms = tokenize(query)
    scored: list[tuple[int, dict[str, Any]]] = []
    for event in EVENTS:
        haystack = " ".join(
            [
                event["id"],
                event["artist"],
                event["genre"],
                event["city"],
                event["venue"],
                event["summary"],
                " ".join(event["tags"]),
            ]
        ).lower()
        score = sum(2 for term in terms if term in haystack)
        if event["city"].lower() in query.lower():
            score += 3
        if event["genre"].lower() in query.lower():
            score += 3
        scored.append((score, event))
    scored.sort(key=lambda pair: (-pair[0], pair[1]["date"], pair[1]["artist"]))
    return scored[0][1]


def section_by_name(event: dict[str, Any], section_name: str | None) -> dict[str, Any]:
    sections = event.get("sections", [])
    if section_name:
        for section in sections:
            if section["name"].lower() == section_name.lower():
                return section
    return sorted(sections, key=lambda item: item["price"] + item["fees"])[0]


def compact_event(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": event["id"],
        "artist": event["artist"],
        "genre": event["genre"],
        "city": event["city"],
        "venue": event["venue"],
        "date": event["date"],
        "doors": event["doors"],
        "age_limit": event["age_limit"],
        "summary": event["summary"],
        "lowest_total_per_ticket": min(section["price"] + section["fees"] for section in event["sections"]),
        "sections": event["sections"],
    }


def search_events_data(query: str, city: str = "", genre: str = "", max_price: float = 0) -> str:
    query_terms = tokenize(" ".join([query, city, genre]))
    matches = []
    for event in EVENTS:
        haystack = " ".join([event["artist"], event["genre"], event["city"], event["venue"], event["summary"], *event["tags"]]).lower()
        lowest_total = min(section["price"] + section["fees"] for section in event["sections"])
        if city and city.lower() != event["city"].lower():
            continue
        if genre and genre.lower() != event["genre"].lower():
            continue
        if max_price and lowest_total > max_price:
            continue
        score = sum(1 for term in query_terms if term in haystack)
        if score or city or genre or not query_terms:
            matches.append((score, event))
    matches.sort(key=lambda pair: (-pair[0], pair[1]["date"], pair[1]["artist"]))
    if not matches:
        matches = [(0, best_event_for_query(query))]
    return json.dumps({"query": query, "matches": [compact_event(event) for _, event in matches[:4]]}, indent=2)


def check_ticket_inventory_data(event_id: str, quantity: int = 2) -> str:
    event = event_by_id(event_id) or best_event_for_query(event_id)
    sections = []
    for section in event["sections"]:
        sections.append(
            {
                "section": section["name"],
                "available": section["available"],
                "requested_quantity_available": section["available"] >= quantity,
                "price": section["price"],
                "fees": section["fees"],
                "total_per_ticket": section["price"] + section["fees"],
                "notes": section["notes"],
            }
        )
    return json.dumps({"event_id": event["id"], "artist": event["artist"], "quantity": quantity, "sections": sections}, indent=2)


def compare_seat_sections_data(event_id: str, preference: str = "balanced") -> str:
    event = event_by_id(event_id) or best_event_for_query(event_id)
    rows = []
    for section in sorted(event["sections"], key=lambda item: item["price"] + item["fees"]):
        rows.append(
            {
                "section": section["name"],
                "total_per_ticket": section["price"] + section["fees"],
                "availability": section["available"],
                "tradeoff": section["notes"],
            }
        )
    return json.dumps({"event_id": event["id"], "artist": event["artist"], "preference": preference, "sections": rows}, indent=2)


def lookup_venue_policy_data(venue: str, policy_type: str = "refund") -> str:
    matched_venue = venue
    if matched_venue not in POLICIES:
        event = best_event_for_query(venue)
        matched_venue = event["venue"]
    policies = POLICIES.get(matched_venue, {})
    return json.dumps(
        {
            "venue": matched_venue,
            "requested_policy": policy_type,
            "policies": policies,
            "demo_limits": POLICY_DATA.get("limits", []),
        },
        indent=2,
    )


def estimate_total_price_data(event_id: str, section_name: str = "", quantity: int = 2) -> str:
    event = event_by_id(event_id) or best_event_for_query(event_id)
    section = section_by_name(event, section_name)
    per_ticket = section["price"] + section["fees"]
    subtotal = per_ticket * max(quantity, 1)
    return json.dumps(
        {
            "event_id": event["id"],
            "artist": event["artist"],
            "section": section["name"],
            "quantity": quantity,
            "price": section["price"],
            "fees": section["fees"],
            "total_per_ticket": per_ticket,
            "estimated_total": subtotal,
            "note": "Workshop estimate only. No payment or real checkout is available.",
        },
        indent=2,
    )


if function_tool:

    @function_tool
    def search_events(query: str, city: str = "", genre: str = "", max_price: float = 0) -> str:
        """Search fictional concert events by request, city, genre, or max per-ticket price."""
        return search_events_data(query, city, genre, max_price)

    @function_tool
    def check_ticket_inventory(event_id: str, quantity: int = 2) -> str:
        """Check fictional ticket availability by event and requested quantity."""
        return check_ticket_inventory_data(event_id, quantity)

    @function_tool
    def compare_seat_sections(event_id: str, preference: str = "balanced") -> str:
        """Compare fictional seat sections by price, availability, and tradeoff."""
        return compare_seat_sections_data(event_id, preference)

    @function_tool
    def lookup_venue_policy(venue: str, policy_type: str = "refund") -> str:
        """Look up venue refund, transfer, parking, accessibility, and age-limit policies."""
        return lookup_venue_policy_data(venue, policy_type)

    @function_tool
    def estimate_total_price(event_id: str, section_name: str = "", quantity: int = 2) -> str:
        """Estimate fictional total ticket cost including fees for a section and quantity."""
        return estimate_total_price_data(event_id, section_name, quantity)

else:  # pragma: no cover - optional dependency fallback
    search_events = None
    check_ticket_inventory = None
    compare_seat_sections = None
    lookup_venue_policy = None
    estimate_total_price = None


def agents_available() -> bool:
    return all([AsyncOpenAI, Agent, ModelSettings, OpenAIChatCompletionsModel, Runner, function_tool])


def nim_base_url() -> str:
    return NIM_BASE_URL.rstrip("/")


def nim_models_url() -> str:
    return f"{nim_base_url()}/models"


def nim_reachable() -> bool:
    if not nim_base_url():
        return False
    request = Request(nim_models_url(), headers={"Authorization": f"Bearer {NIM_API_KEY or SHOPMATE_NIM_API_KEY}"})
    try:
        with urlopen(request, timeout=TICKETMATE_NIM_HEALTH_TIMEOUT):
            return True
    except HTTPError as exc:
        # Any HTTP response from the model service proves the endpoint is reachable.
        return 400 <= exc.code < 500
    except (OSError, URLError):
        return False


def build_model() -> Any:
    if not agents_available():
        raise RuntimeError("OpenAI Agents SDK dependencies are not installed")
    if not nim_base_url():
        raise RuntimeError("NIM_BASE_URL is not configured")
    if set_tracing_disabled:
        set_tracing_disabled(disabled=TICKETMATE_DISABLE_OPENAI_AGENT_TRACING)
    client = AsyncOpenAI(api_key=NIM_API_KEY or "nim-local-key", base_url=nim_base_url())
    return OpenAIChatCompletionsModel(model=NIM_MODEL, openai_client=client)


def build_agents() -> dict[str, Any]:
    model = build_model()
    settings = ModelSettings(temperature=0.1, max_tokens=280)
    fact_rule = "\n\nAlways call your assigned tool before answering. Keep the output under 120 words."
    return {
        "ConcertFinderAgent": Agent(
            name="ConcertFinderAgent",
            instructions=SYSTEM_PROMPT + fact_rule + "\nUse search_events to find the best matching concerts.",
            model=model,
            model_settings=settings,
            tools=[search_events],
        ),
        "SeatAdvisorAgent": Agent(
            name="SeatAdvisorAgent",
            instructions=SYSTEM_PROMPT + fact_rule + "\nUse compare_seat_sections and check_ticket_inventory before recommending seats.",
            model=model,
            model_settings=settings,
            tools=[compare_seat_sections, check_ticket_inventory],
        ),
        "BudgetAgent": Agent(
            name="BudgetAgent",
            instructions=SYSTEM_PROMPT + fact_rule + "\nUse estimate_total_price to compare the estimated total with the user's budget.",
            model=model,
            model_settings=settings,
            tools=[estimate_total_price],
        ),
        "PolicyAgent": Agent(
            name="PolicyAgent",
            instructions=SYSTEM_PROMPT + fact_rule + "\nUse lookup_venue_policy to explain refund, transfer, parking, accessibility, and age-limit concerns.",
            model=model,
            model_settings=settings,
            tools=[lookup_venue_policy],
        ),
        "CheckoutCoachAgent": Agent(
            name="CheckoutCoachAgent",
            instructions=(
                SYSTEM_PROMPT
                + "\n\nSynthesize the prior specialist outputs into one final recommendation. "
                + "Do not call a checkout or payment action. Include the best event, section, total estimate, and one policy caveat."
            ),
            model=model,
            model_settings=ModelSettings(temperature=0.1, max_tokens=360),
        ),
    }


def format_history(history: list[dict[str, str]]) -> str:
    if not history:
        return ""
    lines = ["Recent conversation:"]
    for item in history[-8:]:
        role = item.get("role", "user")
        content = item.get("content", "")
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def event_context(message: str, payload: dict[str, Any]) -> dict[str, Any]:
    event_id = str(payload.get("event_id") or "").strip()
    event = event_by_id(event_id) if event_id else best_event_for_query(message)
    return compact_event(event or best_event_for_query(message))


def request_context(payload: dict[str, Any]) -> str:
    fields = {
        "scenario": payload.get("scenario", "free-chat"),
        "city": payload.get("city", ""),
        "genre": payload.get("genre", ""),
        "budget": payload.get("budget", ""),
        "tickets": payload.get("tickets", ""),
        "event_id": payload.get("event_id", ""),
    }
    return "\n".join(f"{key}: {value}" for key, value in fields.items() if value not in ("", None))


def extract_usage(result: Any, output: str, prompt: str) -> dict[str, int]:
    prompt_tokens = 0
    completion_tokens = 0
    for response in getattr(result, "raw_responses", []) or []:
        usage = getattr(response, "usage", None)
        if not usage and isinstance(response, dict):
            usage = response.get("usage")
        if not usage:
            continue
        get_value = usage.get if isinstance(usage, dict) else lambda key, default=0: getattr(usage, key, default)
        prompt_tokens += int(get_value("prompt_tokens", 0) or get_value("input_tokens", 0) or 0)
        completion_tokens += int(get_value("completion_tokens", 0) or get_value("output_tokens", 0) or 0)
    if prompt_tokens == 0 and completion_tokens == 0:
        prompt_tokens = estimate_tokens(prompt)
        completion_tokens = estimate_tokens(output)
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    }


async def run_agent(agent: Any, prompt: str) -> tuple[str, dict[str, int]]:
    result = await Runner.run(agent, prompt, max_turns=TICKETMATE_AGENT_MAX_TURNS)
    output = str(result.final_output)
    return output, extract_usage(result, output, prompt)


async def run_ticketmate(payload: dict[str, Any]) -> dict[str, Any]:
    message = str(payload.get("message") or payload.get("task") or "").strip()
    if not message:
        raise ValueError("message is required")

    history = payload.get("history") or []
    selected_event = event_context(message, payload)
    base_context = "\n\n".join(
        part
        for part in [
            format_history(history),
            f"Current user request: {message}",
            request_context(payload),
            "Selected event context:\n" + json.dumps(selected_event, indent=2),
            "Use the current user request as the task. Prior turns are context only.",
        ]
        if part
    )
    agents = build_agents()
    outputs: list[dict[str, Any]] = []
    total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    agent_prompts = [
        ("ConcertFinderAgent", base_context + "\n\nFind the best matching concerts. Call search_events."),
        (
            "SeatAdvisorAgent",
            base_context
            + f"\n\nEvaluate seat sections and inventory for event_id={selected_event['id']}. Call compare_seat_sections and check_ticket_inventory.",
        ),
        (
            "BudgetAgent",
            base_context
            + f"\n\nEstimate total cost for event_id={selected_event['id']} using quantity={payload.get('tickets', 2)}. Call estimate_total_price.",
        ),
        (
            "PolicyAgent",
            base_context
            + f"\n\nExplain venue policies for venue={selected_event['venue']}. Call lookup_venue_policy.",
        ),
    ]

    if payload.get("scenario") == "wrong-tool-call":
        agent_prompts.insert(
            1,
            (
                "SeatAdvisorAgent",
                base_context
                + "\n\nThis request mixes refunds, seat views, parking, and transfer limits. Start with seat comparisons even if policy may be more relevant.",
            ),
        )

    for name, prompt in agent_prompts:
        output, usage = await run_agent(agents[name], prompt)
        outputs.append({"name": name, "output": output, "usage": usage})
        for key in total_usage:
            total_usage[key] += usage[key]

    specialist_summary = "\n\n".join(f"[{item['name']}]\n{item['output']}" for item in outputs)
    final_prompt = "\n\n".join(
        [
            base_context,
            "Specialist outputs:",
            specialist_summary,
            "Produce the final TicketMate recommendation for the user.",
        ]
    )
    final_output, final_usage = await run_agent(agents["CheckoutCoachAgent"], final_prompt)
    outputs.append({"name": "CheckoutCoachAgent", "output": final_output, "usage": final_usage})
    for key in total_usage:
        total_usage[key] += final_usage[key]

    return {
        "reply": final_output,
        "agents": outputs,
        "usage": total_usage,
        "model": NIM_MODEL,
        "nim_enabled": True,
        "selected_event": selected_event,
    }


class TicketMateHandler(SimpleHTTPRequestHandler):
    server_version = "TicketMateAI/0.1"

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
        if self.path == "/healthz":
            self.send_json(
                {
                    "ok": True,
                    "service": "ticketmate-ai",
                    "nim_configured": bool(nim_base_url()),
                    "nim_reachable": nim_reachable(),
                    "nim_base_url": nim_base_url(),
                    "agents_available": agents_available(),
                    "model": NIM_MODEL,
                }
            )
            return
        if self.path == "/api/events":
            self.send_json({"events": [compact_event(event) for event in EVENTS]})
            return
        super().do_GET()

    def do_POST(self) -> None:
        try:
            if self.path not in ("/api/chat", "/api/plan"):
                self.send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
                return
            payload = self.read_json()
            started = time.perf_counter()
            try:
                result = asyncio.run(run_ticketmate(payload))
            except ValueError as exc:
                self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            except Exception as exc:
                traceback.print_exc()
                latency_ms = round((time.perf_counter() - started) * 1000)
                self.send_json(
                    {
                        "error": f"TicketMate model path failed: {type(exc).__name__}: {exc}",
                        "latency_ms": latency_ms,
                        "nim_enabled": False,
                    },
                    HTTPStatus.BAD_GATEWAY,
                )
                return
            result["latency_ms"] = round((time.perf_counter() - started) * 1000)
            self.send_json(result)
        except Exception as exc:  # pragma: no cover - defensive server boundary
            traceback.print_exc()
            self.send_json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)


def main() -> None:
    display_host = "127.0.0.1" if HOST == "0.0.0.0" else HOST
    print(f"TicketMate AI running at http://{display_host}:{PORT}/")
    print(f"NIM configured: {bool(nim_base_url())}")
    print(f"OpenAI Agents SDK available: {agents_available()}")
    ThreadingHTTPServer((HOST, PORT), TicketMateHandler).serve_forever()


if __name__ == "__main__":
    main()
