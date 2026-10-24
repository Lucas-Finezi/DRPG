#!/usr/bin/env python3
"""L14 (part) — Species traits as feature entries.

Usage: python3 -I tools/build/l14_species_traits.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from classlib import feature, trait_nodes  # noqa: E402
from entrylib import extend_registries, md, write_entry  # noqa: E402

LOT = "L14"
C = lambda s: f"dnd5e/condition/{s}"  # noqa: E731
S = lambda s: f"dnd5e/spell/{s}"  # noqa: E731
PB = {"var": "proficiency_bonus"}
LONG = {"event": "long_rest_finished"}
SHORT_OR_LONG = [{"on": {"event": "short_rest_finished"}, "amount": "all"}, {"on": LONG, "amount": "all"}]

REGISTRY = {
    "variables": [
        {"id": "chosen", "description": "Value fixed by an earlier choice of the same entry (param: the choice id).", "params": ["choice"], "type": "identifier", "pages": [84]},
    ],
    "events": [
        {"id": "condition_gained", "description": "The creature gains a condition (param: condition slug).", "params": ["condition"], "type": "event", "pages": [84]},
        {"id": "attack_action_attack", "description": "One of the attacks of the creature's Attack action on its turn.", "type": "event", "pages": [84]},
        {"id": "hits_with_attack_roll", "description": "The creature hits a target with an attack roll and deals damage to it.", "type": "event", "pages": [85]},
        {"id": "rolls_natural_1", "description": "The creature rolls a 1 on the d20 of a D20 Test.", "type": "event", "pages": [86]},
        {"id": "reduced_to_0_hp_not_killed", "description": "The creature is reduced to 0 Hit Points but not killed outright.", "type": "event", "pages": [86]},
        {"id": "damaged_by_creature_within", "description": "The creature takes damage from a creature within 'feet'.", "params": ["feet"], "type": "event", "pages": [85]},
    ],
    "predicates": [
        {"id": "on_stone_surface", "description": "The creature is on or touching a stone surface.", "type": "predicate", "pages": [84]},
        {"id": "big_enough_space", "description": "The creature is in a space big enough for the new size.", "type": "predicate", "pages": [85]},
        {"id": "obscured_by_larger_creature", "description": "The creature is obscured only by a creature at least one size larger.", "type": "predicate", "pages": [86]},
        {"id": "character_level_at_least", "description": "Character level is at least 'level'.", "params": ["level"], "type": "predicate", "pages": [84]},
        {"id": "save_against_condition", "description": "The saving throw is made to avoid or end the condition (param).", "params": ["condition"], "type": "predicate", "pages": [84]},
        {"id": "check_to_end_condition", "description": "The ability check is made to end the condition (param).", "params": ["condition"], "type": "predicate", "pages": [85]},
    ],
    "stats": [
        {"id": "size", "description": "The creature's size category.", "pages": [85]},
        {"id": "size_for_carrying_capacity", "description": "Size used to determine carrying capacity.", "pages": [85]},
        {"id": "hp_max_per_level", "description": "Hit Point maximum increase per level.", "pages": [84]},
    ],
    "restrictions": [
        {"id": "need_sleep", "description": "The creature doesn't need to sleep.", "pages": [85]},
        {"id": "magical_sleep", "description": "Magic can't put the creature to sleep.", "pages": [85]},
    ],
}


def T(species, trait, items, **kw):
    sp = species.lower()
    return feature(sp, trait, trait_nodes(species, trait), f"Character Origins/Character Species/Species Descriptions/{species}",
                   items, "species_trait", f"dnd5e/species/{sp}", **kw)


def darkvision(species, feet):
    return T(species, "Darkvision", [(None, "fx", {"op": "sense", "sense": "darkvision", "range_feet": feet})])


def lineage_spells(prefix, table_species, choose_label):
    return [
        ("When you reach character levels 3 and 5", "rule", {
            "id": "lineage_spells", "levels": [3, 5], "from_table": f"dnd5e/species/{table_species}",
            "always_prepared": True, "free_casting": {"count": 1, "recovery": "long_rest_finished"},
            "may_use_slots": True}),
        ("Intelligence, Wisdom, or Charisma is your spellcasting ability", "fx", {
            "op": "choice", "id": "spellcasting_ability", "choose": 1, "options": [
                {"id": a, "label": a.upper(), "value": a, "effects": []} for a in ("int", "wis", "cha")],
            "note": f"Spellcasting ability for the spells of this {choose_label}."}),
    ]


def at_level(level, spell):
    return {"op": "grant", "refs": [S(spell)], "when": {"pred": "level_at_least", "args": {"level": level}},
            "note": f"Character level {level}: always prepared."}


def lineage_option(id_, label, level_1, spell_3, spell_5):
    """One row of a lineage/legacy table as effects (D-005): Level 1 benefit, then the level 3 and 5 spells."""
    return {"id": id_, "label": label, "effects": [*level_1, at_level(3, spell_3), at_level(5, spell_5)]}


def entries():
    E = []
    # Dragonborn
    E.append(T("Dragonborn", "Draconic Ancestry", [(None, "fx", {
        "op": "choice", "id": "draconic_ancestry", "choose": 1, "options": [
            {"id": d.lower(), "label": d, "value": t, "effects": []}
            for d, t in [("Black", "acid"), ("Blue", "lightning"), ("Brass", "fire"), ("Bronze", "lightning"),
                         ("Copper", "acid"), ("Gold", "fire"), ("Green", "poison"), ("Red", "fire"),
                         ("Silver", "cold"), ("White", "cold")]]})]))
    ancestry = {"var": "chosen.draconic_ancestry"}

    def breath(shape, size, width=None):
        area = {"shape": shape, "size_feet": size, "origin": "self"}
        if width:
            area["width_feet"] = width
        return {"op": "save", "ability": "dex", "dc": {"op": "add", "args": [8, {"var": "ability_mod.con"}, PB]},
                "target": {"kind": "area", "area": area},
                "on_fail": [{"op": "damage", "amount": {"scale": {"by": "level", "steps": [
                    {"from": 1, "value": "1d10"}, {"from": 5, "value": "2d10"}, {"from": 11, "value": "3d10"},
                    {"from": 17, "value": "4d10"}]}}, "damage_type": ancestry}],
                "half_on_success": True}
    E.append(T("Dragonborn", "Breath Weapon", [
        (None, "fx", [{"op": "resource", "resource": "breath_weapon", "max": PB, "recovery": [{"on": LONG, "amount": "all"}]},
                      {"op": "trigger", "event": {"event": "attack_action_attack"}, "optional": True,
                       "note": "Replaces one attack of the Attack action on your turn.",
                       "then": [{"op": "spend", "resource": "breath_weapon", "amount": 1},
                                {"op": "choice", "choose": 1, "options": [
                                    {"id": "cone", "label": "15-foot Cone", "effects": [breath("cone", 15)]},
                                    {"id": "line", "label": "30-foot Line, 5 feet wide",
                                     "effects": [breath("line", 30, 5)]}]}]}]),
        ("You can use this Breath Weapon a number of times", "rule", {"id": "uses", "max": "proficiency_bonus",
                                                                       "recovery": "long_rest"})]))
    E.append(T("Dragonborn", "Damage Resistance", [(None, "fx", {"op": "defense", "kind": "resistance",
                                                                "damage_types": [{"var": "chosen.draconic_ancestry"}]})]))
    E.append(darkvision("Dragonborn", 60))
    E.append(T("Dragonborn", "Draconic Flight", [(None, "fx", [
        {"op": "resource", "resource": "draconic_flight", "max": 1, "recovery": [{"on": LONG, "amount": "all"}]},
        {"op": "activation", "name": "Draconic Flight", "cost": "bonus_action",
         "requires": {"pred": "character_level_at_least", "args": {"level": 5}},
         "uses": {"resource": "draconic_flight", "amount": 1},
         "then": [{"op": "speed", "movement": "fly", "mode": "equal_to_walk", "value": 0,
                   "duration": {"kind": "minutes", "amount": 10, "ends_on": [
                       {"event": "condition_gained.incapacitated", "whose": "self"}]},
                   "note": "Ends early if you retract the wings (no action) or have the Incapacitated condition."}]}])]))
    # Dwarf
    E.append(darkvision("Dwarf", 120))
    E.append(T("Dwarf", "Dwarven Resilience", [(None, "fx", [
        {"op": "defense", "kind": "resistance", "damage_types": ["poison"]},
        {"op": "roll_mode", "mode": "advantage", "rolls": ["saving_throw"],
         "when": {"pred": "save_against_condition", "args": {"condition": "poisoned"}}}])]))
    E.append(T("Dwarf", "Dwarven Toughness", [(None, "fx", [
        {"op": "modifier", "stat": "hp_max", "mode": "add", "value": {"var": "level"},
         "note": "+1 now and +1 per level gained."}])]))
    E.append(T("Dwarf", "Stonecunning", [
        (None, "fx", {"op": "activation", "name": "Stonecunning", "cost": "bonus_action",
                      "uses": {"resource": "stonecunning", "amount": 1},
                      "then": [{"op": "sense", "sense": "tremorsense", "range_feet": 60,
                                "duration": {"kind": "minutes", "amount": 10},
                                "when": {"pred": "on_stone_surface"}}]}),
        ("You can use this Bonus Action a number of times", "fx", {
            "op": "resource", "resource": "stonecunning", "max": PB, "recovery": [{"on": LONG, "amount": "all"}]})]))
    # Elf
    E.append(darkvision("Elf", 60))
    E.append(T("Elf", "Elven Lineage", [
        (None, "fx", {"op": "choice", "id": "lineage", "choose": 1, "options": [
            lineage_option("drow", "Drow", [
                {"op": "sense", "sense": "darkvision", "range_feet": 120, "note": "Darkvision range increases to 120 feet."},
                {"op": "grant", "refs": [S("dancing-lights")]}], "faerie-fire", "darkness"),
            lineage_option("high_elf", "High Elf", [
                {"op": "grant", "refs": [S("prestidigitation")],
                 "note": "After a Long Rest it can be replaced by another Wizard cantrip."}], "detect-magic", "misty-step"),
            lineage_option("wood_elf", "Wood Elf", [
                {"op": "speed", "movement": "walk", "mode": "set", "value": 35},
                {"op": "grant", "refs": [S("druidcraft")]}], "longstrider", "pass-without-trace")],
            "note": "Elven Lineages table (data.tables of dnd5e/species/elf)."}),
        *lineage_spells("elf", "elf", "lineage")]))
    E.append(T("Elf", "Fey Ancestry", [(None, "fx", {"op": "roll_mode", "mode": "advantage", "rolls": ["saving_throw"],
                                                    "when": {"pred": "save_against_condition",
                                                             "args": {"condition": "charmed"}}})]))
    E.append(T("Elf", "Keen Senses", [(None, "fx", {"op": "proficiency", "category": "skill", "choose": 1,
                                                   "from": ["insight", "perception", "survival"]})]))
    E.append(T("Elf", "Trance", [(None, "fx", [{"op": "restrict", "restrictions": ["need_sleep", "magical_sleep"],
                                                "note": "Immunities: no need to sleep; magic can't cause sleep."}]),
                                 ("You can finish a Long Rest in 4 hours", "rule", {
                                     "id": "trance", "long_rest_hours": 4, "conscious": True})]))
    # Gnome
    E.append(darkvision("Gnome", 60))
    E.append(T("Gnome", "Gnomish Cunning", [(None, "fx", {"op": "roll_mode", "mode": "advantage",
                                                         "rolls": ["saving_throw.int", "saving_throw.wis",
                                                                   "saving_throw.cha"]})]))
    E.append(T("Gnome", "Gnomish Lineage", [
        (None, "fx", {"op": "choice", "choose": 1, "options": [
            {"id": "forest_gnome", "label": "Forest Gnome", "effects": [
                {"op": "grant", "refs": [S("minor-illusion"), S("speak-with-animals")]},
                {"op": "resource", "resource": "speak_with_animals_free", "max": PB,
                 "recovery": [{"on": LONG, "amount": "all"}]}]},
            {"id": "rock_gnome", "label": "Rock Gnome", "effects": [
                {"op": "grant", "refs": [S("mending"), S("prestidigitation")]}]}]}),
        (None, "rule", {"id": "spellcasting_ability", "choose_from": ["int", "wis", "cha"], "when": "lineage_chosen"}),
        ("**Forest Gnome.**", "rule", {"id": "forest_gnome", "cantrip": S("minor-illusion"),
                                       "always_prepared": S("speak-with-animals"),
                                       "free_casts": "proficiency_bonus", "recovery": "long_rest",
                                       "may_use_slots": True}),
        ("**Rock Gnome.**", "rule", {"id": "rock_gnome", "cantrips": [S("mending"), S("prestidigitation")],
                                     "clockwork_device": {"casting_minutes": 10, "size": "tiny", "ac": 5, "hp": 1,
                                                          "effect": "one_prestidigitation_effect",
                                                          "activation": "bonus_action_touch", "max_devices": 3,
                                                          "lasts_hours": 8, "dismantle": "utilize_action"}})]))
    # Goliath
    gb = {"op": "resource", "resource": "giant_ancestry", "max": PB, "recovery": [{"on": LONG, "amount": "all"}]}
    E.append(T("Goliath", "Giant Ancestry", [
        (None, "fx", [gb, {"op": "choice", "choose": 1, "options": [
            {"id": "clouds_jaunt", "label": "Cloud’s Jaunt (Cloud Giant)", "effects": [
                {"op": "activation", "cost": "bonus_action", "uses": {"resource": "giant_ancestry"},
                 "then": [{"op": "move", "mode": "teleport", "distance_feet": 30,
                           "note": "To an unoccupied space you can see."}]}]},
            {"id": "fires_burn", "label": "Fire’s Burn (Fire Giant)", "effects": [
                {"op": "trigger", "event": {"event": "hits_with_attack_roll"}, "optional": True,
                 "then": [{"op": "spend", "resource": "giant_ancestry", "amount": 1},
                          {"op": "damage", "amount": "1d10", "damage_type": "fire", "target": {"kind": "inherit"}}]}]},
            {"id": "frosts_chill", "label": "Frost’s Chill (Frost Giant)", "effects": [
                {"op": "trigger", "event": {"event": "hits_with_attack_roll"}, "optional": True,
                 "then": [{"op": "spend", "resource": "giant_ancestry", "amount": 1},
                          {"op": "damage", "amount": "1d6", "damage_type": "cold", "target": {"kind": "inherit"}},
                          {"op": "speed", "movement": "walk", "mode": "add", "value": -10, "target": {"kind": "inherit"},
                           "duration": {"kind": "until_event", "until": {"event": "turn_start", "whose": "source"}}}]}]},
            {"id": "hills_tumble", "label": "Hill’s Tumble (Hill Giant)", "effects": [
                {"op": "trigger", "event": {"event": "hits_with_attack_roll"}, "optional": True,
                 "then": [{"op": "spend", "resource": "giant_ancestry", "amount": 1},
                          {"op": "apply_condition", "condition": C("prone"),
                           "target": {"kind": "inherit", "filter": {"sizes": ["tiny", "small", "medium", "large"]}}}]}]},
            {"id": "stones_endurance", "label": "Stone’s Endurance (Stone Giant)", "effects": [
                {"op": "trigger", "event": {"event": "damage_taken"}, "cost": "reaction", "optional": True,
                 "then": [{"op": "spend", "resource": "giant_ancestry", "amount": 1},
                          {"op": "modifier", "stat": "damage_taken", "mode": "add",
                           "value": {"op": "neg", "args": [{"op": "add", "args": ["1d12", {"var": "ability_mod.con"}]}]}}]}]},
            {"id": "storms_thunder", "label": "Storm’s Thunder (Storm Giant)", "effects": [
                {"op": "trigger", "event": {"event": "damaged_by_creature_within.60"}, "cost": "reaction",
                 "optional": True, "then": [{"op": "spend", "resource": "giant_ancestry", "amount": 1},
                                            {"op": "damage", "amount": "1d8", "damage_type": "thunder",
                                             "target": {"kind": "inherit"}}]}]}]}]),
        ("**Cloud’s Jaunt (Cloud Giant).**", "sys", ["/effects/1/options/0"]),
        ("**Fire’s Burn (Fire Giant).**", "sys", ["/effects/1/options/1"]),
        ("**Frost’s Chill (Frost Giant).**", "sys", ["/effects/1/options/2"]),
        ("**Hill’s Tumble (Hill Giant).**", "sys", ["/effects/1/options/3"]),
        ("**Stone’s Endurance (Stone Giant).**", "sys", ["/effects/1/options/4"]),
        ("**Storm’s Thunder (Storm Giant).**", "sys", ["/effects/1/options/5"])]))
    E.append(T("Goliath", "Large Form", [(None, "fx", [
        {"op": "resource", "resource": "large_form", "max": 1, "recovery": [{"on": LONG, "amount": "all"}]},
        {"op": "activation", "name": "Large Form", "cost": "bonus_action", "uses": {"resource": "large_form"},
         "requires": {"all": [{"pred": "character_level_at_least", "args": {"level": 5}}, {"pred": "big_enough_space"}]},
         "then": [{"op": "modifier", "stat": "size", "mode": "set", "value": 3, "note": "Large.",
                   "duration": {"kind": "minutes", "amount": 10}},
                  {"op": "roll_mode", "mode": "advantage", "rolls": ["ability_check.str"],
                   "duration": {"kind": "minutes", "amount": 10}},
                  {"op": "speed", "movement": "walk", "mode": "add", "value": 10,
                   "duration": {"kind": "minutes", "amount": 10}}],
         "note": "You can end it early (no action required)."}])]))
    E.append(T("Goliath", "Powerful Build", [(None, "fx", [
        {"op": "roll_mode", "mode": "advantage", "rolls": ["ability_check"],
         "when": {"pred": "check_to_end_condition", "args": {"condition": "grappled"}}},
        {"op": "modifier", "stat": "size_for_carrying_capacity", "mode": "add", "value": 1}])]))
    # Halfling
    E.append(T("Halfling", "Brave", [(None, "fx", {"op": "roll_mode", "mode": "advantage", "rolls": ["saving_throw"],
                                                  "when": {"pred": "save_against_condition",
                                                           "args": {"condition": "frightened"}}})]))
    E.append(T("Halfling", "Halfling Nimbleness", [(None, "rule", {"id": "nimbleness", "move_through": "creature_one_size_larger",
                                                                   "stop_in_space": False})]))
    E.append(T("Halfling", "Luck", [(None, "fx", {"op": "trigger", "event": {"event": "rolls_natural_1"}, "optional": True,
                                                 "then": [{"op": "reroll", "rolls": ["d20_test"], "keep": "new"}]})]))
    E.append(T("Halfling", "Naturally Stealthy", [(None, "rule", {"id": "hide_behind_larger",
                                                                  "hide_allowed_when": {"pred": "obscured_by_larger_creature"}})]))
    # Human
    E.append(T("Human", "Resourceful", [(None, "fx", {"op": "trigger", "event": LONG, "then": [
        {"op": "restore", "resource": "heroic_inspiration", "amount": 1}]})]))
    E.append(T("Human", "Skillful", [(None, "fx", {"op": "proficiency", "category": "skill", "choose": 1, "from": ["any"],
                                                  "note": "Any skill."})]))
    E.append(T("Human", "Versatile", [(None, "fx", {"op": "grant", "refs": ["dnd5e/feat/alert", "dnd5e/feat/magic-initiate",
                                                                           "dnd5e/feat/savage-attacker", "dnd5e/feat/skilled"],
                                                   "choose": 1, "note": "An Origin feat of your choice; Skilled is recommended."})]))
    # Orc
    E.append(T("Orc", "Adrenaline Rush", [
        (None, "fx", {"op": "activation", "name": "Adrenaline Rush", "cost": "bonus_action",
                      "uses": {"resource": "adrenaline_rush", "amount": 1},
                      "then": [{"op": "reference", "rule": "dnd5e/action/dash"}, {"op": "temp_hp", "amount": PB}]}),
        ("You can use this trait a number of times", "fx", {"op": "resource", "resource": "adrenaline_rush", "max": PB,
                                                            "recovery": SHORT_OR_LONG})]))
    E.append(darkvision("Orc", 120))
    E.append(T("Orc", "Relentless Endurance", [(None, "fx", [
        {"op": "resource", "resource": "relentless_endurance", "max": 1, "recovery": [{"on": LONG, "amount": "all"}]},
        {"op": "trigger", "event": {"event": "reduced_to_0_hp_not_killed"}, "optional": True,
         "then": [{"op": "spend", "resource": "relentless_endurance", "amount": 1},
                  {"op": "modifier", "stat": "hp", "mode": "set", "value": 1}]}])]))
    # Tiefling
    E.append(darkvision("Tiefling", 60))
    E.append(T("Tiefling", "Fiendish Legacy", [
        (None, "fx", {"op": "choice", "id": "legacy", "choose": 1, "options": [
            lineage_option(l.lower(), l, [{"op": "defense", "kind": "resistance", "damage_types": [dmg]},
                                          {"op": "grant", "refs": [S(cantrip)]}], s3, s5)
            for l, dmg, cantrip, s3, s5 in (("Abyssal", "poison", "poison-spray", "ray-of-sickness", "hold-person"),
                                            ("Chthonic", "necrotic", "chill-touch", "false-life", "ray-of-enfeeblement"),
                                            ("Infernal", "fire", "fire-bolt", "hellish-rebuke", "darkness"))],
            "note": "Fiendish Legacies table (data.tables of dnd5e/species/tiefling)."}),
        *lineage_spells("tiefling", "tiefling", "legacy")]))
    E.append(T("Tiefling", "Otherworldly Presence", [(None, "fx", {
        "op": "grant", "refs": [S("thaumaturgy")], "note": "Uses the Fiendish Legacy spellcasting ability."})]))
    return E


if __name__ == "__main__":
    extend_registries(REGISTRY, LOT)
    out = entries()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
