#!/usr/bin/env python3
"""L30 — Adventuring equipment: Trinkets, Tools (25), Adventuring Gear (98 items incl. ammunition
and focus forms, saddles and feed), Mounts and Vehicles (8 mounts, 12 vehicles), Lifestyle
Expenses (7), Food, Drink, and Lodging, Hirelings and Spellcasting services (28 services).

Usage: python3 -I tools/build/l30_gear.py
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import NODES, build, extend_registries, find, section, slugify, write_entry  # noqa: E402
from itemlib import money, row_entry, table_rows, weight  # noqa: E402

LOT = "L30"
ROOT = Path(__file__).resolve().parents[2]
INV = {(e["kind"], e["name"]): e for e in json.loads((ROOT / "inventory/dnd5e/srd-5.2.1/entries.json").read_text(
    encoding="utf-8"))["entries"] if e["lot"] == LOT}
C = lambda s: f"dnd5e/condition/{s}"  # noqa: E731
G = lambda s: f"dnd5e/gear/{slugify(s)}"  # noqa: E731
DEX_DC = {"op": "add", "args": [8, {"var": "ability_mod.dex"}, {"var": "proficiency_bonus"}]}
INHERIT = {"kind": "inherit"}
ABIL = {"Strength": "str", "Dexterity": "dex", "Constitution": "con", "Intelligence": "int", "Wisdom": "wis",
        "Charisma": "cha"}


def slug_of(kind, name):
    return INV[(kind, name)]["ref"].split("/")[-1]


def md(name, prompt, source_text, reason="gm_judgment", pages=None):
    d = {"id": name, "reason": reason, "prompt": prompt, "source_text": source_text}
    if pages:
        d["pages"] = pages
    return d


def light(bright, dim, shape=None):
    """Light shed in a radius (default) or in a registered area shape (Cone)."""
    d = {"id": "light", "bright_feet": bright, "dim_feet": dim}
    if shape:
        d["shape"] = shape
    d["rules"] = ["dnd5e/rule/bright-light", "dnd5e/rule/dim-light"]
    return d


def drop_foreign_tables(nodes, keep=None):
    """The column flow can place another captioned table (level 5) inside an item's section: drop it."""
    out, skip = [], False
    for n in nodes:
        if n.type == "h" and n.level == 5:
            skip = n.text != keep
        elif n.type != "t" and not (n.type == "p" and re.match(r"^\*[^*].*\*$", n.text)):
            skip = False
        if not skip:
            out.append(n)
    return out


def thrown(name, effects, rng=20, **kw):
    return {"op": "trigger", "event": {"event": "takes_attack_action"}, "optional": True,
            "note": f"Replace one attack with throwing the {name}; target within {rng} feet you can see.",
            "then": [{"op": "save", "ability": "dex", "dc": DEX_DC, "target": {"kind": "creature_or_object",
                                                                              "range": {"kind": "distance", "feet": rng},
                                                                              "must_see": True},
                      "on_fail": effects, **kw}]}


def capacity(text):
    m = re.search(r"holds up to ([^.]+)\.", text)
    return {"id": "capacity", "holds": m.group(1)} if m else None


# ---------------------------------------------------------------- tools

def parse_tool(name, nodes):
    cells = next(n.cells for n in nodes if n.type == "t")
    data = {"ability": ABIL[cells[0].split(":", 1)[1].strip()], "weight_lb": weight(cells[1].split(":", 1)[1].strip())}
    items = [(None, "sys", ["/data/ability", "/data/weight_lb", "/data/cost"])]
    text = "\n".join(n.text for n in nodes if n.type == "p")
    for label in ("Utilize", "Craft", "Variants"):
        m = re.search(rf"\*\*{label}:\*\* (.+?)(?=\n\*\*|\Z)", text, flags=re.S)
        if not m:
            continue
        body = re.sub(r"\s+", " ", m.group(1)).strip()
        if label == "Utilize":
            data["utilize"] = [{"task": t.strip(), **({"dc": int(d)} if d else {})}
                               for t, d in re.findall(r"(?:, or |^)([^,(]+?(?:\([^)D][^)]*\))?[^,(]*?)(?: \(DC (\d+)\))?(?=, or |$)", body)]
            items.append(("**Utilize:**", "sys", ["/data/utilize"]))
            items.append(("**Utilize:**", "ref", ["dnd5e/action/utilize"]))
        elif label == "Craft":
            data["craft"] = [x.strip().strip("*") for x in re.split(r",\s*(?![^()]*\))", body)]
            items.append(("**Craft:**", "sys", ["/data/craft"]))
        else:
            data["variants"] = [x.strip() for x in re.split(r",\s*(?![^()]*\))", body)]
            items.append(("**Variants:**", "sys", ["/data/variants"]))
    return data, items


def tool_entries():
    E = []
    for e in [x for (k, _), x in INV.items() if k == "tool"]:
        name = e["name"]
        i = next(k for k, n in enumerate(NODES) if n.type == "h" and n.level == 4 and n.text.startswith(name + " (")
                 and n.page in (93, 94))
        title = NODES[i].text
        nodes = section(title, 4, page=NODES[i].page)
        data, items = parse_tool(name, nodes)
        data["cost"] = money(re.search(r"\((.+)\)$", title).group(1))
        data["category"] = e["facets"]["category"]
        if name == "Thieves’ Tools":
            pass
        E.append(build("tool", e["ref"].split("/")[-1], name, nodes, LOT, f"Equipment/Tools/{e['facets']['category']}/{name}",
                       items, data=data, facets={"category": slugify(e["facets"]["category"]), "ability": data["ability"],
                                                 "cost_cp": data["cost"].get("cp", 0)}))
    return E


# ---------------------------------------------------------------- adventuring gear

