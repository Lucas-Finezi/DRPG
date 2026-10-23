#!/usr/bin/env python3
"""Shared helpers for the spell lots (L17-L26).

SPELL(name, items) builds a spell entry. The header of the description (level/school/classes
line, Casting Time, Range, Components, Duration) is parsed from the source into facets and
data and covered as one structured segment; `items` cover the rest of the text as in
entrylib.build. Two placeholders may be used inside effects and are replaced by the spell's
own header values: "@duration" (the spell's duration) and "@range" (the spell's range).
The anchor "^" stands for the start of the first paragraph after the header.

Classes come from the description header (decision D-001), the school too.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import NODES, build, find, section, slugify  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
INV = {e["name"]: e for e in json.loads((ROOT / "inventory/dnd5e/srd-5.2.1/entries.json").read_text(
    encoding="utf-8"))["entries"] if e["kind"] == "spell"}
RELOCATED = json.loads((ROOT / "inventory/dnd5e/srd-5.2.1/outline.json").read_text(encoding="utf-8")).get(
    "relocated_fragments", [])
SCHOOLS = ["abjuration", "conjuration", "divination", "enchantment", "evocation", "illusion", "necromancy",
           "transmutation"]
NUM = {"one": 1, "two": 2, "three": 3}
_HIT_MELEE = [{"event": "hits_with_attack_roll"}]
TRIGGERS = {  # casting-time trigger wording -> events (the wording stays in 'trigger')
    "when you see a creature within 60 feet of yourself casting a spell with Verbal, Somatic, or Material components":
        [{"event": "sees_creature_casting_spell", "whose": "any"}],
    "immediately after hitting a target with a Melee weapon or an Unarmed Strike": _HIT_MELEE,
    "immediately after hitting a creature with a weapon": _HIT_MELEE,
    "immediately after hitting a creature with a Melee weapon or an Unarmed Strike": _HIT_MELEE,
    "when you or a creature you can see within 60 feet of you falls": [{"event": "falls", "whose": "any"}],
    "in response to taking damage from a creature that you can see within 60 feet of yourself":
        [{"event": "damaged_by_creature_within_feet.60"}],
    "when you are hit by an attack roll or targeted by the Magic Missile spell":
        [{"event": "hit_by_attack_roll"}, {"event": "targeted_by_spell.magic-missile"}],
}

# ---------------------------------------------------------------- header parsing


def _plain(s):
    return re.sub(r"\s+", " ", s.replace("*", "")).strip()


def parse_level_line(line):
    t = _plain(line)
    m = re.fullmatch(r"Level (\d) (\w+) \((.+)\)", t) or re.fullmatch(r"(\w+) Cantrip \((.+)\)", t)
    if not m:
        raise ValueError(f"unparsed spell level line: {line!r}")
    if t.startswith("Level"):
        level, school, classes = int(m.group(1)), m.group(2), m.group(3)
    else:
        level, school, classes = 0, m.group(1), m.group(2)
    return level, school.lower(), [slugify(c.strip()) for c in classes.split(",")]


def parse_casting_time(t):
    t = _plain(t)
    out = {"text": t}
    if t.startswith("Action (Overgrowth) or 8 hours"):
        return {"cost": "action", "alternatives": [{"cost": "time", "minutes": 480, "text": "8 hours (Enrichment)"}],
                "text": t}
    if t.endswith(" or Ritual"):
        out["ritual"] = True
        t = t[: -len(" or Ritual")]
    m = re.fullmatch(r"(Action|Bonus Action|Reaction)(?:, which you take (.+))?", t)
    if m:
        out["cost"] = {"Action": "action", "Bonus Action": "bonus_action", "Reaction": "reaction"}[m.group(1)]
        if m.group(2):
            out["trigger"] = m.group(2)
            out["triggers"] = TRIGGERS[m.group(2)]
        return out
    m = re.fullmatch(r"(\d+) (minute|minutes|hour|hours)", t)
    if not m:
        raise ValueError(f"unparsed casting time: {t!r}")
    out["cost"] = "time"
    out["minutes"] = int(m.group(1)) * (60 if m.group(2).startswith("hour") else 1)
    return out


def parse_range(t):
    t = _plain(t)
    if t in ("Self", "Touch", "Sight", "Unlimited", "Special"):
        return {"kind": t.lower() if t != "Special" else "special"}
    m = re.fullmatch(r"([\d,]+) (feet|mile|miles)", t)
    if not m:
        raise ValueError(f"unparsed range: {t!r}")
    n = int(m.group(1).replace(",", ""))
    return {"kind": "distance", **({"feet": n} if m.group(2) == "feet" else {"miles": n})}


def parse_components(t):
    t = _plain(t)
    m = re.fullmatch(r"([VSM, ]+?)(?: \((.+)\))?", t)
    if not m:
        raise ValueError(f"unparsed components: {t!r}")
    letters = [x.strip() for x in m.group(1).split(",")]
    out = {"verbal": "V" in letters, "somatic": "S" in letters}
    if "M" in letters:
        mat = m.group(2)
        out["material"] = mat
        c = re.search(r"worth ([\d,]+)\+\s?GP", mat)
        if c:
            out["material_cost_gp"] = int(c.group(1).replace(",", ""))
        if "which the spell consumes" in mat:
            out["material_consumed"] = True
    return out


def parse_duration(t):
    t = _plain(t)
    out = {"text": t}
    if t == "Instantaneous":
        return {"kind": "instantaneous", "text": t}
    if t == "Until dispelled":
        return {"kind": "until_dispelled", "text": t}
    if t == "Until dispelled or triggered":
        return {"kind": "until_dispelled_or_triggered", "text": t}
    if t == "Special":
        return {"kind": "special", "text": t}
    m = re.fullmatch(r"(Concentration,? )?([Uu]p to )?(\d+) (round|minute|hour|day)s?", t)
    if not m:
        raise ValueError(f"unparsed duration: {t!r}")
    out["kind"] = m.group(4) + "s"
    out["amount"] = int(m.group(3))
    if m.group(1):
        out["concentration"] = True
    if m.group(1) or m.group(2):
        out["up_to"] = True
    return out


def header(name):
    """(facets, data, header_node_count) of a spell, parsed from its description header."""
    inv = INV[name]
    i = find(name, 4, inv["page"])
    fields, k = {}, i + 2
    level, school, classes = parse_level_line(NODES[i + 1].text)
    last = None
    while True:
        t = NODES[k].text
        m = re.match(r"^\*\*(Casting Time|Range|Components?|Duration):\*\* ?(.*)$", t)
        if m:
            last = "Components" if m.group(1) == "Component" else m.group(1)  # some headers say "Component:"
            fields[last] = m.group(2)
        else:  # continuation of a wrapped header line
            fields[last] += " " + t
        k += 1
        if last == "Duration" and not re.match(r"^\*\*", NODES[k].text) and fields["Duration"]:
            break
    data = {"casting_time": parse_casting_time(fields["Casting Time"]), "range": parse_range(fields["Range"]),
            "components": parse_components(fields["Components"]), "duration": parse_duration(fields["Duration"])}
    facets = {"level": level, "school": school, "classes": classes,
              "concentration": bool(data["duration"].get("concentration")),
              "ritual": bool(data["casting_time"].get("ritual"))}
    if school not in SCHOOLS:
        raise ValueError(f"{name}: unknown school {school}")
    return facets, data

# ---------------------------------------------------------------- effect helpers


DC = {"var": "spell_save_dc"}
SLOT = {"var": "spell_slot_level"}
SELF = {"kind": "self"}
INHERIT = {"kind": "inherit"}


def C(s):
    return f"dnd5e/condition/{s}"


def SP(s):
    return f"dnd5e/spell/{s}"


def above(level, per=1):
    """per * (slot level - level): the 'for each spell slot level above N' increment."""
    return {"op": "mul", "args": [per, {"op": "sub", "args": [SLOT, level]}]} if per != 1 else \
        {"op": "sub", "args": [SLOT, level]}


def up(base, level, per=1):
    """base + per for each slot level above `level`."""
    return {"op": "add", "args": [base, above(level, per)]}


def dice(count, faces):
    return {"dice": {"count": count, "faces": faces}} if not isinstance(count, int) else f"{count}d{faces}"


def updice(count, faces, level, per=1):
    """countdF, plus `per` dice for each slot level above `level`."""
    return dice(up(count, level, per), faces)


def cantrip_dice(faces, base=1):
    """Cantrip Upgrade: base dice at level 1, +base at character levels 5, 11 and 17."""
    return {"dice": {"count": {"scale": {"by": "level", "steps": [
        {"from": 1, "value": base}, {"from": 5, "value": 2 * base}, {"from": 11, "value": 3 * base},
        {"from": 17, "value": 4 * base}]}}, "faces": faces}}


def cantrip_count(base=1):
    return {"scale": {"by": "level", "steps": [{"from": 1, "value": base}, {"from": 5, "value": base + 1},
                                               {"from": 11, "value": base + 2}, {"from": 17, "value": base + 3}]}}


def dmg(amount, dtype, **kw):
    if isinstance(dtype, (list, tuple)):
        dtype = {"choose_from": list(dtype)}
    return {"op": "damage", "amount": amount, "damage_type": dtype, **kw}


def heal(amount, **kw):
    return {"op": "heal", "amount": amount, **kw}


def cond(name, duration="@duration", **kw):
    d = {"op": "apply_condition", "condition": C(name), **kw}
    if duration is not None:
        d["duration"] = duration
    return d


def save(ability, on_fail=None, on_success=None, half=False, target=None, repeat=None, **kw):
    d = {"op": "save", "ability": ability, "dc": DC}
    if target:
        d["target"] = target
    if on_fail:
        d["on_fail"] = on_fail if isinstance(on_fail, list) else [on_fail]
    if on_success:
        d["on_success"] = on_success if isinstance(on_success, list) else [on_success]
    if half:
        d["half_on_success"] = True
    if repeat:
        d["repeat"] = repeat
    d.update(kw)
    return d


def attack(kind, on_hit=None, target=None, **kw):
    d = {"op": "attack", "attack_type": kind}
    if target:
        d["target"] = target
    if on_hit:
        d["on_hit"] = on_hit if isinstance(on_hit, list) else [on_hit]
    d.update(kw)
    return d


def area(shape, size, origin="point", rng="@range", **filt):
    t = {"kind": "area", "area": {"shape": shape, "size_feet": size, "origin": origin}}
    if rng and origin != "self":
        t["range"] = rng
    if filt:
        t["filter"] = filt
    return t


def creatures(count=1, rng="@range", must_see=False, **filt):
    t = {"kind": "creature"}
    if count != 1:
        t["count"] = count
    if rng:
        t["range"] = rng
    if must_see:
        t["must_see"] = True
    if filt:
        t["filter"] = filt
    return t


def touch(**filt):
    t = {"kind": "creature", "range": {"kind": "touch"}}
    if filt:
        t["filter"] = filt
    return t


def until_turn(event="turn_start", whose="self", which="next"):
    return {"kind": "until_event", "until": {"event": event, "whose": whose, "which": which}}


EACH_END = {"on": {"event": "turn_end", "whose": "target", "which": "each"}, "ends": "effect_on_self"}


def ref(rule, **kw):
    return {"op": "reference", "rule": rule, **kw}


def md(name, prompt, source_text, reason="gm_judgment", options=None, pages=None):
    d = {"id": name, "reason": reason, "prompt": prompt, "source_text": source_text}
    if options:
        d["options"] = options
    if pages:
        d["pages"] = pages
    return d

# ---------------------------------------------------------------- entry


def _fill(n, facets, data):
    if isinstance(n, dict):
        return {k: _fill(v, facets, data) for k, v in n.items()}
    if isinstance(n, list):
        return [_fill(v, facets, data) for v in n]
    if n == "@duration":
        return {k: v for k, v in data["duration"].items() if k != "text"}
    if n == "@range":
        return data["range"]
    return n


def resolve_rule_refs(plan):
    """'rule:<id>' in a sys payload -> the pointer of that rule in data.rules (by item order)."""
    index = {}
    for _, tag, payload in plan:
        if tag == "rule":
            index[payload["id"]] = len(index)
    out = []
    for anchor, tag, payload in plan:
        if tag == "sys":
            payload = [f"/data/rules/{index[p[5:]]}" if p.startswith("rule:") else p for p in payload]
        out.append((anchor, tag, payload))
    return out


def SPELL(name, items, lot, extra_data=None, skip=(), **kw):
    """Build a spell entry: parsed header + coverage items for the description."""
    inv = INV[name]
    facets, data = header(name)
    if extra_data:
        data.update(extra_data)
    nodes = section(name, 4, page=inv["page"])
    for f in RELOCATED:  # fragments printed inside another spell's section
        if f["printed_in"] == name:
            nodes = [n for n in nodes if not (n.page == f["page"] and n.text.startswith(f["prefix"]))]
        if f["belongs_to"] == name:  # inserted after the paragraph it continues (cut mid-sentence)
            moved = [n for n in NODES if n.page == f["page"] and n.text.startswith(f["prefix"])]
            k = next(i for i, n in enumerate(nodes) if n.type == "p" and n.text.rstrip().endswith(f["after"]))
            nodes = nodes[:k + 1] + moved + nodes[k + 1:]
    if skip:
        nodes = [n for n in nodes if n.text not in skip]
    # first paragraph after the header (the header ends with the Duration line)
    k = next(i for i, n in enumerate(nodes) if n.text.startswith("**Duration:**"))
    while re.match(r"^\*\*", nodes[k + 1].text) is None and nodes[k + 1].text and \
            not nodes[k + 1].text[0].isupper() and not nodes[k + 1].text.startswith("*"):
        k += 1  # wrapped duration line (not seen in the SRD, kept for safety)
    first = nodes[k + 1].text[:50] if k + 1 < len(nodes) else None
    plan = [(None, "sys", ["/facets", "/data/casting_time", "/data/range", "/data/components", "/data/duration"])]
    plan += [(first if anchor == "^" else anchor, tag, _fill(payload, facets, data)) for anchor, tag, payload in items]
    plan = resolve_rule_refs(plan)
    e = build("spell", slugify(name), name, nodes, lot, f"Spells/Spell Descriptions/{name}", plan,
              facets=facets, data=data, **kw)
    return e


def light(bright=0, dim=0, **kw):
    """Light shed by a spell effect (Bright/Dim Light rules in L41)."""
    d = {"bright_feet": bright, "dim_feet": dim, **kw}
    d["rules"] = [r for r, n in (("dnd5e/rule/bright-light", bright), ("dnd5e/rule/dim-light", dim)) if n]
    return d


def write_all(entries, registry=None, lot=None):
    from entrylib import extend_registries, write_entry
    if registry:
        extend_registries(registry, lot)
    for e in entries:
        write_entry(e)
    print(f"wrote {len(entries)} entries")


MOD = {"var": "spellcasting_mod"}
MAGIC = {"cost": "action", "action": "dnd5e/action/magic"}
STUDY = {"op": "check", "ability": "int", "skill": "investigation", "dc": DC,
         "note": "A creature that takes the Study action; on a success it discerns the illusion."}
BLOCKED = {"id": "blocked_by", "blocked_by": ["1_foot_stone_dirt_or_wood", "1_inch_metal", "thin_sheet_of_lead"]}
DAMAGE_TYPES = ("acid", "bludgeoning", "cold", "fire", "force", "lightning", "necrotic", "piercing", "poison", "psychic",
                "radiant", "slashing", "thunder")


def active(slug):
    return {"pred": "effect_active", "args": {"effect": slug}}


def all_but(*excluded):
    return [t for t in DAMAGE_TYPES if t not in excluded]


def extra_targets(level, base=1):
    """'You can target one additional creature for each spell slot level above N'."""
    return up(base, level)


def S_for(lot):
    return lambda name, items, **kw: SPELL(name, items, lot, **kw)


def tab(caption, columns, tid=None, page=None, nodes=None):
    """A captioned table of the source as data: body rows (header rows in bold are skipped)."""
    from entrylib import table_nodes
    rows = [n.cells for n in (nodes or table_nodes(caption, page))[1:] if n.type == "t" and not n.text.startswith("| **")]
    return {"id": tid or slugify(caption).replace("-", "_"), "caption": caption, "columns": columns, "rows": rows}
