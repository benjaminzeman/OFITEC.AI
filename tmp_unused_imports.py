import ast, os
base = r"custom_addons"
unused = {}
for root, _, files in os.walk(base):
    for fn in files:
        if not fn.endswith('.py'):
            continue
        p = os.path.join(root, fn)
        try:
            src = open(p, 'r', encoding='utf-8', errors='ignore').read()
            tree = ast.parse(src, filename=p)
        except Exception as e:
            print('PARSE_ERR', p, e)
            continue
        imported = set()
        import_nodes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                import_nodes.append(node)
                for a in node.names:
                    name = a.asname or a.name.split('.')[0]
                    imported.add(name)
            elif isinstance(node, ast.ImportFrom):
                import_nodes.append(node)
                if any(n.name == '*' for n in node.names):
                    continue
                for a in node.names:
                    name = a.asname or a.name
                    imported.add(name)
        used = set()
        class V(ast.NodeVisitor):
            def visit_Name(self, n):
                used.add(n.id)
        V().visit(tree)
        un = sorted(n for n in imported - used if n != '_')
        if un:
            print(p)
            print(' ', ', '.join(un))