GEAR_TABLE = {}  # name in the Adventuring Gear table -> (weight, cost)


def gear_fx(name):
    """Coverage items (after the description start) for gear with mechanics."""
    M = {
        "Acid": [("^", "fx", thrown("Acid", [{"op": "damage", "amount": "2d6", "damage_type": "acid"}]))],
        "Alchemist’s Fire": [("^", "fx", thrown("Alchemist’s Fire", [{"op": "damage", "amount": "1d4", "damage_type": "fire"},
                                                                    {"op": "reference", "rule": "dnd5e/hazard/burning"}]))],
        "Antitoxin": [("^", "fx", {"op": "activation", "cost": "bonus_action", "then": [
            {"op": "roll_mode", "mode": "advantage", "rolls": ["saving_throw"], "duration": {"kind": "hours", "amount": 1},
             "when": {"pred": "save_against_condition", "args": {"condition": "poisoned"}}}]})],
        "Ball Bearings": [("^", "fx", {"op": "activation", "cost": "action", "action": "dnd5e/action/utilize", "then": [
            {"op": "trigger", "event": {"event": "enters_or_starts_turn_in_area"}, "frequency": {"count": 1, "per": "turn"},
             "then": [{"op": "save", "ability": "dex", "dc": 10, "target": INHERIT,
                       "on_fail": [{"op": "apply_condition", "condition": C("prone")}]}],
             "note": "10-foot-square area within 10 feet; a creature entering it for the first time on a turn."}]}),
                          ("^", "rule", {"id": "recover", "minutes": 10})],
        "Bedroll": [("^", "rule", {"id": "bedroll", "sleeps": 1, "sizes": ["small", "medium"],
                                   "auto_success_saves_vs": "extreme_cold", "rule": "dnd5e/environment/extreme-cold"})],
        "Blanket": [("^", "fx", {"op": "roll_mode", "mode": "advantage", "rolls": ["saving_throw"],
                                 "when": {"pred": "save_against_hazard", "args": {"hazard": "extreme-cold"}},
                                 "note": "While wrapped in it."})],
        "Block and Tackle": [("^", "rule", {"id": "hoist", "lift_multiplier": 4})],
        "Book": [("^", "fx", {"op": "modifier", "stat": "ability_check.int", "mode": "add", "value": 5,
                              "when": {"pred": "consulting_accurate_source"},
                              "note": "Arcana, History, Nature or Religion checks about the book's topic."})],
        "Caltrops": [("^", "fx", {"op": "activation", "cost": "action", "action": "dnd5e/action/utilize", "then": [
            {"op": "trigger", "event": {"event": "enters_or_starts_turn_in_area"}, "frequency": {"count": 1, "per": "turn"},
             "then": [{"op": "save", "ability": "dex", "dc": 15, "target": INHERIT,
                       "on_fail": [{"op": "damage", "amount": 1, "damage_type": "piercing"},
                                   {"op": "speed", "movement": "walk", "mode": "set", "value": 0,
                                    "duration": {"kind": "until_event", "until": {"event": "turn_start", "whose": "target"}}}]}],
             "note": "5-foot-square area within 5 feet."}]}),
                     ("^", "rule", {"id": "recover", "minutes": 10})],
        "Candle": [("^", "rule", {**light(5, 5), "hours": 1})],
        "Chain": [("^", "fx", {"op": "activation", "cost": "action", "action": "dnd5e/action/utilize", "then": [
            {"op": "check", "ability": "str", "skill": "athletics", "dc": 13,
             "on_success": [{"op": "apply_condition", "condition": C("restrained"), "note": "If its legs are bound, until it escapes."}]}],
            "note": "An unwilling creature within 5 feet that is Grappled, Incapacitated or Restrained."}),
                  ("^", "rule", {"id": "escape", "escape": {"ability": "dex", "skill": "acrobatics", "dc": 18, "cost": "action"},
                                 "burst": {"ability": "str", "skill": "athletics", "dc": 20, "cost": "action"}})],
        "Climber’s Kit": [("^", "rule", {"id": "anchor", "cost": "dnd5e/action/utilize", "max_fall_feet": 25, "max_distance_feet": 25,
                                         "undo": "bonus_action"})],
        "Clothes, Fine": [("^", "md", md("dress_code", "Does this event or location require Fine Clothes?",
                                         "Some events and locations admit only people wearing these clothes.", reason="narrative"))],
        "Component Pouch": [("^", "rule", {"id": "pouch", "watertight": True, "holds": "free_material_components"})],
        "Costume": [("^", "fx", {"op": "roll_mode", "mode": "advantage", "rolls": ["ability_check"],
                                 "when": {"pred": "impersonating_costume_subject"}})],
        "Crowbar": [("^", "fx", {"op": "roll_mode", "mode": "advantage", "rolls": ["ability_check.str"],
                                 "when": {"pred": "leverage_applies"}})],
        "Grappling Hook": [("^", "fx", {"op": "activation", "cost": "action", "action": "dnd5e/action/utilize", "then": [
            {"op": "check", "ability": "dex", "skill": "acrobatics", "dc": 13, "note": "Catches a railing, ledge or other catch within 50 feet; with a Rope tied, you can climb it."}]})],
        "Healer’s Kit": [("^", "fx", [{"op": "resource", "resource": "healers_kit", "max": 10},
                                      {"op": "activation", "cost": "action", "action": "dnd5e/action/utilize",
                                       "uses": {"resource": "healers_kit", "amount": 1},
                                       "then": [{"op": "reference", "rule": "dnd5e/rule/stable",
                                                 "note": "Stabilize an Unconscious creature with 0 Hit Points without a Wisdom (Medicine) check."}]}])],
        "Holy Water": [("^", "fx", thrown("Holy Water", [{"op": "damage", "amount": "2d8", "damage_type": "radiant",
                                                          "when": {"pred": "creature_type_in", "args": {"types": ["fiend", "undead"]}}}]))],
        "Hunting Trap": [("^", "rule", {"id": "set", "cost": "dnd5e/action/utilize"}),
                         ("The trap is affixed", "fx", {"op": "trigger", "event": {"event": "steps_on_trap"}, "then": [
                             {"op": "save", "ability": "dex", "dc": 13, "target": INHERIT,
                              "on_fail": [{"op": "damage", "amount": "1d4", "damage_type": "piercing"},
                                          {"op": "speed", "movement": "walk", "mode": "set", "value": 0,
                                           "duration": {"kind": "until_event", "until": {"event": "turn_start", "whose": "target"}}}]}]}),
                         ("The trap is affixed", "rule", {"id": "escape", "chain_feet": 3,
                                                          "break_free": {"ability": "str", "skill": "athletics", "dc": 13, "cost": "action",
                                                                         "failure_damage": {"amount": 1, "type": "piercing"}}})],
        "Ladder": [("^", "rule", {"id": "ladder", "height_feet": 10, "must_climb": True})],
        "Lamp": [("^", "rule", {**light(15, 30), "fuel": G("Oil")})],
        "Lantern, Bullseye": [("^", "rule", {**light(60, 60, "cone"), "fuel": G("Oil")})],
        "Lantern, Hooded": [("^", "rule", {**light(30, 30), "fuel": G("Oil"), "hood": {"cost": "bonus_action", "lowered": {"dim_feet": 5}}})],
        "Lock": [("^", "rule", {"id": "lock", "key": True, "pick": {"tool": "dnd5e/tool/thieves-tools", "ability": "dex",
                                                                    "skill": "sleight_of_hand", "dc": 15}})],
        "Magnifying Glass": [("^", "fx", {"op": "roll_mode", "mode": "advantage", "rolls": ["ability_check"],
                                          "when": {"pred": "appraising_detailed_item"}}),
                             ("^", "rule", {"id": "fire", "requires": ["sunlight_bright_light", "tinder"], "minutes": 5})],
        "Manacles": [("^", "fx", {"op": "activation", "cost": "action", "action": "dnd5e/action/utilize", "then": [
            {"op": "check", "ability": "dex", "skill": "sleight_of_hand", "dc": 13,
             "on_success": [{"op": "roll_mode", "mode": "disadvantage", "rolls": ["attack_roll"], "note": "While bound; Restrained if attached to a fixed chain or hook."}]}],
            "note": "An unwilling Small or Medium creature within 5 feet that is Grappled, Incapacitated or Restrained."}),
                     ("^", "rule", {"id": "escape", "escape": {"ability": "dex", "skill": "sleight_of_hand", "dc": 20, "cost": "action"},
                                    "burst": {"ability": "str", "skill": "athletics", "dc": 25, "cost": "action"}}),
                     ("Each set of Manacles", "rule", {"id": "lock", "key": True, "pick": {"tool": "dnd5e/tool/thieves-tools", "ability": "dex",
                                                                                          "skill": "sleight_of_hand", "dc": 15}})],
        "Map": [("^", "fx", {"op": "modifier", "stat": "ability_check.wis", "mode": "add", "value": 5,
                             "when": {"all": [{"pred": "consulting_accurate_source"}, {"pred": "check_uses_skill", "args": {"skill": "survival"}}]},
                             "note": "To find your way in the place represented."})],
        "Net": [("^", "fx", thrown("Net", [{"op": "apply_condition", "condition": C("restrained"), "note": "Until it escapes; Huge or larger automatically succeed."}], rng=15)),
                ("To escape, the target", "rule", {"id": "escape", "check": {"ability": "str", "skill": "athletics", "dc": 10, "cost": "action"},
                                                   "net_object": {"ac": 10, "hp": 5, "immunities": ["bludgeoning", "poison", "psychic"]}})],
        "Oil": [("^", "rule", {"id": "uses", "options": ["douse_creature_or_object", "douse_space", "fuel"]}),
                ("***Dousing a Creature or an Object.***", "fx", thrown("Oil flask", [{"op": "trigger", "event": {"event": "takes_fire_damage"},
                                                                                    "duration": {"kind": "minutes", "amount": 1},
                                                                                    "then": [{"op": "damage", "amount": 5, "damage_type": "fire"}]}])),
                ("***Dousing a Space.***", "fx", {"op": "activation", "cost": "action", "action": "dnd5e/action/utilize", "then": [
                    {"op": "trigger", "event": {"event": "enters_or_ends_turn_in_area"}, "frequency": {"count": 1, "per": "turn"},
                     "duration": {"kind": "rounds", "amount": 2}, "then": [{"op": "damage", "amount": 5, "damage_type": "fire", "target": INHERIT}],
                     "note": "5-foot square within 5 feet, once lit."}]}),
                ("***Fuel.***", "rule", {"id": "fuel", "hours_per_flask": 6, "for": [G("Lamp"), G("Lantern, Bullseye"), G("Lantern, Hooded")],
                                        "extinguish": "dnd5e/action/utilize"})],
        "Perfume": [("^", "fx", {"op": "roll_mode", "mode": "advantage", "rolls": ["ability_check.cha"], "duration": {"kind": "hours", "amount": 1},
                                 "when": {"pred": "influencing_indifferent_humanoid_within_feet", "args": {"feet": 5}},
                                 "note": "Charisma (Persuasion) checks."})],
        "Poison, Basic": [("^", "fx", {"op": "activation", "cost": "bonus_action", "then": [
            {"op": "trigger", "event": {"event": "deals_damage"}, "duration": {"kind": "minutes", "amount": 1},
             "condition": {"any": [{"pred": "deals_damage_type", "args": {"type": "piercing"}}, {"pred": "deals_damage_type", "args": {"type": "slashing"}}]},
             "then": [{"op": "damage", "amount": "1d4", "damage_type": "poison", "target": INHERIT},
                      {"op": "end_effect", "scope": "this_entry"}]}],
            "note": "Coat one weapon or up to three pieces of ammunition."})],
        "Pole": [("^", "fx", {"op": "roll_mode", "mode": "advantage", "rolls": ["ability_check.str"],
                              "when": {"pred": "check_for_jump"}, "note": "Strength (Athletics) checks as part of a High or Long Jump."}),
                 ("^", "rule", {"id": "reach_feet", "touch_up_to_feet": 10})],
        "Potion of Healing": [("^", "fx", {"op": "activation", "cost": "bonus_action", "then": [
            {"op": "heal", "amount": {"op": "add", "args": ["2d4", 2]}, "note": "You or another creature within 5 feet that drinks it."}]}),
                              ("^", "ref", ["dnd5e/magic-item/potions-of-healing"])],
        "Ram, Portable": [("^", "fx", [{"op": "modifier", "stat": "ability_check.str", "mode": "add", "value": 4,
                                        "when": {"pred": "breaking_down_door"}},
                                       {"op": "roll_mode", "mode": "advantage", "rolls": ["ability_check.str"],
                                        "when": {"pred": "helped_by_other_character"}}])],
        "Rations": [("^", "ref", ["dnd5e/hazard/malnutrition"])],
        "Robe": [("^", "md", md("robe_code", "Does this event or location require a Robe with certain colors or symbols?",
                                "Some events and locations admit only people wearing a Robe bearing certain colors or symbols.", reason="narrative"))],
        "Rope": [("^", "fx", {"op": "activation", "cost": "action", "action": "dnd5e/action/utilize", "then": [
            {"op": "check", "ability": "dex", "skill": "sleight_of_hand", "dc": 10, "note": "Tie a knot."}]}),
                 ("^", "rule", {"id": "burst", "check": {"ability": "str", "skill": "athletics", "dc": 20}}),
                 ("You can bind an unwilling creature", "rule", {"id": "bind", "requires": ["grappled", "incapacitated", "restrained"],
                                                                 "legs_bound": C("restrained"),
                                                                 "escape": {"ability": "dex", "skill": "acrobatics", "dc": 15, "cost": "action"}})],
        "Shovel": [("^", "rule", {"id": "dig", "hours": 1, "hole_feet": 5})],
        "Signal Whistle": [("^", "rule", {"id": "sound", "cost": "dnd5e/action/utilize", "audible_feet": 600})],
        "Bell": [("^", "rule", {"id": "sound", "cost": "dnd5e/action/utilize", "audible_feet": 60})],
        "Spell Scroll": [("^", "rule", {"id": "scroll", "levels": [0, 1], "cast_if_on_class_list": True, "normal_casting_time": True,
                                        "material_components": False}),
                         ("^", "ref", ["dnd5e/magic-item/spell-scroll"]),
                         ("If the spell requires a saving throw", "rule", {"id": "numbers", "save_dc": 13, "attack_bonus": 5,
                                                                           "disintegrates_after_casting": True})],
        "Spikes, Iron": [("^", "rule", {"id": "spikes", "bundle": 10, "hammer": "dnd5e/action/utilize", "uses": ["jam_door", "anchor_rope_or_chain"]})],
        "Spyglass": [("^", "rule", {"id": "magnification", "multiplier": 2})],
        "String": [("^", "rule", {"id": "string", "length_feet": 10, "knot": "dnd5e/action/utilize"})],
        "Tent": [("^", "rule", {"id": "tent", "sleeps": 2, "sizes": ["small", "medium"]})],
        "Tinderbox": [("^", "rule", {"id": "light", "exposed_fuel": "bonus_action", "other_fire_minutes": 1})],
        "Torch": [("^", "rule", {**light(20, 20), "hours": 1}),
                  ("^", "fx", {"op": "attack", "attack_type": "melee_weapon", "on_hit": [{"op": "damage", "amount": 1, "damage_type": "fire"}],
                               "note": "As a Simple Melee weapon when you take the Attack action."})],
        "Waterskin": [("^", "ref", ["dnd5e/hazard/dehydration"])],
        "Ink": [("^", "rule", {"id": "ink", "ounces": 1, "pages": 500})],
        "Ink Pen": [("^", "rule", {"id": "pen", "requires": G("Ink")})],
        "Paper": [("^", "rule", {"id": "words_per_sheet", "words": 250})],
        "Parchment": [("^", "rule", {"id": "words_per_sheet", "words": 250})],
        "Backpack": [("^", "rule", {"id": "capacity", "pounds": 30, "cubic_feet": 1, "saddlebag": True})],
        "Basket": [("^", "rule", {"id": "capacity", "pounds": 40, "cubic_feet": 2})],
        "Sack": [("^", "rule", {"id": "capacity", "pounds": 30, "cubic_feet": 1})],
        "Pouch": [("^", "rule", {"id": "capacity", "pounds": 6, "cubic_feet": 0.2})],
        "Bottle, Glass": [("^", "md", md("bottle_capacity", "What is the Glass Bottle's capacity?",
                                         "A Glass Bottle holds up to 11/2 pints.", reason="ambiguous_source", pages=[96]))],
    }
    return M.get(name)


