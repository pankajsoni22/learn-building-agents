"""
Lesson 2, Example 2: Raw HTTP Call to Gemini with Function Calling

This script makes a REAL API call to Google Gemini using raw HTTP (requests).
No SDK — just a POST request, so you see exactly what goes over the wire.

We send:
  1. A user message ("What's the weather in Tokyo?")
  2. Tool declarations (the schemas from Example 1)

Gemini responds with either:
  - A function call (it wants us to run a tool)
  - Or plain text (it answered directly)

Prerequisites:
  - Create a .env file with: GOOGLE_API_KEY=your-key-here
  - Get a free key from: https://aistudio.google.com/apikey

Run: python3 02-tool-use/02_raw_gemini_call.py
"""

import json
import os

import requests
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    print("ERROR: No GOOGLE_API_KEY found.")
    print("Create a .env file with: GOOGLE_API_KEY=your-key-here")
    print("Get a free key from: https://aistudio.google.com/apikey")
    exit(1)

# --- THE MODEL ---
# gemini-2.0-flash is free-tier, fast, and supports function calling.
MODEL = "gemini-3.5-flash-lite"

# --- THE URL ---
# This is the Gemini REST API endpoint. We append the API key as a query param.
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

# --- TOOL DECLARATIONS ---
# Same schemas from Example 1, wrapped in the format Gemini's API expects.
tools = [
    {
        "function_declarations": [
            {
                "name": "get_weather",
                "description": "Get the current weather for a given city.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "The city name, e.g. 'London'",
                        }
                    },
                    "required": ["city"],
                },
            },
            {
                "name": "calculate",
                "description": "Evaluate a mathematical expression.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "A math expression, e.g. '2 + 3 * 4'",
                        }
                    },
                    "required": ["expression"],
                },
            },
        ]
    }
]

# --- THE REQUEST BODY ---
# Gemini expects:
#   - contents: the conversation history (list of messages)
#   - tools: the function declarations
request_body = {
    "contents": [
        {
            "role": "user",
            "parts": [{"text": "What's the weather like in Tokyo right now?"}],
        }
    ],
    "tools": tools,
}

# --- MAKE THE CALL ---
print("=" * 60)
print("REQUEST (what we send to Gemini)")
print("=" * 60)
print(f"POST {URL[:80]}...")
print(f"Body:\n{json.dumps(request_body, indent=2)}")

response = requests.post(
    URL,
    headers={"Content-Type": "application/json"},
    json=request_body,
)

print(f"\nHTTP Status: {response.status_code}")

if response.status_code != 200:
    print(f"Error: {response.text}")
    exit(1)

# --- PARSE THE RESPONSE ---
data = response.json()

print("\n" + "=" * 60)
print("RESPONSE (what Gemini sends back)")
print("=" * 60)
print(json.dumps(data, indent=2))

# --- EXTRACT THE TOOL CALL ---
print("\n" + "=" * 60)
print("EXTRACTED TOOL CALL")
print("=" * 60)

parts = data["candidates"][0]["content"]["parts"]
for part in parts:
    if "functionCall" in part:
        fc = part["functionCall"]
        print(f"Tool:  {fc['name']}")
        print(f"Args:  {fc['args']}")
        print(f"\nGemini didn't answer the question directly.")
        print(f"Instead, it said: 'Call get_weather with city=Tokyo'")
        print(f"Now OUR code would run get_weather('Tokyo'),")
        print(f"get the result, and send it back to Gemini.")
    elif "text" in part:
        print(f"Gemini answered directly: {part['text']}")
