#!/usr/bin/env python3
"""Shared helpers for the magic item lots (L31 magic items, L32 potions and scrolls).

MI(name, items) builds a magic item entry. The italic type line under the item's heading
("*Weapon (Any Simple or Martial), Rare (Requires Attunement)*") is parsed into data.item
(category, the items it applies to, rarity per variant, attunement and its prerequisite)
and covered as one structured segment; `items` cover the rest of the text as in
entrylib.build. The anchor "^" stands for the start of the first paragraph after the
type line. The lot is the inventory lot of the item (L31 or L32).

Effect conventions: "this" in a predicate's `item` argument is the item itself; charges
are the resource "charges" of the item (data.item.charges, effect `resource`); the bonus
of a "+1, +2, or +3" item is the variable `item_bonus` (data.item.rarity[].bonus).
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import NODES, build, find, section, slugify  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
_ALL = json.loads((ROOT / "inventory/dnd5e/srd-5.2.1/entries.json").read_text(encoding="utf-8"))["entries"]
INV = {e["name"]: e for e in _ALL if e["kind"] == "magic-item"}
ENTRIES = ROOT / "knowledge" / "dnd5e" / "entries"
CATEGORIES = {"Armor": "armor", "Weapon": "weapon", "Wondrous Item": "wondrous_item", "Potion": "potion",
              "Ring": "ring", "Rod": "rod", "Scroll": "scroll", "Staff": "staff", "Wand": "wand"}
RARITIES = ["Common", "Uncommon", "Rare", "Very Rare", "Legendary", "Artifact"]
ABIL = {"Strength": "str", "Dexterity": "dex", "Constitution": "con", "Intelligence": "int", "Wisdom": "wis",
        "Charisma": "cha"}

# ---------------------------------------------------------------- type line


def _plain(s):
    return re.sub(r"\s+", " ", s.replace("*", "")).strip()


def _base_refs(text):
    """Refs of the named weapons/armor/gear an item applies to ("Longsword", "Plate Armor")."""
    refs = []
    for part in re.split(r", or |, | or ", re.sub(r"^Any ", "", text)):
        part = part.strip()
        for kind in ("weapon", "armor", "gear"):
            if (ENTRIES / kind / f"{slugify(part)}.json").exists():
                refs.append(f"dnd5e/{kind}/{slugify(part)}")
                break
    return refs


def parse_type_line(line):
    t = _plain(line)
    out = {"type_line": t}
    att = re.search(r" \(Requires Attunement(?: by (.+?))?\)$", t)
    if att:
        out["attunement"] = {"required": True}
        if att.group(1):
            out["attunement"]["by"] = att.group(1)
            classes = re.findall(r"\b(Bard|Cleric|Druid|Paladin|Sorcerer|Warlock|Wizard)\b", att.group(1))
            if classes:
                out["attunement"]["classes"] = [f"dnd5e/class/{c.lower()}" for c in classes]
            if att.group(1) == "a Spellcaster":
                out["attunement"]["spellcaster"] = True
        t = t[: att.start()]
    m = re.match(r"^(Armor|Weapon|Wondrous Item|Potion|Ring|Rod|Scroll|Staff|Wand)(?: \(([^()]*)\))?, (.+)$", t)
    if not m:
        raise ValueError(f"unparsed type line: {line!r}")
    out["category"] = CATEGORIES[m.group(1)]
    if m.group(2):
        out["applies_to"] = {"text": m.group(2)}
        refs = _base_refs(m.group(2))
        if refs:
            out["applies_to"]["refs"] = refs
    rar = m.group(3)
    if rar == "Rarity Varies":
        out["rarity"] = [{"rarity": "varies"}]
    else:
        out["rarity"] = []
        for tok in re.findall(r"(?:Common|Uncommon|Rare|Very Rare|Legendary|Artifact)(?: \([^()]*\))?", rar):
            r = re.fullmatch(r"(Common|Uncommon|Rare|Very Rare|Legendary|Artifact)(?: \((.+)\))?", tok.strip())
            if not r:
                raise ValueError(f"unparsed rarity {tok!r} in {line!r}")
            d = {"rarity": r.group(1).lower().replace(" ", "_")}
            if r.group(2):
                b = re.fullmatch(r"\+(\d)", r.group(2))
                if b:
                    d["bonus"] = int(b.group(1))
                else:
                    d["variant"] = r.group(2)
            out["rarity"].append(d)
    return out


# ---------------------------------------------------------------- effect helpers

THIS = {"item": "this"}
WEAR = {"pred": "wearing_item", "args": THIS}
WIELD = {"pred": "wielding_item", "args": THIS}
HOLD = {"pred": "holds_item", "args": THIS}
ATTUNED = {"pred": "attuned_to_item", "args": THIS}
BONUS = {"var": "item_bonus"}
CHARGES = {"var": "resource.charges"}
SELF = {"kind": "self"}
INHERIT = {"kind": "inherit"}
MAGIC = "dnd5e/action/magic"
DAWN = {"count": 1, "per": "dawn"}


def C(s):
    return f"dnd5e/condition/{s}"


def SP(s):
    return f"dnd5e/spell/{slugify(s)}"


def CR(s):
    return f"dnd5e/creature/{slugify(s)}"


def all_(*preds):
    return {"all": [p for p in preds if p]}


def per_dawn(n=1):
    return {"count": n, "per": "dawn"}


def charges(max_, regain=None, **kw):
    """The item's charges: resource 'charges' with optional regain at dawn."""
    d = {"op": "resource", "resource": "charges", "name": "Charges", "max": max_}
    if regain is not None:
        d["recovery"] = [{"on": {"event": "dawn"}, "amount": regain}]
    d.update(kw)
    return d


