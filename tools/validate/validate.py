#!/usr/bin/env python3
"""Validate DRPG schemas, examples and knowledge files.

Checks, in order:
  1. every schema/*.schema.json is a valid JSON Schema (draft 2020-12);
  2. every schema/examples/<schema>[.<label>].example.json validates against <schema>;
  3. every knowledge/<system>/system.json validates against system;
  4. every catalog entry (examples named catalog_entry.* and knowledge/**/entries/*.json)
     passes structural validation plus semantic checks:
       - ref = <system>/<kind>/<slug>, with kind and system matching the entry;
       - coverage segments, joined, reproduce `text` exactly (whitespace-normalized);
       - coverage pointers resolve; 'md:<id>' and master_decision effects name declared decisions;
       - `refs`, when present, equals the set of refs actually used by the entry;
       - every registry name (variables, stats, rolls, events, predicates, frequencies,
         damage types, sizes, creature types, area shapes, senses, movement modes, action
         costs, abilities, skills) is declared in the system's registries.

Usage: python3 -I tools/validate/validate.py [paths...]   (default: whole repository)
Exit status 1 if any error is found.
"""
import json
import re
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schema"
KNOWLEDGE = ROOT / "knowledge"

REF_RE = re.compile(r"^(?:[a-z0-9]+|custom/[A-Za-z0-9_-]+)/[a-z0-9-]+/[a-z0-9]+(?:-[a-z0-9]+)*$")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def schema_registry():
    schemas, resources = {}, []
    for p in sorted(SCHEMA_DIR.glob("*.schema.json")):
        doc = load_json(p)
        name = p.name[: -len(".schema.json")]
        schemas[name] = doc
        resources.append((doc["$id"], Resource.from_contents(doc)))
    return schemas, Registry().with_resources(resources)


def norm(text):
    return re.sub(r"\s+", " ", text).strip()


def resolve_pointer(doc, pointer):
    cur = doc
    for part in pointer.split("/")[1:]:
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(cur, list):
            if not part.isdigit() or int(part) >= len(cur):
                return False
            cur = cur[int(part)]
        elif isinstance(cur, dict):
            if part not in cur:
                return False
            cur = cur[part]
        else:
            return False
    return True


# ---------------------------------------------------------------- vocabulary walk

class Vocab:
    """Names declared by a system.json, used to close the effect vocabulary."""

    def __init__(self, system):
        self.doc = system
        self.ref = system.get("ref")
        reg = system["registries"]
        self.sets = {k: {i["id"] for i in v} for k, v in reg.items()}
        self.sets["abilities"] = {a["id"] for a in system["abilities"]}
        self.sets["skills"] = {s["id"] for s in system.get("skills", [])}
        self.sets["action_costs"] = {a["id"] for a in system["action_economy"]} | {"none"}

    def has(self, registry, name):
        head = name.split(".", 1)[0]
        return head in self.sets.get(registry, set())


