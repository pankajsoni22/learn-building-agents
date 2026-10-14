# Lesson 3: Multi-Step Reasoning — Agent State, Hard Stops, and Trusting the Model Less

## Overview

Lesson 2 gave the agent memory through conversation history — the `messages` list the LLM re-reads every call. This lesson introduces a second, different kind of memory: **agent state**, plain Python data our own code tracks and the LLM never directly touches. We use it to enforce deduplication, date filtering, and counting toward a target — precision tasks that belong in code, not in a model's "memory" of the conversation. We also add two defensive checks (validating arguments, validating the model's claim that it's "finished") that protect the agent against a model misbehaving, regardless of which provider is behind it. This lesson is a direct rehearsal for the capstone's requirement: *search 10 recently posted jobs, no duplicates in the last 24 hours.*

This lesson runs against **Groq** (`qwen/qwen3.8-27b`), this project's primary LLM provider — see `CLAUDE.md` for why (Gemini's 20/day free-tier quota was too restrictive for iterative development; a brief local-model experiment was also tried and dropped for reliability and resource reasons; a first Groq model, `openai/gpt-oss-20b`, was also dropped after it leaked an internal formatting token into a tool call on a multi-turn request).

## Key Concepts

1. **Agent State vs. Conversation History** — Conversation history (`messages`) is what the LLM reads and re-reads each call. Agent state (e.g. the `collected` dict here) is separate Python data the LLM never sees directly — only text summaries derived from it.
   - *Analogy:* Conversation history is the transcript of a meeting; agent state is the spreadsheet someone keeps off to the side, updated based on what's said, but never handed to every participant to edit themselves.
   - *Why it matters:* Precision tasks — dedup, counting, date math — belong in code, not in the model's "memory" of the conversation. Code either dedupes correctly or it has a bug you can find and fix; a model's internal recollection of "which IDs have I already mentioned" has no such guarantee.

2. **Pushing Bookkeeping Into the Tool, Not the Prompt** — `search_jobs()` deduplicates and filters by freshness *inside its own Python code*, before ever returning text to the model.
   - *Analogy:* Like validating input at the database layer instead of trusting every caller to pass clean data.
   - *Why it matters:* Asking an LLM to "remember which IDs you've already shown me, and don't repeat them" via prompt instructions is fragile — it depends on the model carrying that constraint correctly across every single turn. Making the tool itself enforce the rule means the LLM's only job is deciding *when* to keep searching, a much more appropriate task for a language model.

3. **The Hard Stop** — The loop checks `len(collected) >= TARGET_COUNT` *before* calling the LLM again, independent of whatever the model wants to do.
   - *Analogy:* A factory safety interlock that cuts power once a sensor threshold is hit — it doesn't ask the machine's opinion first.
   - *Why it matters:* If the stop condition only ever came from "the LLM says it's done," a confused or stubborn model could loop forever (burning compute and API quota) or stop too early (incomplete results). A hard, code-enforced condition guarantees termination and correctness regardless of what the model does.

4. **Validate the Model's Claim That It's Finished** — `tool_calls is None` is treated by `parse_response()` as "the model has no more tool calls to make," but that alone doesn't prove the model's text content is a *legitimate, useful* final answer.
   - *Analogy:* An employee saying "I'm done" doesn't make the deliverable correct — you still check the work.
   - *Why it matters:* `looks_like_malformed_tool_call()` is a defensive check: if the "final answer" text looks suspiciously like a broken attempt at a tool call (starts with `{`, contains `"function"` or `"parameters"`) AND we haven't hit our target yet, we don't accept it — we nudge the model to retry properly instead. This generalizes the hard-stop principle from Concept 3: **every exit path from the loop needs validation, not just the happy path.** This specific check never actually triggered in our Groq test runs — both completed cleanly — but the defense costs nothing when unused and protects against a model (any model, any provider) occasionally doing this.

5. **Defensive Argument Handling** — `execute_tool()` wraps `TOOL_REGISTRY[name](**args)` in `try/except TypeError`, converting a model inventing undeclared arguments (or omitting a required one) into a recoverable error string instead of a crash.
   - *Analogy:* A function call with surprise extra keyword arguments is like an HTTP request with unexpected form fields — a robust server validates and rejects/ignores unknown fields rather than crashing.
   - *Why it matters:* An LLM can send arguments your schema never declared. Blindly unpacking them with `**args` raises an unhandled `TypeError` that takes down the whole script. This is the same principle as `calculate()`'s `try/except` in Lesson 2, generalized to *any* tool call through one central dispatch function, rather than relying on each tool to defend itself individually.

