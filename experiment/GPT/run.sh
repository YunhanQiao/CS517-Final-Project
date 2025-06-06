#!/bin/bash

# Directory containing input .cnf files
INPUT_DIR="/workspaces/CS517-Final-Project/Vertex_Cover_optimization/input"
OUTPUT_DIR="/workspaces/CS517-Final-Project/result/GPT/opt"

# Make sure output directory exists
mkdir -p "$OUTPUT_DIR"

# Iterate over all .cnf files in the input directory
for INPUT_CNF in "$INPUT_DIR"/*.graph; do
    BASENAME=$(basename "$INPUT_CNF" .graph)
    OUTPUT_FILE="${OUTPUT_DIR}/${BASENAME}_gpt_output.txt"

    # Run the Python script
    python3 /workspaces/CS517-Final-Project/experiment/GPT/run_opt_gpt.py "$INPUT_CNF" > "$OUTPUT_FILE"

    # The Python script already writes output as <basename>_gpt_output.txt in the same directory as the input,
    # so you may not need to move/rename. If you want to ensure, uncomment the next line:
    # mv "$(dirname "$INPUT_CNF")/${BASENAME}_gpt_output.txt" "$OUTPUT_FILE"

    echo "Output saved to $OUTPUT_FILE"
done