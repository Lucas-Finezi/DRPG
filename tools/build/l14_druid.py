#!/usr/bin/env python3
"""L14 (part) — Druid and Circle of the Land features."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from classlib import CF, col, spell_table, spellcasting  # noqa: E402
from entrylib import extend_registries, md, table_nodes, write_entry  # noqa: E402

LOT = "L14"
D = "Druid"
LONG = {"event": "long_rest_finished"}
SHORT = {"event": "short_rest_finished"}
C = lambda s: f"dnd5e/condition/{s}"  # noqa: E731
WIS = {"var": "ability_mod.wis"}
MAGIC = {"cost": "action", "action": "dnd5e/action/magic"}
WILD = {"resource": "wild_shape", "amount": 1}
LANDS = ("Arid", "Polar", "Temperate", "Tropical")


def rows(caption):
    return [n.cells for n in table_nodes(caption)[1:] if n.type == "t" and not n.text.startswith("| **")]


def entries():
    E = []
    E.append(CF(D, "Spellcasting", 1, spellcasting(
        D, "wis", ["dnd5e/gear/druidic-focus"], 4, ["Animal Friendship", "Cure Wounds", "Faerie Fire", "Thunderwave"],
        "long_rest_any", cantrips=(2, ["Druidcraft", "Produce Flame"], "level_gained"))))
    E.append(CF(D, "Druidic", 1, [
        (None, "fx", [{"op": "proficiency", "category": "language", "items": ["druidic"]},
                      {"op": "grant", "refs": ["dnd5e/spell/speak-with-animals"], "note": "Always prepared."}]),
        ("You can use Druidic to leave hidden messages.", "rule", {
            "id": "hidden_messages", "auto_spot": "knows_druidic",
            "others_spot": {"check": {"ability": "int", "skill": "investigation", "dc": 15}},
            "decipher_requires": "magic"})]))
    E.append(CF(D, "Primal Order", 1, [
        (None, "fx", {"op": "choice", "id": "primal_order", "choose": 1, "options": [
            {"id": "magician", "label": "Magician", "effects": [
                {"op": "modifier", "stat": "cantrips_known", "mode": "add", "value": 1,
                 "note": "One extra cantrip from the Druid spell list."},
                {"op": "modifier", "stat": "ability_check.int", "mode": "add", "value": {"op": "max", "args": [1, WIS]},
                 "when": {"any": [{"pred": "check_uses_skill", "args": {"skill": "arcana"}},
                                  {"pred": "check_uses_skill", "args": {"skill": "nature"}}]}}]},
            {"id": "warden", "label": "Warden", "effects": [
                {"op": "proficiency", "category": "weapon", "items": ["martial"]},
                {"op": "proficiency", "category": "armor", "items": ["medium"]}]}]}),
        ("***Magician.***", "sys", ["/effects/0/options/0"]),
        ("***Warden.***", "sys", ["/effects/0/options/1"])]))
    shapes = rows("Beast Shapes")
    E.append(CF(D, "Wild Shape", 2, [
        (None, "fx", {"op": "activation", "name": "Wild Shape", "cost": "bonus_action", "uses": WILD,
                      "then": [{"op": "transform", "into": {"creature_types": ["beast"],
                                                            "predicate": {"pred": "known_wild_shape_form"}},
                                "keeps": ["creature_type", "hp", "hp_max", "hit_point_dice", "ability_score.int",
                                          "ability_score.wis", "ability_score.cha", "class_features", "languages",
                                          "feats", "skill_proficiencies", "saving_throw_proficiencies",
                                          "proficiency_bonus"],
                                "duration": {"kind": "hours", "amount": {"op": "div", "args": [
                                    {"var": "class_level.druid"}, 2]}}},
                               {"op": "temp_hp", "amount": {"var": "class_level.druid"}}]}),
        ("You stay in that form", "rule", {"id": "ends", "ends_on": ["wild_shape_used_again", C("incapacitated"),
                                                                      "death"],
                                           "leave_early": "bonus_action"}),
        ("***Number of Uses.***", "fx", {"op": "resource", "resource": "wild_shape", "name": "Wild Shape",
                                        "max": col(D, "Wild Shape"),
                                        "recovery": [{"on": SHORT, "amount": 1}, {"on": LONG, "amount": "all"}]}),
        ("***Known Forms.***", "rule", {"id": "known_forms", "start": 4, "max_cr": 0.25, "fly_speed": False,
                                       "recommended": ["dnd5e/creature/rat", "dnd5e/creature/riding-horse",
                                                       "dnd5e/creature/spider", "dnd5e/creature/wolf"],
                                       "replace_on_long_rest": 1}),
        ("When you reach certain Druid levels", "sys", ["/data/tables/0"]),
        ("When choosing known forms", "md", md(
            "other_sources", "May the player look in other sources for eligible Beasts?",
            "When choosing known forms, you may look in other sources for eligible Beasts if the Game Master permits "
            "you to do so.", pages=[42])),
        ("##### Beast Shapes", "table", {
            "id": "beast_shapes", "caption": "Beast Shapes",
            "columns": ["Druid Level", "Known Forms", "Max CR", "Fly Speed"], "rows": shapes}),
        ("***Rules While Shape-Shifted.***", "rule", {"id": "retain", "retains": ["personality", "memories",
                                                                                 "ability_to_speak"]}),
        ("**Temporary Hit Points.**", "sys", ["/effects/0/then/1"]),
        ("**Game Statistics.**", "sys", ["/effects/0/then/0"]),
        ("**Game Statistics.**", "rule", {"id": "game_statistics", "gains_form_proficiencies": True,
                                         "use_higher_of_skill_or_save_modifiers": True}),
        ("**No Spellcasting.**", "fx", {"op": "restrict", "restrictions": ["cast_spells"],
                                       "when": {"pred": "effect_active", "args": {"effect": "druid-wild-shape"}},
                                       "note": "Shape-shifting doesn't break Concentration or interfere with a spell already cast."}),
        ("**Objects.**", "rule", {"id": "objects", "handling_by_form_limbs": True,
                                 "equipment_choice": ["falls", "merges", "worn"], "merged_equipment_has_no_effect": True,
                                 "equipment_does_not_resize": True}),
        ("Worn equipment functions as normal, but the GM decides", "md", md(
            "wearable_equipment", "Is it practical for the new form to wear this piece of equipment?",
            "Worn equipment functions as normal, but the GM decides whether it’s practical for the new form to wear a "
            "piece of equipment based on the creature’s size and shape.", pages=[43])),
        ("Your equipment doesn’t change size", "sys", ["/data/rules/4"])]))
    E.append(CF(D, "Wild Companion", 2, [
        (None, "fx", {"op": "choice", "id": "wild_companion_cost", "choose": 1, "options": [
            {"id": "spell_slot", "label": "Expend a spell slot", "effects": [
                {"op": "activation", **MAGIC, "uses": {"resource": "spell_slot", "amount": 1},
                 "then": [{"op": "cast_spell", "spell": "dnd5e/spell/find-familiar", "components": ["V", "S"]}]}]},
            {"id": "wild_shape", "label": "Expend a use of Wild Shape", "effects": [
                {"op": "activation", **MAGIC, "uses": WILD,
                 "then": [{"op": "cast_spell", "spell": "dnd5e/spell/find-familiar", "slot": "none",
                           "components": ["V", "S"]}]}]}]}),
        ("When you cast the spell in this way", "rule", {"id": "fey_familiar", "creature_type": "fey",
                                                         "disappears_on": "long_rest_finished"})]))
    E.append(CF(D, "Druid Subclass", 3, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/subclass/circle-of-the-land"], "choose": 1,
        "note": "Gain each subclass feature of your Druid level or lower."})]))
    E.append(CF(D, "Ability Score Improvement", 4, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/feat/ability-score-improvement"],
        "note": "Or another feat you qualify for; again at Druid levels 8, 12 and 16."})]))
    E.append(CF(D, "Wild Resurgence", 5, [
        (None, "fx", {"op": "activation", "cost": "none", "requires": {"pred": "resource_empty", "args": {"resource": "wild_shape"}},
                      "uses": {"resource": "spell_slot", "amount": 1}, "frequency": {"count": 1, "per": "turn"},
                      "then": [{"op": "restore", "resource": "wild_shape", "amount": 1}]}),
        ("In addition, you can expend one use", "fx", {
            "op": "activation", "cost": "none", "uses": WILD, "frequency": {"count": 1, "per": "long_rest"},
            "then": [{"op": "restore", "resource": "spell_slot", "amount": 1, "level": 1}]})]))
    E.append(CF(D, "Elemental Fury", 7, [
        (None, "fx", {"op": "choice", "id": "elemental_fury", "choose": 1, "options": [
            {"id": "potent_spellcasting", "label": "Potent Spellcasting", "effects": [
                {"op": "modifier", "stat": "damage_roll", "mode": "add", "value": WIS,
                 "when": {"pred": "cantrip_of_class", "args": {"class": "druid"}}}]},
            {"id": "primal_strike", "label": "Primal Strike", "effects": [
                {"op": "trigger", "event": {"event": "hits_with_attack_roll"}, "optional": True,
                 "condition": {"all": [{"pred": "own_turn"}, {"any": [{"pred": "attack_uses_weapon"},
                                                                      {"pred": "wild_shape_form_attack"}]}]},
                 "frequency": {"count": 1, "per": "turn"},
                 "then": [{"op": "damage", "amount": "1d8", "target": {"kind": "inherit"},
                           "damage_type": {"choose_from": ["cold", "fire", "lightning", "thunder"]}}]}]}]}),
        ("***Potent Spellcasting.***", "sys", ["/effects/0/options/0"]),
        ("***Primal Strike.***", "sys", ["/effects/0/options/1"])]))
    E.append(CF(D, "Improved Elemental Fury", 15, [
        (None, "rule", {"id": "improves", "feature": "dnd5e/feature/druid-elemental-fury"}),
        ("***Potent Spellcasting.***", "rule", {"id": "potent_spellcasting", "druid_cantrip_min_range_feet": 10,
                                               "range_increase_feet": 300}),
        ("***Primal Strike.***", "rule", {"id": "primal_strike", "damage": "2d8"})]))
    E.append(CF(D, "Beast Spells", 18, [(None, "rule", {
        "id": "beast_spells", "can_cast_in_wild_shape": True, "overrides": "dnd5e/feature/druid-wild-shape",
        "except": ["material_component_with_cost", "consumed_material_component"]})]))
    E.append(CF(D, "Epic Boon", 19, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/feat/boon-of-dimensional-travel"],
        "note": "An Epic Boon feat or another feat you qualify for; Boon of Dimensional Travel is recommended."})]))
    E.append(CF(D, "Archdruid", 20, [
        (None, "desc", None),
        ("***Evergreen Wild Shape.***", "fx", {
            "op": "trigger", "event": {"event": "initiative_rolled"},
            "condition": {"pred": "resource_empty", "args": {"resource": "wild_shape"}},
            "then": [{"op": "restore", "resource": "wild_shape", "amount": 1}]}),
        ("***Nature Magician.***", "fx", {
            "op": "activation", "cost": "none", "frequency": {"count": 1, "per": "long_rest"},
            "uses": {"resource": "wild_shape", "amount": {"var": "chosen.wild_shape_uses"}},
            "then": [{"op": "restore", "resource": "spell_slot", "amount": 1,
                      "level": {"op": "mul", "args": [2, {"var": "chosen.wild_shape_uses"}]}}]}),
        ("***Longevity.***", "rule", {"id": "longevity", "aging_rate": 0.1})]))

    S = "Circle of the Land"
    land_rows = {land: spell_table(f"{land} Land") for land in LANDS}
    items = [(None, "fx", {"op": "choice", "id": "land_type", "choose": 1, "options": [
        {"id": land.lower(), "label": land, "effects": [
            {"op": "grant", "refs": r["spells"], "note": "Prepared.",
             "when": {"pred": "class_level_at_least", "args": {"class": "druid", "level": r["level"]}}}
            for r in land_rows[land]]} for land in LANDS]}),
             (None, "rule", {"id": "land_choice", "rechoose_on": "long_rest_finished"})]
    for k, land in enumerate(LANDS):
        items.append((f"##### {land} Land", "ref", [f"dnd5e/spell-list/circle-of-the-land-spells-{land.lower()}-land"]))
        items.append((f"##### {land} Land", "table", {
            "id": f"{land.lower()}_land", "caption": f"{land} Land", "columns": ["Druid Level", "Circle Spells"],
            "rows": [[r["level"], r["spells"]] for r in land_rows[land]]}))
    E.append(CF(D, "Circle of the Land Spells", 3, items, sub=S))
    E.append(CF(D, "Land’s Aid", 3, [
        (None, "fx", {"op": "activation", **MAGIC, "uses": WILD,
                      "then": [{"op": "save", "ability": "con", "dc": {"var": "spell_save_dc"}, "half_on_success": True,
                                "target": {"kind": "area", "range": {"kind": "distance", "feet": 60},
                                           "area": {"shape": "sphere", "size_feet": 10},
                                           "filter": {"predicate": {"pred": "chosen_by_source"}}},
                                "on_fail": [{"op": "damage", "damage_type": "necrotic",
                                             "amount": {"dice": {"count": "LANDS_AID", "faces": 6}}}]},
                               {"op": "heal", "amount": {"dice": {"count": "LANDS_AID", "faces": 6}},
                                "target": {"kind": "creature"}, "note": "One creature of your choice in the area."}]}),
        ("The damage and healing increase", "sys", ["/effects/0/then/0/on_fail/0/amount"])], sub=S))
    E.append(CF(D, "Natural Recovery", 6, [
        (None, "fx", {"op": "activation", "cost": "none", "frequency": {"count": 1, "per": "long_rest"},
                      "then": [{"op": "cast_spell", "spell": "dnd5e/feature/circle-of-the-land-circle-of-the-land-spells",
                                "slot": "none", "note": "One level 1+ spell prepared from Circle Spells; normal casting time."}]}),
        ("In addition, when you finish a Short Rest", "fx", {
            "op": "trigger", "event": SHORT, "optional": True, "frequency": {"count": 1, "per": "long_rest"},
            "then": [{"op": "restore", "resource": "spell_slot", "amount": {"op": "div", "round": "up", "args": [
                {"var": "class_level.druid"}, 2]}, "note": "Combined slot levels; none of level 6+."}]})], sub=S))
    ward = rows("Nature’s Ward")
    E.append(CF(D, "Nature’s Ward", 10, [
        (None, "fx", [{"op": "defense", "kind": "immunity", "conditions": [C("poisoned")]},
                      {"op": "defense", "kind": "resistance", "damage_types": [{"var": "chosen.land_type_damage"}]}]),
        ("##### Nature’s Ward", "table", {"id": "natures_ward", "caption": "Nature’s Ward",
                                          "columns": ["Land Type", "Resistance"], "rows": ward})], sub=S))
    E.append(CF(D, "Nature’s Sanctuary", 14, [
        (None, "fx", {"op": "activation", **MAGIC, "uses": WILD,
                      "then": [{"op": "defense", "kind": "resistance", "damage_types": [{"var": "chosen.land_type_damage"}],
                                "target": {"kind": "area", "range": {"kind": "distance", "feet": 120},
                                           "area": {"shape": "cube", "size_feet": 15},
                                           "filter": {"allies_only": True}},
                                "duration": {"kind": "minutes", "amount": 1}},
                               {"op": "reference", "rule": "dnd5e/rule/cover",
                                "note": "You and your allies have Half Cover while in the area."}]}),
        ("They last there", "rule", {"id": "duration", "minutes": 1, "ends_early": [C("incapacitated"), "death"]}),
        ("As a Bonus Action, you can move the Cube", "fx", {
            "op": "activation", "cost": "bonus_action", "requires": {"pred": "effect_active",
                                                                    "args": {"effect": "circle-of-the-land-natures-sanctuary"}},
            "then": [{"op": "move", "mode": "move", "distance_feet": 60,
                      "note": "The Cube, to ground within 120 feet of you."}]})], sub=S))
    return E


def fix_counts(E):
    """Land's Aid dice: 2d6, 3d6 at Druid level 10, 4d6 at 14."""
    scale = {"scale": {"by": "class_level.druid", "steps": [{"from": 3, "value": 2}, {"from": 10, "value": 3},
                                                            {"from": 14, "value": 4}]}}

    def walk(n):
        if isinstance(n, dict):
            for k, v in n.items():
                if v == "LANDS_AID":
                    n[k] = scale
                else:
                    walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)
    for e in E:
        walk(e.get("effects", []))
    return E