def walk_vocab(node, vocab, errors, where, ctx=None):
    """Collect registry-name violations and refs used inside an entry."""
    refs = set()

    def chk(registry, name, path):
        if vocab is not None and not vocab.has(registry, name):
            errors.append(f"{where}{path}: '{name}' is not declared in registry '{registry}'")

    def ident_or_choice(value, registry, path):
        if isinstance(value, str):
            chk(registry, value, path)
        elif isinstance(value, dict):
            for v in value.get("choose_from", []):
                chk(registry, v, path)
            if "var" in value:
                chk("variables", value["var"], path)

    def rec(n, path):
        if isinstance(n, list):
            for i, x in enumerate(n):
                rec(x, f"{path}/{i}")
            return
        if not isinstance(n, dict):
            return
        if "var" in n and isinstance(n["var"], str):
            chk("variables", n["var"], path)
        if "scale" in n and isinstance(n["scale"], dict):
            chk("variables", n["scale"].get("by", ""), path + "/scale")
        if "pred" in n and isinstance(n["pred"], str):
            chk("predicates", n["pred"], path)
        if "event" in n and isinstance(n["event"], str):
            chk("events", n["event"], path)
        if "shape" in n and isinstance(n["shape"], str):
            chk("area_shapes", n["shape"], path)
        if "creature_types" in n or "sizes" in n or "exclude_creature_types" in n:
            for t in n.get("creature_types", []) + n.get("exclude_creature_types", []):
                chk("creature_types", t, path)
            for t in n.get("sizes", []):
                chk("sizes", t, path)
        op = n.get("op")
        if op == "damage":
            ident_or_choice(n.get("damage_type"), "damage_types", path)
        elif op == "modifier":
            chk("stats", n.get("stat", ""), path)
        elif op == "roll_mode":
            for r in n.get("rolls", []):
                chk("rolls", r, path)
        elif op == "defense":
            for d in n.get("damage_types", []):
                ident_or_choice(d, "damage_types", path)
        elif op in ("save", "check"):
            ident_or_choice(n.get("ability"), "abilities", path)
            if "skill" in n:
                ident_or_choice(n["skill"], "skills", path)
        elif op == "restrict":
            for r in n.get("restrictions", []):
                chk("restrictions", r, path)
        elif op == "reroll":
            for r in n.get("rolls", []):
                chk("rolls", r, path)
        elif op == "auto_result":
            for r in n.get("rolls", []):
                chk("rolls", r, path)
        elif op == "sense":
            chk("senses", n.get("sense", ""), path)
        elif op == "speed":
            chk("movement_modes", n.get("movement", ""), path)
        elif op in ("trigger", "activation"):
            if "cost" in n:
                chk("action_costs", n["cost"], path)
        if "frequency" in n and isinstance(n["frequency"], dict):
            chk("frequencies", n["frequency"].get("per", ""), path + "/frequency")
        for key in ("ref", "condition", "rule", "spell", "creature", "into", "table", "extends"):
            v = n.get(key)
            if isinstance(v, str) and REF_RE.match(v):
                refs.add(v)
        for key in ("conditions", "refs"):
            for v in n.get(key, []) if isinstance(n.get(key), list) else []:
                if isinstance(v, str) and REF_RE.match(v):
                    refs.add(v)
        for k, v in n.items():
            if k in ("text", "note", "prompt", "source_text", "coverage", "refs", "source"):
                continue
            rec(v, f"{path}/{k}")

    rec(node, "")
    return refs


# ---------------------------------------------------------------- entry checks

def check_entry(entry, where, vocab):
    errors = []
    ref = entry["ref"]
    parts = ref.split("/")
    system = parts[0] if parts[0] != "custom" else None
    kind = parts[-2]
    if kind != entry["kind"]:
        errors.append(f"{where}: ref kind '{kind}' differs from kind '{entry['kind']}'")
    if system and system != entry["source"]["system"]:
        errors.append(f"{where}: ref system '{system}' differs from source.system '{entry['source']['system']}'")

    md_ids = [m["id"] for m in entry.get("master_decisions", [])]
    if len(md_ids) != len(set(md_ids)):
        errors.append(f"{where}: duplicate master decision ids")

    if "text" in entry:
        joined = " ".join(s["text"] for s in entry["coverage"])
        if norm(joined) != norm(entry["text"]):
            a, b = norm(joined), norm(entry["text"])
            k = next((i for i in range(min(len(a), len(b))) if a[i] != b[i]), min(len(a), len(b)))
            errors.append(f"{where}: coverage does not reproduce text (first difference at char {k}: "
                          f"coverage '{a[k:k + 40]}' vs text '{b[k:k + 40]}')")
    for i, seg in enumerate(entry["coverage"]):
        for by in seg.get("by", []):
            if by.startswith("/"):
                if not resolve_pointer(entry, by):
                    errors.append(f"{where}/coverage/{i}: pointer '{by}' does not resolve")
            elif "#" in by:
                target, ptr = by.split("#", 1)
                if not REF_RE.match(target):
                    errors.append(f"{where}/coverage/{i}: '{by}' has an invalid ref")
                elif vocab is not None and target == vocab.ref and not resolve_pointer(vocab.doc, ptr):
                    errors.append(f"{where}/coverage/{i}: pointer '{ptr}' does not resolve in {target}")
            elif by.startswith("md:"):
                if by[3:] not in md_ids:
                    errors.append(f"{where}/coverage/{i}: master decision '{by[3:]}' not declared")
            elif not REF_RE.match(by):
                errors.append(f"{where}/coverage/{i}: '{by}' is neither a pointer, a ref nor md:<id>")
        if seg["status"] == "master_decision" and not any(b.startswith("md:") for b in seg.get("by", [])):
            errors.append(f"{where}/coverage/{i}: status master_decision needs an 'md:<id>'")
        if seg["status"] == "shared_rule" and not any(REF_RE.match(b) for b in seg.get("by", [])):
            errors.append(f"{where}/coverage/{i}: status shared_rule needs a ref")

    def find_md(n):
        if isinstance(n, dict):
            if n.get("op") == "master_decision" and n.get("decision") not in md_ids:
                errors.append(f"{where}: effect references undeclared master decision '{n.get('decision')}'")
            for v in n.values():
                find_md(v)
        elif isinstance(n, list):
            for v in n:
                find_md(v)

    find_md(entry.get("effects", []))
    for m in entry.get("master_decisions", []):
        find_md(m.get("options", []))

    used = walk_vocab({k: v for k, v in entry.items() if k not in ("ref",)}, vocab, errors, where)
    used |= {b.split("#", 1)[0] for s in entry["coverage"] for b in s.get("by", [])
             if REF_RE.match(b.split("#", 1)[0])}
    if "refs" in entry and set(entry["refs"]) != used:
        missing, extra = used - set(entry["refs"]), set(entry["refs"]) - used
        errors.append(f"{where}: refs field out of date (missing {sorted(missing)}, extra {sorted(extra)})")
    return errors


