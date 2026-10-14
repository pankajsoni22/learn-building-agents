"""
Lesson 2, Example 3: Complete Agent Loop with Gemini + Tools

This brings everything together:
  - The agent loop from Lesson 1
  - Tool schemas and registry from Example 1
  - Real Gemini API calls from Example 2

The agent can use tools (get_weather, calculate) and loops until
it has enough information to give a final text answer.

Run: python3 02-tool-use/03_agent_with_tools.py
"""

import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    print("ERROR: Set GOOGLE_API_KEY in .env file")
    exit(1)

MODEL = "gemini-3.5-flash-lite"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"


# ============================================================
# TOOLS: the functions our agent can call
# ============================================================

def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    fake_data = {
        "London": "15°C, cloudy, humidity 78%",
        "Tokyo": "22°C, sunny, humidity 45%",
        "New York": "18°C, rainy, humidity 85%",
        "Paris": "17°C, partly cloudy, humidity 65%",
    }
    return fake_data.get(city, f"No weather data available for {city}")


def calculate(expression: str) -> str:
    """Evaluate a math expression safely."""
    try:
        result = eval(expression, {"__builtins__": {}})
        return f"Result: {result}"
    except Exception as e:
        return f"Error evaluating '{expression}': {e}"


# ============================================================
# TOOL REGISTRY: maps name → function
# ============================================================

TOOL_REGISTRY = {
    "get_weather": get_weather,
    "calculate": calculate,
}

# ============================================================
# TOOL SCHEMAS: what we tell Gemini about our tools
# ============================================================

TOOL_SCHEMAS = [
    {
        "function_declarations": [
            {
                "name": "get_weather",
                "description": "Get the current weather for a given city. "
                               "Returns temperature, conditions, and humidity.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "The city name",
                        }
                    },
                    "required": ["city"],
                },
            },
            {
                "name": "calculate",
                "description": "Evaluate a mathematical expression and return the result.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "A math expression, e.g. '(5 + 3) * 2'",
                        }
                    },
                    "required": ["expression"],
                },
            },
        ]
    }
]


# ============================================================
# GEMINI API CALL: send messages + tools, get response
# ============================================================

def call_gemini(messages: list, tools: list) -> dict:
    """Make a single API call to Gemini.

    Args:
        messages: conversation history in Gemini's format
        tools: function declarations

    Returns:
        The raw API response as a dict
    """
    body = {"contents": messages, "tools": tools}
    response = requests.post(
        URL,
        headers={"Content-Type": "application/json"},
        json=body,
    )

    if response.status_code != 200:
        raise RuntimeError(f"Gemini API error {response.status_code}: {response.text}")

    return response.json()


# ============================================================
# RESPONSE PARSING: extract tool calls or text from response
# ============================================================

def parse_response(response: dict) -> tuple[str, dict | None]:
    """Parse Gemini's response into either text or a tool call.

    Returns:
        (text, None) if Gemini answered with text
        ("", tool_call_dict) if Gemini wants to call a tool

    When returning a tool call, the dict includes the raw 'part' from the
    response so we can echo it back exactly — Gemini requires a
    'thoughtSignature' field to be preserved across the round-trip.
    """
    parts = response["candidates"][0]["content"]["parts"]
    print(f"Response: {response}")
    for part in parts:
        if "functionCall" in part:
            fc = part["functionCall"]
            return "", {
                "name": fc["name"],
                "args": fc["args"],
                "raw_part": part,
            }
        if "text" in part:
            return part["text"], None

    return "No response from model", None


# ============================================================
# AGENT LOOP: the core observe → think → act cycle
# ============================================================

def run_agent(user_query: str, max_steps: int = 10):
    """Run the agent loop until Gemini gives a final text answer."""

    print(f"\nUser: {user_query}")
    print("=" * 60)

    # Start the conversation with the user's message
    messages = [
        {"role": "user", "parts": [{"text": user_query}]},
    ]

    for step in range(1, max_steps + 1):
        print(f"\n--- Step {step} ---")

        # THINK: ask Gemini what to do
        print("  Calling Gemini...")
        response = call_gemini(messages, TOOL_SCHEMAS)
        text, tool_call = parse_response(response)

        # Case 1: Gemini answered with text → we're done
        if text and tool_call is None:
            print(f"  Gemini answered: {text}")
            print("\n" + "=" * 60)
            print(f"Final Answer: {text}")
            return text

        # Case 2: Gemini wants to call a tool
        if tool_call:
            print(f"  Gemini wants to call: {tool_call['name']}({tool_call['args']})")

            # ACT: execute the tool
            if tool_call["name"] not in TOOL_REGISTRY:
                tool_result = f"Error: unknown tool '{tool_call['name']}'"
            else:
                fn = TOOL_REGISTRY[tool_call["name"]]
                tool_result = fn(**tool_call["args"])

            print(f"  Tool result: {tool_result}")

            # OBSERVE: add the tool call and result to conversation history
            # so Gemini can see what happened.
            # We echo back the raw part (including thoughtSignature) —
            # Gemini requires this for verifying the call came from its reasoning.
            messages.append({
                "role": "model",
                "parts": [tool_call["raw_part"]],
            })
            messages.append({
                "role": "user",
                "parts": [{"functionResponse": {"name": tool_call["name"], "response": {"result": tool_result}}}],
            })

    print(f"\nAgent hit max steps ({max_steps}) without finishing.")
    return None


# ============================================================
# MAIN: try different queries to see the agent in action
# ============================================================

if __name__ == "__main__":
    queries = [
        "What's the weather in Tokyo and London? Which city is warmer?",
        "What is 15 * 7 + 23?",
    ]

    for query in queries:
        print("\n" + "#" * 60)
        run_agent(query)
        print()
