#!/usr/bin/env python3
"""L46 — Final audit: compares the L00 inventory with the generated catalog and writes
docs/audit.md and knowledge/dnd5e/audit.json.

Checks: every expected entry exists (by ref) and was extracted by the expected lot; no entry
outside the inventory except section entries; no duplicate refs; source coverage of every
lot (tools/validate/coverage.py); refs resolved (graph from L43); master decisions and
not-automated stat block abilities; source defects recorded in the inventory.

Usage: python3 -I tools/build/l46_final_audit.py
"""
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INV = ROOT / "inventory" / "dnd5e" / "srd-5.2.1"
KNOW = ROOT / "knowledge" / "dnd5e"


def main():
    inv = json.loads((INV / "entries.json").read_text(encoding="utf-8"))
    expected = {e["ref"]: e for e in inv["entries"]}
    entries = {}
    dup = []
    for p in sorted((KNOW / "entries").rglob("*.json")):
        e = json.loads(p.read_text(encoding="utf-8"))
        if e["ref"] in entries:
            dup.append(e["ref"])
        entries[e["ref"]] = e
    missing = sorted(r for r in expected if r not in entries)
    wrong_lot = sorted(r for r, e in expected.items() if r in entries and entries[r]["source"]["extracted_by"] != e["lot"])
    extra = sorted(r for r in entries if r not in expected)
    extra_kinds = Counter(entries[r]["kind"] for r in extra)
    cov = json.loads(subprocess.run([sys.executable, "-I", "tools/validate/coverage.py"], cwd=ROOT, capture_output=True, text=True).stdout)
    graph = json.loads((KNOW / "graph" / "refs.json").read_text(encoding="utf-8"))["summary"]
    mds = Counter(m["reason"] for e in entries.values() for m in e.get("master_decisions", []))
    reports = {p.stem.split("_")[0]: json.loads(p.read_text(encoding="utf-8")) for p in sorted((INV / "reports").glob("*_master_decisions.json"))}
    lots = json.loads((INV / "lots.json").read_text(encoding="utf-8"))["lots"]
    per_lot = []
    for l in lots:
        exp = [r for r, e in expected.items() if e["lot"] == l["lot"]]
        got = [r for r, e in entries.items() if e["source"]["extracted_by"] == l["lot"]]
        c = cov.get(l["lot"], {})
        per_lot.append({"lot": l["lot"], "title": l["title"], "expected": len(exp), "present": sum(1 for r in exp if r in entries),
                        "entries": len(got), "source_nodes": c.get("nodes"), "uncovered": c.get("uncovered")})
    audit = {
        "inventory_entries": len(expected), "catalog_entries": len(entries), "missing": missing, "wrong_lot": wrong_lot,
        "duplicates": dup, "extra_section_entries": dict(extra_kinds), "graph": graph,
        "coverage": {"lots": len(cov), "nodes": sum(v["nodes"] for v in cov.values()), "uncovered": sum(v["uncovered"] for v in cov.values())},
        "master_decisions_by_reason": dict(mds),
        "stat_block_abilities": {k: {"automated": v["automated"], "rider_decision": v["partial_riders"], "master_decision": v["not_automated"]}
                                 for k, v in reports.items()},
        "source_inconsistencies": len(inv.get("source_inconsistencies", [])),
        "lots": per_lot,
    }
    ok = not (missing or wrong_lot or dup or graph["unresolved"] or audit["coverage"]["uncovered"])
    audit["ok"] = ok
    (KNOW / "audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = ["# Auditoria final (L46)", "",
             f"- Inventário: {len(expected)} entradas esperadas; catálogo: {len(entries)} entradas "
             f"({len(entries) - len(expected) + len(missing)} entradas de seção/regra além do inventário).",
             f"- Faltando: {len(missing)}; lote errado: {len(wrong_lot)}; duplicadas: {len(dup)}.",
             f"- Cobertura da fonte: {audit['coverage']['nodes']} nós em {audit['coverage']['lots']} lotes, {audit['coverage']['uncovered']} sem cobertura.",
             f"- Grafo de refs: {graph['entries']} nós, {graph['edges']} arestas, {graph['unresolved']} não resolvidas, {graph['unreferenced']} sem referência de entrada.",
             f"- Decisões do mestre por motivo: " + ", ".join(f"{k} {v}" for k, v in sorted(mds.items())) + ".",
             f"- Inconsistências da fonte registradas no inventário: {audit['source_inconsistencies']}.",
             "", "| Lote | Título | Esperadas | Presentes | Entradas | Nós da fonte | Sem cobertura |", "|---|---|---|---|---|---|---|"]
    for r in per_lot:
        lines.append(f"| {r['lot']} | {r['title']} | {r['expected']} | {r['present']} | {r['entries']} | {r['source_nodes'] if r['source_nodes'] is not None else '—'} | "
                     f"{r['uncovered'] if r['uncovered'] is not None else '—'} |")
    lines += ["", "## Habilidades de bloco de estatísticas (L33–L40)", "", "| Lote | Automatizadas | Decisão (complemento) | Decisão do mestre |", "|---|---|---|---|"]
    for k, v in audit["stat_block_abilities"].items():
        lines.append(f"| {k} | {v['automated']} | {v['rider_decision']} | {v['master_decision']} |")
    lines += ["", f"Resultado: {'OK' if ok else 'FALHAS'}", ""]
    (ROOT / "docs" / "audit.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({k: audit[k] for k in ("inventory_entries", "catalog_entries", "coverage", "ok")}))
    if missing:
        print("MISSING", missing[:20])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
