# Learn Building Agents

## Project Purpose

This is a **learning project**, not a production build. The goal is to understand how to design, build, and reason about multi-step AI agents and agentic workflows using Python. Every piece of code written here exists to teach a concept — clarity and understanding come before cleverness or performance.

## Teaching Approach

Act as a knowledgeable technology professor. When introducing any concept or code:

1. **Explain the "why" before the "how"** — why does this pattern exist? What problem does it solve? What would go wrong without it?
2. **Go step by step** — never skip ahead assuming prior knowledge of a library or pattern.
3. **Name every library and method explicitly** — when calling `foo.bar()`, explain what `foo` is, what `bar` does, why we chose this over alternatives, and what it returns.
4. **Show trade-offs** — for every design decision, explain what we gain and what we give up. Compare at least one alternative approach.
5. **Use analogies** — connect agent concepts to familiar software engineering patterns (state machines, pipelines, middleware, etc.).
6. **Build incrementally** — start with the simplest version that works, then layer on complexity one concept at a time.

## Auto-Generated Course Notes

Every concept taught in this project must be automatically logged as structured course notes. Think of this as an EdTech platform producing self-contained study material — someone should be able to read the notes alone and learn the topic without replaying the conversation.

### When to Write Notes

- **After every lesson or concept is taught**, create or update the notes file in that lesson's directory.
- **After every code example is written**, append the annotated walkthrough to the notes.
- Do not wait until the end — log as you go, so the notes grow incrementally alongside the conversation.

### Notes File Format

Each lesson directory contains a `NOTES.md` file with this structure:

```markdown
# Lesson N: <Title>

## Overview
One paragraph: what this lesson covers, why it matters, and what you'll be able to do after completing it.

## Key Concepts
A numbered list of core ideas, each with:
- **Concept Name** — 1-2 sentence explanation in plain language.
- *Analogy:* A familiar software engineering comparison.
- *Why it matters:* What breaks or gets harder without this concept.

## How It Works (Step by Step)
A walkthrough of the mechanism — the flow, the loop, the pattern — written as a numbered sequence with diagrams (ASCII if needed). This is the "textbook explanation" section.

## Code Walkthrough
For each code file in the lesson:
- **File:** `filename.py`
- **Purpose:** What this script demonstrates.
- **Key Lines Explained:** A table or annotated list of the important lines/blocks, what they do, and why they're written that way.
- **Run it:** The exact command to execute, and what output to expect.

## Trade-Offs & Alternatives
A table or comparison list:
| Decision We Made | Alternative | Why We Chose This | What We Give Up |

## Common Pitfalls
Bulleted list of mistakes a beginner would likely make, and how to avoid them.

## Quick Reference
A cheat-sheet section — the 5-10 things worth memorizing from this lesson (method signatures, patterns, mental models). Formatted for fast scanning.

## What's Next
One sentence linking this lesson to the next one — what gap remains that the next lesson fills.
```

### Notes Conventions

- **Language:** Clear, direct, jargon-free where possible. When jargon is necessary, define it on first use.
- **Brevity with completeness:** Cover everything, but don't pad. If a concept takes one sentence to explain well, don't stretch it to a paragraph.
- **Code in notes is annotated:** Never paste raw code without inline comments explaining the non-obvious parts. But keep comments tight — one line max per annotation.
- **Runnable examples:** Every code block in the notes should be copy-pasteable and runnable (or clearly marked as a snippet if not).
- **Progressive:** Notes for Lesson N can reference Lesson N-1 concepts by name but should not require re-reading earlier notes to understand the current one.

### Master Index

Maintain a `notes/INDEX.md` at the project root that serves as a table of contents:

```markdown
# Course Notes — Building Multi-Step Agents

| # | Topic | Status | Key Takeaway |
|---|-------|--------|--------------|
| 1 | Foundations | Done | Agents = LLM + tools + loop |
| 2 | Tool Use | In Progress | ... |
| 3 | Multi-Step Reasoning | Not Started | ... |
```

Update this index every time a lesson's notes are completed or updated.

## Constraints

- **Free tools only.** Every LLM, API, and library used must have a free tier or be fully open source. It is acceptable if a tool is slow — correctness and learning matter more than speed.
- **Avoid rate limiting.** Prefer models and providers with generous free-tier limits. When hitting a rate limit is likely, implement delays, caching, or batching — and explain *why* each mitigation works.
- **Python only.** All code is written in Python 3.10+.
- **No black boxes.** Do not use high-level agent frameworks (like LangChain agents or CrewAI) without first building the equivalent from scratch so the learner understands what the framework abstracts away.

## Curriculum Topics (Planned)

These are the core areas to cover, roughly in order:

