import json
import os
import copy
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ╔══════════════════════════════════════════════════════════════════╗
# ║  PERFIS DE REBUILD — descomente UM bloco e comente o outro     ║
# ╚══════════════════════════════════════════════════════════════════╝

# ── Perfil EN: reconstruir de volta para inglês (teste roundtrip) ──
#PROFILE = "EN"
#PONTOON_DIR = os.path.join(BASE_DIR, "weblate", "EN")
#SOURCE_DIR  = os.path.join(BASE_DIR, "EN")
#OUTPUT_DIR  = os.path.join(BASE_DIR, "rebuilt", "EN")

# ── Perfil PTBR: reconstruir tradução português ──
PROFILE = "PTBR"
PONTOON_DIR = os.path.join(BASE_DIR, "weblate", "PTBR")
SOURCE_DIR  = os.path.join(BASE_DIR, "EN")
OUTPUT_DIR  = os.path.join(BASE_DIR, "rebuilt", "PTBR")

LINE_MARKER = "\n"

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


def resolve_path(original, parts):
    """
    Resolve a flat key like "12.40.1" against the original template.
    Returns the real path as a list of keys.

    The ambiguity: "12.40.1" could be:
      - ["12", "40", "1"]   (dict "12" -> list/dict "40" -> index 1)
      - ["12", "40.1"]      (dict "12" -> key "40.1")

    Strategy: try greedy left-to-right. At each node, check if joining
    remaining dots forms a valid key. Prefer the longest matching key
    that exists in the template.
    """
    result = []
    obj = original
    i = 0

    while i < len(parts):
        if not isinstance(obj, (dict, list)):
            # Leaf reached but parts remain — use remaining as-is
            result.extend(parts[i:])
            break

        # Try progressively longer key combinations (greedy: longest first)
        matched = False
        for end in range(len(parts), i, -1):
            candidate = ".".join(parts[i:end])
            ok, next_obj = safe_get(obj, candidate)
            if ok:
                result.append(candidate)
                obj = next_obj
                i = end
                matched = True
                break

        if not matched:
            # No match found — use single part and move on
            result.append(parts[i])
            ok, next_obj = safe_get(obj, parts[i])
            if ok:
                obj = next_obj
            i += 1

    return result


def convert_to_original_type(value, original):
    if isinstance(original, bool):
        return value.lower() in ("true", "1", "yes")
    elif isinstance(original, int):
        try:
            return int(value)
        except (ValueError, TypeError):
            return value
    elif isinstance(original, float):
        try:
            return float(value)
        except (ValueError, TypeError):
            return value
    elif original is None:
        return None if value == "" else value
    return value


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
    else:
        i = int(last)
        while len(obj) <= i:
            obj.append(None)

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
            new_val = new_val[:template_len - 1] + [
                LINE_MARKER.join(new_val[template_len - 1:])
            ]

        if isinstance(obj, dict):
            obj[last] = new_val
        else:
            obj[i] = new_val
    else:
        converted = convert_to_original_type(value, orig_last)
        if isinstance(obj, dict):
            obj[last] = converted
        else:
            obj[i] = converted


def rebuild():
    suffix_map = {"PTBR": ("PTBR", "EN"), "EN": ("EN", "EN")}
    from_tag, to_tag = suffix_map.get(PROFILE, (PROFILE, "EN"))

    if not os.path.isdir(PONTOON_DIR):
        print(f"ERRO: Diretório não encontrado: {PONTOON_DIR}")
        print(f"Crie a pasta e coloque os JSONs flat lá.")
        sys.exit(1)

    count = 0
    for fname in os.listdir(PONTOON_DIR):
        if not fname.endswith(".json"):
            continue

        pontoon_path = os.path.join(PONTOON_DIR, fname)

        source_name = fname.replace(from_tag, to_tag) if from_tag != to_tag else fname
        source_path = os.path.join(SOURCE_DIR, source_name)

        if not os.path.exists(source_path):
            print(f"  Template não encontrado: {source_name}")
            continue

        with open(pontoon_path, "r", encoding="utf-8") as f:
            flat = json.load(f)

        with open(source_path, "r", encoding="utf-8") as f:
            original = json.load(f)

        rebuilt = copy.deepcopy(original)

        for key, value in flat.items():
            parts = key.split(".")
            path = resolve_path(original, parts)
            set_value(rebuilt, original, path, value)

        out_name = source_name.replace(to_tag, from_tag) if from_tag != to_tag else fname
        out_path = os.path.join(OUTPUT_DIR, out_name)

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(rebuilt, f, indent=2, ensure_ascii=False)

        count += 1
        print(f"  {fname} → {out_name}")

    print(f"\n[{PROFILE}] {count} arquivo(s) reconstruído(s) em: {OUTPUT_DIR}")


if __name__ == "__main__":
    print(f"Rebuild perfil: {PROFILE}")
    print(f"  Weblate:  {PONTOON_DIR}")
    print(f"  Template: {SOURCE_DIR}")
    print(f"  Output:   {OUTPUT_DIR}\n")
    rebuild()