PACKS = {"Burglar’s Pack", "Diplomat’s Pack", "Dungeoneer’s Pack", "Entertainer’s Pack", "Explorer’s Pack",
         "Priest’s Pack", "Scholar’s Pack"}
SUBTABLES = {"Ammunition": ("Ammunition", ["Type", "Amount", "Storage", "Weight", "Cost"]),
             "Arcane Focus": ("Arcane Focuses", ["Focus", "Weight", "Cost"]),
             "Druidic Focus": ("Druidic Focuses", ["Focus", "Weight", "Cost"]),
             "Holy Symbol": ("Holy Symbols", ["Symbol", "Weight", "Cost"])}
FOCUS_CLASSES = {"Arcane Focus": ["sorcerer", "warlock", "wizard"], "Druidic Focus": ["druid", "ranger"],
                 "Holy Symbol": ["cleric", "paladin"]}


def gear_entries():
    E = []
    for _, n in table_rows("Adventuring Gear", 95):
        GEAR_TABLE[re.sub(r"\*", "", n.cells[0]).strip()] = (n.cells[1], n.cells[2])
    heads = [n for n in NODES if n.type == "h" and n.level == 4 and 94 <= n.page <= 100]
    for e in [x for (k, _), x in INV.items() if k == "gear" and x["page"] <= 100 and ":" not in x["name"]
              and x["name"] not in ("Feed per day",) and not x["name"].startswith("Saddle")]:
        name = e["name"]
        h = next(n for n in heads if n.text == name or n.text.startswith(name + " ("))
        sub = SUBTABLES.get(name)
        nodes = drop_foreign_tables(section(h.text, 4, page=h.page), sub[0] if sub else None)
        data = {"cost": money(re.search(r"\((.+)\)$", h.text).group(1)) if "(" in h.text else {}}
        if name == "Spell Scroll":  # "(Cantrip, 30 GP; Level 1, 50 GP)"
            data["cost"] = {"by_spell_level": [{"level": 0 if lv == "Cantrip" else int(lv.split()[1]), **money(c)}
                                               for lv, c in re.findall(r"(Cantrip|Level \d), ([\d,]+ [GSC]P)", h.text)]}
        wt = GEAR_TABLE.get(name, GEAR_TABLE.get(f"{name} (Cantrip)", (None, None)))[0]
        if wt is not None:
            data["weight_lb"] = weight(wt) if wt not in ("Varies",) else {"text": "Varies"}
        items = [(None, "sys", ["/data/cost"])]
        if name in PACKS:
            contents = re.search(r"contains the following items: (.+)\.$", nodes[0].text).group(1)
            data["contents"] = [x.strip() for x in re.split(r", (?:and )?", contents)]
            items.append(("^", "sys", ["/data/contents"]))
        elif name in FOCUS_CLASSES:
            items.append(("^", "rule", {"id": "spellcasting_focus", "classes": [f"dnd5e/class/{c}" for c in FOCUS_CLASSES[name]],
                                        "rule": "dnd5e/rule/spellcasting-focus"}))
        if sub:
            cap, cols = sub
            tn = [NODES[find(cap, 5)]] + [r for _, r in table_rows(cap)]
            nodes = nodes + [x for x in tn if x not in nodes]
            if name == "Holy Symbol":
                data["forms"] = [{"form": r.cells[0], "weight_lb": weight(r.cells[1]), "cost": money(r.cells[2])}
                                 for _, r in table_rows(cap)]
                items.append(("The table indicates", "rule", {"id": "carry", "held_worn_or_borne": True}))
            items.append((f"##### {cap}", "table", {"id": slugify(cap).replace("-", "_"), "caption": cap, "columns": cols,
                                                     "rows": [r.cells for _, r in table_rows(cap)]}))
        extra = gear_fx(name)
        if name == "Ammunition":
            extra = [("^", "ref", ["dnd5e/weapon-property/ammunition"])]
        if extra:
            items = items[:1] + extra + [it for it in items[1:]]
        elif not (name in PACKS or name in FOCUS_CLASSES or sub):
            items.append(("^", "desc", None))
        items = [it if it[0] != "^" else (nodes[0].text[:40], it[1], it[2]) for it in items]
        # keep anchors in text order
        text_order = "\n".join(n.text for n in nodes)
        head, rest = items[:1], items[1:]
        rest.sort(key=lambda it: text_order.find(it[0].lstrip("# ")))
        items = head + rest
        E.append(build("gear", e["ref"].split("/")[-1], name, nodes, LOT, f"Equipment/Adventuring Gear/{name}", items,
                       data=data, facets={"cost_cp": data["cost"].get("cp", 0)} if "cp" in data["cost"] else None))
    # sub-items from the focus and ammunition tables
    for parent, (cap, cols) in SUBTABLES.items():
        if parent == "Holy Symbol":
            continue
        for _, r in table_rows(cap):
            name = f"{parent}: {r.cells[0]}"
            ref = INV[("gear", name)]["ref"]
            if parent == "Ammunition":
                data = {"amount": int(r.cells[1]), "storage": r.cells[2], "weight_lb": weight(r.cells[3]), "cost": money(r.cells[4])}
            else:
                data = {"form": r.cells[0], "weight_lb": weight(r.cells[1]), "cost": money(r.cells[2])}
            data["parent"] = G(parent)
            E.append(row_entry("gear", name, r, LOT, f"Equipment/Adventuring Gear/{parent}/{r.cells[0]}", data,
                               slug=ref.split("/")[-1], facets={"cost_cp": data["cost"].get("cp", 0)}))
    return E