def last_charge(on_1, die="1d20"):
    """'If you expend the item's last charge, roll 1d20. On a 1, ...'"""
    return {"op": "trigger", "event": {"event": "expends_last_charge"},
            "then": [{"op": "choice", "id": "last_charge_roll", "choose": 1, "note": f"Roll {die}; on a 1:",
                      "options": [{"id": "on_1", "label": "1", "effects": on_1 if isinstance(on_1, list) else [on_1]},
                                  {"id": "other", "label": "2+", "effects": [{"op": "reference", "rule": "dnd5e/rule/magic-items",
                                                                              "note": "No further effect."}]}]}]}


DESTROYED = {"op": "end_effect", "scope": "this_entry", "note": "The item is destroyed."}
DIES = {"op": "modifier", "stat": "hp", "mode": "set", "value": 0, "note": "The creature dies."}
_DICE_K = re.compile(r"^(\d+d\d+) ([+−-]) (\d+)$")


def expr(v):
    """'1d4 + 1' -> {'op': 'add', 'args': ['1d4', 1]} (dice plus/minus a constant), recursively."""
    if isinstance(v, str):
        m = _DICE_K.match(v)
        if m:
            return {"op": "add" if m.group(2) == "+" else "sub", "args": [m.group(1), int(m.group(3))]}
        return v
    if isinstance(v, list):
        return [expr(x) for x in v]
    if isinstance(v, dict):
        return {k: (x if k in ("note", "text", "label") else expr(x)) for k, x in v.items()}
    return v


def act(then, cost="action", action=MAGIC, uses=None, freq=None, name=None, **kw):
    d = {"op": "activation", "cost": cost}
    if name:
        d["name"] = name
    if cost == "action" and action:
        d["action"] = action
    if uses is not None:
        d["uses"] = {"resource": "charges", "amount": uses}
    if freq:
        d["frequency"] = freq
    d["then"] = then if isinstance(then, list) else [then]
    d.update(kw)
    return d


def cast(spell, level=None, dc=None, attack=None, **kw):
    """Cast a spell from the item: no slot, no components unless noted (Spells Cast from Items)."""
    d = {"op": "cast_spell", "spell": SP(spell), "slot": "none", "components": []}
    if level is not None:
        d["level"] = level
    if dc is not None:
        d["save_dc"] = dc
    if attack is not None:
        d["attack_bonus"] = attack
    d.update({k: v for k, v in kw.items() if v is not None})
    return d


def spells_table(rows, dc=None, attack=None, cost="action", action=MAGIC):
    """[(spell, charge cost[, level])] -> one activation per spell, spending charges."""
    out = []
    for r in rows:
        spell, n = r[0], r[1]
        lvl = r[2] if len(r) > 2 else None
        out.append(act(cast(spell, level=lvl, dc=dc, attack=attack), cost=cost, action=action, uses=n))
    return out


def mod(stat, value, when=None, **kw):
    d = {"op": "modifier", "stat": stat, "mode": "add", "value": value}
    if when:
        d["when"] = when
    d.update(kw)
    return d


def setv(stat, value, when=None, **kw):
    d = {"op": "modifier", "stat": stat, "mode": "set", "value": value}
    if when:
        d["when"] = when
    d.update(kw)
    return d


def resist(types, when=None, kind="resistance", **kw):
    d = {"op": "defense", "kind": kind, "damage_types": types if isinstance(types, list) else [types]}
    if when:
        d["when"] = when
    d.update(kw)
    return d


def immune_cond(conds, when=None, **kw):
    d = {"op": "defense", "kind": "immunity", "conditions": [C(c) for c in conds]}
    if when:
        d["when"] = when
    d.update(kw)
    return d


def adv(rolls, when=None, mode="advantage", **kw):
    d = {"op": "roll_mode", "mode": mode, "rolls": rolls if isinstance(rolls, list) else [rolls]}
    if when:
        d["when"] = when
    d.update(kw)
    return d


def dmg(amount, dtype, **kw):
    if isinstance(dtype, (list, tuple)):
        dtype = {"choose_from": list(dtype)}
    return {"op": "damage", "amount": amount, "damage_type": dtype, **kw}


def heal(amount, **kw):
    return {"op": "heal", "amount": amount, **kw}


def cond(name, duration=None, **kw):
    d = {"op": "apply_condition", "condition": C(name), **kw}
    if duration is not None:
        d["duration"] = duration
    return d


