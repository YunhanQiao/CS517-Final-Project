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


def parse_cnf(path):
    """
    Returns (num_vars, clauses)
      num_vars: int
      clauses: List[List[int]]
    """
    clauses = []
    num_vars = 0
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line.startswith('c') or line == '':
                continue
            if line.startswith('p'):
                parts = line.split()
                num_vars = int(parts[2])
                continue
            if line == '0' or line == '%':
                continue
            clause = [int(x) for x in line.split() if x != '0']
            if clause:
                clauses.append(clause)
    return num_vars, clauses

def build_cnf_formula(num_vars, clauses):
    # Create Boolean symbols x1...xn
    xs = {i: Symbol(f"x{i}", BOOL) for i in range(1, num_vars+1)}
    # Each clause is an Or of literals
    def lit(l):
        v = abs(l)
        return xs[v] if l > 0 else ~xs[v]
    clause_exprs = [Or([lit(l) for l in clause]) for clause in clauses]
    formula = And(clause_exprs)
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
        description="SAT/Vertex Cover Solver using pysmt"
    )
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Path to the instance file"
    )
    parser.add_argument(
        "-p", "--problem",
        choices=["vc", "cnf"],
        required=True,
        help="Problem type: 'vc' for Vertex Cover, 'cnf' for DIMACS CNF"
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

    if args.problem == "vc":
        n, edges, k = parse_vc(args.input)
        formula, xs = build_vc_formula(n, edges, k)
    elif args.problem == "cnf":
        num_vars, clauses = parse_cnf(args.input)
        formula, xs = build_cnf_formula(num_vars, clauses)
    else:
        raise ValueError("Unknown problem type")

    sat, assignment = solve_formula(
        formula,
        xs,
        backend=args.backend,
        timeout=args.timeout
    )

    output_vc_result(sat, assignment, out_path=args.output)


if __name__ == "__main__":
    main()

