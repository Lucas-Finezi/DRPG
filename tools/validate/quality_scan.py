#!/usr/bin/env python3
"""Quality scan: signals the structural validator does not catch, to decide what still
blocks a definitive version of the catalog. Read-only; writes nothing unless --out is given.

Checks
  decisions      master decisions by reason, kind and lot
  placeholders   'reference' effects pointing at the entry itself (behaviour only in a note)
  hidden_rules   effect notes that carry numbers, dice or DCs (mechanics not in fields)
  descriptive    descriptive coverage segments whose text looks mechanical
  text_breaks    paragraphs still cut mid-sentence; broken markdown emphasis
  registry       registered names never used; predicate/variable params not matching usage
  spells         upcast / cantrip-upgrade text without a matching structure
  creatures      stat blocks missing core values; attacks without damage; saves without effect
  kind_schemas   entry kinds whose data has no kind schema
  rules_text     data.rules items whose only content is free text

Usage: python3 -I tools/validate/quality_scan.py [--out FILE]
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KNOW = ROOT / "knowledge" / "dnd5e"
MECH = re.compile(r"\b(DC \d+|\d+d\d+|saving throw|Advantage|Disadvantage|bonus to|damage|Hit Points?|Speed|condition)\b")


def walk(o, path=""):
    if isinstance(o, dict):
        yield path, o
        for k, v in o.items():
            yield from walk(v, f"{path}/{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk(v, f"{path}/{i}")


def main():
    entries = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((KNOW / "entries").rglob("*.json"))]
    system = json.loads((KNOW / "system.json").read_text(encoding="utf-8"))
    reg = system["registries"]
    out = {}

    # decisions
    by_reason, by_kind_reason, by_lot = Counter(), Counter(), Counter()
    for e in entries:
        for m in e.get("master_decisions", []):
            by_reason[m["reason"]] += 1
            by_kind_reason[(e["kind"], m["reason"])] += 1
            by_lot[(e["source"]["extracted_by"], m["reason"])] += 1
    out["decisions"] = {"by_reason": dict(by_reason),
                        "by_kind": {f"{k}/{r}": v for (k, r), v in sorted(by_kind_reason.items())},
                        "not_automatable_by_lot": {l: v for (l, r), v in sorted(by_lot.items()) if r == "not_automatable"}}

    # placeholders and hidden rules
    ph, hidden = defaultdict(list), defaultdict(list)
    for e in entries:
        for path, d in walk(e.get("effects", []), "/effects"):
            if d.get("op") == "reference" and d.get("rule") == e["ref"]:
                ph[e["kind"]].append(f"{e['ref']}{path}: {d.get('note', '')[:90]}")
            n = d.get("note")
            if isinstance(n, str) and re.search(r"\b(\d+d\d+|DC \d+|\d+ (feet|minutes?|hours?|days?)|[+−-]\d+)\b", n) and d.get("op") not in ("reference",):
                hidden[e["kind"]].append(f"{e['ref']}{path} [{d.get('op')}]: {n[:100]}")
    out["placeholders"] = {"count_by_kind": {k: len(v) for k, v in ph.items()}, "examples": {k: v[:6] for k, v in ph.items()}}
    out["hidden_rules"] = {"count_by_kind": {k: len(v) for k, v in hidden.items()}, "examples": {k: v[:5] for k, v in hidden.items()}}

    # descriptive segments that look mechanical
    desc = defaultdict(list)
    for e in entries:
        for s in e["coverage"]:
            if s["status"] == "descriptive" and len(MECH.findall(s["text"])) >= 2:
                desc[e["kind"]].append(f"{e['ref']}: {s['text'][:110]}")
    out["descriptive_mechanical"] = {"count": sum(len(v) for v in desc.values()), "by_kind": {k: len(v) for k, v in desc.items()},
                                     "examples": [x for v in desc.values() for x in v][:25]}

    # text breaks (labelled header lines and column word lists are layout, counted apart)
    def strip_emph(t):
        t, prev = t.replace("\\*", ""), None
        while prev != t:
            prev = t
            t = re.sub(r"\*\*\*([^*]+?)\*\*\*", r"\1", t)
            t = re.sub(r"\*\*([^*]+?)\*\*", r"\1", t)
            t = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"\1", t)
        return t
    breaks, emph, wordlists = [], [], []
    for e in entries:
        paras = e["text"].split("\n\n")
        for a, b in zip(paras, paras[1:]):
            a1, b1 = a.rstrip(), b.lstrip()
            if not a1 or not b1 or a1.startswith(("|", "#", "- ")) or b1.startswith(("|", "#", "- ", "*", "**")):
                continue
            if re.match(r"^\*\*[^*]+:\*\*", a1):
                continue
            if re.fullmatch(r"(?:[A-Z][a-z]+(?: |$)){2,6}", a1 + " "):
                wordlists.append(e["ref"])
                continue
            if re.search(r"[A-Za-z,’]$", a1) and re.match(r"^([a-z]|\d+ [a-z(]|[A-Z][a-z]+[ .,])", b1):
                breaks.append(f"{e['ref']}: …{a1[-45:]!r} | {b1[:40]!r}")
        for ln in e["text"].split("\n"):
            if "*" in strip_emph(ln):
                emph.append(f"{e['ref']}: {ln[:90]!r}")
    out["column_word_lists"] = sorted(set(wordlists))
    out["nbsp_in_text"] = sum(e["text"].count("\xa0") for e in entries)
    out["text_breaks"] = {"count": len(breaks), "examples": breaks[:40]}
    out["broken_emphasis"] = {"count": len(emph), "examples": emph[:25]}

    # registry usage and params
    used = defaultdict(Counter)
    bad_args = []
    params = {k: {x["id"]: set(x.get("params", [])) for x in v} for k, v in reg.items()}
    for e in entries + [system]:
        for path, d in walk(e):
            if "pred" in d and isinstance(d["pred"], str):
                used["predicates"][d["pred"]] += 1
                exp = params.get("predicates", {}).get(d["pred"])
                got = set((d.get("args") or {}).keys())
                if exp is not None and got and not got <= exp | {"item"}:
                    bad_args.append(f"{e.get('ref')}{path}: {d['pred']} args {sorted(got)} vs params {sorted(exp)}")
            if "var" in d and isinstance(d["var"], str):
                used["variables"][d["var"].split(".")[0]] += 1
            if "event" in d and isinstance(d["event"], str):
                used["events"][d["event"].split(".")[0]] += 1
            if d.get("op") == "modifier" and isinstance(d.get("stat"), str):
                used["stats"][d["stat"].split(".")[0]] += 1
            if d.get("op") == "restrict":
                for r in d.get("restrictions", []):
                    used["restrictions"][r] += 1
            for r in [x for x in d.get("rolls", []) if isinstance(x, str)] if isinstance(d.get("rolls"), list) else []:
                used["rolls"][r.split(".")[0]] += 1
    unused = {k: sorted(set(params.get(k, {})) - set(used[k])) for k in ("predicates", "variables", "events", "stats", "restrictions")}
    out["registry"] = {"sizes": {k: len(v) for k, v in reg.items()}, "unused": {k: v for k, v in unused.items() if v},
                       "unused_count": {k: len(v) for k, v in unused.items()}, "bad_args": bad_args[:30], "bad_args_count": len(bad_args)}

    # spells
    sp_issues = []
    for e in entries:
        if e["kind"] != "spell":
            continue
        blob = json.dumps({k: e.get(k) for k in ("effects", "data")})
        if "Using a Higher-Level Spell Slot" in e["text"] and "spell_slot_level" not in blob and "upcast" not in blob:
            sp_issues.append(f"{e['ref']}: higher-level text without slot-level structure")
        if "Cantrip Upgrade" in e["text"] and '"by": "level"' not in blob and "cantrip" not in blob.lower():
            sp_issues.append(f"{e['ref']}: Cantrip Upgrade without level scaling")
        if not e.get("effects") and not (e.get("data") or {}).get("rules"):
            sp_issues.append(f"{e['ref']}: no effects and no rules")
    out["spells"] = {"count": len(sp_issues), "items": sp_issues}

    # creatures
    cr_issues = []
    for e in entries:
        if e["kind"] != "creature":
            continue
        d = e["data"]
        miss = [k for k in ("ac", "hp", "speed", "abilities") if k not in d]
        if "cr" not in d and e["facets"].get("group") != "embedded":
            miss.append("cr")
        if miss:
            cr_issues.append(f"{e['ref']}: missing {miss}")
        for path, x in walk(e.get("effects", []), "/effects"):
            if x.get("op") == "attack" and not x.get("on_hit"):
                cr_issues.append(f"{e['ref']}{path}: attack without on_hit")
            if x.get("op") == "save" and not (x.get("on_fail") or x.get("on_success")):
                cr_issues.append(f"{e['ref']}{path}: save without outcome")
    out["creatures"] = {"count": len(cr_issues), "items": cr_issues[:60]}

    # kind schemas
    have = {p.stem.replace(".schema", "") for p in (ROOT / "schema" / "kinds").glob("*.schema.json")}
    kinds = Counter(e["kind"] for e in entries)
    out["kind_schemas"] = {"with_schema": sorted(have), "without_schema": {k: v for k, v in sorted(kinds.items()) if k not in have}}

    # rules with only text
    rt = []
    for e in entries:
        for i, r in enumerate((e.get("data") or {}).get("rules", [])):
            keys = set(r) - {"id"}
            if keys and keys <= {"text"}:
                rt.append(f"{e['ref']}/data/rules/{i} ({r['id']})")
    out["rules_text_only"] = {"count": len(rt), "examples": rt[:20]}

    # tiers
    out["tier0"] = [e["ref"] for e in entries if e["tier"] == 0]
    out["inconsistencies"] = [f"{e['ref']}: {i.get('type', '')} {str(i.get('detail', i))[:80]}" for e in entries for i in e.get("inconsistencies", [])]

    txt = json.dumps(out, ensure_ascii=False, indent=1)
    if "--out" in sys.argv:
        Path(sys.argv[sys.argv.index("--out") + 1]).write_text(txt + "\n", encoding="utf-8")
    summary = {k: (v.get("count") if isinstance(v, dict) and "count" in v else (len(v) if isinstance(v, list) else None)) for k, v in out.items()}
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