# ---------------------------------------------------------------- mounts, vehicles, services

def mounts_and_vehicles():
    E = []
    for _, r in table_rows("Mounts and Other Animals", 100):
        name = r.cells[0]
        data = {"carrying_capacity_lb": weight(r.cells[1].replace(",", "")), "cost": money(r.cells[2]),
                "creature": f"dnd5e/creature/{slugify(name.split(', ')[1] + ' ' + name.split(', ')[0]) if ', ' in name else slugify(name)}"}
        E.append(row_entry("mount", name, r, LOT, f"Equipment/Mounts and Vehicles/Mounts and Other Animals/{name}", data,
                           slug=slug_of("mount", name), facets={"cost_cp": data["cost"].get("cp", 0)}))
    for group, r in table_rows("Tack, Harness, and Drawn Vehicles", 100):
        name = r.cells[0] if not group else f"{group}, {r.cells[0]}"
        kind = next(k for k in ("vehicle", "gear", "service") if (k, name) in INV)
        data = {"weight_lb": weight(r.cells[1]), "cost": money(r.cells[2])}
        items = []
        if name.startswith("Saddle"):
            items = [(None, "ref", ["dnd5e/rule/saddles"])]
        E.append(row_entry(kind, name, r, LOT, f"Equipment/Mounts and Vehicles/Tack, Harness, and Drawn Vehicles/{name}", data,
                           items=items, slug=slug_of(kind, name), facets={"cost_cp": data["cost"].get("cp", 0)}))
    for _, r in [x for x in table_rows("Airborne and Waterborne Vehicles", 101) if len(x[1].cells) == 9]:
        name, speed, crew, pas, cargo, ac, hp, dt, cost = r.cells
        num = lambda x: None if x == "—" else (float(x.replace("½", ".5").replace("1/2", "0.5")) if re.search(r"[½/.]", x) else int(x.replace(",", "")))  # noqa: E731
        data = {"speed_mph": num(speed.replace(" mph", "")), "crew": num(crew), "passengers": num(pas), "cargo_tons": num(cargo),
                "ac": int(ac), "hp": int(hp), "damage_threshold": num(dt), "cost": money(cost)}
        E.append(row_entry("vehicle", name, r, LOT, f"Equipment/Mounts and Vehicles/Large Vehicles/{name}", data,
                           items=[(None, "ref", ["dnd5e/rule/damage-threshold"])] if dt != "—" else None,
                           slug=slug_of("vehicle", name), facets={"cost_cp": data["cost"].get("cp", 0)}))
    return E


