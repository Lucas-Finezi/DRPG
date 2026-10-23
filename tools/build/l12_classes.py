#!/usr/bin/env python3
"""L12 — Classes: core traits, multiclass traits, level progression (Features table) and the
class sidebars. Features, subclasses and spell lists are separate entries (L14, L13, L27).

The class entry's text is the class section minus its feature descriptions, subclass and
option lists and spell list; the Features table stays with the class.

Usage: python3 -I tools/build/l12_classes.py
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from classlib import CLASSES, INV, features_table, resolve_feature_names  # noqa: E402
from entrylib import NODES, build, find, md, render, section, sidebar, slugify, write_entry  # noqa: E402

LOT = "L12"
ABIL = {"Strength": "str", "Dexterity": "dex", "Constitution": "con", "Intelligence": "int", "Wisdom": "wis",
        "Charisma": "cha"}
SKILLS = {e: e for e in ()}  # filled lazily from system.json
SUBCLASS_HEAD = re.compile(r"^(\w+) Subclass: ")


def class_nodes(cls):
    """Class section nodes, excluding feature descriptions, subclasses, option lists and the spell list,
    but keeping the class's Features table."""
    i = find(cls, 2)
    j = i + 1
    while j < len(NODES) and not (NODES[j].type == "h" and NODES[j].level <= 2 and not NODES[j].sidebar):
        j += 1
    out, excluded, k = [], False, i + 1
    while k < j:
        n = NODES[k]
        if n.sidebar:
            k += 1
            continue
        if n.type == "h" and n.level == 5 and n.text == f"{cls} Features":
            out.append(n)
            k += 1
            while k < j and (NODES[k].type == "t" or (NODES[k].type == "p" and re.fullmatch(r"\*\*[^*]+\*\*",
                                                                                              NODES[k].text))):
                out.append(NODES[k])
                k += 1
            continue
        if n.type == "h" and n.level == 4:
            excluded = bool(re.match(r"^Level \d+: ", n.text)) or excluded and n.level > 3
        if n.type == "h" and n.level == 3:
            excluded = bool(SUBCLASS_HEAD.match(n.text)) or n.text.endswith("Spell List") \
                or n.text in ("Metamagic Options", "Eldritch Invocation Options")
        if not excluded:
            out.append(n)
        k += 1
    return out


def skill_ids():
    import json
    sysj = json.loads((Path(__file__).resolve().parents[2] / "knowledge/dnd5e/system.json").read_text(encoding="utf-8"))
    return {s["name"]: s["id"] for s in sysj["skills"]}


ITEM_KINDS = ("weapon", "armor", "gear", "tool")


def item_ref(name):
    """Inventory ref of an equipment item named in a starting-equipment list (None if absent)."""
    base = re.sub(r" \((.+)\)$", "", name)
    variant = re.search(r"\((.+)\)$", name)
    cands = [base, base.rstrip("s"), base[:-2] if base.endswith("es") else base]
    if base == "Arrows":
        cands = ["Ammunition: Arrows"]
    if variant and base in ("Arcane Focus", "Druidic Focus"):
        cands = [f"{base}: {variant.group(1)}"] + cands
    for c in cands:
        hit = [e["ref"] for e in INV if e["kind"] in ITEM_KINDS and e["name"].lower().startswith(c.lower())
               and (e["name"].lower() == c.lower() or e["name"].lower().startswith(c.lower() + " ("))]
        if len(hit) == 1:
            return hit[0]
    return None


def parse_equipment(text):
    """'Choose A or B: (A) X, 4 Y, and 15 GP; or (B) 75 GP' -> options."""
    body = text.split(":", 1)[1]
    options = []
    for label, content in re.findall(r"\(([A-C])\) (.+?)(?=; (?:or )?\([A-C]\)|$)", body):
        parts = [p.strip() for p in re.split(r",\s*(?:and\s+)?", content.strip())]
        items, gp = [], 0
        for p in parts:
            m = re.fullmatch(r"(?:and )?([\d,]+) GP", p)
            if m:
                gp = int(m.group(1).replace(",", ""))
                continue
            q = re.match(r"^(\d+) (.+)$", p)
            qty, name = (int(q.group(1)), q.group(2)) if q else (1, p)
            ref = item_ref(name)
            item = {"name": name, "quantity": qty}
            if ref:
                item["ref"] = ref
            items.append(item)
        options.append({"id": label.lower(), "items": items, "gp": gp})
    return options


