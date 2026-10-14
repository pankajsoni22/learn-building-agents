# Lesson 3: Multi-Step Reasoning — Agent State & Hard Stops

## What You'll Learn
- The difference between conversation history (memory) and agent state (bookkeeping your own code owns)
- Why deduplication, date filtering, and counting belong in tool code, not in the LLM's "memory"
- Hard stop conditions enforced by code, independent of what the model wants to keep doing
- Why you must validate a model's claim that it's "finished," not just trust it
- Defensive argument handling so an LLM inventing undeclared arguments doesn't crash your agent
- Groq's OpenAI-compatible tool-calling format (a different wire shape than Gemini's)

## Prerequisites
- Python 3.10+, `requests` and `python-dotenv` installed
- A free Groq API key from https://console.groq.com (no credit card), in `.env` as `GROQ_API_KEY=your-key-here`

## Files

| File | What It Demonstrates |
|------|---------------------|
| `01_dedup_accumulator_agent.py` | Searches a simulated job board until at least 10 unique, recent postings are collected — direct rehearsal for the capstone's core requirement |

## How to Run

```bash
python3 03-multi-step/01_dedup_accumulator_agent.py
```

Each run is somewhat random (job batches are sampled randomly from a fixed pool), so the exact number of steps and query phrasings will vary — but it should reliably reach exactly 10/10 unique, fresh postings.

## Study Material
See [NOTES.md](NOTES.md) for the full lesson notes.
