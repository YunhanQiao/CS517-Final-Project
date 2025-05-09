from pysmt.shortcuts import Symbol, Or, And, Ite, LE, Plus
from pysmt.typing import BOOL, INT
from pysmt.shortcuts import Int
from pysmt.shortcuts import Solver
import json
import argparse


def parse_vc(path):
    """
    Returns (num_vertices, edges, k)
      num_vertices: int
      edges: List[Tuple[int,int]]
      k: int
    """
    with open(path) as f:
        first = f.readline().split()
        n, m, k = map(int, first)
        edges = [tuple(map(int, line.split())) for line in f]
    return n, edges, k


def build_vc_formula(n, edges, k):
    # 1) create Boolean symbols x1…xn
    xs = {i: Symbol(f"x{i}", BOOL) for i in range(1, n+1)}

    # 2) edge constraints: x_u ∨ x_v
    edge_cls = [Or(xs[u], xs[v]) for u, v in edges]

    # 3) cardinality: sum(Ite(xi,1,0)) ≤ k
    summands = [Ite(xs[i], Int(1), Int(0)) for i in range(1, n+1)]
    card = LE(Plus(summands), Int(k))

    # 4) conjoin everything
    formula = And(edge_cls + [card])
    return formula, xs


def solve_formula(formula, xs, backend="z3", timeout=None):
    # Initialize the solver without passing timeout
    with Solver(name=backend) as solver:
        solver.add_assertion(formula)
        # Set timeout separately if supported by the solver
        if timeout is not None and hasattr(solver, 'set_timeout'):
            solver.set_timeout(timeout)
        sat = solver.solve()
        if not sat:
            return False, {}
        model = solver.get_model()
        # Translate back to {vertex → True/False}
        assignment = {i: model.get_value(xs[i]).is_true()
                      for i in xs}
        return True, assignment

def output_vc_result(sat, assignment, out_path=None):
    result = {
      "status": "sat" if sat else "unsat",
      "cover": [i for i,val in assignment.items() if val]
    }
    text = json.dumps(result, indent=2)
    if out_path:
        open(out_path,"w").write(text)
    else:
        print(text)


def main():
    # 1. CLI argument parsing
    parser = argparse.ArgumentParser(
        description="Vertex Cover Solver using pysmt"
    )
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Path to the instance file (edge list + k)"
    )
    parser.add_argument(
        "-b", "--backend",
        default="z3",
        help="Which pysmt solver to use (e.g. z3, cvc4)"
    )
    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=None,
        help="Timeout in seconds (optional)"
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="If given, write JSON result here; otherwise stdout"
    )
    args = parser.parse_args()

    # 2. Parse the input format
    n, edges, k = parse_vc(args.input)

    # 3. Build the pysmt formula + symbol map
    formula, xs = build_vc_formula(n, edges, k)

    # 4. Solve and extract a model
    sat, assignment = solve_formula(
        formula,
        xs,
        backend=args.backend,
        timeout=args.timeout
    )

    # 5. Output the result
    output_vc_result(sat, assignment, out_path=args.output)


if __name__ == "__main__":
    main()

