import ast

def build_name_from_defs(function_defs, base=''):
    ret = {}
    for f in function_defs:
        ret[base + '.' + f.name if base else f.name] = (f.lineno, f.end_lineno)
    return ret

def map_func_to_lines(filename):
    with open(filename, 'r') as f:
        res = ast.parse(f.read(), filename)
    ret = {}
    classes = [r for r in res.body if isinstance(r, ast.ClassDef)]
    for c in classes:
        ret |= build_name_from_defs([f for f in c.body if isinstance(f, ast.FunctionDef)], base=c.name)

    functions = [r for r in res.body if isinstance(r, ast.FunctionDef)]
    ret |= build_name_from_defs(functions)
    return ret 
