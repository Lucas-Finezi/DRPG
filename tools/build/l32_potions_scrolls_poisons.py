#!/usr/bin/env python3
"""L32 — Potions, oils and the Spell Scroll (25 magic items), Brewing Potions of Healing,
Scribing Spell Scrolls, and Poison with its 14 sample poisons.

Usage: python3 -I tools/build/l32_potions_scrolls_poisons.py
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import build, extend_registries, section, slugify, write_entry  # noqa: E402
from itemlib import money  # noqa: E402
from magiclib import (INHERIT, MI, SELF, SP, adv, cast, check, cond, dmg, hours, item_nodes, md, mins, mod, ref,  # noqa: E402
                      resist, rows_of, save, setv, speed, tab, trig)
from l31_registry import REGISTRY  # noqa: E402

LOT = "L32"
ROOT = Path(__file__).resolve().parents[2]
INV = {e["name"]: e for e in json.loads((ROOT / "inventory/dnd5e/srd-5.2.1/entries.json").read_text(encoding="utf-8"))["entries"]
       if e["lot"] == LOT and e["kind"] == "poison"}
DRINK = {"op": "activation", "cost": "bonus_action", "name": "Drink"}
EACH_END = {"on": {"event": "turn_end", "whose": "target", "which": "each"}, "ends": "effect_on_self"}


def drink(effects, **kw):
    """Drinking or administering a potion (a Bonus Action, see Potions)."""
    return {**DRINK, "then": effects if isinstance(effects, list) else [effects], **kw}


def oil(effects, minutes, **kw):
    return {"op": "activation", "cost": "none", "name": "Apply", "then": effects if isinstance(effects, list) else [effects],
            "note": f"Applying the oil takes {minutes} minute{'s' if minutes != 1 else ''}.", **kw}


def potion(name, items, flavor=None):
    items = list(items)
    if flavor:
        items.append((flavor, "desc", None))
    return MI(name, items)


def no_conc(spell, dur=None, **kw):
    return cast(spell, note="No Concentration required." + (f" Lasts {dur}." if dur else ""), **kw)


def entries():
    E = []
    E.append(potion("Elixir of Health", [
        ("^", "fx", drink([ref("dnd5e/rule/magical-contagions", note="Cured of all magical contagions."),
                           {"op": "remove_condition", "conditions": [f"dnd5e/condition/{c}" for c in ("blinded", "deafened", "paralyzed", "poisoned")]}]))],
        "The clear, red liquid"))
    E.append(potion("Oil of Etherealness", [
        ("^", "fx", oil(cast("Etherealness", note="The covered creature gains the spell's effect for 1 hour."), 10)),
        ("^", "rule", {"id": "coverage", "vials": "1 per Medium or smaller creature; +1 per size category above Medium", "includes_gear": True})],
        "Beads of this cloudy"))
    E.append(potion("Oil of Sharpness", [
        ("^", "fx", oil(ref("dnd5e/magic-item/weapon-plus1-plus2-or-plus3", note="The coated weapon becomes a +3 Weapon; ammunition becomes +3 Ammunition."), 1)),
        ("^", "rule", {"id": "coverage", "one_melee_weapon_or_ammunition": 20, "only": "nonmagical, Slashing or Piercing"})],
        "This clear, gelatinous oil"))
    E.append(potion("Oil of Slipperiness", [
        ("^", "fx", oil(cast("Freedom of Movement", note="Effect for 8 hours on the covered creature."), 10)),
        ("^", "rule", {"id": "coverage", "vials": "1 per Medium or smaller creature; +1 per size category above Medium"}),
        ("Alternatively, the oil can be poured", "fx", {"op": "activation", "cost": "action", "action": "dnd5e/action/magic",
                                                        "then": [cast("Grease", note="Duplicates Grease in a 10-foot square for 8 hours.")]})],
        "This sticky, black unguent"))
    E.append(potion("Philter of Love", [
        ("^", "fx", drink(cond("charmed", hours(1), note="By the next creature you see within 10 minutes after drinking.")))],
        "This rose-hued"))
    E.append(potion("Potion of Animal Friendship", [("^", "fx", drink(cast("Animal Friendship", level=3, dc=13)))], "Agitating this potion"))
    E.append(potion("Potion of Clairvoyance", [("^", "fx", drink(no_conc("Clairvoyance")))], "An eyeball bobs"))
    E.append(potion("Potion of Climbing", [
        ("^", "fx", drink([speed("climb", 0, mode="equal_to_walk", duration=hours(1)),
                           adv("ability_check", {"all": [{"pred": "check_uses_skill", "args": {"skill": "athletics"}},
                                                         {"pred": "check_for_movement", "args": {"modes": ["climb"]}}]}, duration=hours(1))]))],
        "This potion is separated"))
    E.append(potion("Potion of Diminution", [("^", "fx", drink(no_conc("Enlarge/Reduce", "1d4 hours (reduce effect)")))], "The red in the potion’s liquid continuously contracts"))
    E.append(potion("Potion of Flying", [
        ("^", "fx", drink(speed("fly", 0, mode="equal_to_walk", hover=True, duration=hours(1)))),
        ("^", "rule", {"id": "expiry", "falls_if_aloft": True})], "This potion’s clear liquid"))
    E.append(potion("Potion of Gaseous Form", [("^", "fx", drink(no_conc("Gaseous Form", "1 hour or until ended as a Bonus Action")))],
                    "This potion’s container seems"))
    gs = item_nodes("Potion of Giant Strength")
    E.append(MI("Potion of Giant Strength", [
        ("^", "fx", drink(setv("ability_score.str", {"var": "item_variant_score"}, duration=hours(1), note="No effect if your Strength is already equal or greater."))),
        ("This potion’s transparent liquid", "desc", None),
        ("| **Potion**", "table", tab("Potion of Giant Strength", ["Potion", "Str.", "Rarity"], rows_of(gs)))],
        data={"item": {"variants": [{"variant": r[0].replace("Potion of Giant Strength ", ""), "score": int(r[1]),
                                     "rarity": r[2].lower().replace(" ", "_")} for r in rows_of(gs)]}}))
    E.append(potion("Potion of Growth", [("^", "fx", drink(no_conc("Enlarge/Reduce", "10 minutes (enlarge effect)")))], "The red in the potion’s liquid continuously expands"))
    heal = item_nodes("Potions of Healing")
    E.append(MI("Potions of Healing", [
        ("^", "fx", drink({"op": "heal", "amount": {"var": "item_variant_healing"}})),
        ("Whatever its potency", "desc", None),
        ("| **Potion**", "table", tab("Potions of Healing", ["Potion", "HP Regained", "Rarity"], rows_of(heal)))],
        data={"item": {"variants": [{"variant": r[0], "hp_regained": r[1], "rarity": r[2].lower().replace(" ", "_")} for r in rows_of(heal)]}}))
    E.append(potion("Potion of Heroism", [
        ("^", "fx", drink([{"op": "temp_hp", "amount": 10, "duration": hours(1)}, no_conc("Bless", "1 hour")]))], "This potion’s blue liquid"))
    E.append(potion("Potion of Invisibility", [
        ("^", "desc", None),
        ("When you drink the potion", "fx", drink(cond("invisible", {"kind": "hours", "amount": 1, "ends_on": [{"event": "attacks_deals_damage_or_casts"}]})))]))
    E.append(potion("Potion of Invulnerability", [
        ("^", "fx", drink(resist(["acid", "bludgeoning", "cold", "fire", "force", "lightning", "necrotic", "piercing", "poison", "psychic", "radiant",
                                  "slashing", "thunder"], duration=mins(1), note="Resistance to all damage.")))], "This potion’s syrupy liquid"))
    E.append(potion("Potion of Longevity", [
        ("^", "fx", drink(ref("dnd5e/magic-item/potion-of-longevity", note="Physical age −(1d6 + 6) years (minimum 13)."))),
        ("^", "rule", {"id": "repeat", "cumulative_failure_percent": 10, "failure": "age +(1d6 + 6) years"})], "Suspended in this amber liquid"))
    E.append(potion("Potion of Mind Reading", [("^", "fx", drink(no_conc("Detect Thoughts", "10 minutes", dc=13)))], "This potion’s dense, purple liquid"))
    E.append(potion("Potion of Poison", [
        ("^", "rule", {"id": "disguise", "looks_like": "a beneficial potion", "identify_reveals": SP("Identify")}),
        ("If you drink this potion", "fx", drink([dmg("4d6", "poison"), save("con", 13, on_fail=cond("poisoned", hours(1)))]))]))
    res = item_nodes("Potion of Resistance")
    E.append(potion("Potion of Resistance", [
        ("^", "fx", drink(resist([{"var": "chosen.resistance_type"}], duration=hours(1)))),
        ("^", "md", md("resistance_type", "Which damage type does the potion resist? (choose or roll 1d10)",
                       "The GM chooses the type or determines it randomly by rolling on the following table.")),
        ("| **1d10**", "table", tab("Potion of Resistance", ["1d10", "Damage Type", "1d10", "Damage Type"], rows_of(res)))]))
    E.append(potion("Potion of Speed", [("^", "fx", drink(no_conc("Haste", "1 minute; no lethargy when it ends")))], "This potion’s yellow fluid"))
    E.append(potion("Potion of Vitality", [
        ("^", "fx", drink([{"op": "remove_condition", "conditions": ["dnd5e/condition/exhaustion", "dnd5e/condition/poisoned"]},
                           {"op": "modifier", "stat": "healing_dice", "mode": "set", "value": 0, "duration": hours(24),
                            "when": {"pred": "roll_is", "args": {"roll": "hit_point_die"}}, "note": "Hit Point Dice spent restore their maximum."}]))],
        "This potion’s crimson liquid"))
    E.append(potion("Potion of Water Breathing", [
        ("^", "fx", drink({"op": "modifier", "stat": "breathe_underwater", "mode": "set", "value": 1, "duration": hours(24)}))], "This potion’s cloudy green fluid"))
    sc = item_nodes("Spell Scroll")
    E.append(MI("Spell Scroll", [
        ("^", "fx", {"op": "activation", "cost": "action", "name": "Read",
                     "then": [ref("dnd5e/magic-item/spell-scroll", note="Cast the stored spell with its normal casting time, without Material components.")],
                     "requires": {"pred": "spell_on_your_list"}}),
        ("^", "rule", {"id": "use", "requires_spell_list": True, "material_components": False, "casting_time": "normal",
                       "crumbles_after_cast": True, "interrupted_not_lost": True}),
        ("If the spell is on your spell list but of a higher level", "fx", check({"var": "spellcasting_ability"}, {"op": "add", "args": [10, {"var": "spell_level"}]},
                                                                                 on_fail=ref("dnd5e/magic-item/spell-scroll", note="The spell disappears with no other effect."),
                                                                                 when={"pred": "spell_level_above_castable"})),
        ("The level of the spell on the scroll", "rule", {"id": "numbers", "by_spell_level": "table"}),
        ("| **Spell Level**", "table", tab("Spell Scroll", ["Spell Level", "Rarity", "Save DC", "Attack Bonus"], rows_of(sc))),
        ("***Copying a Scroll into a Spellbook.***", "fx", check("int", {"op": "add", "args": [10, {"var": "spell_level"}]}, skill="arcana",
                                                                 on_success=ref("dnd5e/feature/wizard-spellcasting", note="The Wizard spell is copied."),
                                                                 note="The scroll is destroyed whether the check succeeds or fails."))],
        data={"item": {"variants": [{"spell_level": 0 if r[0] == "Cantrip" else int(r[0]), "rarity": r[1].lower().replace(" ", "_"),
                                     "save_dc": int(r[2]), "attack_bonus": int(r[3])} for r in rows_of(sc)]}}))
    return E


POISON_TYPES = {"Contact": "contact", "Ingested": "ingested", "Inhaled": "inhaled", "Injury": "injury"}


def poison_fx(name):
    S = lambda dc, **kw: save("con", dc, target={"kind": "creature"}, **kw)  # noqa: E731
    return {
        "Assassin’s Blood": [S(10, on_fail=[dmg("1d12", "poison"), cond("poisoned", hours(24))], half=True, note="On a success, half damage only.")],
        "Burnt Othur Fumes": [S(13, on_fail=dmg("3d6", "poison"),
                                note="Repeat the save at the start of each turn: 1d6 Poison damage on each failure; ends after three successes.")],
        "Crawler Mucus": [S(13, on_fail=[cond("poisoned", mins(1)), cond("paralyzed", {"kind": "while", "while": {"pred": "has_condition", "args": {"condition": "poisoned"}}})],
                            repeat=EACH_END)],
        "Essence of Ether": [S(15, on_fail=[cond("poisoned", hours(8)),
                                            cond("unconscious", {"kind": "while", "while": {"pred": "has_condition", "args": {"condition": "poisoned"}},
                                                                 "ends_on": [{"event": "damage_taken"}, {"event": "shaken_awake"}]})])],
        "Malice": [S(15, on_fail=[cond("poisoned", hours(1)), cond("blinded", {"kind": "while", "while": {"pred": "has_condition", "args": {"condition": "poisoned"}}})])],
        "Midnight Tears": [trig({"event": "midnight"}, S(17, on_fail=dmg("9d6", "poison"), half=True),
                                note="No effect until midnight; anything that ends the Poisoned condition neutralizes it.")],
        "Oil of Taggit": [S(13, on_fail=[cond("poisoned", hours(24)),
                                         cond("unconscious", {"kind": "while", "while": {"pred": "has_condition", "args": {"condition": "poisoned"}},
                                                              "ends_on": [{"event": "damage_taken"}]})])],
        "Pale Tincture": [S(16, on_fail=[dmg("1d6", "poison"), cond("poisoned")],
                            note="Repeat every 24 hours (1d6 Poison damage on failure); the damage can't be healed while Poisoned; ends after seven successes.")],
        "Purple Worm Poison": [S(21, on_fail=dmg("10d6", "poison"), half=True)],
        "Serpent Venom": [S(11, on_fail=dmg("3d6", "poison"), half=True)],
        "Spider’s Sting": [S(13, on_fail=[cond("poisoned", hours(1))],
                             note="Failing by 5 or more: also Unconscious while Poisoned; wakes on damage or when shaken awake (action).")],
        "Torpor": [S(15, on_fail=[cond("poisoned", {"kind": "hours", "amount": "4d6"}),
                                  {"op": "speed", "movement": "walk", "mode": "multiply", "value": 0.5,
                                   "when": {"pred": "has_condition", "args": {"condition": "poisoned"}}}])],
        "Truth Serum": [S(11, on_fail=[cond("poisoned", hours(1)), {"op": "restrict", "restrictions": ["speak_deliberate_lie"],
                                                                    "when": {"pred": "has_condition", "args": {"condition": "poisoned"}}}])],
        "Wyvern Poison": [S(14, on_fail=dmg("7d6", "poison"), half=True)],
    }[name]


def poisons():
    E = []
    for name, e in INV.items():
        h = next(t for t in [f"{name} ({e['facets']['cost']})"])
        nodes = section(h, 4, page=e["page"])
        ptype = re.match(r"^\*(\w+) Poison\*$", nodes[0].text).group(1)
        data = {"cost": money(e["facets"]["cost"]), "poison_type": POISON_TYPES[ptype], "rules": [{"id": "type", "ref": f"dnd5e/rule/poison"}]}
        items = [(None, "sys", ["/data/cost", "/data/poison_type", "/data/rules/0"]),
                 (nodes[1].text[:40], "fx", [_expr(x) for x in poison_fx(name)])]
        if name == "Spider’s Sting":
            items.append((nodes[1].text[:40], "rule", {"id": "deep_sleep", "fail_by": 5, "condition": "dnd5e/condition/unconscious"}))
        E.append(build("poison", e["ref"].split("/")[-1], name, nodes, LOT, f"Gameplay Toolbox/Poison/Sample Poisons/{name}", items,
                       data=data, facets={"poison_type": POISON_TYPES[ptype], "cost_cp": data["cost"]["cp"]}))
    return E


def _expr(x):
    from magiclib import expr
    return expr(x)


def sections():
    E = []
    E.append(build("rule", "brewing-potions-of-healing", "Brewing Potions of Healing", section("Brewing Potions of Healing", 2, page=103), LOT,
                   "Equipment/Brewing Potions of Healing", [
                       (None, "rule", {"id": "brew", "proficiency": "dnd5e/tool/herbalism-kit", "cost_gp": 25, "days": 1, "hours": 8,
                                       "product": "dnd5e/magic-item/potions-of-healing"})]))
    E.append(build("rule", "scribing-spell-scrolls", "Scribing Spell Scrolls", section("Scribing Spell Scrolls", 2, page=103, stop_titles=("Time and Cost",)), LOT,
                   "Equipment/Scribing Spell Scrolls", [(None, "rule", {"id": "scribe", "product": "dnd5e/magic-item/spell-scroll"})]))
    E.append(build("rule", "scribing-time-and-cost", "Time and Cost (Scribing)", section("Time and Cost", 3, page=103), LOT,
                   "Equipment/Scribing Spell Scrolls/Time and Cost", [
                       (None, "rule", {"id": "time", "table": "spell_scroll_costs", "hours_per_day": 8, "consecutive": False})]))
    E.append(build("rule", "prerequisites-for-the-scribe", "Prerequisites for the Scribe", section("Prerequisites for the Scribe", 3, page=103), LOT,
                   "Equipment/Scribing Spell Scrolls/Prerequisites for the Scribe", [
                       (None, "rule", {"id": "prerequisites", "proficiency_any": ["arcana", "dnd5e/tool/calligraphers-supplies"],
                                       "spell_prepared_each_day": True, "material_components_at_hand": True, "consumed_on_completion": True,
                                       "uses": ["spell_save_dc", "spell_attack_bonus"]})]))
    cn = section("Cantrips", 3, page=103)
    E.append(build("rule", "scribing-cantrips", "Cantrips (Scribing)", cn, LOT, "Equipment/Scribing Spell Scrolls/Cantrips", [
        (None, "rule", {"id": "cantrip", "caster_level": "yours"}),
        ("##### Spell Scroll Costs", "table", {"id": "spell_scroll_costs", "caption": "Spell Scroll Costs", "columns": ["Spell Level", "Time", "Cost"],
                                               "rows": [n.cells for n in cn if n.type == "t" and not n.text.startswith("| **")]})]))
    E.append(build("rule", "poison", "Poison", section("Poison", 2, page=197, stop_titles=("Purchasing Poison",)), LOT, "Gameplay Toolbox/Poison", [
        (None, "desc", None),
        ("Poisons come in the following four types", "rule", {"id": "types", "values": list(POISON_TYPES.values())}),
        ("**Contact.**", "rule", {"id": "contact", "smeared_on_object": True, "until": ["touched", "washed off"], "exposed_skin": True}),
        ("**Ingested.**", "rule", {"id": "ingested", "whole_dose": True, "via": ["food", "liquid"]}),
        ("**Ingested.**", "md", md("partial_dose", "Does a partial dose have a reduced effect (e.g. Advantage on the save or half damage)?",
                                   "You may decide that a partial dose has a reduced effect")),
        ("**Inhaled.**", "rule", {"id": "inhaled", "area": {"shape": "cube", "size_feet": 5}, "dissipates": "immediately", "holding_breath_ineffective": True}),
        ("**Injury.**", "rule", {"id": "injury", "apply": "bonus_action", "on": ["weapon", "ammunition", "similar object"],
                                 "until": ["delivered", "washed off"], "exposure": "piercing or slashing damage from the coated object"})]))
    E.append(build("rule", "purchasing-poison", "Purchasing Poison", section("Purchasing Poison", 3, page=197), LOT, "Gameplay Toolbox/Poison/Purchasing Poison", [
        (None, "md", md("poison_availability", "Can the characters acquire poison here, and at what difficulty?",
                        "In some settings, laws prohibit the possession and use of poison", reason="narrative"))]))
    E.append(build("rule", "harvesting-poison", "Harvesting Poison", section("Harvesting Poison", 3, page=197), LOT, "Gameplay Toolbox/Poison/Harvesting Poison", [
        (None, "fx", {"op": "check", "ability": "int", "skill": "nature", "dc": 20,
                      "on_success": [ref("dnd5e/rule/poison", note="One dose; nothing more can be harvested from that creature.")],
                      "on_fail": [ref("dnd5e/rule/poison", note="No poison; failing by 5 or more exposes the character to the creature's poison.")],
                      "note": "Takes 1d6 minutes with a Poisoner's Kit; the creature is dead or Incapacitated."}),
        (None, "rule", {"id": "harvest", "tool": "dnd5e/tool/poisoners-kit", "minutes": "1d6", "creature": "venomous, dead or incapacitated",
                        "fail_by_5": "exposed"})]))
    E.append(build("rule", "sample-poisons", "Sample Poisons", section("Sample Poisons", 3, page=197, stop_titles=("Assassin’s Blood (150 GP)",)), LOT,
                   "Gameplay Toolbox/Poison/Sample Poisons", [(None, "rule", {"id": "order", "alphabetical": True, "fields": ["price", "type", "effects"]})]))
    return E


L32_REGISTRY = {
    "events": [{"id": "midnight", "description": "The stroke of midnight.", "type": "event", "pages": [197]},
               {"id": "shaken_awake", "description": "Another creature takes an action to shake the creature awake.", "type": "event", "pages": [197]}],
    "predicates": [{"id": "spell_on_your_list", "description": "The spell is on the creature's spell list.", "type": "predicate", "pages": [244]},
                   {"id": "spell_level_above_castable", "description": "The spell is of a higher level than the creature can normally cast.", "type": "predicate", "pages": [244]}],
    "variables": [{"id": "item_variant_healing", "description": "Hit Points regained by the potion's variant (Potions of Healing table).", "type": "number", "pages": [236]},
                  {"id": "spellcasting_ability", "description": "The creature's spellcasting ability.", "type": "identifier", "pages": [244]}],
}

if __name__ == "__main__":
    extend_registries(REGISTRY, "L31")
    extend_registries(L32_REGISTRY, LOT)
    out = entries() + poisons() + sections()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
