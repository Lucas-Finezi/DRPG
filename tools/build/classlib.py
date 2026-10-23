"""Class tables and feature lookup shared by the L12-L14 builders."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import NODES, find, slugify  # noqa: E402

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
