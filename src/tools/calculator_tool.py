from langchain_core.tools import tool
import ast
import operator

@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression. Use for calculations, e.g., '2 + 2' or 'sqrt(16)'."""
    # Allowed operators and functions for safety
    allowed_ops = {
        ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg
    }
    allowed_functions = {"abs": abs, "round": round, "sqrt": lambda x: x**0.5}
    
    def safe_eval(node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            return allowed_ops[type(node.op)](safe_eval(node.left), safe_eval(node.right))
        elif isinstance(node, ast.UnaryOp):
            return allowed_ops[type(node.op)](safe_eval(node.operand))
        elif isinstance(node, ast.Call):
            if node.func.id in allowed_functions:
                return allowed_functions[node.func.id](*(safe_eval(arg) for arg in node.args))
        raise ValueError("Unsupported expression")
    
    try:
        tree = ast.parse(expression, mode='eval')
        result = safe_eval(tree.body)
        return f"Result: {result}"
    except Exception as e:
        return f"Calculation error: {e}"