def check_lookups(docs):
    """Every table lookup names a table (by id) and a column that exist in the referenced entry."""
    errors = []

    def tables(n, out):
        if isinstance(n, dict):
            if "id" in n and isinstance(n.get("columns"), list):
                out[n["id"]] = n["columns"]
            for v in n.values():
                tables(v, out)
        elif isinstance(n, list):
            for v in n:
                tables(v, out)
        return out

    def walk(n, where):
        if isinstance(n, dict):
            if "table" in n and "column" in n and "key" in n:
                target = docs.get(n["table"])
                if target is None:
                    errors.append(f"{where}: lookup table entry '{n['table']}' not found")
                else:
                    cols = tables(target[0].get("data", {}), {})
                    tid = n.get("table_id")
                    if tid is not None and tid not in cols:
                        errors.append(f"{where}: table '{tid}' not in {n['table']}")
                    elif tid is not None and n["column"] not in cols[tid]:
                        errors.append(f"{where}: column '{n['column']}' not in table '{tid}'")
            for v in n.values():
                walk(v, where)
        elif isinstance(n, list):
            for v in n:
                walk(v, where)

    for doc, rel in docs.values():
        walk({k: v for k, v in doc.items() if k in ("effects", "data", "master_decisions")}, rel)
    return errors


# ---------------------------------------------------------------- main

def main(args):
    errors, counts = [], {"schemas": 0, "examples": 0, "systems": 0, "entries": 0}
    schemas, registry = schema_registry()
    validators = {}
    for name, doc in schemas.items():
        try:
            Draft202012Validator.check_schema(doc)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"schema/{name}.schema.json: invalid schema: {exc}")
            continue
        validators[name] = Draft202012Validator(doc, registry=registry)
        counts["schemas"] += 1

    systems = {}
    for p in sorted(KNOWLEDGE.glob("*/system.json")) if KNOWLEDGE.exists() else []:
        doc = load_json(p)
        errs = sorted(validators["system"].iter_errors(doc), key=lambda e: list(e.path))
        errors += [f"{p.relative_to(ROOT)}{'/' + '/'.join(map(str, e.path)) if e.path else ''}: {e.message}" for e in errs]
        systems[doc["id"]] = Vocab(doc)
        counts["systems"] += 1

    def validate_file(path, schema_name):
        doc = load_json(path)
        rel = str(path.relative_to(ROOT))
        errs = sorted(validators[schema_name].iter_errors(doc), key=lambda e: list(e.path))
        for e in errs:
            loc = "/".join(map(str, e.path))
            errors.append(f"{rel}{'/' + loc if loc else ''}: {e.message[:300]}")
        if not errs and schema_name == "catalog_entry":
            vocab = systems.get(doc["source"]["system"])
            if vocab is None and doc["source"]["origin"] == "official":
                errors.append(f"{rel}: no system.json for system '{doc['source']['system']}'")
            errors.extend(check_entry(doc, rel, vocab))
            counts["entries"] += 1
        return doc

    for p in sorted((SCHEMA_DIR / "examples").glob("*.example.json")):
        name = p.name.split(".", 1)[0]
        if name not in validators:
            errors.append(f"{p.relative_to(ROOT)}: no schema named '{name}'")
            continue
        validate_file(p, name)
        counts["examples"] += 1

    docs = {}
    for p in sorted(KNOWLEDGE.glob("**/entries/**/*.json")) if KNOWLEDGE.exists() else []:
        doc = validate_file(p, "catalog_entry")
        if isinstance(doc, dict) and "ref" in doc:
            docs[doc["ref"]] = (doc, str(p.relative_to(ROOT)))
    errors.extend(check_lookups(docs))

    for e in errors:
        print("ERROR", e)
    print(json.dumps({"ok": not errors, "errors": len(errors), **counts}))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
