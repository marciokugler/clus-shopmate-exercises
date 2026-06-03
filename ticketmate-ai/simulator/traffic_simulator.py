#!/usr/bin/env python3
"""Generate TicketMate workshop traffic through the public app API."""

from __future__ import annotations

import argparse
import json
import random
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass


PROFILES = {
    "baseline": [
        ["Find two tickets for a pop or rock show under $220 total."],
        ["Help me pick an acoustic concert for a quiet night out."],
        ["Find an all ages concert with the best value seats."],
    ],
    "free-chat": [
        [
            "Plan a concert night for three coworkers with a flexible budget.",
            "Compare the cheapest and most comfortable sections.",
            "Check the refund and transfer policy before we decide.",
        ],
        [
            "I want a high-energy show in any city.",
            "Narrow it to seats that are not the most expensive.",
            "Summarize the final plan for my group.",
        ],
    ],
    "token-surge": [
        [
            "Plan a detailed concert weekend for four people with different music tastes, budgets, seating preferences, accessibility needs, refund concerns, parking constraints, and transfer requirements.",
            "Compare every plausible event and section, explain tradeoffs, include total cost reasoning, and rewrite the recommendation for a group chat.",
            "Now change the budget, keep the accessibility and refund constraints, and produce a final recommendation with backup options.",
        ],
        [
            "Build a complete concert-night plan for a team celebration with pop, jazz, rock, and electronic options across every listed city.",
            "For each option, compare seating quality, ticket availability, refund policy, transfer policy, parking, age restrictions, and estimated cost.",
            "Pick the safest final choice and provide a detailed explanation that a finance reviewer could use.",
        ],
    ],
    "wrong-tool-call": [
        [
            "I care about refunds, transfers, parking, and accessibility, but also tell me if the balcony view is better than the floor.",
            "Before answering the policy question, compare seats and estimate prices again.",
            "Now correct any policy assumptions and explain what evidence changed.",
        ],
        [
            "Can I transfer VIP tickets, park nearby, and avoid obstructed views for a high-demand show?",
            "Use seat comparisons first, then check whether that was the right path.",
        ],
    ],
    "problem-agent-behavior": [
        [
            "Find four front-row tickets under $50 total, refundable, tonight, any city, with VIP parking, all ages, and guaranteed transfer.",
            "Try again but keep every constraint and explain all alternatives in detail.",
            "Give me the closest possible match and list why the impossible parts failed.",
        ],
        [
            "Find premium seats for the cheapest possible price with no fees, full refund, instant transfer, parking included, and no age restriction.",
            "Recheck inventory, policy, and total price because I need every condition satisfied.",
        ],
    ],
}


@dataclass
class WorkerStats:
    requests: int = 0
    errors: int = 0
    tokens: int = 0


def post_json(url: str, payload: dict, timeout: float) -> dict:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def run_worker(args: argparse.Namespace, worker_id: int, stop_at: float, stats: WorkerStats) -> None:
    endpoint = args.target.rstrip("/") + "/api/chat"
    randomizer = random.Random(args.seed + worker_id)
    while time.time() < stop_at:
        conversation = randomizer.choice(PROFILES[args.profile])
        history: list[dict[str, str]] = []
        for turn in conversation:
            if time.time() >= stop_at:
                break
            payload = {
                "message": turn,
                "history": history[-8:],
                "scenario": args.profile,
                "tickets": args.tickets,
                "budget": args.budget,
                "student_id": args.student_id,
                "department": args.department,
                "chargeback_account": args.chargeback_account,
            }
            try:
                response = post_json(endpoint, payload, args.timeout)
                stats.requests += 1
                stats.tokens += int(response.get("usage", {}).get("total_tokens", 0) or 0)
                history.append({"role": "user", "content": turn})
                history.append({"role": "assistant", "content": str(response.get("reply", ""))})
                print(
                    f"worker={worker_id} profile={args.profile} status=ok "
                    f"tokens={response.get('usage', {}).get('total_tokens', 0)}"
                )
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                stats.errors += 1
                print(f"worker={worker_id} profile={args.profile} status=error error={type(exc).__name__}: {exc}")
            time.sleep(args.think_time)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate TicketMate AI workshop traffic.")
    parser.add_argument("--target", default="http://127.0.0.1:8080", help="TicketMate base URL.")
    parser.add_argument("--profile", choices=sorted(PROFILES), default="baseline")
    parser.add_argument("--duration", type=int, default=120, help="Run duration in seconds.")
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--think-time", type=float, default=1.5)
    parser.add_argument("--timeout", type=float, default=90)
    parser.add_argument("--tickets", type=int, default=2)
    parser.add_argument("--budget", type=int, default=250)
    parser.add_argument("--student-id", default="student-01")
    parser.add_argument("--department", default="field-marketing")
    parser.add_argument("--chargeback-account", default="cb-student-01")
    parser.add_argument("--seed", type=int, default=2026)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    stop_at = time.time() + args.duration
    stats = WorkerStats()
    threads = [
        threading.Thread(target=run_worker, args=(args, index + 1, stop_at, stats), daemon=True)
        for index in range(args.concurrency)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    print(
        f"summary profile={args.profile} requests={stats.requests} "
        f"errors={stats.errors} approximate_tokens={stats.tokens}"
    )


if __name__ == "__main__":
    main()