def food_rows():
    """Rows of the Food, Drink, and Lodging table, which the column flow interleaves with the
    Airborne and Waterborne Vehicles table (pp. 101-102): two-column rows only."""
    i = find("Food, Drink, and Lodging", 5, 101)
    out, group = [], None
    for n in NODES[i + 1:]:
        if n.type == "h" and n.level <= 2:
            break
        if n.type == "p" and re.match(r"^\*[^*].*\*$", n.text):
            group = n.text.strip("*")
        elif n.type == "t" and len(n.cells) == 2 and not n.text.startswith("| **"):
            out.append((group if n.indented else None, n))
        elif n.type == "t" and len(n.cells) == 2:
            continue
    return out


def services():
    E = []
    for group, r in food_rows():
        name = r.cells[0] if not group else f"{group}: {r.cells[0]}"
        data = {"cost": money(r.cells[1])}
        E.append(row_entry("service", name, r, LOT, f"Equipment/Food, Drink, and Lodging/{name}", data,
                           slug=slug_of("service", name), facets={"cost_cp": data["cost"].get("cp", 0)}))
    for _, r in table_rows("Hirelings", 102):
        m = re.fullmatch(r"(\d+ \w+) per (day|mile)", r.cells[1])
        data = {"cost": money(m.group(1)), "per": m.group(2)}
        E.append(row_entry("service", r.cells[0], r, LOT, f"Equipment/Hirelings/{r.cells[0]}", data,
                           slug=slug_of("service", r.cells[0]), facets={"cost_cp": data["cost"].get("cp", 0)}))
    for _, r in table_rows("Spellcasting Services", 102):
        name = f"Spellcasting: {r.cells[0]}"
        data = {"spell_level": r.cells[0], "availability": r.cells[1], "cost": money(r.cells[2])}
        E.append(row_entry("service", name, r, LOT, f"Equipment/Spellcasting/{r.cells[0]}", data,
                           slug=slug_of("service", name), facets={"cost_cp": data["cost"].get("cp", 0)}))
    return E


