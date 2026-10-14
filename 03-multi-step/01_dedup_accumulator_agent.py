"""
Lesson 3, Example 1: Agent State — Deduplication, Filtering, and a Hard Stop

An agent already has memory via conversation history (the `messages` list
re-sent and re-read on every call — see Lesson 2). But conversation
history is NOT the only kind of state an agent needs.

This example introduces AGENT STATE — plain Python data that our own code
tracks, which the LLM never directly manipulates — to enforce things an
LLM should not be trusted with doing itself:

  - Deduplication ("have I already shown this job to the user?")
  - Freshness filtering ("posted within the last 24 hours")
  - Counting toward a target ("find AT LEAST 10")

This is a direct rehearsal for the capstone project's requirement:
"search 10 recently posted jobs, no duplicates in last 24 hours."

We call Groq here — same free-tier-friendly idea as Gemini in Lesson 2,
but with much more headroom for iterative development (observed via
response headers: 1000 requests per rolling window, vs. Gemini's
20/day). Groq uses the OpenAI-compatible API shape, a different wire
format than Gemini's own shape — see parse_response() below.

Model choice: we use `qwen/qwen3.8-27b`, not `openai/gpt-oss-20b`. We
tried gpt-oss-20b first and hit a real, repeatable issue: on a second
tool-calling turn, it leaked an internal formatting token
(`<|channel|>commentary`, part of OpenAI's "Harmony" response format)
directly into the tool name, which Groq's own server-side validation
rejected with an HTTP 400 before we even got a response to handle.
Qwen does not use this channel architecture and ran cleanly across
multiple tests. Lesson: evaluate the actual model you plan to use, not
just "the provider" — reliability varies by model, not just by vendor.

Prerequisites:
  - A free Groq API key from https://console.groq.com (no credit card)
  - .env file with: GROQ_API_KEY=your-key-here

Run: python3 03-multi-step/01_dedup_accumulator_agent.py
"""

import json
import os
import random

import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    print("ERROR: Set GROQ_API_KEY in .env file")
    print("Get a free key from: https://console.groq.com")
    exit(1)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "qwen/qwen3.8-27b"

TARGET_COUNT = 10
MAX_STEPS = 8

# Simulates a job board's search index: 12 "fresh" postings (<24h old)
# and 6 "stale" ones (>24h) that must be filtered out regardless of
# relevance. A real search_jobs tool would call Adzuna/Remotive instead.
JOB_POOL = [
    {"id": "J01", "title": "Backend Engineer", "company": "Acme", "posted_hours_ago": 2},
    {"id": "J02", "title": "Data Scientist", "company": "Globex", "posted_hours_ago": 5},
    {"id": "J03", "title": "DevOps Engineer", "company": "Initech", "posted_hours_ago": 8},
    {"id": "J04", "title": "ML Engineer", "company": "Umbrella", "posted_hours_ago": 1},
    {"id": "J05", "title": "Frontend Engineer", "company": "Acme", "posted_hours_ago": 12},
    {"id": "J06", "title": "Platform Engineer", "company": "Hooli", "posted_hours_ago": 3},
    {"id": "J07", "title": "Data Engineer", "company": "Globex", "posted_hours_ago": 20},
    {"id": "J08", "title": "Backend Engineer", "company": "Initech", "posted_hours_ago": 6},
    {"id": "J09", "title": "Site Reliability Engineer", "company": "Hooli", "posted_hours_ago": 9},
    {"id": "J10", "title": "Full Stack Engineer", "company": "Umbrella", "posted_hours_ago": 4},
    {"id": "J11", "title": "Cloud Engineer", "company": "Acme", "posted_hours_ago": 15},
    {"id": "J12", "title": "Backend Engineer", "company": "Hooli", "posted_hours_ago": 7},
    {"id": "J13", "title": "Data Scientist", "company": "Initech", "posted_hours_ago": 30},
    {"id": "J14", "title": "QA Engineer", "company": "Acme", "posted_hours_ago": 48},
    {"id": "J15", "title": "Support Engineer", "company": "Globex", "posted_hours_ago": 36},
    {"id": "J16", "title": "Project Manager", "company": "Umbrella", "posted_hours_ago": 72},
    {"id": "J17", "title": "Recruiter", "company": "Hooli", "posted_hours_ago": 50},
    {"id": "J18", "title": "Sales Engineer", "company": "Initech", "posted_hours_ago": 40},
]

# AGENT STATE — lives in Python, outside the conversation history.
# The LLM never sees these dicts directly, only the text summaries below.
collected: dict[str, dict] = {}


def search_jobs(query: str) -> str:
    """Simulates one call to a job board's search API: a random batch of
    6 postings. Deduplication and the 24h freshness filter are enforced
    HERE, in Python — not left to the LLM to track across the conversation."""
    batch = random.sample(JOB_POOL, 6)

    added = 0
    for job in batch:
        if job["posted_hours_ago"] > 24:
            continue  # enforce "posted in the last 24 hours"
        if job["id"] in collected:
            continue  # enforce "no duplicates"
        collected[job["id"]] = job
        added += 1

    return (
        f"Searched for '{query}'. Found {len(batch)} postings, "
        f"{added} were new, unique, and within 24 hours. "
        f"Total unique qualifying jobs collected so far: {len(collected)}/{TARGET_COUNT}."
    )


