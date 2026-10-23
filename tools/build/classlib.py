"""Class tables and feature lookup shared by the L12-L14 builders."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import NODES, find, slugify, table_nodes  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
INV = json.loads((ROOT / "inventory/dnd5e/srd-5.2.1/entries.json").read_text(encoding="utf-8"))["entries"]

SLOTS9 = [str(i) for i in range(1, 10)]
SLOTS5 = [str(i) for i in range(1, 6)]
BASE = ["Level", "Proficiency Bonus", "Class Features"]
# Column labels joined from the two-line headers printed in each class's Features table.
COLUMNS = {
    "Barbarian": BASE + ["Rages", "Rage Damage", "Weapon Mastery"],
    "Bard": BASE + ["Bardic Die", "Cantrips", "Prepared Spells"] + SLOTS9,
    "Cleric": BASE + ["Channel Divinity", "Cantrips", "Prepared Spells"] + SLOTS9,
    "Druid": BASE + ["Wild Shape", "Cantrips", "Prepared Spells"] + SLOTS9,
    "Fighter": BASE + ["Second Wind", "Weapon Mastery"],
    "Monk": BASE + ["Martial Arts", "Focus Points", "Unarmored Movement"],
    "Paladin": BASE + ["Channel Divinity", "Prepared Spells"] + SLOTS5,
    "Ranger": BASE + ["Favored Enemy", "Prepared Spells"] + SLOTS5,
    "Rogue": BASE + ["Sneak Attack"],
    "Sorcerer": BASE + ["Sorcery Points", "Cantrips", "Prepared Spells"] + SLOTS9,
    "Warlock": BASE + ["Eldritch Invocations", "Cantrips", "Prepared Spells", "Spell Slots", "Slot Level"],
    "Wizard": BASE + ["Cantrips", "Prepared Spells"] + SLOTS9,
}
CLASSES = list(COLUMNS)


def features_table(cls):
    """Rows (one per level 1-20) of the class's Features table, as dicts keyed by column."""
    i = find(f"{cls} Features", 5)
    rows = []
    for n in NODES[i + 1:]:
        if n.type == "h" and n.level <= 4 and not n.text.startswith("Level"):
            break
        if n.type == "t" and re.fullmatch(r"\d+", n.cells[0]) and len(rows) < 20:
            if int(n.cells[0]) == len(rows) + 1:
                rows.append(n.cells)
        if len(rows) == 20:
            break
    cols = COLUMNS[cls]
    bad = [r for r in rows if len(r) != len(cols)]
    if len(rows) != 20 or bad:
        raise ValueError(f"{cls} Features table: {len(rows)} rows, malformed: {bad[:2]}")
    return cols, [dict(zip(cols, r)) for r in rows]


def class_features(cls):
    """Inventory class features of a class: list of (level, name, ref)."""
    owner = f"dnd5e/class/{slugify(cls)}"
    out = []
    for e in INV:
        f = e.get("facets", {})
        if e["kind"] == "feature" and f.get("owner") == owner and f.get("feature_type") == "class_feature":
            out.append((f["level"], e["name"], e["ref"]))
    return out


def subclass_features(subclass_ref):
    out = []
    for e in INV:
        f = e.get("facets", {})
        if e["kind"] == "feature" and f.get("owner") == subclass_ref:
            out.append((f["level"], e["name"], e["ref"]))
    return out


def resolve_feature_names(cls, level, names):
    """Map the feature names of a table row to feature refs ('Subclass feature' -> None)."""
    feats = class_features(cls)
    out = []
    for name in names:
        if name.lower() == "subclass feature":
            out.append({"subclass_feature": True})
            continue
        m = re.match(r"^(.+?) \((.+)\)$", name)
        base, note = (m.group(1), m.group(2)) if m else (name, None)
        hit = [r for lv, n, r in feats if lv == level and n == base]
        item = {}
        if not hit:  # granted again at a later level: the feature described earlier
            earlier = sorted((lv, r) for lv, n, r in feats if n == base and lv < level)
            if earlier:
                hit = [earlier[-1][1]]
                item["again"] = True
        if len(hit) != 1:
            raise KeyError(f"{cls} level {level}: feature {name!r} -> {hit}")
        item = {"ref": hit[0], **item}
        if note:
            item["table_note"] = note
        out.append(item)
    return out