def lifestyles():
    E = []
    for e in [x for (k, _), x in INV.items() if k == "lifestyle"]:
        h = next(n for n in NODES if n.type == "h" and n.level == 3 and n.text.startswith(e["name"] + " (") and n.page == 101)
        cost = re.search(r"\((.+)\)$", h.text).group(1)
        data = {"cost": money(cost.replace(" per Day", "")) if cost != "Free" else {"amount": 0, "unit": "gp", "cp": 0},
                "per": "day"}
        E.append(build("lifestyle", e["ref"].split("/")[-1], e["name"], section(h.text, 3, page=101), LOT,
                       f"Equipment/Lifestyle Expenses/{h.text}",
                       [(None, "sys", ["/data/cost"]), (None, "desc", None)], data=data,
                       facets={"cost_cp_per_day": data["cost"].get("cp", 0)}))
    return E


# ---------------------------------------------------------------- sections

def sections():
    E = []
    tr = [NODES[find("Trinkets", 5)]] + [r for _, r in table_rows("Trinkets")]
    E.append(build("rule", "trinkets", "Trinkets", section("Trinkets", 2) + [], LOT, "Character Creation/Trinkets", [
        (None, "rule", {"id": "trinket", "roll": "1d100", "size": "tiny", "at_character_creation": 1}),
        (None, "md", md("trinket_use", "Does the GM use the Trinkets table here (e.g. stocking a room)?",
                        "The GM might also use this table. It can help stock a room in a dungeon or fill a creature’s pockets.")),
        ("##### Trinkets", "table", {"id": "trinkets", "caption": "Trinkets", "columns": ["1d100", "Trinket"],
                                     "rows": [r.cells for _, r in table_rows("Trinkets")]})]))
    E.append(build("rule", "tools", "Tools", section("Tools", 2, stop_titles=("Tool Proficiency",)), LOT, "Equipment/Tools", [
        (None, "rule", {"id": "tools", "entries": ["ability", "utilize", "craft", "variants"]}),
        ("**Utilize.**", "ref", ["dnd5e/action/utilize"]),
        ("**Craft.**", "ref", ["dnd5e/rule/crafting-nonmagical-items", "dnd5e/rule/brewing-potions-of-healing",
                               "dnd5e/rule/scribing-spell-scrolls"]),
        ("**Variants.**", "rule", {"id": "variants", "separate_proficiency_each": True})]))
    E.append(build("rule", "tool-proficiency", "Tool Proficiency", section("Tool Proficiency", 3), LOT, "Equipment/Tools/Tool Proficiency", [
        (None, "fx", [{"op": "modifier", "stat": "ability_check", "mode": "add", "value": {"var": "proficiency_bonus"},
                       "when": {"pred": "check_uses_proficient_tool"}},
                      {"op": "roll_mode", "mode": "advantage", "rolls": ["ability_check"],
                       "when": {"all": [{"pred": "check_uses_proficient_tool"}, {"pred": "check_uses_proficient_skill"}]}}]),
        ("Your features might give you proficiency", "rule", {"id": "sources", "features": True, "monsters_proficient_with_stat_block_tools": True})]))
    E.append(build("rule", "artisans-tools", "Artisan’s Tools", section("Artisan’s Tools", 3, page=93, stop_titles=("Alchemist’s Supplies (50 GP)",)),
                   LOT, "Equipment/Tools/Artisan’s Tools", [(None, "rule", {"id": "artisans_tools", "separate_proficiency_each": True})]))
    ot = section("Other Tools", 3, page=94, stop_titles=("Disguise Kit (25 GP)",))
    if ot:
        E.append(build("rule", "other-tools", "Other Tools", ot, LOT, "Equipment/Tools/Other Tools", [(None, "desc", None)]))
    ag_i = find("Adventuring Gear", 5, 95)
    ag = section("Adventuring Gear", 2, stop_titles=("Acid (25 GP)",)) + [NODES[ag_i]] + \
        [n for n in NODES[ag_i + 1:ag_i + 120] if n.type == "t" and len(n.cells) == 3 and n.page in (95,)]
    gear_rows = [r.cells for _, r in table_rows("Adventuring Gear", 95)]
    E.append(build("rule", "adventuring-gear", "Adventuring Gear", ag, LOT, "Equipment/Adventuring Gear", [
        (None, "rule", {"id": "order", "alphabetical": True, "price_after_name": True}),
        ("##### Adventuring Gear", "table", {"id": "adventuring_gear", "caption": "Adventuring Gear",
                                             "columns": ["Item", "Weight", "Cost"], "rows": gear_rows})]))
    mv = section("Mounts and Vehicles", 2, stop_titles=("Mounts and Cargo",))
    E.append(build("rule", "mounts-and-vehicles", "Mounts and Vehicles", mv, LOT, "Equipment/Mounts and Vehicles", [
        (None, "rule", {"id": "mounts", "purpose": "carry_gear", "stat_blocks": "dnd5e/rule/monster"})]))
    mi = find("Mounts and Other Animals", 5, 100)
    E.append(build("rule", "mounts-and-cargo", "Mounts and Cargo", section("Mounts and Cargo", 3) +
                   [NODES[mi], NODES[mi + 1]], LOT, "Equipment/Mounts and Vehicles/Mounts and Cargo", [
                       (None, "rule", {"id": "pulling", "capacity_multiplier": 5, "includes_vehicle_weight": True,
                                       "multiple_animals_add": True}),
                       ("##### Mounts and Other Animals", "rule", {"id": "table", "rows": "dnd5e/mount/*"})]))
    E.append(build("rule", "barding", "Barding", section("Barding", 3), LOT, "Equipment/Mounts and Vehicles/Barding", [
        (None, "rule", {"id": "barding", "any_armor": "dnd5e/rule/armor", "cost_multiplier": 4, "weight_multiplier": 2})]))
    ti = find("Tack, Harness, and Drawn Vehicles", 5, 100)
    tack_head = [NODES[ti], NODES[ti + 1]] + [n for n in NODES[ti + 1:ti + 16] if n.type == "p" and n.text == "*Saddle*"]
    E.append(build("rule", "saddles", "Saddles", section("Saddles", 3) + tack_head, LOT, "Equipment/Mounts and Vehicles/Saddles", [
        (None, "rule", {"id": "saddle", "includes": ["bit", "bridle", "reins"]}),
        ("A Military Saddle gives Advantage", "fx", {"op": "roll_mode", "mode": "advantage", "rolls": ["ability_check"],
                                                     "when": {"pred": "check_to_remain_mounted"}, "note": "Military Saddle."}),
        ("A Military Saddle gives Advantage", "rule", {"id": "exotic", "required_for": ["aquatic_mount", "flying_mount"]}),
        ("##### Tack, Harness, and Drawn Vehicles", "rule", {"id": "table", "rows": ["dnd5e/vehicle/*", "dnd5e/gear/saddle-*"]})]))
    lv = section("Large Vehicles", 3)
    vi = find("Airborne and Waterborne Vehicles", 5, 101)
    lv = [n for n in lv if not (n.type == "t" and len(n.cells) == 2)]
    E.append(build("rule", "large-vehicles", "Large Vehicles", lv + [NODES[vi], NODES[vi + 1]], LOT,
                   "Equipment/Mounts and Vehicles/Large Vehicles", [
                       (None, "rule", {"id": "table", "rows": "dnd5e/vehicle/*"}),
                       ("#### Speed", "rule", {"id": "speed", "against_strong_wind": 0.5, "dead_calm": "rowed",
                                               "downstream_add_current_mph": 3, "rowboat_weight_lb": 100}),
                       ("#### Crew", "rule", {"id": "crew", "skilled_hirelings_required": True, "rule": "dnd5e/service/skilled-hireling"}),
                       ("#### Passengers", "rule", {"id": "passengers", "private_accommodations_fraction": 0.2,
                                                    "hammock_cost": money("5 SP"), "cabin_cost": money("2 GP")}),
                       ("#### Damage Threshold", "ref", ["dnd5e/rule/damage-threshold"]),
                       ("#### Ship Repair", "rule", {"id": "repair", "per_hp": {"days": 1, "cost": money("20 GP")},
                                                     "shipyard_multiplier": 0.5})]))
    le = section("Lifestyle Expenses", 2, stop_titles=("Wretched (Free)",))
    E.append(build("rule", "lifestyle-expenses", "Lifestyle Expenses", le, LOT, "Equipment/Lifestyle Expenses", [
        (None, "rule", {"id": "lifestyle", "options": [f"dnd5e/lifestyle/{s}" for s in
                                                       ("wretched", "squalid", "poor", "modest", "comfortable", "wealthy", "aristocratic")]}),
        ("At the start of each week or month", "md", md("lifestyle_period", "Is the lifestyle paid weekly or monthly?",
                                                         "At the start of each week or month (GM’s choice), choose a lifestyle below")),
        ("Lifestyles have no inherent consequences", "md", md("lifestyle_effects", "Does the lifestyle affect risks or perceptions here?",
                                                              "Lifestyles have no inherent consequences, but the GM might take them into account when determining risks or how others perceive your character."))]))
    fi = find("Food, Drink, and Lodging", 5, 101)
    fd_heads = [n for n in NODES[fi:fi + 40] if (n.type == "h" and n.text == "Food, Drink, and Lodging")
                or (n.type == "t" and n.text.startswith("| **Item** | **Cost**"))
                or (n.type == "p" and n.text in ("*Inn Stay per Day*", "*Meal*", "*Wine (bottle)*"))]
    E.append(build("rule", "food-drink-and-lodging", "Food, Drink, and Lodging", section("Food, Drink, and Lodging", 2) + fd_heads, LOT,
                   "Equipment/Food, Drink, and Lodging", [
                       (None, "rule", {"id": "prices", "single_night": True, "included_in": "dnd5e/rule/lifestyle-expenses"}),
                       ("##### Food, Drink, and Lodging", "rule", {"id": "table", "rows": "dnd5e/service/*"})]))
    hi = find("Hirelings", 5, 102)
    E.append(build("rule", "hirelings", "Hirelings", section("Hirelings", 2) + [NODES[hi], NODES[hi + 1]], LOT, "Equipment/Hirelings", [
        (None, "rule", {"id": "hirelings", "skilled": "involves_a_proficiency", "untrained": "no_proficiency", "pay_is_minimum": True}),
        ("##### Hirelings", "rule", {"id": "table", "rows": ["dnd5e/service/skilled-hireling", "dnd5e/service/untrained-hireling",
                                                             "dnd5e/service/messenger"]})]))
    si = find("Spellcasting Services", 5, 102)
    E.append(build("rule", "spellcasting-services", "Spellcasting", section("Spellcasting", 2, page=102) + [NODES[si], NODES[si + 1]], LOT,
                   "Equipment/Spellcasting", [
                       (None, "rule", {"id": "services", "add_expensive_component_cost": True, "higher_level_harder_to_find": True}),
                       ("##### Spellcasting Services", "rule", {"id": "table", "rows": "dnd5e/service/spellcasting-*"})]))
    return E


