import argparse
import json
from pysmt.shortcuts import Symbol, And, Or, Not, Solver, BOOL, Plus, Int, Ite, LE, GE

def parse_graph_file(path):
    with open(path) as f:
        # Skip blank lines and comment lines (those starting with 'c')
        lines = [line.strip() for line in f if line.strip() and not line.startswith('c')]
    # First meaningful line is "n m 0" (we only need n)
    header = lines[0].split()
    n = int(header[0])
    adjacency = []
    for line in lines[1:]:
        neighbors = list(map(int, line.split()))
        adjacency.append(neighbors)
    # Build an undirected‐edge set without duplicates
    edges = set()
    for i, neighbors in enumerate(adjacency):
        for j in neighbors:
            if (i + 1) < j:
                edges.add((i + 1, j))
    return n, list(edges)

def build_vc_formula(n, edges, k):
    # Create Boolean variable x_i which is true ⇔ vertex i is in the cover
    xs = {i: Symbol(f"x{i}", BOOL) for i in range(1, n + 1)}

    # Each edge (u,v) must be covered: x_u ∨ x_v
    edge_covered = [Or(xs[u], xs[v]) for (u, v) in edges]

    # Encode “sum_{i=1..n} [x_i]” as an integer term:
    #   for each i, Ite(x_i, 1, 0), then Plus(…)
    sum_terms = [Ite(xs[i], Int(1), Int(0)) for i in range(1, n + 1)]
    total = Plus(sum_terms)

    # Enforce |cover| ≥ k  ⇔  total ≥ k
    at_least_k = GE(total, Int(k))

    # Enforce |cover| ≤ k  ⇔  total ≤ k
    at_most_k = LE(total, Int(k))

    # Conjoin everything
    formula = And(And(edge_covered), at_least_k, at_most_k)
    return formula, xs

def solve_formula(formula, xs, backend="z3", timeout=None):
    with Solver(name=backend) as solver:
        solver.add_assertion(formula)
        # If the solver implementation supports timeouts, set it
        if timeout is not None and hasattr(solver, "set_timeout"):
            solver.set_timeout(timeout)
        sat = solver.solve()
        if not sat:
            return False, {}
        model = solver.get_model()
        assignment = {i: model.get_value(xs[i]).is_true() for i in xs}
        return True, assignment

def find_min_vertex_cover(input_path, backend="z3", timeout=None):
    n, edges = parse_graph_file(input_path)
    left, right = 0, n
    best_assignment = None
    best_k = None

    while left <= right:
        mid = (left + right) // 2
        formula, xs = build_vc_formula(n, edges, mid)
        sat, assignment = solve_formula(formula, xs, backend=backend, timeout=timeout)
        if sat:
            best_k = mid
            best_assignment = assignment
            right = mid - 1
        else:
            left = mid + 1

    return best_k, best_assignment

def main():
    parser = argparse.ArgumentParser(description="Minimum Vertex Cover Optimizer")
    parser.add_argument(
        "-i", "--input", required=True,
        help="Path to vertex cover instance file"
    )
    parser.add_argument(
        "-b", "--backend", default="z3",
        help="pysmt solver backend (default: z3)"
    )
    parser.add_argument(
        "-t", "--timeout", type=int, default=None,
        help="Timeout in seconds (optional)"
    )
    parser.add_argument(
        "-o", "--output", default=None,
        help="Output file for JSON result (optional)"
    )
    args = parser.parse_args()

    best_k, assignment = find_min_vertex_cover(
        args.input, backend=args.backend, timeout=args.timeout
    )

    if assignment is None:
        result = {"status": "unsat", "cover": []}
    else:
        result = {
            "status": "sat",
            "cover_size": best_k,
            "cover": [i for i, v in assignment.items() if v]
        }

    text = json.dumps(result, indent=2)
    if args.output:
        with open(args.output, "w") as f:
            f.write(text)
    else:
        print(text)

if __name__ == "__main__":
    main()
