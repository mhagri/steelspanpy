# -*- coding: utf-8 -*-
"""
Created on Wed Jul 23 14:05:12 2025

@author: mhaka
"""

import os

def create_file(path):
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            pass  # boş dosya oluştur

def init_project():
    base_dir = os.path.dirname(os.path.abspath(__file__))  # scripts klasörü
    root_dir = os.path.abspath(os.path.join(base_dir, ".."))  # steelspanpy ana dizin

    # Klasör yapıları
    folders = [
        os.path.join(root_dir, 'steelspanpy'),
        os.path.join(root_dir, 'steelspanpy', 'tests'),
        os.path.join(root_dir, 'steelspanpy', 'examples'),
        os.path.join(root_dir, 'scripts'),
    ]

    for folder in folders:
        os.makedirs(folder, exist_ok=True)

    # steelspanpy modül dosyaları (ana kodlar)
    module_files = [
        '__init__.py',
        'geometry.py',
        'model.py',
        'loads.py',
        'materials.py',
        'utils.py',
        'config.py',
    ]

    for file in module_files:
        path = os.path.join(root_dir, 'steelspanpy', file)
        create_file(path)

    # tests klasör dosyaları
    test_files = [
        '__init__.py',
        'test_geometry.py',
        'test_model.py',
    ]

    for file in test_files:
        path = os.path.join(root_dir, 'steelspanpy', 'tests', file)
        create_file(path)

    # examples klasör dosyaları
    example_files = [
        'basic_model_example.py',
    ]

    for file in example_files:
        path = os.path.join(root_dir, 'steelspanpy', 'examples', file)
        create_file(path)

    # scripts klasör dosyaları
    script_files = [
        'init_project.py',      # kendisi
        'start_etabs.py',       # ileride ekleyeceğimiz ETABS başlangıç scripti için yer tutucu
    ]

    for file in script_files:
        path = os.path.join(root_dir, 'scripts', file)
        create_file(path)

    # Diğer dosyalar ana dizinde
    other_files = [
        '.gitignore',
        'README.md',
        'requirements.txt',
        'pyproject.toml',
        'LICENSE',
    ]

    for file in other_files:
        path = os.path.join(root_dir, file)
        create_file(path)

    print("Proje klasör ve dosya yapısı başarıyla oluşturuldu.")

if __name__ == "__main__":
    init_project()