6. **A Different Tool-Calling Wire Format (Groq / OpenAI-Compatible)** — Groq's API shape differs from Gemini's in specific, concrete ways.
   - *Analogy:* Two couriers delivering the same package in different box shapes — the contents (a tool call request) are equivalent, but you have to unpack each box differently.
   - *Why it matters:* Groq puts tool calls in `message["tool_calls"]`, a list of `{"id", "function": {"name", "arguments"}}` — but critically, **`arguments` is a JSON-encoded string**, not a dict like Gemini's `functionCall.args`, so it must be parsed with `json.loads()` before use. Sending results back requires echoing the assistant's `tool_calls` message exactly as received, then one `{"role": "tool", "tool_call_id": ..., "content": ...}` message per call — the `tool_call_id` link is Groq/OpenAI-specific; Gemini has no equivalent concept, relying on message order instead. **Never assume a new provider's wire format matches one you've already learned** — check the actual response shape every time (we did, via a direct `curl` and reading the real JSON, which is also how we caught that our assumed model name didn't exist).

7. **Reliability Varies by Model, Not Just by Provider** — Switching from Gemini to Groq (a provider-level change) didn't automatically guarantee reliable tool-calling. The *first* model we tried on Groq, `openai/gpt-oss-20b`, ran cleanly twice, then on a third attempt leaked an internal formatting token (`<|channel|>commentary`, part of its "Harmony" response format) directly into a tool name — Groq's own server rejected it with an HTTP 400 before our code even got a response to validate. Switching to `qwen/qwen3.8-27b` (same provider, different model) resolved it.
   - *Analogy:* Changing car rental companies doesn't guarantee every car in the new company's fleet drives the same way — you still have to test-drive the specific vehicle.
   - *Why it matters:* "We moved to a more reliable provider" is not the same claim as "every model on that provider is reliable." Evaluate the specific model you intend to use in your actual tool-calling scenario (ideally across several runs and several turns — this failure only showed up on a *second* tool-calling turn, not the first), and keep your defensive code (Concepts 4 and 5 above) regardless of how trustworthy a given model has seemed so far.

## How It Works (Step by Step)

```mermaid
flowchart TD
    A[Start: collected = empty dict] --> B{len(collected) >= TARGET?}
    B -->|Yes - HARD STOP| Z[Print final results from collected]
    B -->|No| C[Call LLM with messages]
    C --> D{Response has tool_calls?}
    D -->|No| E{Does text look like a\nmalformed tool call?}
    E -->|Yes, and target not met| F[Nudge model to retry properly]
    F --> B
    E -->|No - genuine final answer| Z
    D -->|Yes| G[For each tool call:\nexecute_tool with try/except]
    G --> H[search_jobs filters by date,\ndedups by ID, updates collected]
    H --> I[Append results to messages]
    I --> B
```

## Code Walkthrough

### File: `01_dedup_accumulator_agent.py`

**Purpose:** An agent that searches a simulated job board until it has collected at least 10 unique postings from the last 24 hours, demonstrating agent state, a hard stop condition, and defensive handling of model misbehavior — regardless of provider.

| Section | What It Does | Why |
|---------|-------------|-----|
| `JOB_POOL` | 18 fake postings, 12 "fresh" (<24h) and 6 "stale" (>24h) | Mirrors the capstone's real job data shape without needing a live API yet |
| `collected: dict[str, dict]` | Module-level agent state, keyed by job ID | A dict keyed by ID gives deduplication "for free" — re-adding the same key just overwrites, never duplicates |
| `search_jobs()` | Draws a random batch, filters by `posted_hours_ago > 24`, filters by `id in collected`, updates `collected`, returns a text summary | All precision logic (filter, dedup, count) lives here in Python — the LLM only ever sees the summary string, never raw data to reason about itself |
| `execute_tool()` | Wraps `TOOL_REGISTRY[name](**args)` in `try/except TypeError` | Defends against the model inventing undeclared arguments — converts a crash into a recoverable error string |
| `looks_like_malformed_tool_call()` | Checks if "final answer" text starts with `{` and contains `"function"`/`"parameters"` | Defends against the model claiming to be done via a broken, half-serialized tool-call string instead of a real answer |
| `call_llm()` / `parse_response()` | Groq-specific request/response handling: `Authorization: Bearer` header, `json.loads()` on `arguments`, `tool_call_id` tracking | Each provider's wire format is a little different — these two functions are the only place that knowledge lives, everything else in the file is provider-agnostic |
| `run_agent()`'s hard stop | `if len(collected) >= TARGET_COUNT: break` *before* calling the LLM | Guarantees termination with correct results regardless of what the model wants to keep doing |
| `print_final_results()` | Builds the final answer entirely from `collected`, never from the model's own narration | The agent's code is the source of truth for the DATA; the LLM's role is deciding strategy, not being trusted with the final count |

**Run it:**
```bash
python3 03-multi-step/01_dedup_accumulator_agent.py
```

**Expected output:** The model issues one or more `search_jobs` calls per step (sometimes several in parallel — see Lesson 2's "Parallel Function Calling"), each with a varied query, the running count climbs toward 10, and the loop stops cleanly at 10 or just above it (parallel batches can overshoot slightly) with a sorted, deduplicated, all-fresh final list. With `qwen/qwen3.8-27b` we observed clean runs reaching the target in 3-4 steps with zero malformed calls or undeclared arguments. An earlier attempt with a different Groq model (`openai/gpt-oss-20b`) and an earlier local-model experiment both hit real reliability issues before we arrived at this combination — see Key Concept 7 and `CLAUDE.md` → "Why Groq, Not a Locally-Run Model" for the specifics.

## Trade-Offs & Alternatives

| Decision We Made | Alternative | Why We Chose This | What We Give Up |
|---|---|---|---|
| Filter/dedup inside the tool function | Ask the LLM to track seen IDs itself via prompt instructions | Precision logic belongs in code we can verify, not in a model's recollection of the conversation | Tool functions carry more logic than a "pure" API wrapper would |
| Hard stop checked between model calls | Check after every individual tool call, even within one batch | Simpler loop structure; the spec is "at least N," which tolerates overshoot | Could overshoot target if a future version issues multiple tool calls per response — would need restructuring for an exact-count spec |
| Reject malformed "final answers" + retry | Accept any `tool_calls is None` response as done | Defends against a known failure mode (a model emitting a broken tool-call string as its answer) at zero cost when it doesn't happen | Risk of a false positive: a legitimate answer that happens to start with `{` would be wrongly rejected (heuristic, not a guarantee — didn't occur in our tests) |
| `try/except TypeError` in `execute_tool()` | Define tool functions with `**kwargs` to silently absorb any extra arguments | Explicit errors are visible and debuggable; silently swallowing bad arguments could mask a real schema mismatch | One extra layer of code around every tool call |
| Groq (`qwen/qwen3.8-27b`) as primary LLM | Stay on Gemini only, run a model locally, or use Groq's `openai/gpt-oss-20b` | Dramatically larger free-tier headroom than Gemini; more reliable tool-calling than both the local experiment and the first Groq model we tried | Requires an internet connection and a separate API key; a different wire format to learn (see Key Concept 6) |

## Common Pitfalls

- **Trusting `tool_calls is None` to always mean "the model is genuinely finished."** Validate the content before accepting it as a real answer, especially while a target/goal hasn't been met yet.
- **Unpacking LLM-supplied arguments directly into a function call** (`fn(**args)`) without a `try/except`. Any model can eventually invent arguments your schema never declared.
- **Letting the LLM own deduplication or counting logic.** If getting the count exactly right matters, that logic belongs in your Python code, not in a prompt instruction hoping the model counts correctly.
- **Assuming a new provider's API shape matches one you already know.** Groq's `arguments` field is a JSON string, not a dict like Gemini's `functionCall.args` — this kind of detail only shows up by actually reading the real response, not by assuming.
- **Forgetting state is global/module-level here for simplicity.** `collected` works fine for a single run of this script, but a real multi-user system would need this state scoped per-request, not as a module global — a simplification intentionally made for teaching clarity.

## Quick Reference

- **Agent state = Python data the LLM never directly edits** (a dict, a set, a counter) — distinct from conversation history.
- **Push precision logic (dedup, filtering, counting) into tool functions**, not into prompts hoping the LLM handles it correctly.
- **Hard stop pattern:** check your real completion condition in code, *before* calling the LLM again — don't rely solely on the LLM deciding to stop.
- **Validate the model's "I'm done" just like you'd validate a tool call** — a text response can itself be malformed or wrong.
- **Wrap tool execution in `try/except`** to survive undeclared/extra arguments from the model.
- **Groq's tool-call `arguments` field is a JSON string — use `json.loads()`.** Echo the assistant's `tool_calls` message back, then one `{"role": "tool", "tool_call_id": ...}` message per call.
- **Always verify a new provider's actual model names and response shape with a real request** — don't trust search results or assumed defaults (we hit a 404 on a model name that had been renamed/retired).

## What's Next

We now have an agent that reliably reaches a target count, using code-enforced state and validation that doesn't depend on which LLM is behind it. In **Lesson 4: Planning & Decomposition**, we'll look at how agents break a complex task into subtasks *before* acting — the ReAct pattern, chain-of-thought prompting for planning, and deciding a strategy upfront rather than reacting one tool call at a time.
