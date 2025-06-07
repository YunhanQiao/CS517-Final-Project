#!/bin/bash

set -e

INPUT_DIR="/workspaces/CS517-Final-Project/Vertex_Cover_optimization/input"
SOLVER="/workspaces/CS517-Final-Project/experiment/solver/Optimization_solver.py"

echo "Running Optimization_solver.py on all input files:"
for f in "$INPUT_DIR"/*; do
    if [[ -f "$f" ]]; then
        echo "Solving $f"
        time python "$SOLVER" -i "$f"
    fi
done