def save(ability, dc, on_fail=None, on_success=None, half=False, target=None, **kw):
    d = {"op": "save", "ability": ability, "dc": dc}
    if target:
        d["target"] = target
    if on_fail:
        d["on_fail"] = on_fail if isinstance(on_fail, list) else [on_fail]
    if on_success:
        d["on_success"] = on_success if isinstance(on_success, list) else [on_success]
    if half:
        d["half_on_success"] = True
    d.update(kw)
    return d


def check(ability, dc, skill=None, on_success=None, on_fail=None, **kw):
    d = {"op": "check", "ability": ability, "dc": dc}
    if skill:
        d["skill"] = skill
    if on_success:
        d["on_success"] = on_success if isinstance(on_success, list) else [on_success]
    if on_fail:
        d["on_fail"] = on_fail if isinstance(on_fail, list) else [on_fail]
    d.update(kw)
    return d


def sense(name, feet, when=None, **kw):
    d = {"op": "sense", "sense": name, "range_feet": feet}
    if when:
        d["when"] = when
    d.update(kw)
    return d


def speed(mode_name, value, mode="set", when=None, **kw):
    d = {"op": "speed", "movement": mode_name, "mode": mode, "value": value}
    if when:
        d["when"] = when
    d.update(kw)
    return d


def trig(event, then, **kw):
    ev = event if isinstance(event, dict) else {"event": event}
    return {"op": "trigger", "event": ev, "then": then if isinstance(then, list) else [then], **kw}


def ref(rule, **kw):
    return {"op": "reference", "rule": rule, **kw}


def area(shape, size, origin="point", **filt):
    t = {"kind": "area", "area": {"shape": shape, "size_feet": size, "origin": origin}}
    if filt:
        t["filter"] = filt
    return t


def creature(feet=None, count=1, must_see=False, **filt):
    t = {"kind": "creature"}
    if count != 1:
        t["count"] = count
    if feet is not None:
        t["range"] = {"kind": "distance", "feet": feet}
    if must_see:
        t["must_see"] = True
    if filt:
        t["filter"] = filt
    return t


def mins(n, **kw):
    return {"kind": "minutes", "amount": n, **kw}


def hours(n, **kw):
    return {"kind": "hours", "amount": n, **kw}


def rounds(n, **kw):
    return {"kind": "rounds", "amount": n, **kw}


def until_turn(event="turn_start", whose="self", which="next"):
    return {"kind": "until_event", "until": {"event": event, "whose": whose, "which": which}}


def while_(pred):
    return {"kind": "while", "while": pred}


def md(name, prompt, source_text, reason="gm_judgment", options=None, pages=None):
    d = {"id": name, "reason": reason, "prompt": prompt, "source_text": source_text}
    if options:
        d["options"] = [o if isinstance(o, dict) else {"id": slugify(o).replace("-", "_"), "label": o} for o in options]
    if pages:
        d["pages"] = pages
    return d


def tab(caption, columns, rows, tid=None):
    return {"id": tid or slugify(caption).replace("-", "_"), "caption": caption, "columns": columns, "rows": rows}


def rows_of(nodes, skip_header=True):
    return [n.cells for n in nodes if n.type == "t" and not (skip_header and n.text.startswith("| **"))]


# ---------------------------------------------------------------- entry

def item_nodes(name, skip=(), extra=(), stop=None):
    inv = INV[name]
    nodes = section(name, 4, page=inv["page"])
    if stop:
        k = next(i for i, n in enumerate(nodes) if n.text == stop or n.text.startswith(stop))
        nodes = nodes[:k]
    if skip:
        nodes = [n for n in nodes if not any(n.text.startswith(s) for s in skip)]
    return nodes + list(extra)


def MI(name, items, data=None, skip=(), extra=(), stop=None, nodes=None, **kw):
    """Build a magic item entry: parsed type line + coverage items for the description."""
    inv = INV[name]
    nodes = nodes if nodes is not None else item_nodes(name, skip, extra, stop)
    head = nodes[0]
    if not head.text.startswith("*"):
        raise ValueError(f"{name}: no type line: {head.text[:60]!r}")
    item = parse_type_line(head.text)
    d = {"item": item}
    if data:
        extra_item = data.pop("item", None)
        if extra_item:
            item.update(extra_item)
        d.update(data)
    facets = {"category": item["category"], "rarity": [r["rarity"] for r in item["rarity"]],
              "attunement": bool(item.get("attunement"))}
    first = nodes[1].text[:40] if len(nodes) > 1 else None
    plan = [(None, "sys", ["/facets", "/data/item"])]
    plan += [(first if anchor == "^" else anchor, tag, expr(payload) if tag == "fx" else payload) for anchor, tag, payload in items]
    return build("magic-item", inv["ref"].split("/")[-1], name, nodes, inv["lot"],
                 f"Magic Items/Magic Items A–Z/{name}", plan, facets=facets, data=d, **kw)


def lot_of(name):
    return INV[name]["lot"]
