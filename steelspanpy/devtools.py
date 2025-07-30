import os
import ast

def list_functions_in_file(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        node = ast.parse(file.read())
    return [n.name for n in ast.walk(node) if isinstance(n, ast.FunctionDef)]

def list_functions_in_directory(directory):
    functions = {}
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                fullpath = os.path.join(root, file)
                relpath = os.path.relpath(fullpath, directory)
                mod_name = relpath.replace(os.sep, ".")[:-3]  # .py kaldır
                funcs = list_functions_in_file(fullpath)
                functions[mod_name] = funcs
    return functions

def main():
    project_dir = os.path.dirname(os.path.abspath(__file__))  # devtools.py'nin klasörü
    output_file = os.path.join(project_dir, "function_list.txt")

    funcs = list_functions_in_directory(project_dir)

    with open(output_file, "w", encoding="utf-8") as f:
        for mod, funclist in funcs.items():
            f.write(f"Module: {mod}\n")
            print(f"Module: {mod}")
            for func in funclist:
                line = f"  - {func}\n"
                f.write(line)
                print(line, end="")

    print(f"\nFunction list saved to: {output_file}")

if __name__ == "__main__":
    main()