1. **Foundations** — What is an agent? How does it differ from a chatbot or a pipeline? The observe-think-act loop.
2. **Tool Use** — How agents call external tools (functions). Designing tool schemas. Parsing and validating LLM tool-call output.
3. **Multi-Step Reasoning** — Loops, state management, and memory across steps. When to stop.
4. **Planning & Decomposition** — How agents break complex tasks into subtasks. ReAct pattern. Chain-of-thought prompting for planning.
5. **Error Handling & Recovery** — What happens when a tool fails, the LLM hallucinates, or the plan is wrong? Retry strategies, fallbacks, and self-correction.
6. **Human-in-the-Loop** — When and how to ask for human input mid-execution. Approval gates.
7. **Multi-Agent Systems** — Orchestrating multiple agents. Delegation, communication, and coordination patterns.
8. **Evaluation & Observability** — How to tell if your agent is working. Logging, tracing, and measuring agent quality.

## Tech Stack

| Component | Tool | Why |
|-----------|------|-----|
| Language | Python 3.10+ | Industry standard for AI/ML, rich ecosystem |
| LLM Provider (primary) | **Groq API** — `qwen/qwen3.8-27b` (free tier) | Verified via `GET /v1/models` on our own key — `llama-3.1-8b-instant` (initially assumed from a web search) returned a 404 on this account; `openai/gpt-oss-20b` worked but leaked an internal format token on a multi-turn tool call (see below). Qwen ran cleanly across multiple tests. Native tool-calling support, no credit card required. |
| LLM Provider (reference/comparison) | Google Gemini API — `gemini-3.5-flash-lite` (free tier) | Used in Lesson 2 Examples 2-4 to learn the tool-calling protocol. Kept as a comparison point — only 20 req/day, but a different model family worth contrasting against. |
| HTTP Client | `requests` or `httpx` | For raw API calls when learning — understand what SDKs abstract |
| Environment | `python-dotenv` | Manage API keys without hardcoding |
| Type Hints | `pydantic` | Validate tool schemas and LLM responses with clear error messages |
| Dev Cache | `02-tool-use/gemini_cache.py` (local disk cache, our own code) | For the Gemini comparison path: identical requests during development cost zero quota on repeat runs |

*This stack may evolve as we progress through topics. Any change will be explained.*

### Why Groq, Not a Locally-Run Model

We briefly ran `llama3.1:8b` locally via Ollama (installed without sudo under `~/.local/`) as an experiment in zero-rate-limit inference. It worked, but repeatedly proved unreliable for tool-calling in ways Gemini never did across any test: it hallucinated invalid extra tool calls, invented undeclared arguments causing a crash, and once returned a malformed half-serialized tool-call string as if it were a finished answer. It also held ~5.5GB of RAM resident even when idle. **We removed the local setup entirely** (no Ollama install, model files, or related scripts remain in this project) and moved to Groq, which hosts the same Llama 3.1 family at full precision with a far more generous free tier than Gemini and much better observed tool-calling reliability than the local quantized build.

### Verified Gemini Free-Tier Rate Limits (observed, not assumed)

We initially assumed "generous" free-tier limits. Reality, confirmed by hitting a 429 during Lesson 2:

- **20 requests/day, per project, per model** (`GenerateRequestsPerDayPerProjectPerModel-FreeTier`) — this is per exact model name, so `gemini-3.5-flash` and `gemini-3.5-flash-lite` have *separate* 20/day buckets.
- The quota resets roughly 24h after first use that day — the 429 error body includes an exact `retryDelay` in seconds.
- **Every script run during development counts.** Debugging the same example 5 times costs 5x quota, even for identical requests — this is why we built the local response cache.
- **Mitigation strategy if using Gemini:** use the local disk cache (`gemini_cache.py`) during development/debugging so re-running a script doesn't re-spend quota; switch model name (e.g. `-lite` variant) if a bucket is exhausted.

### Verified Groq Free-Tier Rate Limits (observed directly on our own key, Oct 2026)

