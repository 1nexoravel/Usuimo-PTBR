import json
import os
import copy

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SOURCE_DIR = os.path.join(BASE_DIR, "EN")
PONTOON_DIR = os.path.join(BASE_DIR, "Pontoon", "locales", "pt-BR")
OUTPUT_DIR = os.path.join(BASE_DIR, "PTBR")

LINE_MARKER = "<LINE>"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def safe_get(obj, key):

    if isinstance(obj, dict):
        if key in obj:
            return True, obj[key]
        return False, None

    if isinstance(obj, list):
        if not key.isdigit():
            return False, None
        i = int(key)
        if i < 0 or i >= len(obj):
            return False, None
        return True, obj[i]

    return False, None


def set_value(data, original, path, value):

    obj = data
    orig = original

    for p in path[:-1]:

        ok, next_orig = safe_get(orig, p)

        if not ok:
            return

        if isinstance(obj, dict):

            if p not in obj:

                if isinstance(next_orig, list):
                    obj[p] = []
                else:
                    obj[p] = {}

            obj = obj[p]

        elif isinstance(obj, list):

            i = int(p)

            while len(obj) <= i:
                obj.append({})

            obj = obj[i]

        orig = next_orig

    last = path[-1]

    ok, orig_last = safe_get(orig, last)

    if not ok:
        return

    if isinstance(obj, dict):

        if last not in obj:
            obj[last] = copy.deepcopy(orig_last)

        target = obj[last]

    else:

        i = int(last)

        while len(obj) <= i:
            obj.append(None)

        target = obj[i]

    if isinstance(orig_last, list) and all(isinstance(x, str) for x in orig_last):

        if value == "":
            new_val = []

        elif LINE_MARKER in value:
            new_val = value.split(LINE_MARKER)

        else:
            new_val = [value]

        template_len = len(orig_last)

        if template_len == 0:
            new_val = []

        elif len(new_val) < template_len:
            new_val += [""] * (template_len - len(new_val))

        elif len(new_val) > template_len:
            new_val = new_val[:template_len-1] + [
                LINE_MARKER.join(new_val[template_len-1:])
            ]

        if isinstance(obj, dict):
            obj[last] = new_val
        else:
            obj[i] = new_val

    else:

        if isinstance(obj, dict):
            obj[last] = value
        else:
            obj[i] = value


def rebuild():

    for fname in os.listdir(PONTOON_DIR):

        if not fname.endswith(".json"):
            continue

        pontoon_path = os.path.join(PONTOON_DIR, fname)

        # converter nome PTBR → EN para achar template
        source_name = fname.replace("PTBR", "EN")
        source_path = os.path.join(SOURCE_DIR, source_name)

        if not os.path.exists(source_path):
            print("Template não encontrado:", source_name)
            continue

        with open(pontoon_path, "r", encoding="utf-8") as f:
            flat = json.load(f)

        with open(source_path, "r", encoding="utf-8") as f:
            original = json.load(f)

        rebuilt = copy.deepcopy(original)

        for key, value in flat.items():

            path = key.split(".")
            set_value(rebuilt, original, path, value)

        new_name = source_name.replace("EN", "PTBR")
        out_path = os.path.join(OUTPUT_DIR, new_name)

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(rebuilt, f, indent=2, ensure_ascii=False)

        print(fname, "→", new_name, "reconstruído")


if __name__ == "__main__":
    rebuild()