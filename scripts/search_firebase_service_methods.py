import ast

file_path = "C:/Users/Sangwa Jesly/Desktop/legalhub-backend/app/services/firebase_service.py"

with open(file_path, 'r', encoding='utf-8') as f:
    tree = ast.parse(f.read())

print("Methods in FirebaseService:")
for node in ast.walk(tree):
    if isinstance(node, ast.ClassDef) and node.name == "FirebaseService":
        for body_node in node.body:
            if isinstance(body_node, ast.FunctionDef):
                # Print function signature
                args = [arg.arg for arg in body_node.args.args]
                print(f"- {body_node.name}({', '.join(args)})")
