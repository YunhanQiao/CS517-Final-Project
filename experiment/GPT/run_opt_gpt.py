#!/usr/bin/env python3
import os
import sys
import argparse
from pathlib import Path

import openai

# -----------------------------------------------------------------------------
# 1. Configure OpenAI API Key
# -----------------------------------------------------------------------------
# Make sure you have set your API key in your environment:
#   export OPENAI_API_KEY="sk-…your_key_here…"
openai.api_key = os.getenv("OPENAI_API_KEY")
if openai.api_key is None:
    print("ERROR: Please set the OPENAI_API_KEY environment variable.", file=sys.stderr)
    sys.exit(1)

# -----------------------------------------------------------------------------
# 2. Parse a single command-line argument: the path to one .cnf file
# -----------------------------------------------------------------------------
parser = argparse.ArgumentParser(
    description="Send a single 3-SAT CNF file (DIMACS format) to GPT and dump the response."
)
parser.add_argument(
    "cnf_file",
    type=Path,
    help="Path to a DIMACS-format .cnf file"
)
parser.add_argument(
    "-m",
    "--model",
    default="gpt-4o-2024-08-06",
    help="OpenAI model to use"
)
parser.add_argument(
    "--max-tokens",
    type=int,
    default=2000,
    help="Maximum tokens for GPT’s response (default: 2000)"
)
parser.add_argument(
    "--temperature",
    type=float,
    default=0.5,
    help="Temperature for GPT sampling (default: 0.0 for deterministic output)"
)
args = parser.parse_args()

# Verify that the input file exists
if not args.cnf_file.is_file():
    print(f"ERROR: File not found: {args.cnf_file}", file=sys.stderr)
    sys.exit(1)

# -----------------------------------------------------------------------------
# 3. Helper: Read the entire .cnf into one string
# -----------------------------------------------------------------------------
def load_cnf_text(path: Path) -> str:
    """
    Read a DIMACS-format .cnf file (including any 'c ...' comments and the 'p cnf ...' header)
    and return its contents as a single string.
    """
    return path.read_text(encoding="utf-8").strip()

# -----------------------------------------------------------------------------
# 4. Helper: Build the messages for the ChatCompletion call
# -----------------------------------------------------------------------------
def build_messages(instance_text: str) -> list[dict]:
    """
    Construct a two‐message list so that GPT knows to:
      1. Act as a vertex-cover optimization expert  
      2. Analyze the graph, show reasoning step-by-step  
      3. Provide the minimum cover size and the chosen vertices  
      4. Finally, report a confidence score
    """
    system_msg = {
        "role": "system",
        "content": (
            "You are an expert in the vertex cover optimization problem. "
            "Follow the pattern in the provided example to solve the new problem step-by-step, showing all reasoning. "
            "Provide the final answer in a clear format, including:\n"
            "  • Minimum vertex cover size\n"
            "  • The set of vertices in that cover\n"
            "After the final answer, include a line:\n"
            "  Confidence: XX%\n"
            "where XX% is your estimate of how confident you are that the answer is correct.\n\n"
            "Example:\n"
            "[Input:\n"
            "Vertices: {1,2,3,4,5}\n"
            "Edges: (1,2),(2,3),(3,4),(4,5),(5,1)\n"
            "Solution:\n"
            "1. Observe that selecting any two opposite vertices covers all edges.\n"
            "2. Verify no single‐vertex cover exists.\n"
            "Final answer:\n"
            "Minimum vertex cover size: 2\n"
            "Cover set: {2,5}\n"
            "Confidence: 92%]\n\n"
            "Problem:\n"
            "[Please refer to the attached graph instance in edge-list format. Analyze it, show your reasoning, and then provide the minimum vertex cover and its vertices.]"
        )
    }

    user_msg = {
        "role": "user",
        "content": (
            "Here is a vertex cover problem instance in edge-list format. "
            "Please analyze it, show your reasoning, and then provide the minimum vertex cover size and the list of vertices.\n\n"
            "-----BEGIN GRAPH-----\n"
            + instance_text +
            "\n-----END GRAPH-----"
        )
    }

    return [system_msg, user_msg]


# -----------------------------------------------------------------------------
# 5. Helper: Actually call OpenAI’s ChatCompletion API
# -----------------------------------------------------------------------------
def query_gpt(messages: list[dict], model: str, temperature: float, max_tokens: int) -> str:
    """
    Send messages to OpenAI’s ChatCompletion endpoint and return the raw text response.
    """
    resp = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=1.0,
    )
    return resp.choices[0].message["content"]

# -----------------------------------------------------------------------------
# 6. Main flow (for a single file)
# -----------------------------------------------------------------------------
def main():
    cnf_path = args.cnf_file
    cnf_name = cnf_path.stem  # e.g. “3_SAT_satisfiable”

    print(f"→ Loading CNF from {cnf_path} …")
    try:
        cnf_text = load_cnf_text(cnf_path)
    except Exception as e:
        print(f"ERROR: Could not read {cnf_path}: {e}", file=sys.stderr)
        sys.exit(1)

    print("→ Building prompt for GPT …")
    messages = build_messages(cnf_text)

    print(f"→ Querying GPT (model={args.model}) …")
    try:
        gpt_output = query_gpt(
            messages,
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
    except Exception as e:
        print(f"ERROR: GPT API call failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Print GPT’s raw response to stdout
    print("===== GPT Response =====")
    print(gpt_output)

if __name__ == "__main__":
    main()
