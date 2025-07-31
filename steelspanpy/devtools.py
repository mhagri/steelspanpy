import os
import ast

def list_functions_in_file(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        node = ast.parse(file.read())
    return [n.name for n in ast.walk(node) if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")]

def list_functions_in_directory(directory):
    functions = {}
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                fullpath = os.path.join(root, file)
                relpath = os.path.relpath(fullpath, directory)
                mod_name = relpath.replace(os.sep, ".")[:-3]  # remove .py
                funcs = list_functions_in_file(fullpath)
                if funcs:
                    functions[mod_name] = funcs
    return functions

def generate_init_lines(functions):
    lines = []
    for mod, funcs in sorted(functions.items()):
        import_line = f"from .{mod} import {', '.join(funcs)}"
        lines.append(import_line)
    return lines

def main():
    # steelspanpy/utils gibi alt klasörde çalışıyorsak orayı hedef al
    project_root = os.path.dirname(os.path.abspath(__file__))
    utils_path = os.path.join(project_root)

    funcs = list_functions_in_directory(utils_path)
    init_lines = generate_init_lines(funcs)

    # Dosyaya yazalım (örneğin bir yere yapıştırmak için)
    output_path = os.path.join(project_root, "init_suggestion.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        for line in init_lines:
            f.write(line + "\n")

    print(f"\nSuggested __init__.py content saved to: {output_path}")

if __name__ == "__main__":
    main()
