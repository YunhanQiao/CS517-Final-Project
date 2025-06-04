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
    default=0.0,
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
def build_messages(cnf_text: str) -> list[dict]:
    """
    Construct a two-message list so that GPT knows to:
      1. Act as a 3-SAT expert
      2. Analyze the CNF, show reasoning, then declare SAT or UNSAT
      3. If SAT, provide a valid assignment
    """
    system_msg = {
        "role": "system",
        "content": (
            "You are an expert in 3-SAT problem. "
            "Follow the pattern in the provided example to solve the new problem step-by-step, showing all reasoning. Provide the final answer in a clear format (e.g., YES/NO for decision problems, a numerical value and solution set for optimization problems). After the final answer, include a line: "
            "Confidence: XX%"
            "where XX% is your estimate of how confident you are that the answer is correct. "
            "Example: [Input:"
                      "p cnf 3 2"
                      "1 2 -3 0"       
                      "-1 3 2 0"
                      "Soluton:"
                      "1. Clauses: {1,2,¬3}, {¬1,3,2}" 
                     "2. Try x1=TRUE: clauses become {T,*,*} (sat), {F,3,2} → still sat if x2=TRUE."
                     "3. Assignment: x1=TRUE, x2=TRUE, x3=FALSE works.]"
            "Problem: [Please refer to the attached CNF problem in DIMACS format. Analyze it, show your reasoning, and then declare SAT or UNSAT. If SAT, give a satisfying assignment.]"
        )
    }
    user_msg = {
        "role": "user",
        "content": (
            "Here is a 3-SAT problem in DIMACS CNF format. "
            "Please analyze it, show your reasoning, and then declare SAT or UNSAT. "
            "If SAT, give a satisfying assignment.\n\n"
            "-----BEGIN CNF-----\n"
            + cnf_text
            + "\n-----END CNF-----"
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

    # Write GPT’s raw response to <basename>_gpt_output.txt
    output_path = cnf_path.with_name(f"{cnf_name}_gpt_output.txt")
    try:
        output_path.write_text(gpt_output, encoding="utf-8")
        print(f"✔ GPT output saved to {output_path}")
    except Exception as e:
        print(f"ERROR: Could not write to {output_path}: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
