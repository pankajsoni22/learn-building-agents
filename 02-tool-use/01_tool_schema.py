"""
Lesson 2, Example 1: Understanding Tool Schemas

Before calling any LLM, we need to understand HOW we describe our tools
to the model. This file defines tools as plain Python functions, then
shows the JSON schema format that Gemini expects.

NO API calls here — just the data structures. Run this to see the schemas.

Run: python3 02-tool-use/01_tool_schema.py
"""

import json


# --- STEP 1: Define tools as regular Python functions ---
# These are the actual functions our agent can call.
# Each one does something real — interacts with the world.

def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    # In a real agent, this would call a weather API.
    # For learning, we return fake data.
    fake_data = {
        "London": "15°C, cloudy",
        "Tokyo": "22°C, sunny",
        "New York": "18°C, rainy",
    }
    return fake_data.get(city, f"Weather data not available for {city}")


def calculate(expression: str) -> str:
    """Evaluate a math expression and return the result."""
    try:
        result = eval(expression, {"__builtins__": {}})
        return str(result)
    except Exception as e:
        return f"Error: {e}"


# --- STEP 2: Describe tools as JSON schemas ---
# This is what we send to Gemini so it knows what tools exist.
# The LLM never sees our Python code — it only sees these descriptions.
#
# Format: Gemini expects "function declarations" with:
#   - name: what the LLM will use to call the tool
#   - description: helps the LLM decide WHEN to use this tool
#   - parameters: JSON Schema describing the expected arguments

tool_schemas = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a given city. "
                       "Use this when the user asks about weather conditions.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The city name, e.g. 'London' or 'Tokyo'",
                }
            },
            "required": ["city"],
        },
    },
    {
        "name": "calculate",
        "description": "Evaluate a mathematical expression. "
                       "Use this when the user asks to compute something.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "A math expression to evaluate, e.g. '2 + 3 * 4'",
                }
            },
            "required": ["expression"],
        },
    },
]


# --- STEP 3: Build a tool registry ---
# Maps tool names (strings) to actual Python functions.
# When the LLM says "call get_weather", we look it up here.

tool_registry = {
    "get_weather": get_weather,
    "calculate": calculate,
}


# --- STEP 4: Simulate what the LLM would return ---
# When Gemini decides to use a tool, it returns a "function call" object.
# This is NOT a real API response — it's what the response looks like.

simulated_llm_response = {
    "candidates": [
        {
            "content": {
                "parts": [
                    {
                        "functionCall": {
                            "name": "get_weather",
                            "args": {"city": "London"},
                        }
                    }
                ]
            }
        }
    ]
}


def extract_tool_call(response: dict) -> dict | None:
    """Parse the LLM response to extract a tool call, if present.
    Returns {'name': 'tool_name', 'args': {...}} or None."""
    parts = response["candidates"][0]["content"]["parts"]
    for part in parts:
        if "functionCall" in part:
            fc = part["functionCall"]
            return {"name": fc["name"], "args": fc["args"]}
    return None


def execute_tool(tool_call: dict, registry: dict) -> str:
    """Look up the tool in the registry and execute it."""
    name = tool_call["name"]
    args = tool_call["args"]

    if name not in registry:
        return f"Error: unknown tool '{name}'"

    fn = registry[name]
    return fn(**args)


if __name__ == "__main__":
    print("=" * 60)
    print("TOOL SCHEMAS (what we send to Gemini)")
    print("=" * 60)
    print(json.dumps(tool_schemas, indent=2))

    print("\n" + "=" * 60)
    print("SIMULATED LLM RESPONSE (what Gemini sends back)")
    print("=" * 60)
    print(json.dumps(simulated_llm_response, indent=2))

    print("\n" + "=" * 60)
    print("PARSING & EXECUTING THE TOOL CALL")
    print("=" * 60)

    tool_call = extract_tool_call(simulated_llm_response)
    print(f"Extracted tool call: {tool_call}")

    result = execute_tool(tool_call, tool_registry)
    print(f"Tool result: {result}")

    print("\n" + "=" * 60)
    print("TOOL REGISTRY")
    print("=" * 60)
    for name, fn in tool_registry.items():
        print(f"  '{name}' → {fn.__name__}()")