# ---------------------------------------------------------------- feature helpers

from entrylib import build, section  # noqa: E402

FEATURE_LOT = "L14"


def trait_nodes(species, trait):
    """Paragraphs of a species trait: from '***Trait.***' to the next trait or heading (tables excluded)."""
    nodes = section(species, 4)
    out, on = [], False
    for n in nodes:
        if n.type == "p" and n.text.startswith("***"):
            on = n.text.startswith(f"***{trait}.***")
        elif n.type == "h":
            if n.level <= 4:
                on = False
            continue
        if on and n.type == "p":
            out.append(n)
    if not out:
        raise KeyError(f"trait not found: {species} / {trait}")
    return out


def feature(owner_slug, name, nodes, path, items, feature_type, owner_ref, level=None, slug=None, **kw):
    facets = {"feature_type": feature_type, "owner": owner_ref}
    if level is not None:
        facets["level"] = level
    return build("feature", slug or f"{owner_slug}-{slugify(name)}", name, nodes, FEATURE_LOT, path, items,
                 facets=facets, **kw)


def CF(cls, name, level, items, sub=None, page=None, slug=None, **kw):
    """Class or subclass feature 'Level N: Name' (the class Features table is excluded from its text)."""
    title = f"Level {level}: {name}"
    owner_cls = slugify(cls)
    hits = [e for e in INV if e["kind"] == "feature" and e["name"] == name and e["facets"].get("level") == level
            and e["facets"]["owner"] == (f"dnd5e/subclass/{slugify(sub)}" if sub else f"dnd5e/class/{owner_cls}")]
    if len(hits) != 1:
        raise KeyError(f"feature not in inventory: {cls}/{sub}/{title}: {hits}")
    inv = hits[0]
    nodes = section(title, 4, page=page or inv["page"], skip_tables=(f"{cls} Features",))
    path = f"Classes/{cls}/" + (f"{cls} Subclass: {sub}/" if sub else f"{cls} Class Features/") + title
    owner = inv["facets"]["owner"]
    return feature(owner_cls if not sub else slugify(sub), name, nodes, path, items,
                   "subclass_feature" if sub else "class_feature", owner, level=level,
                   slug=slug or inv["ref"].rsplit("/", 1)[1], **kw)


def col(cls, column):
    """Expression reading a column of the class Features table at the current class level."""
    s = slugify(cls)
    return {"table": f"dnd5e/class/{s}", "table_id": f"{s}_features", "key": {"var": f"class_level.{s}"},
            "column": column}


def active(slug):
    return {"pred": "effect_active", "args": {"effect": slug}}


COMMON_REGISTRY = {
    "predicates": [
        {"id": "effect_active", "description": "An effect of the creature (param: entry slug, e.g. barbarian-rage) is active.", "params": ["effect"], "type": "predicate", "pages": [28]},
        {"id": "wearing_armor_any", "description": "The creature wears any armor.", "type": "predicate", "pages": [29]},
        {"id": "using_shield", "description": "The creature uses a Shield.", "type": "predicate", "pages": [29]},
        {"id": "attack_uses_ability", "description": "The attack uses the ability (param).", "params": ["ability"], "type": "predicate", "pages": [28]},
        {"id": "first_attack_this_turn", "description": "It is the creature's first attack roll on its turn.", "type": "predicate", "pages": [29]},
        {"id": "own_turn", "description": "It is the creature's turn.", "type": "predicate", "pages": [29]},
    ],
    "events": [
        {"id": "takes_attack_action", "description": "The creature takes the Attack action on its turn.", "type": "event", "pages": [29]},
        {"id": "drops_to_0_hp_not_killed", "description": "The creature drops to 0 Hit Points and doesn't die outright.", "type": "event", "pages": [30]},
        {"id": "damaged_by_creature_within_feet", "description": "The creature takes damage from a creature within 'feet'.", "params": ["feet"], "type": "event", "pages": [30]},
        {"id": "enters_effect", "description": "The creature activates an effect (param: entry slug).", "params": ["effect"], "type": "event", "pages": [29]},
    ],
    "stats": [
        {"id": "base_ac", "description": "Base Armor Class calculation (one alternative may be chosen).", "pages": [29]},
        {"id": "attacks_per_attack_action", "description": "Number of attacks when taking the Attack action.", "pages": [29]},
        {"id": "weapon_mastery_kinds", "description": "Kinds of weapons whose mastery property the creature can use.", "pages": [29]},
        {"id": "ability_score_max", "description": "Maximum of an ability score (param).", "params": ["ability"], "pages": [30]},
        {"id": "ability_score", "description": "An ability score (param).", "params": ["ability"], "pages": [30]},
    ],
}


