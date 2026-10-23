#!/usr/bin/env python3
"""Stat block parsing shared by creature entries (first used for creatures embedded in spells).

parse(title, page) reads a stat block: the size/type/alignment line, AC, HP, Speed, the ability
table, the other labelled lines (Saving Throws, Skills, Resistances, Immunities, Senses,
Languages, CR, Gear...) and the Traits / Actions / Bonus Actions / Reactions / Legendary Actions
sections, each a list of named abilities. creature_entry() turns it into a catalog entry whose
coverage points every line to the structured value; `overrides` adds expressions for values the
text gives as formulas (e.g. "10 + 1 per spell level").
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import NODES, build, find, slugify  # noqa: E402

SECTIONS = ("Traits", "Actions", "Bonus Actions", "Reactions", "Legendary Actions")
ABIL = ("Str", "Dex", "Con", "Int", "Wis", "Cha")
SIZES = ("Tiny", "Small", "Medium", "Large", "Huge", "Gargantuan")


def nodes_of(title, page, level=None, end_at_cr=False):
    """Nodes of a stat block. `end_at_cr`: the block ends with its CR line (a stat block printed
    inside another description, whose text goes on after it)."""
    i = find(title, level or 3, page)
    j = i + 1
    while j < len(NODES) and not (NODES[j].type == "h" and NODES[j].level <= 4 and not NODES[j].sidebar):
        j += 1
        if end_at_cr and NODES[j - 1].text.startswith("**CR**"):
            break
    return [n for n in NODES[i + 1:j] if not n.sidebar]


def _num(s):
    return int(s.replace("−", "-").replace("+", ""))


def parse(title, page, level=None, end_at_cr=False):
    nodes = nodes_of(title, page, level, end_at_cr)
    data, section, lines = {}, None, []
    # rejoin wrapped labelled lines and wrapped ability names
    merged = []
    for n in nodes:
        t = n.text
        if merged and merged[-1][0] == "p" and n.type == "p" and section is None and \
                not re.match(r"^(\*\*\*|\*\*[A-Z])", t) and not t.startswith("*") and merged[-1][1].startswith("**"):
            merged[-1] = ("p", merged[-1][1] + " " + t)
            continue
        if merged and n.type == "p" and re.fullmatch(r"\*\*\*[^*]+\*\*\*", merged[-1][1]) and \
                not re.search(r"\.\*\*\*$", merged[-1][1]) and t.startswith("***"):
            merged[-1] = ("p", merged[-1][1][:-3] + " " + t[3:])  # "***Healing Touch (... Long***" + "***Rest).***"
            continue
        merged.append((n.type if n.type != "h" else f"h{n.level}", t))
    first = merged[0][1].strip("*")
    m = re.match(r"^(\S+(?: or Smaller)?) (.+), ([^,]+)$", first)
    data["size"], data["type"], data["alignment"] = (m.group(1), m.group(2), m.group(3)) if m else (None, None, first)
    abilities = {}
    for kind, t in merged[1:]:
        if kind == "h5" and t in SECTIONS:
            section = slugify(t).replace("-", "_")
            data.setdefault(section, [])
            continue
        if kind == "t" and "**AC**" in t:  # "| **AC** 11 | **Initiative** +1 (11) |"
            for label, val in re.findall(r"\*\*(AC|Initiative)\*\* ([^|]+)", t):
                data[label.lower()] = {"text": val.strip()}
            continue
        if kind == "t":
            for a, score, mod, sv in re.findall(r"\*\*(Str|Dex|Con|Int|Wis|Cha)\*\*\s*\|?\s*(\d+)\s*\|\s*([+−-]\d+)\s*\|\s*([+−-]\d+)", t):
                abilities[a.lower()] = {"score": int(score), "mod": _num(mod), "save": _num(sv)}
            continue
        if section:
            m = re.match(r"^\*\*\*(.+?)\.\*\*\*\s*(.*)$", t)
            if m:
                data[section].append(parse_ability(m.group(1), m.group(2)))
            else:  # continuation paragraph of the previous ability
                data[section][-1]["text"] += "\n\n" + t
            continue
        m = re.match(r"^\*\*([^*]+?)\*\*\s*(.*)$", t)
        if m:
            data[slugify(m.group(1)).replace("-", "_")] = {"text": m.group(2)}
    data["abilities"] = abilities
    return data, nodes


def parse_ability(name, text):
    d = {"name": name, "text": text}
    m = re.match(r"^(.+?) \((.+)\)$", name)
    if m:
        d["name"], d["qualifiers"] = m.group(1), [q.strip() for q in m.group(2).split(";")]
    m = re.match(r"^\*(Melee|Ranged|Melee or Ranged) Attack Roll:\* (.+?)\. \*Hit:\* (.+)$", text)
    if m:
        d["attack"] = {"kind": m.group(1).lower().replace(" or ", "_or_"), "terms": m.group(2), "hit": m.group(3)}
    m = re.match(r"^\*(\w+) Saving Throw:\* (.+?)\. \*Failure:\* (.+)$", text)
    if m:
        d["save"] = {"ability": m.group(1)[:3].lower(), "terms": m.group(2), "failure": m.group(3)}
    return d


def creature_entry(title, page, lot, path, slug=None, overrides=None, fx=None, level=None, end_at_cr=False, **kw):
    """Catalog entry for a stat block: every line is covered by the parsed data."""
    data, nodes = parse(title, page, level, end_at_cr)
    for k, v in (overrides or {}).items():
        data[k] = {**data.get(k, {}), **v} if isinstance(v, dict) and isinstance(data.get(k), dict) else v
    items = [(None, "sys", ["/data/size", "/data/type", "/data/alignment"])]
    for kind, key in (("**AC**", "ac"), ("**HP**", "hp"), ("**Speed**", "speed")):
        items.append((kind, "sys", [f"/data/{key}"]))
    items.append(("| MOD SAVE", "sys", ["/data/abilities"]))
    for n in nodes:
        m = re.match(r"^\*\*([^*]+?)\*\*", n.text)
        if m and m.group(1) not in ("AC", "HP", "Speed") and not n.text.startswith("***"):
            items.append((n.text[:len(m.group(0))], "sys", [f"/data/{slugify(m.group(1)).replace('-', '_')}"]))
    for sec in SECTIONS:
        key = slugify(sec).replace("-", "_")
        if key in data:
            items.append((f"##### {sec}", "sys", [f"/data/{key}"]))
            for i, a in enumerate(data[key]):
                raw = f"***{a['name']}"
                items.append((raw, "sys", [f"/data/{key}/{i}"]))
                for e in (fx or {}).get(a["name"], []):
                    items.append((raw, "fx", e))
    return build("creature", slug or slugify(title), title, nodes, lot, path, items,
                 facets={"group": "embedded", "size": data["size"], "type": data["type"]}, data=data, **kw)
