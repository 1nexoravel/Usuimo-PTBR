#!/usr/bin/env python3
"""
Detecta strings em PTBR que são significativamente mais curtas que a origem EN.

Uso:
    python detect_short.py [--ratio 0.5] [--min-src 20] [--out short.csv]

Espera estrutura:
    EN/arquivoXXENXX.json
    PTBR/arquivoXXPTBRXX.json

Pareamento: substitui "EN" por "PTBR" no nome do arquivo.
"""

import argparse
import csv
import json
import sys
from pathlib import Path


def flatten(obj, prefix=""):
    """Achata um JSON aninhado em (caminho_da_chave, valor_string)."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_prefix = f"{prefix}.{k}" if prefix else k
            yield from flatten(v, new_prefix)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            new_prefix = f"{prefix}.{i}" if prefix else str(i)
            yield from flatten(v, new_prefix)
    elif isinstance(obj, str):
        yield prefix, obj


def pair_files(en_dir: Path, pt_dir: Path):
    en_files = sorted(en_dir.glob("*.json"))
    print(f"[scan] {len(en_files)} arquivo(s) .json em {en_dir}/")
    for f in en_files:
        print(f"  - {f.name}")

    pt_files_existing = sorted(pt_dir.glob("*.json"))
    print(f"\n[scan] {len(pt_files_existing)} arquivo(s) .json em {pt_dir}/")
    for f in pt_files_existing:
        print(f"  - {f.name}")

    print(f"\n[pareamento] substituindo 'EN' por 'PTBR' nos nomes...")
    pairs = []
    for en_file in en_files:
        pt_name = en_file.name.replace("EN", "PTBR")
        pt_file = pt_dir / pt_name
        if pt_file.exists():
            print(f"  OK   {en_file.name}  <->  {pt_name}")
            pairs.append((en_file, pt_file))
        else:
            print(f"  MISS {en_file.name}  ->  esperado {pt_name} (nao existe)")
    return pairs


def analyze(en_file: Path, pt_file: Path, ratio: float, min_src: int):
    print(f"\n[analisando] {en_file.name}  vs  {pt_file.name}")

    try:
        with open(en_file, encoding="utf-8") as f:
            en_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"  [erro] JSON invalido em {en_file.name}: {e}")
        return []
    try:
        with open(pt_file, encoding="utf-8") as f:
            pt_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"  [erro] JSON invalido em {pt_file.name}: {e}")
        return []

    en_pairs = list(flatten(en_data))
    pt_pairs = list(flatten(pt_data))
    pt_map = dict(pt_pairs)

    print(f"  EN: {len(en_pairs)} strings   PT: {len(pt_pairs)} strings")

    findings = []
    skipped_short_src = 0
    missing_in_pt = 0
    checked = 0

    for key, src in en_pairs:
        if len(src) < min_src:
            skipped_short_src += 1
            continue
        if key not in pt_map:
            missing_in_pt += 1
            continue
        checked += 1
        tgt = pt_map[key]
        threshold = len(src) * ratio
        if len(tgt) < threshold:
            findings.append({
                "file": en_file.name,
                "key": key,
                "src_len": len(src),
                "tgt_len": len(tgt),
                "ratio": round(len(tgt) / len(src), 2) if len(src) else 0,
                "source": src,
                "target": tgt,
            })

    print(f"  comparadas: {checked}   ignoradas (src curto): {skipped_short_src}   "
          f"sem par no PT: {missing_in_pt}   suspeitas: {len(findings)}")
    return findings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--en-dir", default="EN")
    ap.add_argument("--pt-dir", default="PTBR")
    ap.add_argument("--ratio", type=float, default=0.5)
    ap.add_argument("--min-src", type=int, default=2)
    ap.add_argument("--out", default="short_translations.csv")
    args = ap.parse_args()

    print(f"[config] en-dir={args.en_dir}  pt-dir={args.pt_dir}  "
          f"ratio={args.ratio}  min-src={args.min_src}  out={args.out}")
    print(f"[config] cwd = {Path.cwd()}\n")

    en_dir = Path(args.en_dir)
    pt_dir = Path(args.pt_dir)

    if not en_dir.is_dir():
        print(f"[erro] pasta EN nao encontrada: {en_dir.resolve()}", file=sys.stderr)
        sys.exit(1)
    if not pt_dir.is_dir():
        print(f"[erro] pasta PTBR nao encontrada: {pt_dir.resolve()}", file=sys.stderr)
        sys.exit(1)

    pairs = pair_files(en_dir, pt_dir)
    print(f"\n[resultado] {len(pairs)} par(es) validos para analise")

    if not pairs:
        print("[erro] nenhum par encontrado.", file=sys.stderr)
        sys.exit(1)

    all_findings = []
    for en_file, pt_file in pairs:
        all_findings.extend(analyze(en_file, pt_file, args.ratio, args.min_src))

    all_findings.sort(key=lambda x: x["ratio"])

    with open(args.out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "file", "key", "src_len", "tgt_len", "ratio", "source", "target"
        ])
        writer.writeheader()
        writer.writerows(all_findings)

    print(f"\n{'='*60}")
    print(f"Total: {len(all_findings)} ocorrencia(s) escrita(s) em {args.out}")
    print(f"{'='*60}")

    if all_findings:
        print(f"\nTop 20 mais gritantes:\n")
        for f in all_findings[:20]:
            print(f'  [{f["file"]}] "{f["key"]}"')
            print(f'    EN ({f["src_len"]}): {f["source"][:80]}')
            print(f'    PT ({f["tgt_len"]}): {f["target"][:80]}')
            print(f'    ratio: {f["ratio"]}\n')
    else:
        print("\nNenhuma ocorrencia encontrada.")
        print("Tente: --ratio 0.7  ou  --min-src 10")


if __name__ == "__main__":
    main()