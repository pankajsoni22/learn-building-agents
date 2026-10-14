"""
Lesson 1, Example 1: The Agent Loop — No LLM, Just the Pattern

This script demonstrates the Observe-Think-Act loop using a simple
number-guessing game. The "agent" tries to guess a secret number.

There is NO LLM here. The "thinking" is a basic algorithm (binary search).
The point is to see the STRUCTURE of an agent — the loop, the tools,
the decision-making — before we replace the "brain" with an LLM.

Run: python 01_simple_loop_agent.py
"""

import random


# --- TOOLS ---
# Tools are functions the agent can call to interact with the world.
# Each tool takes input and returns an observation (a string the agent reads).

def guess_checker(guess: int, secret: int) -> str:
    """Tool: checks a guess against the secret number.
    Returns a string observation — 'too high', 'too low', or 'correct'."""
    if guess < secret:
        return "too low"
    elif guess > secret:
        return "too high"
    else:
        return "correct"


# --- THINK FUNCTION ---
# This is where the "brain" lives. Right now it's a simple algorithm.
# In later lessons, this becomes an LLM call.

def think(observation: str, state: dict) -> dict:
    """Decide what to do next based on the observation and current state.
    Returns an action dict: {'tool': 'guess_checker', 'args': {'guess': N}}
    or {'tool': 'done', 'args': {'answer': N}} when finished."""

    if observation == "correct":
        return {"tool": "done", "args": {"answer": state["last_guess"]}}

    if observation == "too low":
        state["low"] = state["last_guess"] + 1
    elif observation == "too high":
        state["high"] = state["last_guess"] - 1

    next_guess = (state["low"] + state["high"]) // 2
    state["last_guess"] = next_guess
    return {"tool": "guess_checker", "args": {"guess": next_guess}}


# --- AGENT LOOP ---
# This is the core pattern: observe → think → act → repeat.

def run_agent(secret: int):
    """Run the agent loop until the task is complete."""

    # Initial state
    state = {"low": 1, "high": 100, "last_guess": 50}
    observation = "start"  # First observation is just "begin the task"
    step = 0
    max_steps = 20  # Safety limit — prevent infinite loops

    print(f"Secret number is: {secret}")
    print(f"Agent starts guessing between 1 and 100\n")

    while step < max_steps:
        step += 1

        # THINK: decide what to do next
        action = think(observation, state)
        print(f"Step {step}:")
        print(f"  Observation: {observation}")
        print(f"  Action:      {action}")

        # CHECK: are we done?
        if action["tool"] == "done":
            print(f"\nAgent finished in {step} steps!")
            print(f"Answer: {action['args']['answer']}")
            return

        # ACT: execute the chosen tool
        if action["tool"] == "guess_checker":
            observation = guess_checker(
                guess=action["args"]["guess"],
                secret=secret,
            )
        else:
            print(f"  Unknown tool: {action['tool']}")
            break

    print(f"\nAgent hit max steps ({max_steps}) without finishing.")


if __name__ == "__main__":
    secret_number = random.randint(1, 100)
    run_agent(secret_number)