def execute_tool(name: str, args: dict) -> str:
    """Execute a tool call defensively. An LLM can supply extra arguments
    the schema never declared, or omit a required one. Blindly doing
    `fn(**args)` turns that into an unhandled TypeError that crashes the
    whole agent. Catching it here converts the mistake into a recoverable
    error string the model can see and adjust to."""
    if name not in TOOL_REGISTRY:
        return f"Error: unknown tool '{name}'"
    try:
        return TOOL_REGISTRY[name](**args)
    except TypeError as e:
        return f"Error calling {name} with args {args}: {e}"


TOOL_REGISTRY = {"search_jobs": search_jobs}

# Groq uses the OpenAI-compatible tool schema shape: {"type": "function",
# "function": {...}}. Note that Groq serializes tool call ARGUMENTS as a
# JSON string, not a dict (see parse_response below) — a real difference
# you need to handle explicitly, not assume is the same as another
# provider's shape.
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_jobs",
            "description": (
                "Search the job board for postings matching a query. Some "
                "returned postings may already be seen or too old — those "
                "are filtered out automatically, and the response tells "
                "you how many NEW qualifying postings were actually added."
            ),
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Search keywords"}},
                "required": ["query"],
            },
        },
    }
]


def call_llm(messages: list) -> dict:
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    body = {"model": MODEL, "messages": messages, "tools": TOOL_SCHEMAS, "tool_choice": "auto"}
    response = requests.post(GROQ_URL, headers=headers, json=body)
    if response.status_code != 200:
        raise RuntimeError(f"Groq error {response.status_code}: {response.text}")
    return response.json()


def parse_response(response: dict) -> tuple[str, list[dict] | None]:
    """Groq's response shape is OpenAI-compatible: message.tool_calls is a
    list of {"id", "function": {"name", "arguments"}} where `arguments`
    is a JSON-encoded STRING that must be parsed with json.loads(), unlike
    Gemini's functionCall.args which is already a dict. Always check the
    actual shape a new provider uses — don't assume it matches one
    you've already seen."""
    message = response["choices"][0]["message"]

    if message.get("tool_calls"):
        tool_calls = [
            {
                "id": tc["id"],
                "name": tc["function"]["name"],
                "args": json.loads(tc["function"]["arguments"]),
            }
            for tc in message["tool_calls"]
        ]
        return "", tool_calls

    return message.get("content", "") or "", None


def looks_like_malformed_tool_call(text: str) -> bool:
    """Defends against a failure mode we hit directly in an earlier
    experiment with a different provider: a model claiming to be "done"
    by emitting what should have been a structured tool call as plain
    text instead. Validate the model's claim that it's finished, exactly
    like we validate dedup/filter state — don't trust it blindly."""
    stripped = text.strip()
    return stripped.startswith("{") and ('"function"' in stripped or '"parameters"' in stripped)


def print_final_results():
    """The actual answer comes from OUR state (`collected`), never from
    whatever the LLM narrates. When precision matters, the agent's code
    — not the model's commentary — is the source of truth."""
    print("\n" + "=" * 60)
    print(f"FINAL RESULT: {len(collected)}/{TARGET_COUNT} unique jobs posted within 24h")
    print("=" * 60)
    for job in sorted(collected.values(), key=lambda j: j["posted_hours_ago"]):
        print(f"  [{job['id']}] {job['title']} at {job['company']} — posted {job['posted_hours_ago']}h ago")


def run_agent(user_query: str):
    print(f"\nUser: {user_query}")
    print("=" * 60)

    messages = [{"role": "user", "content": user_query}]

    for step in range(1, MAX_STEPS + 1):
        # HARD STOP enforced by our code — independent of what the LLM wants.
        if len(collected) >= TARGET_COUNT:
            print(f"\n[Agent loop] Target of {TARGET_COUNT} reached — stopping before calling the model again.")
            break

        print(f"\n--- Step {step} ---")
        print(f"  Calling Groq ({MODEL})...")
        response = call_llm(messages)
        text, tool_calls = parse_response(response)

        if tool_calls is None:
            if looks_like_malformed_tool_call(text) and len(collected) < TARGET_COUNT:
                print(f"  Model emitted a malformed tool-call-like response instead of a real tool call.")
                print(f"  Raw text: {text[:100]}")
                print(f"  Not accepting this as a final answer — nudging the model to retry properly.")
                messages.append({
                    "role": "user",
                    "content": "That was not a valid tool call. Please call the search_jobs "
                                "function using the proper tool-calling mechanism, not plain text.",
                })
                continue
            print(f"  Model decided to stop and answered: {text}")
            break

        print(f"  Model requested {len(tool_calls)} tool call(s):")

        # OpenAI-compatible format: echo the assistant's tool_calls message
        # exactly as received, then one "tool" role message per call,
        # each referencing its call's `id` via tool_call_id.
        messages.append(response["choices"][0]["message"])

        for tc in tool_calls:
            print(f"    -> {tc['name']}({tc['args']})")
            result = execute_tool(tc["name"], tc["args"])
            print(f"       result: {result}")
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})
    else:
        print(f"\n[Agent loop] Hit max steps ({MAX_STEPS}) before reaching the target.")

    print_final_results()


if __name__ == "__main__":
    run_agent(
        f"Search the job board for 'software engineer' jobs and find at least "
        f"{TARGET_COUNT} unique postings from the last 24 hours. Keep searching "
        f"with different queries until you have enough, then summarize them."
    )
