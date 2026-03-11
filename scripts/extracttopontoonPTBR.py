#!/usr/bin/env python3
# export_to_pontoon.py
# Transforma cada JSON "original" em um JSON plano estilo Pontoon.
# - listas de strings viram uma única string com <LINE> entre linhas
# - listas vazias são exportadas como "" (o rebuild usa o arquivo original como template)
# - outras estruturas são percorridas recursivamente

import json
import os
from pathlib import Path

INPUT_DIR = "PTBR"                  # onde ficam os JSONs originais (template)
OUTPUT_DIR = os.path.join("pontoon2", "PTBR")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def is_list_of_strings(obj):
    return isinstance(obj, list) and all(isinstance(x, str) for x in obj)

def flatten(obj, path, out):
    """
    out[path_string] = value
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            flatten(v, path + [str(k)], out)
    elif isinstance(obj, list):
        if is_list_of_strings(obj):
            key = ".".join(path)
            # preserve empty strings inside the list; empty list -> empty string ""
            out[key] = "<LINE>".join(obj)
        else:
            # list of dicts or nested lists -> index and recurse
            for i, v in enumerate(obj):
                flatten(v, path + [str(i)], out)
    elif isinstance(obj, str):
        key = ".".join(path)
        out[key] = obj
    else:
        # numbers, booleans, nulls -> convert to string for translation context
        key = ".".join(path)
        out[key] = "" if obj is None else str(obj)

def process_file(in_path, out_path):
    with open(in_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    flat = {}
    flatten(data, [], flat)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(flat, f, indent=4, ensure_ascii=False)

    print(f"{in_path.name}: {len(flat)} strings extraídas -> {out_path}")

if __name__ == "__main__":
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    for fname in os.listdir(INPUT_DIR):
        if not fname.endswith(".json"):
            continue
        in_path = Path(INPUT_DIR) / fname
        out_path = Path(OUTPUT_DIR) / fname
        process_file(in_path, out_path)