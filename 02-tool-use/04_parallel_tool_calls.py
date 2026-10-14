"""
Lesson 2, Example 4: Parallel Function Calling

Example 3 had a hidden bug: parse_response() returned only the FIRST
functionCall it found in a response, silently dropping any others.

Gemini can return MULTIPLE functionCall parts in a single response when
it determines the calls are independent (don't need each other's results
first) — e.g. "weather in Tokyo, London, and Paris" are three unrelated
lookups. This is called PARALLEL FUNCTION CALLING.

This matters for rate limits: batching 3 tool calls into 1 round trip
instead of 3 means 1 API call instead of 3 — directly fewer requests
against your free-tier quota.

Run: python3 02-tool-use/04_parallel_tool_calls.py
"""

import json
import os

import requests
from dotenv import load_dotenv

from gemini_cache import get_cached, save_to_cache

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    print("ERROR: Set GOOGLE_API_KEY in .env file")
    exit(1)

MODEL = "gemini-3.5-flash-lite"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"


def get_weather(city: str) -> str:
    fake_data = {
        "London": "15°C, cloudy, humidity 78%",
        "Tokyo": "22°C, sunny, humidity 45%",
        "New York": "18°C, rainy, humidity 85%",
        "Paris": "17°C, partly cloudy, humidity 65%",
    }
    return fake_data.get(city, f"No weather data available for {city}")


def calculate(expression: str) -> str:
    try:
        result = eval(expression, {"__builtins__": {}})
        return f"Result: {result}"
    except Exception as e:
        return f"Error evaluating '{expression}': {e}"


TOOL_REGISTRY = {
    "get_weather": get_weather,
    "calculate": calculate,
}

TOOL_SCHEMAS = [
    {
        "function_declarations": [
            {
                "name": "get_weather",
                "description": "Get the current weather for a given city. "
                               "Independent lookups for different cities can be "
                               "requested together.",
                "parameters": {
                    "type": "object",
                    "properties": {"city": {"type": "string", "description": "The city name"}},
                    "required": ["city"],
                },
            },
            {
                "name": "calculate",
                "description": "Evaluate a mathematical expression and return the result.",
                "parameters": {
                    "type": "object",
                    "properties": {"expression": {"type": "string", "description": "A math expression"}},
                    "required": ["expression"],
                },
            },
        ]
    }
]


def call_gemini(messages: list, tools: list) -> dict:
    body = {"contents": messages, "tools": tools}

    # Check the cache first — an identical request (same messages + tools)
    # costs zero quota if we've made it before.
    cached = get_cached(body)
    if cached is not None:
        print("  (served from cache, no API call made)")
        return cached

    response = requests.post(URL, headers={"Content-Type": "application/json"}, json=body)
    if response.status_code != 200:
        raise RuntimeError(f"Gemini API error {response.status_code}: {response.text}")

    result = response.json()
    save_to_cache(body, result)
    return result


def parse_response(response: dict) -> tuple[str, list[dict] | None]:
    """Parse Gemini's response into either final text OR a LIST of tool calls.

    The key fix vs. Example 3: we collect ALL functionCall parts, not just
    the first one. A response is either all-tool-calls or all-text, so we
    check: any functionCall parts present? -> return the full list.
    Otherwise -> return the text.
    """
    parts = response["candidates"][0]["content"]["parts"]

    tool_calls = []
    for part in parts:
        if "functionCall" in part:
            fc = part["functionCall"]
            tool_calls.append({"name": fc["name"], "args": fc["args"], "raw_part": part})

    if tool_calls:
        return "", tool_calls

    for part in parts:
        if "text" in part:
            return part["text"], None

    return "No response from model", None


def run_agent(user_query: str, max_steps: int = 10):
    print(f"\nUser: {user_query}")
    print("=" * 60)

    messages = [{"role": "user", "parts": [{"text": user_query}]}]

    for step in range(1, max_steps + 1):
        print(f"\n--- Step {step} ---")
        print("  Calling Gemini...")
        response = call_gemini(messages, TOOL_SCHEMAS)
        text, tool_calls = parse_response(response)

        # Case 1: final text answer
        if tool_calls is None:
            print(f"  Gemini answered: {text}")
            print("\n" + "=" * 60)
            print(f"Final Answer: {text}")
            return text

        # Case 2: one or more tool calls in THIS SAME response
        print(f"  Gemini requested {len(tool_calls)} tool call(s) in this response:")

        model_parts = []
        response_parts = []

        for tc in tool_calls:
            print(f"    -> {tc['name']}({tc['args']})")

            if tc["name"] not in TOOL_REGISTRY:
                result = f"Error: unknown tool '{tc['name']}'"
            else:
                fn = TOOL_REGISTRY[tc["name"]]
                result = fn(**tc["args"])

            print(f"       result: {result}")

            model_parts.append(tc["raw_part"])
            response_parts.append({
                "functionResponse": {"name": tc["name"], "response": {"result": result}}
            })

        # Batch ALL tool calls from this step into ONE model message,
        # and ALL results into ONE user message — this preserves the
        # 1-API-call-per-step relationship even with multiple tools.
        messages.append({"role": "model", "parts": model_parts})
        messages.append({"role": "user", "parts": response_parts})

    print(f"\nAgent hit max steps ({max_steps}) without finishing.")
    return None


if __name__ == "__main__":
    # Three independent lookups — a good candidate for parallel calling,
    # since none of them depend on each other's result.
    run_agent("What's the weather in Tokyo, London, and Paris? Rank them from warmest to coldest.")
