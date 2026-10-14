# Lesson 2: Tool Use — Giving the Agent Hands

## What You'll Learn
- How LLMs "call" functions (they don't — they request calls, we execute them)
- Tool schema format (JSON function declarations)
- The tool registry pattern for dispatching calls
- The full round-trip: question → function call → execute → result → answer
- Gemini's thoughtSignature requirement, and parallel function calling
- Why we hit a real free-tier rate limit, and how we worked around it (response caching, switching model variants)

## Prerequisites
- Python 3.10+, `requests` and `python-dotenv` installed
- A free Google Gemini API key from https://aistudio.google.com/apikey, in a `.env` file as `GOOGLE_API_KEY=your-key-here`

## Files

| File | What It Demonstrates | Needs |
|------|---------------------|-----------------|
| `01_tool_schema.py` | Tool schemas, registry, and simulated response parsing | Nothing |
| `02_raw_gemini_call.py` | Single raw HTTP call to Gemini with function calling | Gemini API key |
| `03_agent_with_tools.py` | Complete agent loop: Gemini + tools + multi-step (handles 1 tool call per response) | Gemini API key |
| `04_parallel_tool_calls.py` | Fixes Example 3's gap: batches multiple tool calls from one response into one round trip; adds response caching | Gemini API key |

## How to Run

```bash
# No API key needed — just data structures
python3 02-tool-use/01_tool_schema.py

# Needs GOOGLE_API_KEY in .env
python3 02-tool-use/02_raw_gemini_call.py
python3 02-tool-use/03_agent_with_tools.py
python3 02-tool-use/04_parallel_tool_calls.py
```

## Study Material
See [NOTES.md](NOTES.md) for the full lesson notes.
