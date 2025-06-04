#!/bin/bash

set -e

SAT_DIR="/workspaces/CS517-Final-Project/3_SAT_satisifiable"
UNSAT_DIR="/workspaces/CS517-Final-Project/3_SAT_unsatisfiable"
SOLVER="/workspaces/CS517-Final-Project/solver/SAT_solver.py"

# Select the first 25 files from each directory (sorted by name)
SAT_FILES=($(ls "$SAT_DIR"/*.cnf | sort | head -n 100))
UNSAT_FILES=($(ls "$UNSAT_DIR"/*.cnf | sort | head -n 100))

echo "Running SAT_solver.py on first 25 satisfiable instances:"
for f in "${SAT_FILES[@]}"; do
    echo "Solving $f"
    python "$SOLVER" -i "$f" -p cnf
done

echo "Running SAT_solver.py on first 25 unsatisfiable instances:"
for f in "${UNSAT_FILES[@]}"; do
    echo "Solving $f"
    python "$SOLVER" -i "$f" -p cnf
done