REGISTRY = {
    "events": [
        {"id": "steps_on_trap", "description": "A creature steps on the trap's pressure plate.", "pages": [98]},
        {"id": "takes_fire_damage", "description": "The creature takes Fire damage.", "pages": [98]}],
    "predicates": [
        {"id": "save_against_hazard", "description": "The saving throw is against this hazard (param).", "params": ["hazard"], "type": "predicate", "pages": [96]},
        {"id": "consulting_accurate_source", "description": "The creature consults an accurate source about the topic or place.", "type": "predicate", "pages": [96]},
        {"id": "impersonating_costume_subject", "description": "The check is made to impersonate the person or type the Costume represents.", "type": "predicate", "pages": [97]},
        {"id": "leverage_applies", "description": "The Crowbar's leverage can be applied to the Strength check.", "type": "predicate", "pages": [97]},
        {"id": "appraising_detailed_item", "description": "The check is made to appraise or inspect a highly detailed item.", "type": "predicate", "pages": [98]},
        {"id": "influencing_indifferent_humanoid_within_feet", "description": "The check influences an Indifferent Humanoid within N feet (param).", "params": ["feet"], "type": "predicate", "pages": [99]},
        {"id": "check_for_jump", "description": "The check is part of a High or Long Jump.", "type": "predicate", "pages": [99]},
        {"id": "breaking_down_door", "description": "The check is made to break down a door.", "type": "predicate", "pages": [99]},
        {"id": "helped_by_other_character", "description": "Another character helps with the ram.", "type": "predicate", "pages": [99]},
        {"id": "check_uses_proficient_tool", "description": "The ability check uses a tool the creature is proficient with.", "type": "predicate", "pages": [93]},
        {"id": "check_uses_proficient_skill", "description": "The ability check also uses a skill the creature is proficient in.", "type": "predicate", "pages": [93]},
        {"id": "check_to_remain_mounted", "description": "The ability check is made to remain mounted.", "type": "predicate", "pages": [100]}],
}

if __name__ == "__main__":
    extend_registries(REGISTRY, LOT)
    out = sections() + tool_entries() + gear_entries() + mounts_and_vehicles() + services() + lifestyles()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
