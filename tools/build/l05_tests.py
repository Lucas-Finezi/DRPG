#!/usr/bin/env python3
"""L05 — D20 Tests, proficiency, Advantage/Disadvantage, Heroic Inspiration, social
interaction and attitudes.

Usage: python3 -I tools/build/l05_tests.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import (build, extend_registries, glossary, md, ref_of, section, sidebar,  # noqa: E402
                      table_nodes, write_entry)

LOT = "L05"
SYS = "dnd5e/system/dnd5e"
D20 = f"{SYS}#/core_die/rules"

REGISTRY = {
    "rolls": [
        {"id": "any_die", "description": "Any die the creature rolls.", "pages": [8, 183]},
    ],
    "events": [
        {"id": "die_rolled", "description": "Immediately after the creature rolls a die.", "type": "event", "pages": [8, 183]},
    ],
    "predicates": [
        {"id": "lacks_ability_score", "description": "The creature lacks the ability score the roll uses.", "type": "predicate", "pages": [187]},
        {"id": "has_proficiency", "description": "The creature has proficiency with the skill, tool, save or weapon used (param).", "params": ["item"], "type": "predicate", "pages": [8]},
        {"id": "has_expertise", "description": "The creature has Expertise in the skill used.", "params": ["skill"], "type": "predicate", "pages": [182]},
        {"id": "influence_check", "description": "The ability check is made to influence the creature.", "type": "predicate", "pages": [182, 183]},
    ],
    "attitudes": [
        {"id": "friendly", "name": "Friendly", "description": "Views you favorably.", "ref": "dnd5e/attitude/friendly", "pages": [182]},
        {"id": "indifferent", "name": "Indifferent", "description": "No desire to help or hinder; the default attitude of a monster.", "ref": "dnd5e/attitude/indifferent", "pages": [184]},
        {"id": "hostile", "name": "Hostile", "description": "Views you unfavorably.", "ref": "dnd5e/attitude/hostile", "pages": [183]},
    ],
}

PG_PROF = "dnd5e/rule/playing-the-game-proficiency"


def g(name, items, kind="rule", **kw):
    return glossary(name, kind, LOT, items, **kw)


def glossary_entries():
    E = []
    E.append(g("Ability Check", [(None, "sys", [f"{D20}/0"]),
                                 ("*See also*", "ref", ["dnd5e/rule/d20-tests", PG_PROF])]))
    E.append(g("Advantage", [(None, "sys", [f"{D20}/7", f"{D20}/8", f"{D20}/9"]),
                             ("*See also*", "ref", ["dnd5e/rule/d20-tests"])]))
    E.append(g("Attitude", [(None, "sys", [f"{SYS}#/registries/attitudes"]),
                            ("*See also*", "ref", ["dnd5e/attitude/friendly", "dnd5e/attitude/hostile",
                                                   "dnd5e/attitude/indifferent", "dnd5e/action/influence"])]))
    E.append(g("D20 Test", [
        (None, "sys", [f"{D20}/0"]),
        ("If something in the game affects D20 Tests", "rule", {"id": "affects_all_three",
                                                               "rolls": ["ability_check", "attack_roll", "saving_throw"]}),
        ("The GM determines whether a D20 Test is warranted", "md", md(
            "test_warranted", "Is a D20 Test warranted here?", "The GM determines whether a D20 Test is warranted in a "
            "given circumstance.", pages=[180])),
        ("*See also*", "ref", ["dnd5e/rule/d20-tests"])]))
    E.append(g("Difficulty Class", [(None, "sys", [f"{D20}/4"]),
                                    ("*See also*", "ref", ["dnd5e/rule/d20-tests"])]))
    E.append(g("Disadvantage", [(None, "sys", [f"{D20}/7", f"{D20}/8", f"{D20}/9"]),
                                ("*See also*", "ref", ["dnd5e/rule/d20-tests"])]))
    E.append(g("Expertise", [
        (None, "rule", {"id": "expertise", "proficiency_bonus_multiplier": 2, "applies_to": "ability_check_with_skill",
                        "unless": "bonus_already_doubled_by_another_feature"}),
        ("If you gain Expertise", "rule", {"id": "gain_expertise", "skills_per_gain": 1,
                                           "requires_proficiency": True, "max_per_skill": 1}),
        ("*See also*", "ref", [PG_PROF])]))
    E.append(g("Friendly", [
        (None, "fx", {"op": "roll_mode", "mode": "advantage", "rolls": ["ability_check"], "direction": "against",
                      "when": {"pred": "influence_check"}, "note": "Checks to influence this creature."}),
        ("*See also*", "ref", ["dnd5e/action/influence"])], kind="attitude"))
    E.append(g("Heroic Inspiration", [
        (None, "fx", [{"op": "resource", "resource": "heroic_inspiration", "name": "Heroic Inspiration", "max": 1},
                      {"op": "trigger", "event": {"event": "die_rolled"}, "optional": True,
                       "frequency": {"count": 1, "per": "turn"},
                       "then": [{"op": "spend", "resource": "heroic_inspiration", "amount": 1},
                                {"op": "reroll", "rolls": ["any_die"], "keep": "new"}],
                       "note": "Player characters only."}]),
        ("If you gain Heroic Inspiration but already have it", "rule", {
            "id": "only_one", "max": 1, "on_gain_when_full": "give_to_pc_without_it_or_lose"})]))
    E.append(g("Hostile", [
        (None, "fx", {"op": "roll_mode", "mode": "disadvantage", "rolls": ["ability_check"], "direction": "against",
                      "when": {"pred": "influence_check"}, "note": "Checks to influence this creature."}),
        ("*See also*", "ref", ["dnd5e/action/influence"])], kind="attitude"))
    E.append(g("Indifferent", [
        (None, "rule", {"id": "default_attitude", "monster_default": "indifferent"}),
        ("*See also*", "ref", ["dnd5e/action/influence"])], kind="attitude"))
    E.append(g("Passive Perception", [
        (None, "md", md("passive_perception_use", "Does the creature notice it (compare against its Passive "
                        "Perception)?", "The GM uses this score when determining whether a creature notices something "
                        "without consciously making a Wisdom (Perception) check.", pages=[186])),
        ("A creature’s Passive Perception equals", "rule", {
            "id": "passive_perception", "score": {"op": "add", "args": [10, {"var": "check_mod.wis.perception"}]},
            "advantage": 5, "disadvantage": -5})]))
    E.append(g("Proficiency", [
        (None, "rule", {"id": "add_proficiency_bonus", "when": {"pred": "has_proficiency"},
                        "kinds": ["skill", "saving_throw", "weapon", "tool"]}),
        ("*See also*", "ref", [PG_PROF])]))
    E.append(g("Save", [(None, "ref", [ref_of("Saving Throw", "rule")])]))
    E.append(g("Saving Throw", [
        (None, "rule", {"id": "saving_throw", "made_when": "rule_requires", "may_choose_to_fail": True,
                        "result_defined_by": "effect"}),
        ("If a target is forced to make a save and lacks the ability score", "fx", {
            "op": "auto_result", "rolls": ["saving_throw"], "result": "fail", "when": {"pred": "lacks_ability_score"}}),
        ("*See also*", "ref", ["dnd5e/rule/d20-tests"])]))
    E.append(g("Skill", [(None, "sys", [f"{SYS}#/skills"]),
                         ("If you have proficiency in a skill", "rule", {"id": "skill_proficiency",
                                                                         "adds": "proficiency_bonus"}),
                         ("*See also*", "ref", [PG_PROF])]))
    return E


def tdata(caption, columns, rows):
    return {"id": caption.lower().replace(" ", "_"), "caption": caption, "columns": columns, "rows": rows}


def sections():
    E = []
    sec = lambda slug, name, nodes, path, items, **kw: build("rule", slug, name, nodes, LOT, path, items, **kw)  # noqa: E731
    nodes = section("D20 Tests", 2, stop_titles=("Ability Checks",))
    E.append(sec("d20-tests", "D20 Tests", nodes, "Playing the Game/D20 Tests", [
        (None, "sys", [f"{D20}/0"]),
        ("**4: Roll 1d20.**", "sys", [f"{D20}/1", f"{D20}/7"]),
        ("**5: Add Modifiers.**", "sys", [f"{D20}/2"]),
        ("**6: Compare the Total to a Target Number.**", "sys", [f"{D20}/3", f"{D20}/4"]),
        ("The Game Master determines target numbers", "md", md(
            "target_numbers", "Set the target number (DC) and tell the player whether the roll succeeds.",
            "The Game Master determines target numbers and tells players whether their rolls are successful.",
            pages=[6]))]))

    nodes = section("Ability Checks", 3, page=6)
    E.append(sec("ability-checks", "Ability Checks", nodes, "Playing the Game/D20 Tests/Ability Checks", [
        (None, "md", md("call_for_check", "Call for an ability check? (something other than an attack with a chance "
                        "of meaningful failure)", "The GM and the rules often call for an ability check when a creature "
                        "attempts something other than an attack that has a chance of meaningful failure.", pages=[6])),
        ("#### Ability Modifier", "table", tdata("Ability Check Examples", ["Ability", "Make a Check To …"], [
            ["Strength", "Lift, push, pull, or break something"], ["Dexterity", "Move nimbly, quickly, or quietly"],
            ["Constitution", "Push your body beyond normal limits"], ["Intelligence", "Reason or remember"],
            ["Wisdom", "Notice things in the environment or in creatures’ behavior"],
            ["Charisma", "Influence, entertain, or deceive"]])),
        ("#### Proficiency Bonus", "rule", {"id": "check_proficiency", "adds_if_relevant_proficiency": ["skill", "tool"],
                                            "either_skill_suffices": True}),
        ("#### Proficiency Bonus", "md", md("relevant_proficiency", "Is this skill or tool proficiency relevant to "
                                            "the check?", "Add your Proficiency Bonus to an ability check when the GM "
                                            "determines that a skill or tool proficiency is relevant to the check and "
                                            "you have that proficiency.", pages=[6])),
        ("#### Difficulty Class", "md", md("set_dc", "Set the DC of this check.", "The rules provide DCs for certain "
                                           "checks, but the GM ultimately sets them.", pages=[6])),
        ("##### Typical Difficulty Classes", "table", tdata("Typical Difficulty Classes", ["Task Difficulty", "DC"], [
            ["Very easy", "5"], ["Easy", "10"], ["Medium", "15"], ["Hard", "20"], ["Very hard", "25"],
            ["Nearly impossible", "30"]]))]))

    nodes = section("Saving Throws", 3, page=7)
    E.append(sec("saving-throws", "Saving Throws", nodes, "Playing the Game/D20 Tests/Saving Throws", [
        (None, "rule", {"id": "save_required", "made_when": "at_risk", "result_defined_by": "effect"}),
        ("If you don’t want to resist the effect", "rule", {"id": "choose_to_fail", "allowed": True, "roll": False}),
        ("#### Ability Modifier", "table", tdata("Saving Throw Examples", ["Ability", "Make a Save To …"], [
            ["Strength", "Physically resist direct force"], ["Dexterity", "Dodge out of harm’s way"],
            ["Constitution", "Endure a toxic hazard"], ["Intelligence", "Recognize an illusion as fake"],
            ["Wisdom", "Resist a mental assault"], ["Charisma", "Assert your identity"]])),
        ("#### Proficiency Bonus", "rule", {"id": "save_proficiency", "adds_if_proficient": True}),
        ("#### Difficulty Class", "rule", {"id": "save_dc", "set_by": ["effect", "gm"],
                                           "spell_dc": {"var": "spell_save_dc"}})]))

    nodes = section("Attack Rolls", 3, page=7)
    E.append(sec("attack-rolls", "Attack Rolls", nodes, "Playing the Game/D20 Tests/Attack Rolls", [
        (None, "sys", [f"{D20}/3", f"{D20}/4"]),
        ("but the GM might also ask for an attack roll", "md", md("non_combat_attack", "Ask for an attack roll in "
                                                                   "this non-combat situation?", "the GM might also ask "
                                                                   "for an attack roll in other situations, such as an "
                                                                   "archery competition.", pages=[7])),
        ("#### Ability Modifier", "table", tdata("Attack Roll Abilities", ["Ability", "Attack Type"], [
            ["Strength", "Melee attack with a weapon or an Unarmed Strike (see “Rules Glossary”)"],
            ["Dexterity", "Ranged attack with a weapon"],
            ["Varies", "Spell attack (the ability used is determined by the spellcaster’s spellcasting feature, as "
                       "explained in “Spells”)"]])),
        ("Some features let you use different ability modifiers", "ref", ["dnd5e/weapon-property/finesse"]),
        ("#### Proficiency Bonus", "rule", {"id": "attack_proficiency", "adds_for": ["proficient_weapon", "spell"]}),
        ("#### Armor Class", "ref", ["dnd5e/rule/create-your-character"]),
        ("***Calculating AC.***", "sys", [f"{SYS}#/levels/rules/7"]),
        ("***Only One Base AC.***", "rule", {"id": "one_base_ac", "multiple_base_calculations": "choose_one"}),
        ("#### Rolling 20 or 1", "sys", [f"{D20}/5", f"{D20}/6"])]))

    nodes = section("Advantage/Disadvantage", 3, page=7)
    E.append(sec("advantage-disadvantage", "Advantage/Disadvantage", nodes,
                 "Playing the Game/D20 Tests/Advantage/Disadvantage", [
        (None, "desc", None),
        ("You usually acquire Advantage or Disadvantage", "md", md(
            "circumstantial_advantage", "Do the circumstances grant Advantage or impose Disadvantage?",
            "The GM can also decide that circumstances grant Advantage or impose Disadvantage.", pages=[7, 8])),
        ("#### Roll Two D20s", "sys", [f"{D20}/7"]),
        ("#### They Don’t Stack", "sys", [f"{D20}/8", f"{D20}/9"]),
        ("#### Interactions with Rerolls", "sys", [f"{D20}/10"])]))

    nodes = section("Proficiency", 2, page=8, stop_titles=("The Bonus Doesn’t Stack",))
    E.append(sec("playing-the-game-proficiency", "Proficiency", nodes, "Playing the Game/Proficiency", [
        (None, "sys", [f"{SYS}#/proficiency_bonus/by_level", f"{SYS}#/proficiency_bonus/by_challenge_rating"]),
        ("This bonus is applied to a D20 Test", "rule", {"id": "applies_to", "d20_tests_with_proficiency": True,
                                                         "spell_attacks": True, "spell_save_dc": True})]))
    nodes = section("The Bonus Doesn’t Stack", 3, page=8)
    E.append(sec("the-bonus-doesnt-stack", "The Bonus Doesn’t Stack", nodes,
                 "Playing the Game/Proficiency/The Bonus Doesn’t Stack", [
        (None, "sys", [f"{SYS}#/proficiency_bonus/rules/0"]),
        ("Occasionally, a Proficiency Bonus might be multiplied", "sys", [f"{SYS}#/proficiency_bonus/rules/1"]),
        ("Occasionally, a Proficiency Bonus might be multiplied", "ref", [ref_of("Expertise", "rule")])]))
    nodes = section("Skill Proficiencies", 3, page=8, extra=table_nodes("Skills", 9))
    E.append(sec("skill-proficiencies", "Skill Proficiencies", nodes, "Playing the Game/Proficiency/Skill Proficiencies", [
        (None, "ref", ["dnd5e/rule/actions"]),
        ("The GM has the ultimate say", "md", md("skill_relevant", "Is this skill relevant to the check?",
                                                 "The GM has the ultimate say on whether a skill is relevant in a "
                                                 "situation.", pages=[8])),
        ("If a creature is proficient in a skill", "rule", {"id": "skill_proficiency", "adds": "proficiency_bonus",
                                                            "without": "no_bonus_but_may_check"}),
        ("#### Skill List", "sys", [f"{SYS}#/skills"]),
        ("#### Determining Skills", "ref", ["dnd5e/rule/create-your-character", ref_of("Stat Block")]),
        ("##### Skills", "sys", [f"{SYS}#/skills"])]))
    nodes = section("Saving Throw Proficiencies", 3, page=9)
    E.append(sec("saving-throw-proficiencies", "Saving Throw Proficiencies", nodes,
                 "Playing the Game/Proficiency/Saving Throw Proficiencies", [
        (None, "rule", {"id": "save_proficiency", "adds": "proficiency_bonus"}),
        ("Each class gives proficiency", "rule", {"id": "class_saves", "minimum_per_class": 2})]))
    nodes = section("Equipment Proficiencies", 3, page=9)
    E.append(sec("equipment-proficiencies", "Equipment Proficiencies", nodes,
                 "Playing the Game/Proficiency/Equipment Proficiencies", [
        (None, "rule", {"id": "sources", "from": ["class", "background"], "categories": ["weapons", "tools"]}),
        ("**Weapons.**", "rule", {"id": "weapon_proficiency", "adds_to": "attack_roll"}),
        ("**Tools.**", "rule", {"id": "tool_proficiency", "adds_to": "ability_check_using_tool",
                                "with_skill_proficiency_too": "advantage"})]))

    nodes = section("Social Interaction", 2)
    E.append(sec("social-interaction", "Social Interaction", nodes, "Playing the Game/Social Interaction", [
        (None, "rule", {"id": "gm_plays_npcs", "npc_roles": "gm"}),
        ("An NPC’s attitude toward your character", "sys", [f"{SYS}#/registries/attitudes"]),
        ("Social interactions progress in two ways", "desc", None),
        ("The GM uses an NPC’s personality", "md", md("npc_reaction", "How does the NPC react (its personality and "
                                                      "the characters' actions and attitudes)?", "The GM uses an NPC’s "
                                                      "personality and your character’s actions and attitudes to "
                                                      "determine how an NPC reacts.", reason="narrative", pages=[10])),
        ("When interacting with an NPC", "desc", None),
        ("### Ability Checks", "md", md("social_dice", "Should dice determine the NPC's response (Influence action)?",
                                        "there might still be an element of chance if the GM wants dice to play a role "
                                        "in determining an NPC’s response to you. In such situations, the GM will "
                                        "typically ask you to take the Influence action.", pages=[10])),
        ("### Ability Checks", "ref", ["dnd5e/action/influence"]),
        ("Pay attention to your skill proficiencies", "desc", None)]))

    E.append(build("rule", "sidebar-heroic-inspiration", "Heroic Inspiration", sidebar("Heroic Inspiration"), LOT,
                   "Playing the Game/D20 Tests", [
        (None, "ref", [ref_of("Heroic Inspiration")]),
        ("***Only One at a Time.***", "rule", {"id": "only_one", "max": 1, "on_gain_when_full": "may_give_to_pc_without_it"}),
        ("***Gaining Heroic Inspiration.***", "md", md("award_inspiration", "Award Heroic Inspiration?",
                                                       "Your GM can give you Heroic Inspiration for a variety of reasons.",
                                                       pages=[8])),
        ("Other rules might allow your character", "ref", ["dnd5e/species/human"])], facets={"sidebar": True}))
    return E


if __name__ == "__main__":
    extend_registries(REGISTRY, LOT)
    out = glossary_entries() + sections()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