def core_traits(cls):
    i = find(f"Core {cls} Traits", 5)
    rows = {}
    for n in NODES[i + 1:]:
        if n.type != "t":
            break
        rows[n.cells[0]] = n.cells[1]
    sk = skill_ids()
    traits = {}
    traits["primary_ability"] = [ABIL[a] for a in re.findall(r"\b(" + "|".join(ABIL) + r")\b",
                                                             rows["Primary Ability"])]
    traits["primary_ability_mode"] = "any" if " or " in rows["Primary Ability"] else "all"
    traits["hit_die"] = "d" + re.search(r"D(\d+)", rows["Hit Point Die"]).group(1)
    traits["saving_throws"] = [ABIL[a] for a in re.findall(r"\b(" + "|".join(ABIL) + r")\b",
                                                           rows["Saving Throw Proficiencies"])]
    s = rows["Skill Proficiencies"]
    m = re.match(r"Choose (any )?(\d+)", s)
    traits["skills"] = {"choose": int(m.group(2)),
                        "from": "any" if m.group(1) else [sk[x] for x in re.findall(
                            "|".join(sorted(sk, key=len, reverse=True)), s)]}
    traits["weapons"] = rows["Weapon Proficiencies"]
    if "Tool Proficiencies" in rows:
        traits["tools"] = rows["Tool Proficiencies"]
    traits["armor_training"] = rows["Armor Training"]
    traits["starting_equipment"] = parse_equipment(rows["Starting Equipment"])
    return rows, traits


def weapon_effect(text):
    fx = {"op": "proficiency", "category": "weapon"}
    if text == "Simple and Martial weapons":
        fx["items"] = ["simple", "martial"]
    elif text == "Simple weapons":
        fx["items"] = ["simple"]
    else:
        fx["items"] = ["simple"]
        fx["note"] = text
        m = re.search(r"Martial weapons that have the (.+) propert", text)
        fx["from"] = [f"martial_with:{p.strip().lower()}" for p in re.split(r" or ", m.group(1))]
    return fx


def armor_effect(text):
    if text == "None":
        return None
    cats = [c.lower() for c in re.findall(r"\b(Light|Medium|Heavy)\b", text)]
    if "Shields" in text:
        cats.append("shield")
    return {"op": "proficiency", "category": "armor", "items": cats}


def multiclass_gains(cls):
    nodes = NODES[find("As a Multiclass Character", 4, after=find(cls, 2)):]
    for n in nodes[1:]:
        if n.type == "p" and n.text.startswith("- Gain the following traits"):
            return n.text[2:]
    return None


def levels_data(cls, sub_ref):
    cols, rows = features_table(cls)
    levels = {}
    for r in rows:
        lv = int(r["Level"])
        names = [x.strip() for x in r["Class Features"].split(",")] if r["Class Features"] != "—" else []
        feats = resolve_feature_names(cls, lv, names)
        for f in feats:
            if f.get("subclass_feature"):
                f["subclass_of"] = sub_ref
        extra = {k: v for k, v in r.items() if k not in ("Level", "Class Features")}
        levels[str(lv)] = {"features": feats, "columns": extra}
    return cols, levels


