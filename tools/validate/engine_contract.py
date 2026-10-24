#!/usr/bin/env python3
"""Engine contract: what the catalog asks of an engine vs what the prototype executes.

For every op, predicate, variable and event used anywhere in the catalog, report whether
tools/engine implements it, and how many entries are fully executable by the prototype.
Also lists effect notes that may still carry a mechanic (keyword heuristic) for review.
The validator already guarantees every name is declared in the registries; this report is
the production engine's to-do list.

Usage: python3 -I tools/validate/engine_contract.py [--out reports/engine_contract.json]
"""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.engine.engine import Engine  # noqa: E402

ENT = ROOT / "knowledge" / "dnd5e" / "entries"
# Words that, in a note, often hide a rule (timing, limits, targeting) rather than clarify.
HINTS = re.compile(r"\b(only|next|unless|until|instead|half|double|once|each|repeat|none of|no more than|"
                   r"at the (start|end)|within|divided|up to)\b", re.I)
EXPR_OPS = {"add", "sub", "mul", "div", "min", "max", "neg"}


def walk(n, out, entry, path=""):
    if isinstance(n, dict):
        op = n.get("op")
        if isinstance(op, str) and op not in EXPR_OPS:
            out["op"][op].add(entry)
            if n.get("note") and HINTS.search(n["note"]):
                out["notes"].append({"ref": entry, "op": op, "note": n["note"]})
            for k in n:
                if k not in ("op", "note", "id", "target", "duration", "when", "then", "on_hit", "on_miss", "on_fail",
                             "on_success", "on_critical", "options", "effects"):
                    out["field"][f"{op}.{k}"].add(entry)
        if "pred" in n:
            out["pred"][n["pred"]].add(entry)
        if "var" in n and isinstance(n["var"], str):
            out["var"][n["var"].split(".")[0]].add(entry)
        if "event" in n and isinstance(n["event"], str):
            out["event"][n["event"].split(".")[0]].add(entry)
        for k, v in n.items():
            walk(v, out, entry, f"{path}/{k}")
    elif isinstance(n, list):
        for i, v in enumerate(n):
            walk(v, out, entry, f"{path}/{i}")


# Fields of ops the prototype reads (anything else is listed as not yet executed).
READ_FIELDS = {
    "attack": {"attack_type", "bonus", "ability_modifier_to_damage"},
    "damage": {"amount", "damage_type", "critical"},
    "heal": {"amount"}, "temp_hp": {"amount"},
    "save": {"ability", "dc", "half_on_success"},
    "check": {"ability", "skill", "dc"},
    "apply_condition": {"condition"}, "remove_condition": {"conditions"},
    "modifier": {"stat", "mode", "value"}, "roll_mode": {"mode", "rolls", "direction"},
    "defense": {"kind", "damage_types"}, "restrict": {"restrictions"}, "auto_result": {"rolls", "result", "direction"},
    "speed": {"movement", "mode", "value"}, "resource": {"resource", "max", "recovery", "name"},
    "spend": {"resource", "amount"}, "restore": {"resource", "amount", "max_level"},
    "trigger": {"event", "condition", "cost", "optional", "frequency"},
    "activation": {"cost", "name", "requires", "uses", "action", "movement_cost"},
    "choice": {"choose", "chooser", "distinct"}, "repeat": {"times"},
    "grant": {"refs", "choose", "items", "gp", "filter"}, "reference": {"rule"},
    "proficiency": {"category", "items", "choose", "from", "expertise"},
    "move": {"mode", "distance_feet"}, "end_effect": {"scope"}, "reroll": {"rolls", "keep"},
    "master_decision": {"decision"}, "sense": {"sense", "range_feet"},
}
VARS = {"ability_mod", "ability_score", "class_level", "chosen", "speed", "condition_level", "proficiency_bonus", "level",
        "hp_max", "spell_slot_level", "damage_amount", "attack_ability_mod", "spellcasting_mod", "spell_save_dc",
        "spell_attack_bonus"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "reports" / "engine_contract.json"))
    a = ap.parse_args(argv)
    use = {k: defaultdict(set) for k in ("op", "pred", "var", "event", "field")}
    use["notes"] = []
    entries = {}
    for p in sorted(ENT.rglob("*.json")):
        e = json.loads(p.read_text(encoding="utf-8"))
        before = {k: {n for n, s in use[k].items() if e["ref"] in s} for k in ("op", "pred", "var", "field")}
        walk(e.get("effects") or [], use, e["ref"])
        entries[e["ref"]] = {k: {n for n, s in use[k].items() if e["ref"] in s} - before[k] or
                             {n for n, s in use[k].items() if e["ref"] in s} for k in ("op", "pred", "var", "field")}
    impl = {
        # resource / proficiency are applied by Engine.init_resources and the Builder
        "op": {m[3:] for m in dir(Engine) if m.startswith("op_")} | {"resource", "proficiency"},
        "pred": {m[2:] for m in dir(Engine) if m.startswith("p_")},
        "var": VARS,
        "field": {f"{op}.{f}" for op, fs in READ_FIELDS.items() for f in fs},
    }
    report = {}
    for k in ("op", "pred", "var", "event", "field"):
        rows = sorted(((n, len(s)) for n, s in use[k].items()), key=lambda r: -r[1])
        have = impl.get(k)
        report[k] = {"used": len(rows),
                     **({"implemented": sum(1 for n, _ in rows if n in have),
                         "missing": [{"name": n, "entries": c} for n, c in rows if n not in have]} if have else {})}
    full = [r for r, u in entries.items() if all(n in impl[k] for k in ("op", "pred", "var", "field") for n in u[k])]
    with_fx = [r for r, u in entries.items() if u["op"]]
    report["entries"] = {"with_effects": len(with_fx), "fully_executable_by_prototype": len([r for r in full if r in with_fx])}
    report["notes_to_review"] = {"count": len(use["notes"]), "by_op": dict(Counter(n["op"] for n in use["notes"]).most_common()),
                                 "items": use["notes"]}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "missing" and kk != "items"} for k, v in report.items()},
                     ensure_ascii=False))
    return report


if __name__ == "__main__":
    main()
