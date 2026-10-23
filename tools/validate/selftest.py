#!/usr/bin/env python3
"""Negative tests for the validator: each mutation of a valid example must be rejected.

Usage: python3 -I tools/validate/selftest.py
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate as V  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
EX = ROOT / "schema" / "examples"


def errors_for(doc, schema_name, vocab):
    schemas, registry = V.schema_registry()
    validator = V.Draft202012Validator(schemas[schema_name], registry=registry)
    errs = [e.message for e in validator.iter_errors(doc)]
    if not errs and schema_name == "catalog_entry":
        errs = V.check_entry(doc, "selftest", vocab)
    return errs


def main():
    system = json.loads((ROOT / "knowledge" / "dnd5e" / "system.json").read_text(encoding="utf-8"))
    vocab = V.Vocab(system)
    base = json.loads((EX / "catalog_entry.spell-fireball.example.json").read_text(encoding="utf-8"))
    assert not errors_for(base, "catalog_entry", vocab), "baseline example must be valid"

    cases = []

    def case(name, mutate, schema="catalog_entry"):
        doc = copy.deepcopy(base)
        mutate(doc)
        cases.append((name, doc, schema))

    case("coverage drops a sentence", lambda d: d["coverage"].pop(2))
    case("coverage alters the text", lambda d: d["coverage"][1].__setitem__("text", d["coverage"][1]["text"] + " X"))
    case("undeclared damage type", lambda d: d["effects"][0]["on_fail"][0].__setitem__("damage_type", "plasma"))
    case("undeclared variable", lambda d: d["effects"][0].__setitem__("dc", {"var": "spell_dc_typo"}))
    case("unknown op", lambda d: d["effects"].append({"op": "explode"}))
    case("op missing required field", lambda d: d["effects"].append({"op": "damage", "damage_type": "fire"}))
    case("broken coverage pointer", lambda d: d["coverage"][1].__setitem__("by", ["/effects/9"]))
    case("undeclared master decision", lambda d: d["effects"].append({"op": "master_decision", "decision": "nope"}))
    case("ref kind mismatch", lambda d: d.__setitem__("kind", "item"))
    case("official entry without text", lambda d: d.pop("text"))
    case("official entry with overrides", lambda d: d.update({"extends": "dnd5e/spell/fire-bolt", "overrides": {}}))
    case("tier 2 without effects", lambda d: (d.pop("effects"), d.pop("master_decisions"), d.__setitem__("tier", 2)))
    case("extra property", lambda d: d.__setitem__("color", "red"))
    case("refs field out of date", lambda d: d.__setitem__("refs", ["dnd5e/spell/fire-bolt"]))
    case("bad area shape", lambda d: d["effects"][0]["target"]["area"].__setitem__("shape", "torus"))
    case("dice with odd faces", lambda d: d["effects"][0]["on_fail"][0]["amount"]["dice"].__setitem__("faces", 7))

    failures = []
    for name, doc, schema in cases:
        errs = errors_for(doc, schema, vocab)
        status = "rejected" if errs else "ACCEPTED"
        print(f"{status:9} {name}: {errs[0][:110] if errs else ''}")
        if not errs:
            failures.append(name)
    print(json.dumps({"cases": len(cases), "failures": failures}))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
