# CS517-Final-Project
This repository provides a reusable command-line tool and Python API for solving NP-hard problems using pysmt as a backend.

# Problem Statement

# Teammates

# NP-Hard Problem Solver Pipeline
The pipeline is structured in four clear, modular stages:

1. **Parsing Input**
   - Read a standardized problem instance file into native Python data structures.
   - Examples:
     - 3-SAT: DIMACS `.cnf` files
     - Vertex Cover: custom `n m k` edge-list format
     - 3-Coloring: custom `n m` edge-list format

2. **Encoding to SMT**
   - Translate the Python representation into a **pysmt** AST (`Formula`) and a symbol map.
   - For each problem:
     - **3-SAT**: one Boolean symbol per variable; `Or` clauses; top-level `And`
     - **Vertex Cover**: Boolean symbols for each vertex; edge constraints `x_u ∨ x_v`; cardinality constraint `∑ x_i ≤ k`
     - **3-Coloring**: Boolean symbols for each (vertex,color) pair; `exactly_one` color constraints; adjacency constraints

3. **Solving with SMT/SAT Backend**
   - Invoke `pysmt.shortcuts.Solver(name=...)` with optional timeout.
   - `solver.add_assertion(formula)` and `solver.solve()` to decide SAT/UNSAT.
   - If SAT, extract the model values for each symbol, mapping back to the original problem variables.
   - Backend options include Z3, CVC4, PicoSAT, etc.

4. **Formatting & Output**
   - Package the result into JSON or plain text:
     ```json
     {
       "status": "sat" | "unsat",
       ... // problem-specific solution details
     }
     ```
   - Print to stdout or write to a file via command-line flag.

---