def class_entry(cls):
    slug = slugify(cls)
    nodes = class_nodes(cls)
    text = render(nodes)
    rows, traits = core_traits(cls)
    sub_ref = [e["ref"] for e in INV if e["kind"] == "subclass" and e["facets"]["class"] == f"dnd5e/class/{slug}"][0]
    cols, levels = levels_data(cls, sub_ref)
    mc = multiclass_gains(cls)
    profs = [{"op": "proficiency", "category": "saving_throw", "items": traits["saving_throws"]},
             {"op": "proficiency", "category": "skill", "choose": traits["skills"]["choose"],
              **({"from": traits["skills"]["from"]} if traits["skills"]["from"] != "any" else {"note": "Any skills."})},
             weapon_effect(traits["weapons"])]
    if "tools" in traits:
        profs.append({"op": "proficiency", "category": "tool", "note": traits["tools"]})
    arm = armor_effect(traits["armor_training"])
    if arm:
        profs.append(arm)
    equip = {"op": "choice", "choose": 1, "options": [
        {"id": o["id"], "label": f"Option ({o['id'].upper()})",
         "effects": [{"op": "reference", "rule": f"dnd5e/class/{slug}", "note": f"Gain data.starting_equipment[{k}]."}]}
        for k, o in enumerate(traits["starting_equipment"])]}
    items = [
        (f"##### Core {cls} Traits", "rule", {"id": "core_traits", **{k: v for k, v in traits.items()
                                                                      if k != "starting_equipment"}}),
        (f"##### Core {cls} Traits", "fx", profs),
        ("| **Starting Equipment** |", "fx", equip),
        (f"### Becoming a {cls} …", "rule", {"id": "level_1", "gain": ["core_traits", "level_1_features"]}),
        ("#### As a Multiclass Character", "rule", {"id": "multiclass", "gain_text": mc,
                                                    "gain": ["listed_core_traits", "level_1_features"]}),
        ("#### As a Multiclass Character", "ref", ["dnd5e/rule/multiclassing"]),
        (f"### {cls} Class Features", "rule", {"id": "features_by_level", "table": f"{slug}_features"}),
        (f"##### {cls} Features", "sys", ["/data/levels"]),
    ]
    items = [it for it in items if it[0] is None or it[0] in text]
    items.sort(key=lambda it: text.find(it[0]))
    data = {"core_traits": rows, "hit_die": traits["hit_die"], "starting_equipment": traits["starting_equipment"],
            "features_table": {"id": f"{slug}_features", "caption": f"{cls} Features", "columns": cols},
            "levels": levels, "subclass": sub_ref}
    unresolved = [i["name"] for o in traits["starting_equipment"] for i in o["items"] if "ref" not in i]
    if unresolved:
        data["unresolved_items"] = unresolved
    return build("class", slug, cls, nodes, LOT, f"Classes/{cls}", items, text=text,
                 facets={"hit_die": traits["hit_die"], "primary_ability": traits["primary_ability"],
                         "saving_throws": traits["saving_throws"]}, data=data)


def entries():
    E = []
    chapter = [n for n in NODES[find("Classes", 1) + 1:find("Barbarian", 2)] if not n.sidebar]
    if chapter:
        E.append(build("rule", "classes", "Classes", chapter, LOT, "Classes", [(None, "desc", None)]))
    E += [class_entry(c) for c in CLASSES]
    for title, cls, feature in (("Metamagic Options", "Sorcerer", "dnd5e/feature/sorcerer-metamagic"),
                                ("Eldritch Invocation Options", "Warlock", "dnd5e/feature/warlock-eldritch-invocations")):
        nodes = section(title, 3)
        nodes = nodes[:next(i for i, n in enumerate(nodes) if n.type == "h")]
        options = [e["ref"] for e in INV if e.get("facets", {}).get("feature_type") ==
                   ("metamagic_option" if "Metamagic" in title else "eldritch_invocation")]
        E.append(build("rule", slugify(title), title, nodes, LOT, f"Classes/{cls}/{title}",
                       [(None, "ref", [feature] + options)], data={"options": options}))
    E.append(build("rule", "sidebar-breaking-your-oath", "Breaking Your Oath", sidebar("Breaking Your Oath"), LOT,
                   "Classes/Paladin", [
        (None, "desc", None),
        ("If your Paladin unrepentantly violates their oath", "md", md(
            "broken_oath", "The Paladin unrepentantly violated their oath: resolve the consequences with the player.",
            "If your Paladin unrepentantly violates their oath, talk to your GM.", reason="narrative", pages=[54]))],
        facets={"sidebar": True}))
    side = sidebar("Expanding and Replacing a Spellbook")
    E.append(build("rule", "sidebar-expanding-and-replacing-a-spellbook", "Expanding and Replacing a Spellbook", side,
                   LOT, "Classes/Wizard", [
        (None, "desc", None),
        ("***Copying a Spell into the Book.***", "rule", {"id": "copy_spell", "spell": "level_1_plus_wizard_spell",
                                                          "requires_slot_level_available": True,
                                                          "hours_per_spell_level": 2, "gp_per_spell_level": 50}),
        ("***Copying the Book.***", "rule", {"id": "copy_book", "hours_per_spell_level": 1, "gp_per_spell_level": 10}),
        ("If you lose your spellbook", "rule", {"id": "replace_book", "procedure": "same_as_copying",
                                                "source": "prepared_spells"})], facets={"sidebar": True}))
    return E


if __name__ == "__main__":
    out = entries()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
