# -*- coding: utf-8 -*-
"""
Created on Wed Jul 23 14:01:15 2025

@author: mhaka
"""

import os

project_name = "steelspanpy"

folders = [
    "utils",
    "model",
    "etabs_api",
    "data"
]

files = {
    "main.py": "",
    "config.py": "",
    "requirements.txt": "",
    ".gitignore": "*.pyc\n__pycache__/\n.env\n",
    "README.md": f"# {project_name}\n\nYapısal çelik hangar modelleme otomasyonu.",
    "utils/geometry.py": "",
    "utils/naming.py": "",
    "utils/helpers.py": "",
    "model/structure.py": "",
    "model/roof.py": "",
    "model/verticals.py": "",
    "model/loading.py": "",
    "etabs_api/etabs_model.py": "",
    "etabs_api/releases.py": "",
    "data/sample_project.json": "{}"
}

# Ana klasörü oluştur
os.makedirs(project_name, exist_ok=True)

# Alt klasörleri oluştur
for folder in folders:
    os.makedirs(os.path.join(project_name, folder), exist_ok=True)

# Dosyaları oluştur
for path, content in files.items():
    file_path = os.path.join(project_name, path)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

print(f"✅ Proje yapısı oluşturuldu: {project_name}")