A web search initially suggested `llama-3.1-8b-instant` with 14,400 requests/day — **this model does not exist on our account** (confirmed via a direct `GET https://api.groq.com/openai/v1/models` call, which is the only way to know for certain; always verify against your own key rather than trusting a generic search result). The actual chat-capable models available on this key: `qwen/qwen3.8-27b`, `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `allam-2-7b`.

We tried `openai/gpt-oss-20b` first — 2/2 clean runs initially, but a 3rd run hit a real, repeatable issue: on a second tool-calling turn, it leaked an internal formatting token (`<|channel|>commentary`, part of OpenAI's "Harmony" response format used by gpt-oss models) directly into the tool name, which Groq's own server-side validation rejected with an HTTP 400. We switched to **`qwen/qwen3.8-27b`**, which does not use this channel architecture and ran cleanly across all tests, including one with 4 parallel tool calls in a single response.

Response headers from a real request (consistent across both models tried):
- `x-ratelimit-limit-requests: 1000`, resetting on a rolling window of a few minutes — not a once-a-day cap like Gemini's. Dramatically more headroom for iterative development than Gemini's 20/day.
- No credit card required for the free tier.
- Native tool/function calling support — Groq uses an OpenAI-compatible API format (different wire shape than Gemini — see `03-multi-step/NOTES.md` for the specifics).

**Lesson learned:** reliability varies by *model*, not just by *provider*. Moving to Groq fixed the local-model reliability problems, but the first model we tried on Groq had its own distinct failure mode. Always test the specific model you plan to use, and keep defensive error handling regardless of how reliable a provider seems.

## Code Conventions

- Every script should be runnable standalone with `python <filename>.py`.
- Use type hints everywhere — they serve as documentation.
- Print intermediate steps (observations, thoughts, actions) to stdout so the learner can see the agent's reasoning at each step.
- Keep each lesson in its own directory: `01-foundations/`, `02-tool-use/`, etc.
- Include a `README.md` in each lesson directory summarizing what it teaches and how to run it.
- **All diagrams must use Mermaid syntax** (```mermaid code blocks). No ASCII art diagrams. Mermaid renders natively on GitHub and in most Markdown viewers, keeping diagrams version-controlled, editable, and consistent across all notes.

## File Structure

```
learn-building-agents/
├── CLAUDE.md                  # This file — project context and conventions
├── .env.example               # Template for API keys (never commit real keys)
├── requirements.txt           # Python dependencies
├── notes/
│   └── INDEX.md               # Master table of contents for all course notes
├── 01-foundations/
│   ├── NOTES.md               # Course notes for this lesson
│   ├── README.md              # How to run this lesson
│   └── *.py                   # Code examples
├── 02-tool-use/
│   ├── NOTES.md
│   ├── README.md
│   └── *.py
├── 03-multi-step/
│   ├── NOTES.md
│   ├── README.md
│   └── *.py
├── 04-planning/
│   ├── NOTES.md
│   ├── README.md
│   └── *.py
├── 05-error-handling/
│   ├── NOTES.md
│   ├── README.md
│   └── *.py
├── 06-human-in-the-loop/
│   ├── NOTES.md
│   ├── README.md
│   └── *.py
├── 07-multi-agent/
│   ├── NOTES.md
│   ├── README.md
│   └── *.py
└── 08-evaluation/
    ├── NOTES.md
    ├── README.md
    └── *.py
```

## Capstone Project: Resume-Based Job Search Agent

Everything we learn across 8 lessons builds toward this agent:

**What it does:** Accepts a resume (PDF/text), extracts the candidate's profile, searches free job APIs for recently posted matching jobs, deduplicates, ranks them by fit, and presents the top 10 results with match reasoning.

**Agent Flow:**
1. Parse resume → extract skills, title, experience, location (LLM)
2. Generate search queries from extracted profile (LLM)
3. Call job search APIs with those queries (Tools: Adzuna + Remotive)
4. Filter to last 24 hours, deduplicate across sources (Python logic)
5. Rank/match results against resume profile (LLM)
6. Present top 10 with match explanations

**Free APIs Used:**
| API | What It Provides | Limit |
|-----|-----------------|-------|
| Adzuna | Broad job listings, multiple countries | 250 req/day (free) |
| Remotive | Remote-only job listings | Unlimited (no key) |

**Which lessons map to which parts:**
| Agent Step | Lesson |
|------------|--------|
| Resume parsing (LLM call) | 01-Foundations, 02-Tool Use |
| Query generation | 04-Planning |
| API calls as tools | 02-Tool Use |
| Filtering & dedup | 03-Multi-Step |
| Error recovery (API down, bad parse) | 05-Error Handling |
| "Approve these results?" flow | 06-Human-in-the-Loop |
| Splitting parse/search/rank across agents | 07-Multi-Agent |
| Measuring match quality | 08-Evaluation |

## Important Reminders

- **Never commit API keys.** Use `.env` files and add `.env` to `.gitignore`.
- **Explain before coding.** Every new file should start with a conversation explaining the concept, then move to implementation.
- **The learner is a software engineer** — use proper engineering vocabulary, don't oversimplify, but don't assume ML/AI background beyond basics.
- **When showing LLM API calls**, first show the raw HTTP request/response so the learner understands the protocol, then introduce SDK convenience methods.
