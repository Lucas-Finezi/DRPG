#!/usr/bin/env python3
"""L09 — Spellcasting rules: gaining and preparing spells, spell level and slots, casting
without slots, schools, class spell lists, casting time, range, components, duration,
effects and targets, Concentration, rituals, areas of effect.

Usage: python3 -I tools/build/l09_spell_rules.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import build, extend_registries, glossary, md, ref_of, section, sidebar, write_entry  # noqa: E402

LOT = "L09"
SYS = "dnd5e/system/dnd5e"
C = lambda slug: f"dnd5e/condition/{slug}"  # noqa: E731
SCHOOLS = [("abjuration", "Prevents or reverses harmful effects"), ("conjuration", "Transports creatures or objects"),
           ("divination", "Reveals information"), ("enchantment", "Influences minds"),
           ("evocation", "Channels energy to create effects that are often destructive"),
           ("illusion", "Deceives the mind or senses"), ("necromancy", "Manipulates life and death"),
           ("transmutation", "Transforms creatures or objects")]

REGISTRY = {
    "schools": [{"id": s, "name": s.title(), "description": d, "pages": [105]} for s, d in SCHOOLS],
    "pools": [
        {"id": "spell_slot", "name": "Spell Slots", "description": "Spell slots by level (param: level).", "pages": [104]},
    ],
    "variables": [
        {"id": "damage_amount", "description": "Amount of damage just taken.", "type": "number", "pages": [179]},
        {"id": "spell_level", "description": "Level of the spell as cast (the slot level when cast with a higher slot).", "type": "number", "pages": [104]},
    ],
    "events": [
        {"id": "concentration_effect_started", "description": "The creature starts casting a Concentration spell or activates another Concentration effect.", "type": "event", "pages": [179]},
        {"id": "dies", "description": "The creature dies.", "type": "event", "pages": [179]},
    ],
    "predicates": [
        {"id": "concentrating", "description": "The creature is concentrating on an effect.", "type": "predicate", "pages": [179]},
        {"id": "has_hand_free", "description": "The creature has a hand free.", "type": "predicate", "pages": [105]},
        {"id": "can_speak_normally", "description": "The creature can utter words in a normal speaking voice (not gagged or in magical silence).", "type": "predicate", "pages": [105]},
    ],
}


def g(name, items, kind="rule", **kw):
    return glossary(name, kind, LOT, items, **kw)


def area(name, items):
    return g(name, items, kind="area")


def glossary_entries():
    E = []
    E.append(g("Area of Effect", [
        (None, "sys", [f"{SYS}#/registries/area_shapes"]),
        ("An area of effect has a point of origin", "rule", {"id": "point_of_origin", "line_blocked_by": "total_cover",
                                                             "blocked_locations_excluded": True}),
        ("*See also*", "ref", [ref_of("Cover")]),
        ("If the creator of an area of effect places it at an unseen point", "rule", {
            "id": "unseen_point", "origin_on_near_side_of_obstruction": True})]))
    E.append(area("Cone", [
        (None, "rule", {"id": "cone", "width_at_distance": "equals_distance", "length_from": "effect"}),
        ("A Cone’s point of origin isn’t included", "rule", {"id": "origin_included", "default": False,
                                                            "creator_may_include": True})]))
    E.append(area("Cube", [
        (None, "rule", {"id": "cube", "origin": "anywhere_on_a_face", "size": "side_length"}),
        ("A Cube’s point of origin isn’t included", "rule", {"id": "origin_included", "default": False,
                                                            "creator_may_include": True})]))
    E.append(area("Cylinder", [
        (None, "rule", {"id": "cylinder", "origin": "center_of_top_or_bottom", "size": ["radius", "height"]}),
        ("A Cylinder’s point of origin is included", "rule", {"id": "origin_included", "default": True})]))
    E.append(area("Emanation", [
        (None, "rule", {"id": "emanation", "origin": "creature_or_object", "size": "distance"}),
        ("An Emanation moves with the creature", "rule", {"id": "moves_with_origin", "unless": ["instantaneous",
                                                                                               "stationary"]}),
        ("An Emanation’s origin (creature or object) isn’t included", "rule", {"id": "origin_included",
                                                                               "default": False,
                                                                               "creator_may_include": True})]))
    E.append(area("Line", [
        (None, "rule", {"id": "line", "size": ["length", "width"]}),
        ("A Line’s point of origin isn’t included", "rule", {"id": "origin_included", "default": False,
                                                            "creator_may_include": True})]))
    E.append(area("Sphere", [
        (None, "rule", {"id": "sphere", "size": "radius"}),
        ("A Sphere’s point of origin is included", "rule", {"id": "origin_included", "default": True})]))
    E.append(g("Cantrip", [(None, "rule", {"id": "cantrip", "level": 0, "spell_slot": False}),
                           ("*See also*", "ref", ["dnd5e/rule/spells"])]))
    conc_dc = {"op": "min", "args": [30, {"op": "max", "args": [10, {"op": "div", "args": [{"var": "damage_amount"}, 2]}]}]}
    E.append(g("Concentration", [
        (None, "rule", {"id": "concentration", "effect_ends_when_lost": True, "max_duration_from_effect": True}),
        ("The creator can end Concentration at any time", "rule", {"id": "end_at_will", "cost": "none"}),
        ("***Another Concentration Effect.***", "fx", {"op": "trigger", "event": {"event": "concentration_effect_started"},
                                                      "then": [{"op": "end_effect", "scope": "concentration"}]}),
        ("***Damage.***", "fx", {"op": "trigger", "event": {"event": "damage_taken"},
                                 "condition": {"pred": "concentrating"},
                                 "then": [{"op": "save", "ability": "con", "dc": conc_dc,
                                           "on_fail": [{"op": "end_effect", "scope": "concentration"}]}]}),
        ("***Incapacitated or Dead.***", "fx", [
            {"op": "trigger", "event": {"event": "dies"}, "then": [{"op": "end_effect", "scope": "concentration"}]},
            {"op": "restrict", "restrictions": ["maintain_concentration"],
             "when": {"pred": "has_condition", "args": {"condition": "incapacitated"}}}])]))
    E.append(g("Ritual", [
        (None, "rule", {"id": "ritual", "requires_prepared": True, "requires_tag": "ritual",
                        "extra_casting_minutes": 10, "spell_slot": False, "higher_level": False}),
        ("*See also*", "ref", ["dnd5e/rule/spells"])]))
    E.append(g("Spell", [(None, "ref", ["dnd5e/rule/spells"])]))
    E.append(g("Spell Attack", [(None, "rule", {"id": "spell_attack", "bonus": {"var": "spell_attack_bonus"}}),
                                ("*See also*", "ref", ["dnd5e/rule/casting-spells"])]))
    E.append(g("Spellcasting Focus", [
        (None, "rule", {"id": "focus", "replaces_material_components_if": ["not_consumed", "no_cost_specified"],
                        "requires": "feature_allowing_focus"}),
        ("*See also*", "ref", ["dnd5e/rule/casting-spells"])]))
    return E


def sections():
    E = []
    side = lambda title, slug, items: build("rule", slug, title, sidebar(title), LOT, "Spells", items,  # noqa: E731
                                            facets={"sidebar": True})
    E.append(side("Casting in Armor", "sidebar-casting-in-armor", [
        (None, "fx", {"op": "restrict", "restrictions": ["cast_spells"], "when": {"pred": "wearing_untrained_armor"}})]))
    E.append(side("Identifying an Ongoing Spell", "sidebar-identifying-an-ongoing-spell", [
        (None, "fx", {"op": "activation", "name": "Identify an ongoing spell", "cost": "action",
                      "then": [{"op": "check", "ability": "int", "skill": "arcana", "dc": 15}],
                      "note": "Study action; the spell must be non-instantaneous with an ongoing duration and "
                              "observable effects."})]))

    sec = lambda slug, title, level, path, items, **kw: build("rule", slug, title, section(title, level, **kw), LOT,  # noqa: E731
                                                              path, items)
    E.append(build("rule", "spells", "Spells", section("Spells", 1, include_heading=True, stop_titles=("Gaining Spells",)),
                   LOT, "Spells", [(None, "desc", None)],
                   data={"sections": ["dnd5e/rule/gaining-spells", "dnd5e/rule/casting-spells"]}))
    E.append(sec("gaining-spells", "Gaining Spells", 2, "Spells/Gaining Spells", [
        (None, "rule", {"id": "access", "requires": ["prepared", "magic_item_access"]}),
        ("Your features specify which spells", "ref", [e for e in ("dnd5e/class/bard", "dnd5e/class/cleric",
                                                                   "dnd5e/class/druid", "dnd5e/class/paladin",
                                                                   "dnd5e/class/ranger", "dnd5e/class/sorcerer",
                                                                   "dnd5e/class/warlock", "dnd5e/class/wizard")]),
        ("### Preparing Spells", "table", {"id": "spell_preparation_by_class", "caption": "Spell Preparation by Class",
                                           "columns": ["Class", "Change When You …", "Number of Spells"], "rows": [
                                               ["Bard", "Gain a level", "One"], ["Cleric", "Finish a Long Rest", "Any"],
                                               ["Druid", "Finish a Long Rest", "Any"], ["Paladin", "Finish a Long Rest", "One"],
                                               ["Ranger", "Finish a Long Rest", "One"], ["Sorcerer", "Gain a level", "One"],
                                               ["Warlock", "Gain a level", "One"], ["Wizard", "Finish a Long Rest", "Any"]]}),
        ("Most spellcasting monsters don’t change", "md", md("monster_spells", "Alter this monster's prepared spells?",
                                                             "Most spellcasting monsters don’t change their lists of "
                                                             "prepared spells, but the GM is free to alter them.",
                                                             when="on_gain", pages=[104])),
        ("### Always-Prepared Spells", "rule", {"id": "always_prepared", "counts_against_prepared_limit": False})]))
    E.append(sec("casting-spells", "Casting Spells", 2, "Spells/Casting Spells", [(None, "desc", None)],
                 stop_titles=("Spell Level",)))
    E.append(sec("spell-level", "Spell Level", 3, "Spells/Casting Spells/Spell Level", [
        (None, "rule", {"id": "levels", "min": 0, "max": 9, "cantrip_level": 0}),
        ("#### Spell Slots", "rule", {"id": "slots", "level_1_plus_requires_slot": True, "pool": "spell_slot"}),
        ("When you cast a spell, you expend a slot", "rule", {"id": "slot_level", "slot_level_at_least_spell_level": True}),
        ("Finishing a Long Rest restores any expended spell slots.", "fx", {
            "op": "trigger", "event": {"event": "long_rest_finished"},
            "then": [{"op": "restore", "resource": "spell_slot", "amount": "all"}]}),
        ("#### Casting without Slots", "rule", {"id": "without_slots", "ways": ["cantrip", "ritual",
                                                                               "special_ability", "magic_item"]}),
        ("**Rituals**.", "ref", [ref_of("Ritual")]),
        ("**Special Abilities.**", "rule", {"id": "special_abilities", "limited_by": "their_description"}),
        ("**Magic Items.**", "ref", ["dnd5e/magic-item/spell-scroll"]),
        ("#### Using a Higher-Level Spell Slot", "rule", {"id": "upcast", "spell_level_becomes": "slot_level",
                                                          "variable": "spell_slot_level"})]))
    E.append(sec("school-of-magic", "School of Magic", 3, "Spells/Casting Spells/School of Magic", [
        (None, "sys", [f"{SYS}#/registries/schools"])]))
    E.append(sec("class-spell-lists", "Class Spell Lists", 3, "Spells/Casting Spells/Class Spell Lists", [
        (None, "rule", {"id": "class_in_header", "class_access_from": "description_header_parentheses",
                        "decision": "D-001"}),
        ("Some features add a spell to a character’s spell list", "rule", {"id": "features_add_spells",
                                                                           "allowed": True})]))
    E.append(sec("casting-time", "Casting Time", 3, "Spells/Casting Spells/Casting Time", [
        (None, "rule", {"id": "casting_times", "values": ["magic_action", "bonus_action", "reaction",
                                                          "one_minute_or_more"]}),
        ("#### One Spell with a Spell Slot per Turn", "rule", {"id": "one_slot_per_turn", "max_slots_per_turn": 1}),
        ("#### Reaction and Bonus Action Triggers", "rule", {"id": "triggers", "defined_in": "casting_time_entry"}),
        ("#### Longer Casting Times", "rule", {"id": "long_casting", "magic_action_each_turn": True,
                                               "concentration_required": True,
                                               "on_concentration_broken": {"spell_fails": True, "slot_expended": False,
                                                                           "restart": True}})]))
    E.append(sec("spell-range", "Range", 3, "Spells/Casting Spells/Range", [
        (None, "rule", {"id": "range", "forms": ["distance", "touch", "self"]}),
        ("If a spell has movable effects", "rule", {"id": "movable_effects", "restricted_by_range": False})],
        page=105))
    E.append(sec("spell-components", "Components", 3, "Spells/Casting Spells/Components", [
        (None, "rule", {"id": "components", "kinds": ["verbal", "somatic", "material"],
                        "missing_component": "cannot_cast"}),
        ("#### Verbal (V)", "rule", {"id": "verbal", "requires": {"pred": "can_speak_normally"}}),
        ("#### Somatic (S)", "rule", {"id": "somatic", "requires": {"pred": "has_hand_free"}}),
        ("#### Material (M)", "rule", {"id": "material", "consumed_only_if_stated": True,
                                       "hand_free_required": True, "may_be_somatic_hand": True}),
        ("If a spell doesn’t consume its materials", "rule", {
            "id": "substitutes", "if": ["not_consumed", "no_cost"],
            "component_pouch": {"hand_free": True}, "spellcasting_focus": {"requires_feature": True, "held": True}}),
        ("If a spell doesn’t consume its materials", "ref", ["dnd5e/gear/component-pouch", ref_of("Spellcasting Focus")])],
        page=105))
    E.append(sec("spell-duration", "Duration", 3, "Spells/Casting Spells/Duration", [
        (None, "desc", None),
        ("**Concentration.**", "ref", [ref_of("Concentration")]),
        ("**Instantaneous.**", "rule", {"id": "instantaneous", "persists": False}),
        ("**Time Span.**", "rule", {"id": "time_span", "dismiss_cost": "none",
                                    "dismiss_requires": {"not": {"pred": "has_condition",
                                                                 "args": {"condition": "incapacitated"}}}})],
        page=106))
    E.append(sec("spell-effects", "Effects", 3, "Spells/Casting Spells/Effects", [
        (None, "md", md("beyond_spell_effects", "Rule on outcomes beyond what the spell's description states.",
                        "Those details present exactly what the spell does, which ignores mundane physical laws; any "
                        "outcomes beyond those effects are under the GM’s purview.", pages=[106])),
        ("#### Targets", "desc", None),
        ("***A Clear Path to the Target.***", "rule", {"id": "clear_path", "blocked_by": "total_cover"}),
        ("***Targeting Yourself.***", "rule", {"id": "target_self", "allowed_if_creature_of_choice": True,
                                               "unless": ["must_be_hostile", "must_be_other_creature"]}),
        ("***Areas of Effect.***", "ref", [ref_of("Area of Effect")]),
        ("***Awareness of Being Targeted.***", "rule", {"id": "awareness", "aware_only_if_perceptible": True}),
        ("***Invalid Targets.***", "rule", {"id": "invalid_target", "no_effect": True, "slot_still_expended": True,
                                            "appears_to_succeed_save_if_save_negates": True}),
        ("#### Saving Throws", "sys", [f"{SYS}#/levels/rules/9"]),
        ("#### Attack Rolls", "sys", [f"{SYS}#/levels/rules/10"]),
        ("#### Combining Spell Effects", "rule", {"id": "combining", "different_spells": "add",
                                                  "same_spell": "most_potent_applies",
                                                  "equal_potency": "most_recent"})], page=106))
    return E


if __name__ == "__main__":
    extend_registries(REGISTRY, LOT)
    out = glossary_entries() + sections()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
