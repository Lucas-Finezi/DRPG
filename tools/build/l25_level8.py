#!/usr/bin/env python3
"""L25 — Level 8 spells (17).

Usage: python3 -I tools/build/l25_level8.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spelllib import (C, DC, EACH_END, INHERIT, MAGIC, MOD, SELF, SLOT, SP, STUDY, S_for, active,  # noqa: E402
                      all_but, area, attack, cond, creatures, dmg, extra_targets, heal, light, md, ref, save, tab, touch,
                      until_turn, up, updice, write_all)

LOT = "L25"
S = S_for(LOT)
HL = "***Using a Higher-Level Spell Slot.***"


def entries():
    E = []
    E.append(S("Animal Shapes", [
        ("^", "fx", {"op": "transform", "into": {"creature_types": ["beast"], "sizes": ["tiny", "small", "medium", "large"],
                                                 "predicate": {"pred": "cr_at_most", "args": {"cr": 4}}},
                     "target": creatures(must_see=True, willing=True),
                     "keeps": ["creature_type", "hp", "hit_point_dice", "alignment", "languages", "ability_score.int",
                               "ability_score.wis", "ability_score.cha"], "duration": "@duration",
                     "note": "Any number of willing creatures; a different form for each."}),
        ("^", "fx", {"op": "activation", **MAGIC, "then": [ref(SP("animal-shapes"), note="Transform the targets again.")]}),
        ("A target’s game statistics are replaced", "fx", {"op": "restrict", "restrictions": ["cast_spells"], "duration": "@duration",
                                                           "note": "Actions limited by the form's anatomy; equipment melds and can't be used."}),
        ("A target’s game statistics are replaced", "ref", ["dnd5e/rule/shape-shifting"]),
        ("The target gains a number of Temporary Hit Points", "fx", [
            {"op": "temp_hp", "amount": {"var": "form_hp"}, "note": "From the first form; they vanish when the spell ends."},
            {"op": "activation", "cost": "bonus_action", "then": [{"op": "end_effect", "scope": "this_entry_on_target"}],
             "note": "The target ends its transformation."}])]))
    E.append(S("Antimagic Field", [
        ("^", "fx", {"op": "restrict", "restrictions": ["cast_spells", "take_magic_action", "create_magical_effects"],
                     "target": area("emanation", 10, "self"), "duration": "@duration"}),
        ("^", "rule", {"id": "aura", "magic_cannot_affect_inside": True, "magic_items_inert_inside": True}),
        ("Areas of effect created by spells", "rule", {"id": "barriers", "areas_cannot_extend_in": True, "teleport_or_planar_travel": False,
                                                       "portals_close": True}),
        ("Ongoing spells, except those cast", "rule", {"id": "suppression", "suppressed": True, "except": ["artifact", "deity"],
                                                       "time_counts": True}),
        ("*Dispel Magic* has no effect", "rule", {"id": "dispel", "dispel_magic": False, "fields_dont_nullify": True})]))
    E.append(S("Antipathy/Sympathy", [
        ("^", "rule", {"id": "target", "creature_or_object_max": "huge", "kind_of_creature": "specified", "range_feet": 120}),
        ("^", "fx", {"op": "trigger", "event": {"event": "comes_within_feet_of_target.120"}, "duration": "@duration",
                     "condition": {"pred": "creature_kind_specified"},
                     "then": [save("wis", {"op": "choice", "id": "mode", "choose": 1, "options": [
                         {"id": "antipathy", "label": "Antipathy", "effects": [cond("frightened", note="Moves as far as possible from the target by the safest route.")]},
                         {"id": "sympathy", "label": "Sympathy", "effects": [cond("charmed", note="Moves as close as possible; can't willingly move away within 5 feet.")]}]},
                                   target=INHERIT)]}),
        ("**Antipathy.**", "sys", ["/effects/0/then/0/on_fail/0/options/0"]),
        ("**Sympathy.**", "sys", ["/effects/0/then/0/on_fail/0/options/1"]),
        ("**Sympathy.**", "fx", {"op": "trigger", "event": {"event": "damaged_by_target"},
                                "then": [save("wis", {"op": "end_effect", "scope": "this_entry_on_target"}, target=INHERIT)]}),
        ("***Ending the Effect.***", "fx", {"op": "trigger", "event": {"event": "turn_end", "whose": "any"},
                                           "condition": {"pred": "farther_than_feet_from_target", "args": {"feet": 120}},
                                           "then": [save("wis", None, target=INHERIT,
                                                         on_success={"op": "end_effect", "scope": "this_entry_on_target"},
                                                         note="A creature that succeeds is immune for 1 minute.")]})]))
    E.append(S("Befuddlement", [
        ("^", "fx", save("int", [dmg("10d12", "psychic"),
                                 {"op": "restrict", "restrictions": ["cast_spells", "take_magic_action"], "duration": {"kind": "until_dispelled"}}],
                         half=True, target=creatures(must_see=True),
                         on_success=dmg({"op": "div", "args": ["10d12", 2]}, "psychic", note="Half damage only."))),
        ("On a failed save", "rule", {"id": "recovery", "repeat_save_every_days": 30,
                                      "ended_by": [SP("greater-restoration"), SP("heal"), SP("wish")]})]))
    E.append(S("Clone", [
        ("^", "rule", {"id": "clone", "touch_creature_or_flesh_cubic_inches": 1, "growth_days": 120, "age_choice": True,
                       "inert_while_vessel_undisturbed": True}),
        ("If the original creature dies", "rule", {"id": "transfer", "soul_must_be_free_and_willing": True,
                                                   "same_personality_memories_abilities": True, "equipment": False,
                                                   "original_remains_unrevivable": True})]))
    E.append(S("Control Weather", [
        ("^", "rule", {"id": "control", "radius_miles": 5, "outdoors_only": True}),
        ("When you cast the spell, you change", "md", md("current_weather", "What are the current weather conditions?",
                                                         "When you cast the spell, you change the current weather conditions, which are determined by the GM.")),
        ("When you cast the spell, you change", "rule", {"id": "change", "dimensions": ["precipitation", "temperature", "wind"],
                                                         "delay_minutes": "1d4 x 10", "returns_to_normal_on_end": True}),
        ("When you change the weather conditions", "rule", {"id": "stages", "step": 1, "wind_direction_change": True}),
        ("##### Precipitation", "table", tab("Precipitation", ["Stage", "Condition"])),
        ("##### Temperature", "table", tab("Temperature", ["Stage", "Condition"])),
        ("##### Wind", "table", tab("Wind", ["Stage", "Condition"], page=None))]))
    E.append(S("Demiplane", [
        ("^", "rule", {"id": "door", "size": "medium", "room_feet": 30, "material": ["wood", "stone"]}),
        ("When the spell ends, the door vanishes", "rule", {"id": "end", "objects_remain": True, "creatures_may_be_shunted_prone": True}),
        ("Each time you cast this spell", "rule", {"id": "connect", "own_previous_demiplane": True, "known_other_demiplane": True})]))
    E.append(S("Dominate Monster", [
        ("^", "fx", [save("wis", cond("charmed"), target=creatures(must_see=True), note="Advantage if you or your allies are fighting it."),
                     {"op": "trigger", "event": {"event": "damage_taken", "whose": "target"}, "duration": "@duration",
                      "then": [save("wis", None, target=INHERIT, on_success={"op": "end_effect", "scope": "this_entry"})]}]),
        ("You have a telepathic link", "rule", {"id": "commands", "telepathic_link": "same_plane", "command_cost": "none",
                                                "obeys_on_its_turn": True, "idle": "protects_itself"}),
        ("You can command the target to take a Reaction", "rule", {"id": "reaction", "costs_your_reaction": True}),
        (HL, "rule", {"id": "longer_concentration", "slot_9_max_hours": 8})]))
    E.append(S("Earthquake", [
        ("^", "rule", {"id": "tremor", "radius_feet": 100, "difficult_terrain": True}),
        ("When you cast this spell and at the end", "fx", {"op": "trigger", "event": {"event": "turn_end", "whose": "self", "which": "each"},
                                                           "duration": "@duration", "note": "Also when you cast it.",
                                                           "then": [save("dex", [cond("prone", None), {"op": "end_effect", "scope": "concentration"}],
                                                                         target=area("cylinder", 100))]}),
        ("You can also cause the effects below", "desc", None),
        ("***Fissures.***", "rule", {"id": "fissures", "count": "1d6", "depth_feet": "1d10 x 10", "width_feet": 10, "not_under_structures": True}),
        ("***Fissures.***", "fx", save("dex", {"op": "move", "mode": "fall", "note": "Falls into the fissure."}, target={"kind": "creature"},
                                      note="A creature in a fissure's space; on a success it moves with the edge.")),
        ("***Structures.***", "rule", {"id": "structures", "damage": 50, "damage_type": "bludgeoning", "when": ["cast", "end_of_each_of_your_turns"],
                                      "collapse_at_0_hp": True}),
        ("A creature within a distance from a collapsing", "fx", save("dex", [dmg("12d6", "bludgeoning"), cond("prone", None)], half=True,
                                                                       target={"kind": "creature"},
                                                                       note="Within half the structure's height; buried: DC 20 Strength (Athletics) check as an action to escape."))]))
    E.append(S("Glibness", [("^", "fx", [
        {"op": "modifier", "stat": "d20_roll", "mode": "set", "value": 15, "duration": "@duration",
         "when": {"pred": "roll_uses_ability", "args": {"ability": "cha"}}, "note": "Optional, on Charisma checks."},
        {"op": "modifier", "stat": "truth_detection_result", "mode": "set", "value": 1, "duration": "@duration",
         "note": "Magic that determines truthfulness indicates you are truthful."}])]))
    E.append(S("Holy Aura", [("^", "fx", [
        {"op": "roll_mode", "mode": "advantage", "rolls": ["saving_throw"], "target": area("emanation", 30, "self"), "duration": "@duration",
         "note": "Creatures of your choice in the aura."},
        {"op": "roll_mode", "mode": "disadvantage", "rolls": ["attack_roll"], "direction": "against", "duration": "@duration"},
        {"op": "trigger", "event": {"event": "hit_by_attack_roll"}, "duration": "@duration",
         "condition": {"all": [{"pred": "attack_is_melee"}, {"pred": "attacker_creature_type_in", "args": {"types": ["fiend", "undead"]}}]},
         "then": [save("con", cond("blinded", until_turn("turn_end", "target")), target={"kind": "creature"},
                       note="The attacker.")]}])]))
    E.append(S("Incendiary Cloud", [
        ("^", "rule", {"id": "cloud", "area": {"shape": "sphere", "radius_feet": 20}, "heavily_obscured": True,
                       "dispersed_by_strong_wind": True, "example": SP("gust-of-wind")}),
        ("When the cloud appears", "fx", [
            save("dex", dmg("10d8", "fire"), half=True, target=area("sphere", 20)),
            {"op": "trigger", "event": {"event": "enters_or_ends_turn_in_area"}, "frequency": {"count": 1, "per": "turn"},
             "duration": "@duration", "then": [save("dex", dmg("10d8", "fire"), half=True, target=INHERIT)]}]),
        ("The cloud moves 10 feet", "fx", {"op": "trigger", "event": {"event": "turn_start", "whose": "self", "which": "each"},
                                           "duration": "@duration",
                                           "then": [{"op": "move", "mode": "move", "distance_feet": 10, "note": "The cloud, away from you."}]})]))
    E.append(S("Maze", [
        ("^", "fx", ref(SP("maze"), target=creatures(must_see=True), note="Banished into a labyrinthine demiplane.")),
        ("The target can take a Study action", "fx", {"op": "activation", "cost": "action", "action": "dnd5e/action/study",
                                                      "then": [{"op": "check", "ability": "int", "skill": "investigation", "dc": 20,
                                                                "on_success": [{"op": "end_effect", "scope": "this_entry"}]}]}),
        ("When the spell ends", "rule", {"id": "return", "to_space_left_or_nearest": True})]))
    E.append(S("Mind Blank", [("^", "fx", [
        {"op": "defense", "kind": "immunity", "damage_types": ["psychic"], "conditions": [C("charmed")], "target": touch(willing=True),
         "duration": "@duration"},
        {"op": "restrict", "restrictions": ["sensed_read_or_located_by_magic"], "duration": "@duration",
         "note": "No spell, not even Wish, can gather information about it, observe it remotely or control its mind."}])]))
    E.append(S("Power Word Stun", [
        ("^", "fx", {"op": "choice", "id": "by_hp", "choose": 1, "chooser": "gm", "target": creatures(must_see=True), "options": [
            {"id": "stunned", "label": "150 Hit Points or fewer", "effects": [cond("stunned", {"kind": "until_dispelled"})]},
            {"id": "slowed", "label": "More than 150 Hit Points", "effects": [
                {"op": "speed", "movement": "walk", "mode": "set", "value": 0, "duration": until_turn("turn_start", "source")}]}]}),
        ("The Stunned target makes", "fx", save("con", None, target=INHERIT, repeat=EACH_END,
                                                on_success={"op": "remove_condition", "conditions": [C("stunned")]}))]))
    E.append(S("Sunburst", [
        ("^", "fx", save("con", [dmg("12d6", "radiant"), cond("blinded", {"kind": "minutes", "amount": 1})], target=area("sphere", 60),
                         on_success=dmg({"op": "div", "args": ["12d6", 2]}, "radiant", note="Half damage only."))),
        ("A creature Blinded by this spell", "fx", save("con", None, target=INHERIT, repeat=EACH_END,
                                                        on_success={"op": "remove_condition", "conditions": [C("blinded")]})),
        ("This spell dispels Darkness", "rule", {"id": "dispel_darkness", "dispels_spell_darkness_in_area": True})]))
    E.append(S("Tsunami", [
        ("^", "rule", {"id": "wall", "length_feet": 300, "height_feet": 300, "thickness_feet": 50}),
        ("When the wall appears", "fx", save("str", dmg("6d10", "bludgeoning"), half=True,
                                             target={"kind": "area", "area": {"shape": "line", "size_feet": 300, "origin": "point"}, "range": "@range"})),
        ("At the start of each of your turns", "fx", {"op": "trigger", "event": {"event": "turn_start", "whose": "self", "which": "each"},
                                                      "duration": "@duration",
                                                      "then": [{"op": "move", "mode": "move", "distance_feet": 50, "note": "The wall and creatures in it, away from you."},
                                                               save("str", dmg({"dice": {"count": {"op": "max", "args": [0, {"op": "sub", "args": [5, {"var": "rounds_elapsed"}]}]}, "faces": 10}}, "bludgeoning"),
                                                                    target={"kind": "creature", "filter": {"sizes": ["tiny", "small", "medium", "large", "huge"]}},
                                                                    note="Once per round; 5d10, reduced by 1d10 on later rounds.")]}),
        ("At the start of each of your turns", "rule", {"id": "shrink", "height_reduction_feet_per_turn": 50, "ends_at_height": 0}),
        ("A creature caught in the wall", "rule", {"id": "swimming", "check": {"ability": "str", "skill": "athletics", "dc": "spell_save_dc"},
                                                   "fail": "cannot_move", "leaving_wall": "falls"})]))
    return E


REGISTRY = {
    "stats": [{"id": "truth_detection_result", "description": "Magic that determines truthfulness reports the creature as truthful (1).", "pages": [137]}],
    "restrictions": [
        {"id": "take_magic_action", "description": "The creature can't take the Magic action.", "pages": [113]},
        {"id": "create_magical_effects", "description": "The creature can't create magical effects.", "pages": [109]},
        {"id": "sensed_read_or_located_by_magic", "description": "Magic can't sense the creature's emotions or alignment, read its thoughts or locate it.", "pages": [149]}],
    "events": [
        {"id": "comes_within_feet_of_target", "description": "A creature comes within N feet (param) of the target.", "params": ["feet"], "pages": [110]},
        {"id": "damaged_by_target", "description": "The creature is damaged by the spell's target.", "pages": [110]}],
    "predicates": [
        {"id": "cr_at_most", "description": "The form's Challenge Rating is at most N (param).", "params": ["cr"], "type": "predicate", "pages": [108]},
        {"id": "creature_kind_specified", "description": "The creature is of the kind specified when the spell was cast.", "type": "predicate", "pages": [110]},
        {"id": "farther_than_feet_from_target", "description": "The creature is more than N feet (param) from the target.", "params": ["feet"], "type": "predicate", "pages": [110]},
        {"id": "attack_is_melee", "description": "The attack is a melee attack roll.", "type": "predicate", "pages": [141]}],
}

if __name__ == "__main__":
    write_all(entries(), REGISTRY, LOT)