def OPT(cls, name, feature_type, group, items, **kw):
    """Option feature listed under a class section (Metamagic, Eldritch Invocation), e.g. '#### Careful Spell'."""
    hits = [e for e in INV if e["kind"] == "feature" and e["name"] == name
            and e["facets"].get("feature_type") == feature_type]
    if len(hits) != 1:
        raise KeyError(f"option not in inventory: {cls}/{name}: {hits}")
    inv = hits[0]
    nodes = section(name, 4, page=inv["page"])
    return feature(slugify(cls), name, nodes, f"Classes/{cls}/{group}/{name}", items, feature_type,
                   inv["facets"]["owner"], slug=inv["ref"].rsplit("/", 1)[1], **kw)


def spell_table(caption, page=None):
    """A subclass 'always prepared' spell table: rows of (class level, [spell refs])."""
    rows = []
    for n in table_nodes(caption, page)[1:]:
        if n.type != "t" or n.text.startswith("| **"):
            continue
        spells = [slugify(re.sub(r"[*]", "", s)) for s in n.cells[1].split(",")]
        rows.append({"level": int(n.cells[0]), "spells": [f"dnd5e/spell/{s}" for s in spells]})
    return rows


def spellcasting(cls, ability, focus, prepared_start, prepared_recommended, change, cantrips=None, extra=()):
    """Items of a class 'Spellcasting' feature (the labelled paragraphs shared by the spellcasting classes).

    cantrips: (start, recommended, replace_on) or None; change: how prepared spells change
    ('level_gain_one', 'long_rest_one' or 'long_rest_any')."""
    s = slugify(cls)
    spell = lambda names: [f"dnd5e/spell/{slugify(n)}" for n in names]  # noqa: E731
    items = [(None, "rule", {"id": "spellcasting", "spell_list_of": f"dnd5e/spell-list/{s}",
                             "note": "Spells whose class list includes this class (D-001)."}),
             ("See “Spells”", "ref", ["dnd5e/rule/spells"])]
    if cantrips:
        start, rec, replace_on = cantrips
        items.append(("***Cantrips.***", "rule", {
            "id": "cantrips", "known": col(cls, "Cantrips"), "start": start, "from": f"dnd5e/spell-list/{s}",
            "recommended": spell(rec), "replace": {"on": replace_on, "count": 1}, "gain_at_levels": [4, 10]}))
    items += [
        ("***Spell Slots.***", "rule", {
            "id": "spell_slots", "pool": "spell_slot",
            "slots_by_spell_level": {str(n): col(cls, str(n)) for n in range(1, 10 if cls not in ("Paladin", "Ranger") else 6)}}),
        ("***Spell Slots.***", "fx", {"op": "trigger", "event": {"event": "long_rest_finished"},
                                     "then": [{"op": "restore", "resource": "spell_slot", "amount": "all"}]}),
        ("***Prepared Spells of Level 1+", "rule", {
            "id": "prepared_spells", "count": col(cls, "Prepared Spells"), "start_level_1_spells": prepared_start,
            "from": f"dnd5e/spell-list/{s}", "recommended": spell(prepared_recommended),
            "must_have_slot_level": True, "always_prepared_from_features_do_not_count": True}),
        ("***Changing Your Prepared Spells.***", "rule", {"id": "changing_prepared_spells", "mode": change}),
        ("***Spellcasting Ability.***", "rule", {"id": "spellcasting_ability", "ability": ability}),
        ("***Spellcasting Focus.***", "rule", {"id": "spellcasting_focus", "focus": focus})]
    return items + list(extra)