REGISTRY = {
    "stats": [
        {"id": "creature_type", "description": "The creature's type.", "pages": [43]},
        {"id": "hit_point_dice", "description": "The creature's Hit Point Dice.", "pages": [43]},
        {"id": "class_features", "description": "The creature's class features.", "pages": [43]},
        {"id": "languages", "description": "The languages the creature knows.", "pages": [43]},
        {"id": "feats", "description": "The creature's feats.", "pages": [43]},
        {"id": "skill_proficiencies", "description": "The creature's skill proficiencies.", "pages": [43]},
        {"id": "saving_throw_proficiencies", "description": "The creature's saving throw proficiencies.", "pages": [43]},
        {"id": "proficiency_bonus", "description": "The creature's Proficiency Bonus.", "pages": [43]}],
    "predicates": [
        {"id": "known_wild_shape_form", "description": "The Beast form is one the Druid has learned for Wild Shape.", "type": "predicate", "pages": [42]},
        {"id": "resource_empty", "description": "The creature has no uses of this resource left (param).", "params": ["resource"], "type": "predicate", "pages": [43]},
        {"id": "wild_shape_form_attack", "description": "The attack is a Beast form's attack made in Wild Shape.", "type": "predicate", "pages": [43]}],
}

if __name__ == "__main__":
    extend_registries(REGISTRY, LOT)
    out = fix_counts(entries())
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
