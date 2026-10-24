#!/usr/bin/env python3
"""L04 — Combat rules: actions, the order of combat, movement, attacks, cover, reach,
opportunity attacks, mounted and underwater combat, and their glossary terms.

Usage: python3 -I tools/build/l04_combat.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import (build, extend_registries, glossary, md, ref_of, section, sidebar,  # noqa: E402
                      write_entry)

LOT = "L04"
SYS = "dnd5e/system/dnd5e"
C = lambda slug: f"dnd5e/condition/{slug}"  # noqa: E731
A = lambda slug: f"dnd5e/action/{slug}"  # noqa: E731

REGISTRY = {
    "stats": [
        {"id": "movement", "description": "Movement (feet) available to the creature this turn.", "pages": [180]},
        {"id": "provokes_opportunity_attacks", "description": "Whether the creature's movement provokes Opportunity Attacks (1 or 0).", "pages": [181]},
        {"id": "reach", "description": "Reach in feet (default 5).", "pages": [186]},
        {"id": "hp", "description": "Current Hit Points.", "pages": [16]},
    ],
    "variables": [
        {"id": "target_ability_score", "description": "An ability score of the target of the current effect.", "params": ["ability"], "type": "number", "pages": [184]},
        {"id": "check_total", "description": "Total of the ability check just made.", "type": "number", "pages": [183]},
        {"id": "height", "description": "The creature's height in feet.", "type": "number", "pages": [183]},
        {"id": "jump_height", "description": "Height in feet of the current High Jump.", "type": "number", "pages": [183]},
        {"id": "escape_dc", "description": "Escape DC of the grapple affecting the creature.", "type": "number", "pages": [182]},
    ],
    "predicates": [
        {"id": "heavily_obscured", "description": "The creature is in a Heavily Obscured area.", "type": "predicate", "pages": [183]},
        {"id": "behind_cover", "description": "The creature is behind cover of a degree ('half', 'three_quarters', 'total') or better.", "params": ["degree"], "type": "predicate", "pages": [183]},
        {"id": "in_enemy_line_of_sight", "description": "The creature is in any enemy's line of sight.", "type": "predicate", "pages": [183]},
        {"id": "hidden", "description": "The creature is hidden (Hide action).", "type": "predicate", "pages": [183]},
        {"id": "underwater", "description": "The creature or attack is underwater.", "type": "predicate", "pages": [16]},
        {"id": "has_speed", "description": "The creature has the movement mode (param).", "params": ["movement_mode"], "type": "predicate", "pages": [16]},
        {"id": "deals_damage_type", "description": "The weapon or attack deals the damage type (param).", "params": ["damage_type"], "type": "predicate", "pages": [16]},
        {"id": "beyond_normal_range", "description": "The target is beyond the attack's normal range.", "type": "predicate", "pages": [15]},
        {"id": "beyond_long_range", "description": "The target is beyond the attack's long (or single) range.", "type": "predicate", "pages": [15]},
        {"id": "enemy_within_feet_sees", "description": "An enemy within 'feet' can see the creature and doesn't have the Incapacitated condition.", "params": ["feet"], "type": "predicate", "pages": [15]},
        {"id": "moved_on_foot_before", "description": "The creature moved at least 'feet' on foot immediately before (jumps).", "params": ["feet"], "type": "predicate", "pages": [183, 184]},
        {"id": "in_difficult_terrain", "description": "The space is Difficult Terrain.", "type": "predicate", "pages": [181]},
        {"id": "mounted", "description": "The creature is riding a mount.", "type": "predicate", "pages": [15]},
    ],
    "events": [
        {"id": "leaves_reach", "description": "A creature the reactor can see leaves its reach (using its action, Bonus Action, Reaction or one of its speeds).", "type": "event", "pages": [15, 185]},
        {"id": "would_drop_to_0_hp_by_melee", "description": "The creature would reduce another creature to 0 Hit Points with a melee attack.", "type": "event", "pages": [17, 184]},
        {"id": "readied_trigger", "description": "The perceivable circumstance chosen with the Ready action occurs.", "type": "event", "pages": [186]},
        {"id": "regains_hit_points", "description": "The creature regains any Hit Points.", "type": "event", "pages": [17]},
        {"id": "attack_roll_made", "description": "The creature makes an attack roll.", "type": "event", "pages": [183]},
        {"id": "mount_moved_against_will", "description": "An effect is about to move the creature's mount against its will.", "type": "event", "pages": [16]},
        {"id": "knocked_prone_while_mounted", "description": "The rider or its mount is knocked Prone.", "type": "event", "pages": [16]},
    ],
}


def act(name, items, **kw):
    return glossary(name, "action", LOT, items, **kw)


def rule(name, items, **kw):
    return glossary(name, "rule", LOT, items, **kw)


def actions():
    E = []
    see_also_actions = ("*See also*", "ref", ["dnd5e/rule/actions"])
    E.append(rule("Action", [
        (None, "sys", [f"{SYS}#/action_economy/0"]),
        ("Choose which action to take", "ref", [A(a) for a in ("attack", "dash", "disengage", "dodge", "help", "hide",
                                                                "influence", "magic", "ready", "search", "study",
                                                                "utilize")]),
        see_also_actions,
        ("These actions are defined elsewhere", "ref", [A("attack"), A("utilize")])]))
    E.append(act("Attack", [
        (None, "fx", {"op": "activation", "name": "Attack", "cost": "action",
                      "then": [{"op": "attack", "attack_type": "melee_weapon",
                                "note": "One attack roll with a weapon or an Unarmed Strike."}]}),
        ("***Equipping and Unequipping Weapons.***", "rule", {"id": "equip_one_weapon", "equip_or_unequip_per_attack": 1,
                                                              "timing": ["before_attack", "after_attack"],
                                                              "equip_includes": ["draw", "pick_up"],
                                                              "unequip_includes": ["sheathe", "stow", "drop"]}),
        ("***Moving between Attacks.***", "rule", {"id": "move_between_attacks", "allowed": True})]))
    E.append(act("Dash", [
        (None, "fx", {"op": "activation", "name": "Dash", "cost": "action", "then": [
            {"op": "modifier", "stat": "movement", "mode": "add", "value": {"var": "speed.walk"},
             "duration": {"kind": "until_event", "until": {"event": "turn_end", "whose": "self"}},
             "note": "Equals your Speed after modifiers."}]}),
        ("If you have a special speed", "rule", {"id": "dash_special_speed", "may_use_special_speed": True,
                                                  "choose_each_time": True}),
        ("*See also*", "ref", [ref_of("Speed", "rule")])]))
    E.append(act("Disengage", [
        (None, "fx", {"op": "activation", "name": "Disengage", "cost": "action", "then": [
            {"op": "modifier", "stat": "provokes_opportunity_attacks", "mode": "set", "value": 0,
             "duration": {"kind": "until_event", "until": {"event": "turn_end", "whose": "self"}}}]})]))
    lose = {"not": {"any": [{"pred": "has_condition", "args": {"condition": "incapacitated"}}, {"pred": "speed_is_zero"}]}}
    until_next = {"kind": "until_event", "until": {"event": "turn_start", "whose": "self"}}
    E.append(act("Dodge", [
        (None, "fx", {"op": "activation", "name": "Dodge", "cost": "action", "then": [
            {"op": "roll_mode", "mode": "disadvantage", "rolls": ["attack_roll"], "direction": "against",
             "when": {"all": [{"pred": "can_see", "args": {"target": "attacker"}}, lose]}, "duration": until_next},
            {"op": "roll_mode", "mode": "advantage", "rolls": ["saving_throw.dex"], "when": lose,
             "duration": until_next}]}),
        ("You lose these benefits", "rule", {"id": "dodge_lost_when", "conditions": [C("incapacitated")],
                                             "speed_zero": True})]))
    E.append(act("Help", [
        (None, "fx", {"op": "activation", "name": "Help", "cost": "action", "then": [{"op": "choice", "choose": 1,
            "options": [
                {"id": "assist_ability_check", "label": "Assist an Ability Check", "effects": [
                    {"op": "roll_mode", "mode": "advantage", "rolls": ["ability_check"],
                     "target": {"kind": "creature", "filter": {"allies_only": True}},
                     "duration": until_next, "note": "Next check with the chosen skill or tool proficiency."}]},
                {"id": "assist_attack_roll", "label": "Assist an Attack Roll", "effects": [
                    {"op": "roll_mode", "mode": "advantage", "rolls": ["attack_roll"], "direction": "against",
                     "target": {"kind": "creature", "range": {"kind": "distance", "feet": 5},
                                "filter": {"enemies_only": True}},
                     "duration": until_next, "note": "Next attack roll by one of your allies against that enemy."}]}]}]}),
        ("***Assist an Ability Check.***", "fx", []),
        ("***Assist an Ability Check.***", "rule", {"id": "assist_check", "choose": "skill_or_tool_proficiency",
                                                    "ally_must_be_near": True, "uses": 1}),
        ("The GM has final say", "md", md("assist_possible", "Is this assistance possible here?",
                                          "The GM has final say on whether your assistance is possible.", pages=[182])),
        ("***Assist an Attack Roll.***", "rule", {"id": "assist_attack", "enemy_within_feet": 5, "uses": 1})]))
    E.append(act("Hide", [
        (None, "fx", {"op": "activation", "name": "Hide", "cost": "action",
                      "requires": {"all": [{"any": [{"pred": "heavily_obscured"},
                                                    {"pred": "behind_cover", "args": {"degree": "three_quarters"}}]},
                                           {"not": {"pred": "in_enemy_line_of_sight"}}]},
                      "then": [{"op": "check", "ability": "dex", "skill": "stealth", "dc": 15,
                                "on_success": [{"op": "apply_condition", "condition": C("invisible"),
                                                "duration": {"kind": "while", "while": {"pred": "hidden"}}}]}]}),
        ("On a successful check", "rule", {"id": "find_dc", "dc_to_find": {"var": "check_total"},
                                           "find_check": {"ability": "wis", "skill": "perception"}}),
        ("You stop being hidden", "rule", {"id": "stop_hidden", "ends_on": ["sound_louder_than_whisper",
                                                                           "found_by_enemy", "attack_roll",
                                                                           "cast_spell_with_verbal_component"]})]))
    E.append(act("Influence", [
        (None, "md", md("monster_disposition", "Is the monster willing, unwilling or hesitant to do what it is urged?",
                        "The GM then determines whether the monster feels willing, unwilling, or hesitant due to "
                        "your interaction", options=[{"id": "willing", "label": "Willing"},
                                                     {"id": "unwilling", "label": "Unwilling"},
                                                     {"id": "hesitant", "label": "Hesitant"}], pages=[184])),
        ("***Willing.***", "rule", {"id": "willing", "check": False, "complies": True}),
        ("***Unwilling.***", "rule", {"id": "unwilling", "check": False, "complies": False}),
        ("***Hesitant.***", "fx", {"op": "activation", "name": "Influence (hesitant)", "cost": "action", "then": [
            {"op": "check", "ability": {"choose_from": ["cha", "wis"], "chooser": "gm"},
             "dc": {"op": "max", "args": [15, {"var": "target_ability_score.int"}]},
             "note": "Check chosen by the GM from the Influence Checks table; affected by the monster's attitude."}]}),
        ("***Hesitant.***", "table", {"id": "influence_checks", "caption": "Influence Checks",
                                      "columns": ["Ability Check", "Interaction"],
                                      "rows": [["Charisma (Deception)", "Deceiving a monster that understands you"],
                                               ["Charisma (Intimidation)", "Intimidating a monster"],
                                               ["Charisma (Performance)", "Amusing a monster"],
                                               ["Charisma (Persuasion)", "Persuading a monster that understands you"],
                                               ["Wisdom (Animal Handling)", "Gently coaxing a Beast or Monstrosity"]]}),
        ("***Hesitant.***", "ref", ["dnd5e/attitude/indifferent", "dnd5e/attitude/friendly", "dnd5e/attitude/hostile"]),
        ("On a failed check, you must wait", "md", md("retry_wait", "How long before the monster can be urged the "
                                                      "same way again (default 24 hours)?",
                                                      "On a failed check, you must wait 24 hours (or a duration set by "
                                                      "the GM) before urging it in the same way again.",
                                                      options=[{"id": "default", "label": "24 hours"}],
                                                      pages=[184]))]))
    E.append(act("Magic", [
        (None, "fx", {"op": "activation", "name": "Magic", "cost": "action", "then": [
            {"op": "reference", "rule": "dnd5e/rule/casting-spells",
             "note": "Cast a spell with a casting time of an action, or use a feature or magic item that requires a Magic action."}]}),
        ("If you cast a spell that has a casting time of 1 minute or longer", "rule", {
            "id": "long_casting", "magic_action_each_turn": True, "concentration_required": True,
            "on_concentration_broken": {"spell_fails": True, "slot_expended": False}}),
        ("*See also*", "ref", [ref_of("Concentration")])]))
    E.append(act("Ready", [
        (None, "fx", {"op": "activation", "name": "Ready", "cost": "action", "then": [
            {"op": "trigger", "event": {"event": "readied_trigger"}, "cost": "reaction", "optional": True,
             "duration": {"kind": "until_event", "until": {"event": "turn_start", "whose": "self"}},
             "then": [{"op": "master_decision", "decision": "readied_response"}]}]}),
        ("First, you decide what perceivable circumstance", "md", md(
            "readied_response", "The readied circumstance occurred: resolve the chosen action (or move up to Speed).",
            "First, you decide what perceivable circumstance will trigger your Reaction. Then, you choose the action "
            "you will take in response to that trigger, or you choose to move up to your Speed in response to it.",
            reason="player_choice_open", pages=[186])),
        ("When the trigger occurs", "rule", {"id": "ready_timing", "when": "right_after_trigger_finishes",
                                             "may_ignore": True}),
        ("When you Ready a spell", "rule", {"id": "ready_spell", "resources_spent_on_ready": True,
                                            "casting_time_required": "action", "concentration_until": "turn_start",
                                            "on_concentration_broken": "spell_dissipates"})]))
    E.append(act("Search", [
        (None, "fx", {"op": "activation", "name": "Search", "cost": "action", "then": [
            {"op": "check", "ability": "wis",
             "skill": {"choose_from": ["insight", "medicine", "perception", "survival"]}}]}),
        ("##### Search", "table", {"id": "search", "caption": "Search", "columns": ["Skill", "Thing to Detect"],
                                   "rows": [["Insight", "Creature’s state of mind"],
                                            ["Medicine", "Creature’s ailment or cause of death"],
                                            ["Perception", "Concealed creature or object"],
                                            ["Survival", "Tracks or food"]]})]))
    E.append(act("Study", [
        (None, "fx", {"op": "activation", "name": "Study", "cost": "action", "then": [
            {"op": "check", "ability": "int",
             "skill": {"choose_from": ["arcana", "history", "investigation", "nature", "religion"]}}]}),
        ("The Areas of Knowledge table", "table", {
            "id": "areas_of_knowledge", "caption": "Areas of Knowledge", "columns": ["Skill", "Areas"], "rows": [
                ["Arcana", "Spells, magic items, eldritch symbols, magical traditions, planes of existence, and certain "
                           "creatures (Aberrations, Constructs, Elementals, Fey, and Monstrosities)"],
                ["History", "Historic events and people, ancient civilizations, wars, and certain creatures (Giants "
                            "and Humanoids)"],
                ["Investigation", "Traps, ciphers, riddles, and gadgetry"],
                ["Nature", "Terrain, flora, weather, and certain creatures (Beasts, Dragons, Oozes, and Plants)"],
                ["Religion", "Deities, religious hierarchies and rites, holy symbols, cults, and certain creatures "
                             "(Celestials, Fiends, and Undead)"]]})]))
    E.append(act("Utilize", [
        (None, "sys", [f"{SYS}#/action_economy/4"]),
        ("When an object requires an action", "fx", {"op": "activation", "name": "Utilize", "cost": "action",
                                                       "then": [{"op": "reference", "rule": "dnd5e/rule/the-order-of-combat",
                                                                 "note": "Use an object that requires an action."}]})]))
    return E


def glossary_rules():
    E = []
    E.append(rule("Attack Roll", [(None, "sys", [f"{SYS}#/core_die/rules"]),
                                  ("*See also*", "ref", ["dnd5e/rule/d20-tests"])]))
    E.append(rule("Bonus Action", [(None, "sys", [f"{SYS}#/action_economy/1"]),
                                   ("*See also*", "ref", ["dnd5e/rule/actions"])]))
    E.append(rule("Breaking Objects", [
        (None, "rule", {"id": "objects_can_be_harmed", "by": ["attacks", "spells"]}),
        ("If an object is exceedingly fragile", "md", md("fragile_object", "Can this exceedingly fragile object be "
                                                         "broken automatically?", "If an object is exceedingly fragile, "
                                                         "the GM may allow a creature to break it automatically with the "
                                                         "Attack or Utilize action.", pages=[177])),
        ("***Armor Class.***", "table", {"id": "object_armor_class", "caption": "Object Armor Class",
                                         "columns": ["AC", "Substance"], "rows": [
                                             ["11", "Cloth, paper, rope"], ["13", "Crystal, glass, ice"], ["15", "Wood"],
                                             ["17", "Stone"], ["19", "Iron, steel"], ["21", "Mithral"],
                                             ["23", "Adamantine"]]}),
        ("***Hit Points.***", "rule", {"id": "object_destroyed_at_0_hp", "huge_or_larger": "track_large_sections"}),
        ("***Hit Points.***", "table", {"id": "object_hit_points", "caption": "Object Hit Points",
                                        "columns": ["Size", "Fragile", "Resilient"], "rows": [
                                            ["Tiny (bottle, lock)", "2 (1d4)", "5 (2d4)"],
                                            ["Small (chest, lute)", "3 (1d6)", "10 (3d6)"],
                                            ["Medium (barrel, chandelier)", "4 (1d8)", "18 (4d8)"],
                                            ["Large (cart, dining table)", "5 (1d10)", "27 (5d10)"]]}),
        ("The GM determines whether destroying part", "md", md("partial_collapse", "Does destroying this part of the "
                                                               "object collapse the whole thing?", "The GM determines "
                                                               "whether destroying part of an object causes the whole "
                                                               "thing to collapse.", pages=[177])),
        ("***Damage Types and Objects.***", "rule", {"id": "object_immunities",
                                                     "immunity": ["poison", "psychic"]}),
        ("The GM might decide that some damage types", "md", md("object_damage_types", "Is this damage type more or "
                                                                "less effective against this object?",
                                                                "The GM might decide that some damage types are more "
                                                                "or less effective against an object.", pages=[177])),
        ("***Damage Threshold.***", "ref", [ref_of("Damage Threshold")]),
        ("***No Ability Scores.***", "rule", {"id": "objects_no_ability_scores", "ability_checks": False,
                                              "saving_throws": "auto_fail"})]))
    E.append(rule("Burrow Speed", [(None, "sys", [f"{SYS}#/registries/movement_modes/1"]),
                                   ("A creature that has a Burrow Speed", "rule", {
                                       "id": "burrow", "through": ["sand", "earth", "mud", "ice"],
                                       "solid_rock": "only_with_trait"}),
                                   ("*See also*", "ref", [ref_of("Speed", "rule")])]))
    E.append(rule("Climbing", [
        (None, "rule", {"id": "climb_cost", "extra_feet_per_foot": 1, "extra_in_difficult_terrain": 2,
                        "ignored_with": "climb_speed"}),
        ("At the GM’s option", "md", md("climb_check", "Does this surface require a DC 15 Strength (Athletics) check?",
                                        "At the GM’s option, climbing a slippery surface or one with few handholds "
                                        "might require a successful DC 15 Strength (Athletics) check.",
                                        options=[{"id": "check", "label": "DC 15 Strength (Athletics)", "effects": [
                                            {"op": "check", "ability": "str", "skill": "athletics", "dc": 15}]},
                                            {"id": "no_check", "label": "No check"}], pages=[178]))]))
    E.append(rule("Climb Speed", [(None, "sys", [f"{SYS}#/registries/movement_modes/2"]),
                                  ("A Climb Speed can be used", "rule", {"id": "climb_speed_no_extra_cost", "applies": True}),
                                  ("*See also*", "ref", [ref_of("Climbing"), ref_of("Speed", "rule")])]))
    E.append(rule("Cover", [
        (None, "rule", {"id": "cover_degrees", "half": {"ac": 2, "dex_saves": 2},
                        "three_quarters": {"ac": 5, "dex_saves": 5}, "total": {"targetable_directly": False},
                        "multiple": "most_protective_only"}),
        ("*See also*", "ref", ["dnd5e/rule/combat-cover"])]))
    E.append(rule("Crawling", [(None, "rule", {"id": "crawl_cost", "extra_feet_per_foot": 1,
                                               "extra_in_difficult_terrain": 2}),
                               ("*See also*", "ref", [ref_of("Speed", "rule")])]))
    E.append(rule("Critical Hit", [
        (None, "sys", [f"{SYS}#/core_die/rules/5"]),
        ("A Critical Hit lets you roll extra dice", "rule", {"id": "critical_damage", "damage_dice": "roll_twice",
                                                             "modifiers": "add_once"}),
        ("*See also*", "ref", ["dnd5e/rule/damage-and-healing"])]))
    E.append(rule("Difficult Terrain", [
        (None, "rule", {"id": "difficult_terrain", "extra_feet_per_foot": 1, "cumulative": False}),
        ("A space is Difficult Terrain if", "rule", {"id": "difficult_terrain_examples", "includes": [
            "creature_not_tiny_or_ally", "furniture_sized_for_your_size_or_larger", "heavy_snow_ice_rubble_undergrowth",
            "liquid_shin_to_waist_deep", "narrow_opening_one_size_smaller", "slope_20_degrees_or_more"],
            "or_similar": True}),
        ("A space is Difficult Terrain if", "md", md("similar_terrain", "Is this space Difficult Terrain (something "
                                                     "similar to the listed examples)?", "A space is Difficult Terrain "
                                                     "if the space contains any of the following or something similar:",
                                                     pages=[181]))]))
    E.append(rule("Flying", [
        (None, "rule", {"id": "falls_when", "conditions": [C("incapacitated"), C("prone")], "fly_speed_zero": True,
                        "unless": "can_hover"}),
        ("*See also*", "ref", [ref_of("Falling"), ref_of("Fly Speed")])]))
    E.append(rule("Fly Speed", [(None, "sys", [f"{SYS}#/registries/movement_modes/3"]),
                                ("While you have a Fly Speed", "rule", {"id": "stay_aloft",
                                                                        "until": ["land", "fall", "die"]}),
                                ("*See also*", "ref", [ref_of("Flying"), ref_of("Speed", "rule")])]))
    E.append(rule("Grappling", [
        (None, "desc", None),
        ("However a grapple is initiated", "ref", [ref_of("Unarmed Strike"), C("grappled")]),
        ("***Grappled Condition.***", "fx", {"op": "apply_condition", "condition": C("grappled")}),
        ("***One Grapple per Hand.***", "rule", {"id": "one_grapple_per_part", "requires_free_hand": True,
                                                 "creatures_per_part": 1,
                                                 "part_cannot_target_others_until_released": True}),
        ("***Ending a Grapple.***", "fx", {"op": "activation", "name": "Escape a grapple", "cost": "action",
                                          "requires": {"pred": "has_condition", "args": {"condition": "grappled"}},
                                          "then": [{"op": "check",
                                                    "ability": {"choose_from": ["str", "dex"]},
                                                    "skill": {"choose_from": ["athletics", "acrobatics"]},
                                                    "dc": {"var": "escape_dc"},
                                                    "on_success": [{"op": "remove_condition",
                                                                    "conditions": [C("grappled")]}]}]}),
        ("***Ending a Grapple.***", "rule", {"id": "grapple_ends", "when": ["grappler_incapacitated",
                                                                         "distance_exceeds_grapple_range",
                                                                         "grappler_releases"],
                                            "release_cost": "none"})]))
    E.append(rule("High Jump", [
        (None, "rule", {"id": "high_jump", "height_feet": {"op": "max", "args": [0, {"op": "add", "args": [
            3, {"var": "ability_mod.str"}]}]}, "running_start_feet": 10, "standing": "half",
            "movement_per_foot": 1}),
        ("You can extend your arms", "rule", {"id": "reach_during_jump", "reach_height": {"op": "add", "args": [
            {"var": "jump_height"}, {"op": "mul", "args": [1.5, {"var": "height"}]}]}})]))
    E.append(rule("Hover", [(None, "rule", {"id": "hover", "prevents_falling_when": ["incapacitated", "prone",
                                                                                     "fly_speed_zero"]}),
                            ("*See also*", "ref", [ref_of("Flying")])]))
    E.append(rule("Improvised Weapons", [
        (None, "rule", {"id": "improvised", "includes": ["object_wielded_as_weapon",
                                                         "ranged_weapon_used_in_melee",
                                                         "melee_weapon_thrown_without_thrown_property"]}),
        ("***Proficiency.***", "rule", {"id": "no_proficiency_bonus", "add_proficiency_bonus": False}),
        ("***Damage.***", "rule", {"id": "damage", "dice": "1d4"}),
        ("***Damage.***", "md", md("improvised_damage_type", "Which damage type does this improvised weapon deal?",
                                   "On a hit, the weapon deals 1d4 damage of a type the GM thinks is appropriate for "
                                   "the object.", options=[{"id": t, "label": t.title()} for t in
                                                           ("bludgeoning", "piercing", "slashing")], pages=[183])),
        ("***Range.***", "rule", {"id": "thrown_range", "normal_feet": 20, "long_feet": 60}),
        ("***Weapon Equivalents.***", "md", md("weapon_equivalent", "Does this improvised weapon function as a "
                                               "Simple or Martial weapon it resembles?", "If an improvised weapon "
                                               "resembles a Simple or Martial weapon, the GM may say it functions as "
                                               "that weapon and uses that weapon’s rules.", pages=[183]))]))
    E.append(rule("Initiative", [
        (None, "sys", [f"{SYS}#/initiative"]),
        ("Sometimes a GM might have combatants use their Initiative scores", "md", md(
            "initiative_scores", "Use Initiative scores instead of rolling?", "Sometimes a GM might have combatants "
            "use their Initiative scores instead of rolling Initiative.", when="campaign_setup",
            options=[{"id": "roll", "label": "Roll Initiative"}, {"id": "score", "label": "Use Initiative scores"}],
            pages=[184])),
        ("Your Initiative score equals", "rule", {"id": "initiative_score", "score": {"op": "add", "args": [
            10, {"var": "ability_mod.dex"}]}, "advantage": 5, "disadvantage": -5}),
        ("*See also*", "ref", ["dnd5e/rule/combat"])]))
    E.append(rule("Jumping", [(None, "ref", [ref_of("Long Jump"), ref_of("High Jump")])]))
    E.append(rule("Knocking Out a Creature", [
        (None, "fx", {"op": "trigger", "event": {"event": "would_drop_to_0_hp_by_melee"}, "optional": True, "then": [
            {"op": "modifier", "stat": "hp", "mode": "set", "value": 1, "target": {"kind": "inherit"}},
            {"op": "apply_condition", "condition": C("unconscious"), "target": {"kind": "inherit"}}]}),
        ("The creature then has the Unconscious condition", "rule", {"id": "starts_short_rest", "target_starts": "short_rest"}),
        ("The creature remains Unconscious", "rule", {"id": "ends_when", "regains_hit_points": True,
                                                      "first_aid": {"cost": "action", "check": {"ability": "wis",
                                                                                                "skill": "medicine",
                                                                                                "dc": 10}}})]))
    E.append(rule("Long Jump", [
        (None, "rule", {"id": "long_jump", "distance_feet": {"var": "ability_score.str"}, "running_start_feet": 10,
                        "standing": "half", "movement_per_foot": 1}),
        ("If you land in Difficult Terrain", "fx", {"op": "check", "ability": "dex", "skill": "acrobatics", "dc": 10,
                                                    "when": {"pred": "in_difficult_terrain"},
                                                    "on_fail": [{"op": "apply_condition", "condition": C("prone")}]}),
        ("This Long Jump rule assumes", "md", md("low_obstacle", "Does clearing this low obstacle require a DC 10 "
                                                 "Strength (Athletics) check?", "At your GM’s option, you must succeed "
                                                 "on a DC 10 Strength (Athletics) check to clear a low obstacle (no "
                                                 "taller than a quarter of the jump’s distance), such as a hedge or low "
                                                 "wall. Otherwise, you hit the obstacle.", pages=[184]))]))
    E.append(rule("Occupied Space", [(None, "rule", {"id": "occupied", "creature_present": True,
                                                     "completely_filled_by_objects": True})]))
    E.append(rule("Opportunity Attacks", [
        (None, "fx", {"op": "trigger", "event": {"event": "leaves_reach", "whose": "any"}, "cost": "reaction",
                      "optional": True, "condition": {"pred": "can_see", "args": {"target": "provoker"}},
                      "then": [{"op": "attack", "attack_type": "melee",
                                "note": "One melee attack with a weapon or an Unarmed Strike, right before the "
                                        "creature leaves your reach."}]}),
        ("*See also*", "ref", ["dnd5e/rule/melee-attacks"])]))
    E.append(rule("Reach", [(None, "rule", {"id": "default_reach", "feet": 5})]))
    E.append(rule("Reaction", [
        (None, "sys", [f"{SYS}#/action_economy/2"]),
        ("The Opportunity Attack is a Reaction available to all creatures.", "ref", [ref_of("Opportunity Attacks")]),
        ("*See also*", "ref", [ref_of("Opportunity Attacks"), "dnd5e/rule/actions"])]))
    E.append(rule("Surprise", [(None, "sys", [f"{SYS}#/initiative/rules/2"]),
                               ("*See also*", "ref", ["dnd5e/rule/combat"])]))
    E.append(rule("Swimming", [
        (None, "rule", {"id": "swim_cost", "extra_feet_per_foot": 1, "extra_in_difficult_terrain": 2,
                        "ignored_with": "swim_speed"}),
        ("At the GM’s option", "md", md("rough_water", "Does moving in this rough water require a DC 15 Strength "
                                        "(Athletics) check?", "At the GM’s option, moving any distance in rough water "
                                        "might require a successful DC 15 Strength (Athletics) check.", pages=[189]))]))
    E.append(rule("Swim Speed", [(None, "sys", [f"{SYS}#/registries/movement_modes/4"]),
                                 ("A Swim Speed can be used", "rule", {"id": "swim_speed_no_extra_cost", "applies": True}),
                                 ("*See also*", "ref", [ref_of("Swimming"), ref_of("Speed", "rule")])]))
    E.append(rule("Target", [(None, "rule", {"id": "target", "selected_by": ["attack_roll", "forced_saving_throw",
                                                                            "selected_for_effect"]})]))
    # The three options are one choice (D-005): the attack uses the attack's ability (Str by
    # default, rule/attack-rolls), so features that change it (Martial Arts) apply.
    us_dc = {"op": "add", "args": [8, {"var": "ability_mod.str"}, {"var": "proficiency_bonus"}]}
    us_choice = {"op": "choice", "id": "unarmed_strike", "choose": 1, "options": [
        {"id": "damage", "label": "Damage", "effects": [
            {"op": "attack", "attack_type": "melee",
             "bonus": {"op": "add", "args": [{"var": "attack_ability_mod"}, {"var": "proficiency_bonus"}]},
             "on_hit": [{"op": "damage", "amount": {"op": "add", "args": [1, {"var": "attack_ability_mod"}]},
                         "damage_type": "bludgeoning"}]}]},
        {"id": "grapple", "label": "Grapple", "effects": [
            {"op": "save", "ability": {"choose_from": ["str", "dex"], "chooser": "target"}, "dc": us_dc,
             "on_fail": [{"op": "apply_condition", "condition": C("grappled"), "params": {"escape_dc": us_dc}}]}]},
        {"id": "shove", "label": "Shove", "effects": [
            {"op": "save", "ability": {"choose_from": ["str", "dex"], "chooser": "target"}, "dc": us_dc,
             "on_fail": [{"op": "choice", "choose": 1, "options": [
                 {"id": "push", "label": "Push 5 feet", "effects": [{"op": "move", "mode": "push",
                                                                      "distance_feet": 5}]},
                 {"id": "prone", "label": "Prone", "effects": [{"op": "apply_condition",
                                                                "condition": C("prone")}]}]}]}]}]}
    E.append(rule("Unarmed Strike", [
        (None, "rule", {"id": "unarmed_strike", "range_feet": 5, "options": ["damage", "grapple", "shove"]}),
        (None, "fx", us_choice),
        ("***Damage.***", "sys", ["/effects/0/options/0"]),
        ("***Grapple.***", "sys", ["/effects/0/options/1"]),
        ("***Grapple.***", "rule", {"id": "grapple_requirements", "max_target_size_steps_larger": 1,
                                    "requires_free_hand": True}),
        ("***Shove.***", "sys", ["/effects/0/options/2"]),
        ("***Shove.***", "rule", {"id": "shove_requirements", "max_target_size_steps_larger": 1})]))
    E.append(rule("Unoccupied Space", [(None, "rule", {"id": "unoccupied", "no_creatures": True,
                                                       "not_completely_filled_by_objects": True})]))
    E.append(rule("Weapon Attack", [(None, "desc", None), ("*See also*", "ref", [ref_of("Weapon")])]))
    return E


def sections():
    E = []
    sec = lambda slug, name, nodes, path, items, **kw: build("rule", slug, name, nodes, LOT, path, items, **kw)  # noqa: E731
    ae = f"{SYS}#/action_economy"
    nodes = section("Actions", 2, page=9, skip_tables=("Skills",))
    E.append(sec("actions", "Actions", nodes, "Playing the Game/Actions", [
        (None, "ref", [A(a) for a in ("attack", "dash", "disengage", "dodge", "help", "hide", "influence", "magic",
                                      "ready", "search", "study", "utilize")]),
        ("Player characters and monsters can also do things", "md", md(
            "improvised_action", "Is this improvised action possible, and which D20 Test (if any) does it require?",
            "When you describe an action not detailed elsewhere in the rules, the Game Master tells you whether that "
            "action is possible and what kind of D20 Test you need to make, if any.", pages=[10])),
        ("### One Thing at a Time", "sys", [f"{ae}/0/rules/1"]),
        ("### Bonus Actions", "sys", [f"{ae}/1"]),
        ("### Reactions", "sys", [f"{ae}/2"]),
        ("The Opportunity Attack, described later", "ref", [ref_of("Opportunity Attacks")]),
        ("When you take a Reaction, you can’t take another one", "sys", [f"{ae}/2/rules/0", f"{ae}/2/rules/1"])]))

    nodes = section("Combat", 2, page=13, stop_titles=("The Order of Combat",))
    E.append(sec("combat", "Combat", nodes, "Playing the Game/Combat", [(None, "desc", None)],
                 data={"sections": ["dnd5e/rule/the-order-of-combat", "dnd5e/rule/movement-and-position",
                                    "dnd5e/rule/making-an-attack", "dnd5e/rule/combat-cover",
                                    "dnd5e/rule/ranged-attacks", "dnd5e/rule/melee-attacks",
                                    "dnd5e/rule/mounted-combat", "dnd5e/rule/underwater-combat"]}))

    ini = f"{SYS}#/initiative/rules"
    nodes = section("The Order of Combat", 3, page=13)
    E.append(sec("the-order-of-combat", "The Order of Combat", nodes, "Playing the Game/Combat/The Order of Combat", [
        (None, "sys", [f"{SYS}#/time/rules/0"]),
        (None, "rule", {"id": "rounds_and_turns", "each_participant_one_turn_per_round": True,
                        "order_by": "initiative", "next_round_if_not_defeated": True}),
        ("#### Combat Step by Step", "rule", {"id": "steps", "procedure": ["establish_positions", "roll_initiative",
                                                                          "take_turns"]}),
        ("**1: Establish Positions.**", "md", md("positions", "Place the characters and monsters and determine where "
                                                 "the adversaries are.", "The Game Master determines where all the "
                                                 "characters and monsters are located.", when="on_use", pages=[13])),
        ("**2: Roll Initiative.**", "sys", [f"{SYS}#/initiative"]),
        ("**3: Take Turns.**", "rule", {"id": "round_end", "round_ends_when": "everyone_had_a_turn",
                                        "repeat_until": "fighting_stops"}),
        ("#### Initiative", "sys", [f"{ini}/0", f"{ini}/1"]),
        ("***Surprise.***", "sys", [f"{ini}/2"]),
        ("***Initiative Order.***", "sys", [f"{ini}/3"]),
        ("***Ties.***", "sys", [f"{ini}/4"]),
        ("#### Your Turn", "sys", [f"{ae}/0/rules/0", f"{ae}/3/rules/0"]),
        ("The main actions you can take", "ref", ["dnd5e/rule/actions", "dnd5e/rule/movement-and-position"]),
        ("***Communicating.***", "sys", [f"{ae}/5"]),
        ("Extended communication", "rule", {"id": "extended_communication", "cost": "action"}),
        ("Extended communication", "ref", [A("influence")]),
        ("***Interacting with Things.***", "sys", [f"{ae}/4"]),
        ("The GM might require you to use an action", "md", md("interaction_cost", "Does this interaction need an "
                                                               "action (special care or an unusual obstacle)?",
                                                               "The GM might require you to use an action for any of "
                                                               "these activities when it needs special care or when it "
                                                               "presents an unusual obstacle.", pages=[13])),
        ("***Doing Nothing on Your Turn.***", "rule", {"id": "do_nothing", "allowed": True}),
        ("#### Ending Combat", "rule", {"id": "ending_combat", "ends_when": ["one_side_defeated",
                                                                            "both_sides_agree"]})]))

    nodes = section("Movement and Position", 3, page=14)
    E.append(sec("movement-and-position", "Movement and Position", nodes, "Playing the Game/Combat/Movement and Position", [
        (None, "rule", {"id": "move_up_to_speed", "may_not_move": True}),
        ("Your movement can include climbing", "ref", [ref_of("Climbing"), ref_of("Crawling"), ref_of("Jumping"),
                                                      ref_of("Swimming")]),
        ("However you’re moving with your Speed", "rule", {"id": "deduct_movement", "deduct_each_part": True}),
        ("A character’s Speed is determined", "ref", [ref_of("Speed", "rule")]),
        ("#### Difficult Terrain", "ref", [ref_of("Difficult Terrain")]),
        ("Every foot of movement in Difficult Terrain", "rule", {"id": "difficult_terrain", "extra_feet_per_foot": 1,
                                                                 "stacks": False}),
        ("#### Breaking Up Your Move", "rule", {"id": "break_up_move", "around": ["action", "bonus_action",
                                                                                  "reaction"]}),
        ("#### Dropping Prone", "fx", {"op": "activation", "name": "Drop prone", "cost": "none",
                                       "requires": {"not": {"pred": "speed_is_zero"}},
                                       "then": [{"op": "apply_condition", "condition": C("prone")}]}),
        ("#### Creature Size", "sys", [f"{SYS}#/registries/sizes"]),
        ("#### Moving around Other Creatures", "rule", {"id": "pass_through", "may_pass": [
            "ally", "incapacitated_creature", "tiny_creature", "creature_two_sizes_larger_or_smaller"]}),
        ("Another creature’s space is Difficult Terrain", "rule", {"id": "creature_space_difficult",
                                                                  "except": ["tiny", "ally"]}),
        ("You can’t willingly end a move", "rule", {"id": "no_shared_space", "willing_end_in_occupied": False,
                                                    "if_ended_in_occupied": {"apply": C("prone"),
                                                                             "unless": ["tiny", "larger_than_other"]}})]))

    nodes = section("Making an Attack", 3, page=14)
    E.append(sec("making-an-attack", "Making an Attack", nodes, "Playing the Game/Combat/Making an Attack", [
        (None, "rule", {"id": "attack_structure", "procedure": ["choose_target", "determine_modifiers",
                                                               "resolve_attack"]}),
        ("**1: Choose a Target.**", "rule", {"id": "choose_target", "targets": ["creature", "object", "location"],
                                             "within_range": True}),
        ("**2: Determine Modifiers.**", "md", md("cover_and_advantage", "Does the target have Cover, and does the "
                                                 "attacker have Advantage or Disadvantage?", "The GM determines whether "
                                                 "the target has Cover (see the next section) and whether you have "
                                                 "Advantage or Disadvantage against the target.", pages=[14])),
        ("**3: Resolve the Attack.**", "sys", [f"{SYS}#/core_die/rules"])]))

    nodes = section("Cover", 3, page=15)
    E.append(sec("combat-cover", "Cover", nodes, "Playing the Game/Combat/Cover", [
        (None, "rule", {"id": "cover_applies", "only_if_effect_originates_opposite_side": True,
                        "multiple": "most_protective_only"}),
        ("##### Cover", "table", {"id": "cover", "caption": "Cover", "columns": ["Degree", "Benefit to Target",
                                                                                 "Offered By …"], "rows": [
            ["Half", "+2 bonus to AC and Dexterity saving throws",
             "Another creature or an object that covers at least half of the target"],
            ["Three-Quarters", "+5 bonus to AC and Dexterity saving throws",
             "An object that covers at least three-quarters of the target"],
            ["Total", "Can’t be targeted directly", "An object that covers the whole target"]]}),
        ("##### Cover", "fx", [{"op": "modifier", "stat": "ac", "mode": "add", "value": 2,
                                "when": {"pred": "behind_cover", "args": {"degree": "half"}}},
                               {"op": "modifier", "stat": "saving_throw.dex", "mode": "add", "value": 2,
                                "when": {"pred": "behind_cover", "args": {"degree": "half"}}},
                               {"op": "modifier", "stat": "ac", "mode": "add", "value": 5,
                                "when": {"pred": "behind_cover", "args": {"degree": "three_quarters"}}},
                               {"op": "modifier", "stat": "saving_throw.dex", "mode": "add", "value": 5,
                                "when": {"pred": "behind_cover", "args": {"degree": "three_quarters"}}}])]))

    nodes = section("Ranged Attacks", 3, page=15)
    E.append(sec("ranged-attacks", "Ranged Attacks", nodes, "Playing the Game/Combat/Ranged Attacks", [
        (None, "desc", None),
        ("#### Range", "rule", {"id": "single_range", "beyond": "cannot_attack"}),
        ("Some ranged attacks, such as those made with a Longbow", "fx", [
            {"op": "roll_mode", "mode": "disadvantage", "rolls": ["attack_roll.ranged"],
             "when": {"pred": "beyond_normal_range"}},
            {"op": "auto_result", "rolls": ["attack_roll.ranged"], "result": "miss",
             "when": {"pred": "beyond_long_range"}, "note": "You can't attack a target beyond long range."}]),
        ("#### Ranged Attacks in Close Combat", "fx", {"op": "roll_mode", "mode": "disadvantage",
                                                      "rolls": ["attack_roll.ranged"],
                                                      "when": {"pred": "enemy_within_feet_sees", "args": {"feet": 5}}})]))

    nodes = section("Melee Attacks", 3, page=15)
    E.append(sec("melee-attacks", "Melee Attacks", nodes, "Playing the Game/Combat/Melee Attacks", [
        (None, "desc", None),
        ("#### Reach", "ref", [ref_of("Reach", "rule")]),
        ("#### Opportunity Attacks", "desc", None),
        ("***Avoiding Opportunity Attacks.***", "rule", {"id": "no_provocation", "when": [
            "disengage", "teleport", "moved_without_own_movement_action_or_reaction"]}),
        ("***Avoiding Opportunity Attacks.***", "ref", [A("disengage"), ref_of("Teleportation")]),
        ("***Making an Opportunity Attack.***", "ref", [ref_of("Opportunity Attacks")])]))

    nodes = section("Mounted Combat", 3, page=15)
    fall_off = {"op": "save", "ability": "dex", "dc": 10, "on_fail": [
        {"op": "move", "mode": "fall", "note": "Fall off into an unoccupied space within 5 feet of the mount."},
        {"op": "apply_condition", "condition": C("prone")}]}
    E.append(sec("mounted-combat", "Mounted Combat", nodes, "Playing the Game/Combat/Mounted Combat", [
        (None, "rule", {"id": "mount_requirements", "willing": True, "min_size_steps_larger": 1,
                        "appropriate_anatomy": True}),
        ("#### Mounting and Dismounting", "fx", {"op": "activation", "name": "Mount or dismount", "cost": "movement",
                                                 "movement_cost": {"op": "div", "args": [{"var": "speed.walk"}, 2],
                                                                   "round": "down"},
                                                 "then": [{"op": "reference", "rule": "dnd5e/rule/mounted-combat"}]}),
        ("#### Controlling a Mount", "rule", {"id": "controlled_mount", "requires_training": True,
                                              "initiative": "matches_rider", "actions": [A("dash"), A("disengage"),
                                                                                         A("dodge")],
                                              "acts_on_mount_turn": True}),
        ("In contrast, an independent mount", "rule", {"id": "independent_mount", "keeps_initiative": True,
                                                       "acts_freely": True}),
        ("#### Falling Off", "fx", [{"op": "trigger", "event": {"event": "mount_moved_against_will"},
                                     "condition": {"pred": "mounted"}, "then": [fall_off]},
                                    {"op": "trigger", "event": {"event": "knocked_prone_while_mounted"},
                                     "condition": {"pred": "mounted"}, "then": [fall_off]}])]))

    nodes = section("Underwater Combat", 3, page=16)
    E.append(sec("underwater-combat", "Underwater Combat", nodes, "Playing the Game/Combat/Underwater Combat", [
        (None, "desc", None),
        ("#### Impeded Weapons", "fx", {"op": "roll_mode", "mode": "disadvantage", "rolls": ["attack_roll.melee_weapon"],
                                        "when": {"all": [{"pred": "underwater"},
                                                         {"not": {"pred": "has_speed", "args": {"movement_mode": "swim"}}},
                                                         {"not": {"pred": "deals_damage_type",
                                                                  "args": {"damage_type": "piercing"}}}]}}),
        ("A ranged attack roll with a weapon underwater", "fx", [
            {"op": "auto_result", "rolls": ["attack_roll.ranged_weapon"], "result": "miss",
             "when": {"all": [{"pred": "underwater"}, {"pred": "beyond_normal_range"}]}},
            {"op": "roll_mode", "mode": "disadvantage", "rolls": ["attack_roll.ranged_weapon"],
             "when": {"all": [{"pred": "underwater"}, {"not": {"pred": "beyond_normal_range"}}]}}]),
        ("#### Fire Resistance", "fx", {"op": "defense", "kind": "resistance", "damage_types": ["fire"],
                                        "when": {"pred": "underwater"}})]))

    side = lambda title, slug, items: build("rule", slug, title, sidebar(title), LOT, "Playing the Game/Combat",  # noqa: E731
                                            items, facets={"sidebar": True})
    E.append(side("Playing on a Grid", "sidebar-playing-on-a-grid", [
        (None, "md", md("use_grid", "Play on a square grid?", "If you play using a square grid and miniatures or other "
                        "tokens, follow these rules.", when="campaign_setup", pages=[13])),
        ("***Squares.***", "rule", {"id": "square_feet", "feet": 5}),
        ("***Speed.***", "rule", {"id": "speed_in_squares", "squares": {"op": "div", "args": [{"var": "speed.walk"}, 5]}}),
        ("***Entering a Square.***", "rule", {"id": "enter_square", "cost_squares": 1, "diagonal_allowed": True,
                                              "difficult_terrain_cost_squares": 2}),
        ("***Corners.***", "rule", {"id": "corners", "diagonal_cannot_cross_filled_corner": True}),
        ("***Ranges.***", "rule", {"id": "grid_range", "count_from_adjacent_square": True, "shortest_route": True})]))
    E.append(side("Unseen Attackers and Targets", "sidebar-unseen-attackers-and-targets", [
        (None, "fx", {"op": "roll_mode", "mode": "disadvantage", "rolls": ["attack_roll"],
                      "when": {"not": {"pred": "can_see", "args": {"target": "target"}}}}),
        ("If the target isn’t in the location you targeted", "rule", {"id": "wrong_location", "result": "miss"}),
        ("When a creature can’t see you", "fx", {"op": "roll_mode", "mode": "advantage", "rolls": ["attack_roll"],
                                                 "when": {"not": {"pred": "can_be_seen_by", "args": {"who": "target"}}}}),
        ("If you are hidden when you make an attack roll", "rule", {"id": "attack_reveals_location", "on": ["hit", "miss"]})]))
    E.append(side("Knocking Out a Creature", "sidebar-knocking-out-a-creature", [
        (None, "ref", [ref_of("Knocking Out a Creature")]),
        (None, "rule", {"id": "short_rest_then_ends", "condition_ends_at_end_of_short_rest": True,
                        "ends_early": ["regains_hit_points", "first_aid_dc_10_wis_medicine"]})]))
    return E


if __name__ == "__main__":
    extend_registries(REGISTRY, LOT)
    out = actions() + glossary_rules() + sections()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
