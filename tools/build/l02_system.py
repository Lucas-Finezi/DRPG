#!/usr/bin/env python3
"""L02 — D&D 5e system definition (knowledge/dnd5e/system.json) and the rule entries L02 owns.

Every rule statement is taken with entrylib.quote(), which fails unless the text occurs
verbatim in the source; every table is read from the extraction, not retyped.

Usage: python3 -I tools/build/l02_system.py
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import (NODES, find, quote, render, section, sidebar, slugify, source, table_rows,  # noqa: E402
                      write_json)

ROOT = Path(__file__).resolve().parents[2]
INV = json.loads((ROOT / "inventory/dnd5e/srd-5.2.1/entries.json").read_text(encoding="utf-8"))["entries"]
LOT = "L02"
SYS_REF = "dnd5e/system/dnd5e"


def inv_page(name, kind=None):
    hits = [e["page"] for e in INV if e["name"] == name and (kind is None or e["kind"] == kind)]
    if len(hits) != 1:
        raise KeyError(f"inventory lookup for {name!r} ({kind}) gave {hits}")
    return [hits[0]]


def caption_rows(caption, page=None, header=None):
    """Data rows of the table under a level-5 caption."""
    i = find(caption, 5, page)
    nodes = []
    for n in NODES[i + 1:]:
        if n.type == "h":
            break
        if n.type == "t" and n.text.startswith("| **") and header and n.cells[0] != header:
            break  # header of a different table printed right after this one
        nodes.append(n)
    return table_rows(nodes, header)


def num(s):
    s = s.replace("−", "-").replace("+", "").replace(",", "").strip()
    return int(s)


def rng(s):
    """'2–3' -> (2, 3); '30' -> (30, 30); 'Up to 4' -> (None, 4)."""
    s = s.strip()
    if s.startswith("Up to "):
        return None, int(s[6:])
    if "–" in s:
        a, b = s.split("–")
        return int(a), int(b)
    return int(s), int(s)


ABILITY_IDS = {"Strength": "str", "Dexterity": "dex", "Constitution": "con",
               "Intelligence": "int", "Wisdom": "wis", "Charisma": "cha"}


def build_system():
    # ---- abilities (Ability Descriptions, p. 5)
    abilities = []
    for name, measures in caption_rows("Ability Descriptions", 5, "Ability"):
        abilities.append({"id": ABILITY_IDS[name], "name": name, "abbreviation": name[:3],
                          "measures": measures, "pages": [5]})
    abbr = {r[0]: r[1] for r in caption_rows_glossary_abbreviations()}
    for a in abilities:  # the glossary abbreviation is "Str." etc.
        a["abbreviation"] = next(k for k, v in abbr.items() if v == a["name"])

    # ---- ability scores (Ability Scores and Ability Modifiers tables, pp. 5-6)
    descriptors = []
    for score, meaning in caption_rows("Ability Scores", 5, "Score"):
        lo, hi = rng(score)
        descriptors.append({"id": f"ability_score.range_{lo}_{hi}", "text": meaning, "pages": [5],
                            "data": {"min": lo, "max": hi}})
    modifiers = []
    for score, mod in caption_rows("Ability Modifiers", 6, "Score"):
        lo, hi = rng(score)
        modifiers.append({"min": lo, "max": hi, "modifier": num(mod)})

    # ---- skills (Skills table, p. 9)
    skills = []
    for name, ability, uses in caption_rows("Skills", 9, "Skill"):
        skills.append({"id": slugify(name).replace("-", "_"), "name": name, "ability": ABILITY_IDS[ability],
                       "example_uses": uses, "pages": [9]})

    # ---- proficiency bonus (Character Advancement p. 23; Proficiency Bonus table p. 8)
    advancement = []
    for level, xp, pb in caption_rows("Character Advancement", 23, "Level"):
        advancement.append({"level": int(level), "xp": num(xp), "proficiency_bonus": num(pb)})
    by_cr = []
    for level_or_cr, bonus in caption_rows("Proficiency Bonus", 8, "Level or CR"):
        lo, hi = rng(level_or_cr)
        by_cr.append({"min": 0 if lo is None else lo, "max": hi, "bonus": num(bonus)})

    # ---- languages (Standard Languages / Rare Languages, p. 20)
    languages = []
    for roll, name in caption_rows("Standard Languages", 20, "1d12"):
        languages.append({"id": slugify(name).replace("-", "_"), "name": name, "category": "standard",
                          "roll": roll, "pages": [20]})
    rare = []
    for row in caption_rows("Rare Languages", 20, "Language"):
        rare += [c for c in row if c]
    i = find("Rare Languages", 5, 20)
    rare += [n.text for n in NODES[i + 1:i + 8] if n.type == "p" and re.fullmatch(r"[A-Z][a-z]+", n.text)]
    primordial_note = quote("Primordial includes the Aquan, Auran, Ignan, and Terran dialects. Creatures that know "
                            "one of these dialects can communicate with those that know a different one.")
    for name in rare:
        clean = name.rstrip("\\*").rstrip("*")
        lang = {"id": slugify(clean).replace("-", "_"), "name": clean, "category": "rare", "pages": [20]}
        if clean == "Primordial":
            lang["note"] = primordial_note["text"]
        languages.append(lang)
    languages.sort(key=lambda x: (x["category"] != "standard", x["name"]))

    # ---- currency (Coin Values, p. 89)
    currency = []
    for coin, value in caption_rows("Coin Values", 89, "Coin"):
        m = re.match(r"(.+) \((\w+)\)", coin)
        gp = eval_fraction(value)
        currency.append({"id": m.group(2).lower(), "name": m.group(1), "abbreviation": m.group(2),
                         "value_in_cp": round(gp * 100, 6), "pages": [89]})

    system = {
        "$schema": "../../schema/system.schema.json",
        "id": "dnd5e",
        "ref": SYS_REF,
        "name": "Dungeons & Dragons fifth edition — System Reference Document 5.2.1",
        "schema_version": "1.0",
        "source": source([1, 5, 6, 7, 8, 9, 10, 13, 19, 20, 21, 22, 23, 24, 89, 176, 192], "System", LOT),
        "core_rules": core_rules(),
        "core_die": {
            "die": "d20",
            "rules": [
                quote("When the outcome of an action is uncertain, the game uses a d20 roll to determine success "
                      "or failure. These rolls are called D20 Tests, and they come in three kinds: ability checks, "
                      "saving throws, and attack rolls.", "d20_test.kinds",
                      {"kinds": ["ability_check", "saving_throw", "attack_roll"]}),
                quote("Roll 1d20. You always want to roll high.", "d20_test.step_roll", {"roll": "1d20"}),
                quote("Add Modifiers. Add these modifiers to the number rolled on the d20:", "d20_test.step_modifiers",
                      {"modifiers": ["ability_modifier", "proficiency_bonus_if_relevant",
                                     "circumstantial_bonuses_and_penalties"]}),
                quote("If the total of the d20 and its modifiers equals or exceeds the target number, the D20 Test "
                      "succeeds. Otherwise, it fails.", "d20_test.success", {"comparison": ">="}),
                quote("The target number for an ability check or a saving throw is called a Difficulty Class (DC). "
                      "The target number for an attack roll is called an Armor Class (AC)", "d20_test.target_numbers",
                      {"ability_check": "dc", "saving_throw": "dc", "attack_roll": "ac"}),
                quote("If you roll a 20 on the d20 (called a “natural 20”) for an attack roll, the attack hits "
                      "regardless of any modifiers or the target’s AC. This is called a Critical Hit",
                      "attack_roll.natural_20", {"roll": "attack_roll", "natural": 20, "result": "hit",
                                                 "critical_hit": True}),
                quote("If you roll a 1 on the d20 (a “natural 1”) for an attack roll, the attack misses regardless "
                      "of any modifiers or the target’s AC.", "attack_roll.natural_1",
                      {"roll": "attack_roll", "natural": 1, "result": "miss"}),
                quote("When a roll has either Advantage or Disadvantage, roll a second d20 when you make the roll. "
                      "Use the higher of the two rolls if you have Advantage, and use the lower roll if you have "
                      "Disadvantage.", "advantage.roll", {"advantage": "highest_of_2d20",
                                                          "disadvantage": "lowest_of_2d20"}),
                quote("If multiple situations affect a roll and they all grant Advantage on it, you still roll only "
                      "two d20s. Similarly, if multiple situations impose Disadvantage on a roll, you roll only two "
                      "d20s.", "advantage.no_stacking", {"stacks": False}),
                quote("If circumstances cause a roll to have both Advantage and Disadvantage, the roll has neither "
                      "of them, and you roll one d20. This is true even if multiple circumstances impose "
                      "Disadvantage and only one grants Advantage or vice versa.", "advantage.cancel",
                      {"both_present": "neither"}),
                quote("When you have Advantage or Disadvantage and something in the game lets you reroll or replace "
                      "the d20, you can reroll or replace only one die, not both. You choose which one.",
                      "advantage.reroll", {"reroll_dice": 1, "chooser": "roller"}),
            ],
        },
        "abilities": abilities,
        "ability_scores": {
            "min": 1, "max": 30, "descriptors": descriptors, "modifier_table": modifiers, "pages": [5, 6],
        },
        "skills": skills,
        "proficiency_bonus": {
            "by_level": {str(a["level"]): a["proficiency_bonus"] for a in advancement},
            "by_challenge_rating": by_cr,
            "rules": [
                quote("Your Proficiency Bonus can’t be added to a die roll or another number more than once.",
                      "proficiency_bonus.once", {"max_additions": 1}),
                quote("Whenever the bonus is used, it can be multiplied only once and divided only once.",
                      "proficiency_bonus.multiply_divide_once", {"max_multiplications": 1, "max_divisions": 1}),
            ],
            "pages": [8, 23],
        },
        "levels": {
            "min": 1, "max": 20, "advancement": advancement,
            "tiers": [
                quote("In tier 1, characters are apprentice adventurers", "tier_1", {"min_level": 1, "max_level": 4}),
                quote("In tier 2, characters are full-fledged adventurers.", "tier_2", {"min_level": 5, "max_level": 10}),
                quote("In tier 3, characters have reached a level of power that makes them special among adventurers.",
                      "tier_3", {"min_level": 11, "max_level": 16}),
                quote("At tier 4, characters achieve the pinnacle of their class features, becoming heroic archetypes.",
                      "tier_4", {"min_level": 17, "max_level": 20}),
            ],
            "rules": level_rules(),
            "pages": [23, 24],
        },
        "action_economy": action_economy(),
        "initiative": {
            "check": "dex",
            "rules": [
                quote("When combat starts, every participant rolls Initiative; they make a Dexterity check that "
                      "determines their place in the Initiative order.", "initiative.check", {"ability": "dex"}),
                quote("The GM rolls for monsters. For a group of identical creatures, the GM makes a single roll, "
                      "so each member of the group has the same Initiative.", "initiative.groups",
                      {"identical_creatures": "single_roll"}),
                quote("If a combatant is surprised by combat starting, that combatant has Disadvantage on their "
                      "Initiative roll.", "initiative.surprise", {"surprised": "disadvantage"}),
                quote("The GM ranks the combatants, from highest to lowest Initiative. This is the order in which "
                      "they act during each round. The Initiative order remains the same from round to round.",
                      "initiative.order", {"sort": "descending", "fixed": True}),
                quote("If a tie occurs, the GM decides the order among tied monsters, and the players decide the "
                      "order among tied characters. The GM decides the order if the tie is between a monster and a "
                      "player character.", "initiative.ties",
                      {"monsters": "gm", "player_characters": "players", "mixed": "gm"}),
            ],
            "pages": [13],
        },
        "rests": [
            {"id": "short_rest", "name": "Short Rest", "ref": "dnd5e/rule/short-rest",
             "minimum_duration": {"kind": "hours", "amount": 1, "text": "1-hour period"}, "pages": inv_page("Short Rest")},
            {"id": "long_rest", "name": "Long Rest", "ref": "dnd5e/rule/long-rest",
             "minimum_duration": {"kind": "hours", "amount": 8, "text": "at least 8 hours"}, "pages": inv_page("Long Rest")},
        ],
        "languages": languages,
        "currency": currency,
        "units": {
            "distance": {"unit": "foot", "pages": inv_page("Speed")},
            "long_distance": {"unit": "mile", "pages": [12]},
            "weight": {"unit": "pound", "conversions": {"coins_per_pound": 50}, "pages": [89]},
        },
        "time": {
            "round_seconds": 6,
            "derived": {"rounds_per_minute": 10},
            "rules": [quote("A round represents about 6 seconds in the game world.", "time.round",
                            {"seconds": 6, "derives": {"rounds_per_minute": "60 seconds / 6 seconds per round"}})],
        },
        "registries": registries(),
        "abbreviations": abbr,
    }
    return system


def eval_fraction(s):
    s = s.strip()
    if "/" in s:
        a, b = s.split("/")
        return int(a) / int(b)
    return float(s)


def caption_rows_glossary_abbreviations():
    """Rows of the abbreviations list in Glossary Conventions (p. 176): table rows plus the
    rows the layout printed as paragraphs ("**Con.** Constitution")."""
    i = find("Glossary Conventions", 2)
    j = find("Rules Definitions", 2)
    rows = []
    started = False
    for n in NODES[i:j]:
        if n.type == "p" and n.text.startswith("**Abbreviations.**"):
            started = True
            continue
        if not started:
            continue
        if n.type == "t":
            rows.append((n.cells[0], n.cells[1]))
        elif n.type == "p":
            m = re.match(r"^\*\*(.+?)\*\* (.+)$", n.text)
            if m:
                rows.append((m.group(1), m.group(2)))
    return rows


def core_rules():
    return [
        quote("General rules govern each part of the game. For example, the combat rules tell you that melee attacks "
              "use Strength and ranged attacks use Dexterity. That’s a general rule, and a general rule is in effect "
              "as long as something in the game doesn’t explicitly say otherwise.", "general_rules"),
        quote("When an exception and a general rule disagree, the exception wins.", "exceptions_supersede",
              {"precedence": ["specific_exception", "general_rule"]}),
        quote("Whenever you divide or multiply a number in the game, round down if you end up with a fraction, even "
              "if the fraction is one-half or greater. Some rules make an exception and tell you to round up.",
              "round_down", {"default_rounding": "down"}),
        quote("If two or more things happen at the same time on a turn, the person at the game table—player or "
              "GM—whose turn it is decides the order in which those things happen.", "simultaneous_effects",
              {"orderer": "controller_of_current_turn"}),
        quote("If a rule says you can use something a certain number of times per day, that means you must finish "
              "a Long Rest to use it again after you run out of uses.", "per_day",
              {"per_day_recovers_on": "long_rest_finish"}),
        quote("A creature is your ally if it is a member of your adventuring party, your friend, on your side in "
              "combat, or a creature that the rules or the GM designates as your ally.", "ally",
              {"relationship": "ally", "designated_by": ["party", "rules", "gm"]}),
        quote("A creature is your enemy if it fights against you in combat, actively works to harm you, or is "
              "designated as your enemy by the rules or GM.", "enemy",
              {"relationship": "enemy", "designated_by": ["combat_side", "rules", "gm"]}),
        quote("A monster is a creature controlled by the GM, even if the creature is benevolent.", "monster",
              {"controller": "gm"}),
        quote("A player character is a character controlled by a player.", "player_character",
              {"controller": "player"}),
        quote("A nonplayer character (NPC) is a monster that has a personal name and a distinct personality.",
              "nonplayer_character", {"is_a": "monster"}),
        quote("An effect is magical if it is created by a spell, a magic item, or a phenomenon that a rule labels "
              "as magical.", "magical_effect", {"sources": ["spell", "magic_item", "rule_labelled_magical"]}),
        quote("Unless that description says otherwise, any ongoing effects on you—conditions, spells, curses, and "
              "the like—carry over from one form to the other. You revert to your true form if you die.",
              "shape_shifting", {"ongoing_effects_carry_over": True, "revert_on_death": True}),
        quote("Unless a rule states otherwise, the contacted creature doesn’t need to share a language with the "
              "telepath to understand this communication, but the contacted creature must be able to understand at "
              "least one language or be telepathic itself to understand.", "telepathy.language",
              {"shared_language_required": False, "target_needs": "any_language_or_telepathy"}),
        quote("A telepath doesn’t need to see a contacted creature, and the telepath can start or end the telepathic "
              "contact at any time (no action required). Telepathic contact can’t be initiated and is immediately "
              "broken if either the telepath or the other creature has the Incapacitated condition. Telepathic "
              "contact is also broken if the contacted creature is no longer within the telepathy’s range or if "
              "the telepath contacts a different creature within range.", "telepathy.contact",
              {"sight_required": False, "action_cost": "none",
               "broken_by": ["incapacitated_either", "out_of_range", "contacts_other_creature"]}),
        quote("A creature without telepathy can receive telepathic messages but can’t initiate a telepathic "
              "conversation. Once a telepathic conversation starts, the non-telepath can communicate mentally to "
              "the telepath until the telepathic connection ends.", "telepathy.non_telepath",
              {"non_telepath_can_initiate": False, "non_telepath_can_reply": True}),
        quote("If you teleport, you disappear and reappear elsewhere instantly, without moving through the "
              "intervening space. This transportation doesn’t expend movement unless a rule tells you otherwise, "
              "and teleportation never provokes Opportunity Attacks.", "teleportation.movement",
              {"expends_movement": False, "provokes_opportunity_attacks": False}),
        quote("When you teleport, all the equipment you’re wearing and carrying teleports with you. If you’re "
              "touching another creature when you teleport, that creature doesn’t teleport with you unless the "
              "teleportation effect says otherwise.", "teleportation.passengers",
              {"carried_equipment": True, "touched_creatures": False}),
        quote("If the destination space of your teleportation is occupied by another creature or blocked by a "
              "solid obstacle, you instead appear in the nearest unoccupied space of your choice.",
              "teleportation.blocked", {"blocked_destination": "nearest_unoccupied_space_of_choice"}),
        quote("If an illusion manifests in space, the illusion is insubstantial and weightless, yet it seems to be "
              "affected by the environment as if the illusion were real unless the effect that created it "
              "specifies otherwise.", "illusions", {"insubstantial": True, "weightless": True}),
        quote("A stat block usually provides both a static number and a die expression for each instance of damage. "
              "For example, an attack might deal 4 (1d4 + 2) damage on a hit. The GM determines whether you use the "
              "static number or the die expression in parentheses; you don’t use both.", "stat_block.damage_notation",
              {"modes": ["static", "dice"], "chooser": "gm"}),
        quote("An attack is against one target unless its entry says otherwise.", "stat_block.attack_targets",
              {"default_targets": 1}),
    ]


def level_rules():
    return [
        quote("When your XP total equals or exceeds a number in the Experience Points column, you reach the "
              "corresponding level.", "level.threshold", {"comparison": ">="}),
        quote("Each time you gain a level, you gain an additional Hit Die. Roll that die, add your Constitution "
              "modifier to the roll, and add the total (minimum of 1) to your Hit Point maximum. Instead of rolling, "
              "you can use the fixed value shown in the Fixed Hit Points by Class table.", "level.hit_points",
              {"hit_dice_gained": 1, "hp_gain": "roll_hit_die_plus_con_mod_min_1_or_fixed", "minimum": 1}),
        quote("When your Constitution modifier increases by 1, your Hit Point maximum increases by 1 for each level "
              "you have attained.", "level.con_retroactive", {"retroactive": True}),
        quote("If you choose a feat that increases one or more of your ability scores, your ability modifier also "
              "changes if the new score is an even number.", "level.ability_modifier_change"),
        quote("You begin with the minimum amount of XP required to reach your starting level.",
              "start_higher.xp", {"starting_xp": "threshold_of_starting_level"}),
        quote("A level 1 character has 0 XP.", "level.start_xp", {"level": 1, "xp": 0}),
        quote("At level 1, your character has 1 Hit Die.", "level.start_hit_dice", {"level": 1, "hit_dice": 1}),
        quote("Without armor or a shield, your base Armor Class is 10 plus your Dexterity modifier.",
              "base_ac", {"formula": {"op": "add", "args": [10, {"var": "ability_mod.dex"}]}}),
        quote("Passive Perception = 10 + Wisdom (Perception) check modifier", "passive_perception",
              {"formula": {"op": "add", "args": [10, {"var": "check_mod.wis.perception"}]}}),
        quote("Spell save DC = 8 + spellcasting ability modifier + Proficiency Bonus", "spell_save_dc",
              {"formula": {"op": "add", "args": [8, {"var": "spellcasting_mod"}, {"var": "proficiency_bonus"}]}}),
        quote("Spell attack bonus = spellcasting ability modifier + Proficiency Bonus", "spell_attack_bonus",
              {"formula": {"op": "add", "args": [{"var": "spellcasting_mod"}, {"var": "proficiency_bonus"}]}}),
        quote("Melee attack bonus = Strength modifier + Proficiency Bonus", "melee_attack_bonus",
              {"formula": {"op": "add", "args": [{"var": "ability_mod.str"}, {"var": "proficiency_bonus"}]}}),
        quote("Ranged attack bonus = Dexterity modifier + Proficiency Bonus", "ranged_attack_bonus",
              {"formula": {"op": "add", "args": [{"var": "ability_mod.dex"}, {"var": "proficiency_bonus"}]}}),
    ]


def action_economy():
    return [
        {"id": "action", "name": "Action", "per": "turn", "count": 1, "refreshes_on": "turn_start",
         "rules": [quote("On your turn, you can move a distance up to your Speed and take one action.",
                         "turn.action_and_move"),
                   quote("You can take only one action at a time.", "action.one_at_a_time")], "pages": [9, 13]},
        {"id": "bonus_action", "name": "Bonus Action", "per": "turn", "count": 1, "refreshes_on": "turn_start",
         "rules": [quote("You can take a Bonus Action only when a special ability, a spell, or another feature of "
                         "the game states that you can do something as a Bonus Action. You otherwise don’t have a "
                         "Bonus Action to take.", "bonus_action.granted_only"),
                   quote("You can take only one Bonus Action on your turn", "bonus_action.one_per_turn"),
                   quote("Anything that deprives you of your ability to take actions also prevents you from taking "
                         "a Bonus Action.", "bonus_action.deprived")], "pages": [10]},
        {"id": "reaction", "name": "Reaction", "per": "round", "count": 1, "refreshes_on": "turn_start",
         "rules": [quote("When you take a Reaction, you can’t take another one until the start of your next turn.",
                         "reaction.refresh"),
                   quote("In terms of timing, a Reaction takes place immediately after its trigger unless the "
                         "Reaction’s description says otherwise.", "reaction.timing")], "pages": [10]},
        {"id": "movement", "name": "Movement", "per": "turn", "refreshes_on": "turn_start",
         "rules": [quote("You decide whether to move first or take your action first.", "turn.order_free")],
         "pages": [13]},
        {"id": "object_interaction", "name": "Interacting with Things", "per": "turn", "count": 1,
         "refreshes_on": "turn_start",
         "rules": [quote("You can interact with one object or feature of the environment for free, during either "
                         "your move or action.", "object_interaction.free"),
                   quote("If you want to interact with a second object, you need to take the Utilize action.",
                         "object_interaction.second")], "pages": [13]},
        {"id": "free", "name": "Communicating", "per": "turn",
         "rules": [quote("You can communicate however you are able—through brief utterances and gestures—as you "
                         "take your turn. Doing so uses neither your action nor your move.", "communicating")],
         "pages": [13]},
    ]


def reg(items):
    return [{k: v for k, v in i.items() if v is not None} for i in items]


def registries():
    g = inv_page
    creature_types = ["Aberration", "Beast", "Celestial", "Construct", "Dragon", "Elemental", "Fey", "Fiend",
                      "Giant", "Humanoid", "Monstrosity", "Ooze", "Plant", "Undead"]
    sizes = caption_rows("Creature Size and Space", 14, "Size")
    damage = caption_rows("Damage Types", None, "Type")
    alignments = [("lawful_good", "Lawful Good (LG)"), ("neutral_good", "Neutral Good (NG)"),
                  ("chaotic_good", "Chaotic Good (CG)"), ("lawful_neutral", "Lawful Neutral (LN)"),
                  ("neutral", "Neutral (N)"), ("chaotic_neutral", "Chaotic Neutral (CN)"),
                  ("lawful_evil", "Lawful Evil (LE)"), ("neutral_evil", "Neutral Evil (NE)"),
                  ("chaotic_evil", "Chaotic Evil (CE)")]
    for _, label in alignments:  # each label is printed as a bold-italic heading on p. 21-22
        quote(label)
    return {
        "variables": reg([
            {"id": "ability_score", "description": "A creature's score in an ability.", "params": ["ability"], "type": "number", "pages": [5]},
            {"id": "ability_mod", "description": "The modifier derived from an ability score (Ability Modifiers table).", "params": ["ability"], "type": "number", "pages": [5, 6]},
            {"id": "proficiency_bonus", "description": "Proficiency Bonus by character level or Challenge Rating.", "type": "number", "pages": [8]},
            {"id": "level", "description": "Character level.", "type": "number", "pages": [23]},
            {"id": "class_level", "description": "Levels the character has in one class.", "params": ["class"], "type": "number", "pages": [24]},
            {"id": "xp", "description": "Experience Points total.", "type": "number", "pages": [23]},
            {"id": "cr", "description": "Challenge Rating of a monster.", "type": "number", "pages": g("Challenge Rating")},
            {"id": "speed", "description": "Speed in feet for a movement mode.", "params": ["movement_mode"], "type": "number", "pages": g("Speed")},
            {"id": "hp_max", "description": "Hit Point maximum.", "type": "number", "pages": [22]},
            {"id": "check_mod", "description": "Total modifier of an ability check (ability, optional skill).", "params": ["ability", "skill"], "type": "number", "pages": [22]},
            {"id": "spellcasting_mod", "description": "Spellcasting ability modifier of the feature that grants the spell.", "type": "number", "pages": [23]},
            {"id": "spell_save_dc", "description": "8 + spellcasting ability modifier + Proficiency Bonus.", "type": "number", "pages": [23]},
            {"id": "spell_attack_bonus", "description": "Spellcasting ability modifier + Proficiency Bonus.", "type": "number", "pages": [23]},
            {"id": "spell_slot_level", "description": "Level of the spell slot used to cast the current spell.", "type": "number", "pages": [104]},
        ]),
        "stats": reg([
            {"id": "ac", "name": "Armor Class", "description": "Target number for attack rolls against the creature.", "pages": [6, 7]},
            {"id": "attack_roll", "description": "Bonus to attack rolls (optionally by attack kind).", "params": ["attack_kind"], "pages": [7]},
            {"id": "damage_roll", "description": "Bonus to damage rolls.", "pages": g("Damage Roll")},
            {"id": "saving_throw", "description": "Bonus to saving throws (optionally one ability).", "params": ["ability"], "pages": [7]},
            {"id": "ability_check", "description": "Bonus to ability checks (optionally one ability or skill).", "params": ["ability", "skill"], "pages": [6]},
            {"id": "initiative", "description": "Initiative modifier.", "pages": [13]},
            {"id": "hp_max", "description": "Hit Point maximum.", "pages": [22]},
            {"id": "speed", "description": "Speed (optionally one movement mode).", "params": ["movement_mode"], "pages": g("Speed")},
            {"id": "passive_perception", "description": "10 + Wisdom (Perception) check modifier.", "pages": [22]},
            {"id": "spell_save_dc", "description": "Spell save DC.", "pages": [23]},
            {"id": "spell_attack_bonus", "description": "Spell attack bonus.", "pages": [23]},
            {"id": "damage_taken", "description": "Damage the creature takes (param: the source's ref slug, e.g. a spell).", "params": ["source"], "pages": [162]},
        ]),
        "rolls": reg([
            {"id": "d20_test", "description": "Any D20 Test: ability check, saving throw or attack roll.", "pages": [6]},
            {"id": "ability_check", "description": "Ability check (optionally one ability or skill).", "params": ["ability", "skill"], "pages": [6]},
            {"id": "saving_throw", "description": "Saving throw (optionally one ability).", "params": ["ability"], "pages": [7]},
            {"id": "attack_roll", "description": "Attack roll (optionally by attack kind).", "params": ["attack_kind"], "pages": [7]},
            {"id": "damage_roll", "description": "Damage roll.", "pages": g("Damage Roll")},
            {"id": "initiative", "description": "Initiative roll (a Dexterity check).", "pages": [13]},
            {"id": "hit_point_die", "description": "Roll of a Hit Point Die.", "pages": [23]},
        ]),
        "events": reg([
            {"id": "turn_start", "description": "Start of a creature's turn.", "type": "event", "pages": [10, 13]},
            {"id": "turn_end", "description": "End of a creature's turn.", "type": "event", "pages": [13]},
            {"id": "round_end", "description": "End of a round (everyone has taken a turn).", "type": "event", "pages": [13]},
            {"id": "initiative_rolled", "description": "Initiative is rolled (combat starts).", "type": "event", "pages": [13]},
            {"id": "d20_rolled", "description": "Immediately after a die is rolled.", "type": "event", "pages": [8]},
            {"id": "short_rest_finished", "description": "A Short Rest is finished.", "type": "event", "pages": g("Short Rest")},
            {"id": "long_rest_finished", "description": "A Long Rest is finished.", "type": "event", "pages": g("Long Rest")},
            {"id": "level_gained", "description": "The character gains a level.", "type": "event", "pages": [23]},
            {"id": "hit_by_attack_roll", "description": "The creature is hit by an attack roll.", "type": "event", "pages": [161]},
            {"id": "targeted_by_spell", "description": "The creature is targeted by a spell (param: spell ref slug).", "params": ["spell"], "type": "event", "pages": [161]},
        ]),
        "predicates": reg([
            {"id": "has_condition", "description": "The creature has the condition (param: condition slug).", "params": ["condition"], "type": "predicate", "pages": g("Condition", "rule")},
            {"id": "wearing_armor", "description": "The creature wears armor of the category (param: light, medium, heavy).", "params": ["category"], "type": "predicate", "pages": [92]},
            {"id": "creature_type", "description": "The creature is of the type (param: creature type id).", "params": ["creature_type"], "type": "predicate", "pages": g("Creature Type", "rule")},
            {"id": "can_see", "description": "The acting creature can see the target.", "type": "predicate", "pages": [14]},
            {"id": "is_ally", "description": "The target is an ally of the acting creature.", "type": "predicate", "pages": g("Ally")},
            {"id": "is_enemy", "description": "The target is an enemy of the acting creature.", "type": "predicate", "pages": g("Enemy")},
        ]),
        "frequencies": reg([
            {"id": "turn", "description": "Once per turn.", "pages": [13]},
            {"id": "round", "description": "Once per round.", "pages": [13]},
            {"id": "short_rest", "description": "Recovers when a Short or Long Rest is finished.", "pages": g("Short Rest")},
            {"id": "long_rest", "description": "Recovers when a Long Rest is finished.", "pages": g("Long Rest")},
            {"id": "day", "description": "Per day: recovers when a Long Rest is finished.", "pages": g("Per Day")},
            {"id": "dawn", "description": "Recovers at the next dawn.", "pages": [206]},
        ]),
        "damage_types": reg([{"id": slugify(t).replace("-", "_"), "name": t, "description": ex,
                              "pages": g("Damage Types", "rule")} for t, ex in damage]),
        "sizes": reg([{"id": slugify(s).replace("-", "_"), "name": s, "description": f"Space {feet}; {squares}.",
                       "pages": [14]} for s, feet, squares in sizes]),
        "creature_types": reg([{"id": t.lower(), "name": t, "description": "Creature type.",
                                "pages": g("Creature Type", "rule")} for t in creature_types]),
        "area_shapes": reg([{"id": shape.lower(), "name": shape, "description": "Area of effect shape.",
                             "ref": f"dnd5e/area/{shape.lower()}", "pages": g(shape, "area")}
                            for shape in ("Cone", "Cube", "Cylinder", "Emanation", "Line", "Sphere")]),
        "senses": reg([{"id": s.lower(), "name": s, "description": "Special sense.",
                        "ref": f"dnd5e/rule/{s.lower()}", "pages": g(s, "rule")}
                       for s in ("Blindsight", "Darkvision", "Tremorsense", "Truesight")]),
        "movement_modes": reg([
            {"id": "walk", "name": "Speed", "description": "Normal Speed.", "ref": "dnd5e/rule/speed", "pages": g("Speed")},
            {"id": "burrow", "name": "Burrow Speed", "description": "Burrow Speed.", "ref": "dnd5e/rule/burrow-speed", "pages": g("Burrow Speed")},
            {"id": "climb", "name": "Climb Speed", "description": "Climb Speed.", "ref": "dnd5e/rule/climb-speed", "pages": g("Climb Speed")},
            {"id": "fly", "name": "Fly Speed", "description": "Fly Speed.", "ref": "dnd5e/rule/fly-speed", "pages": g("Fly Speed")},
            {"id": "swim", "name": "Swim Speed", "description": "Swim Speed.", "ref": "dnd5e/rule/swim-speed", "pages": g("Swim Speed")},
        ]),
        "alignments": reg([{"id": i, "name": label, "description": "Alignment.", "pages": [21, 22]}
                           for i, label in alignments]
                          + [{"id": "unaligned", "name": "Unaligned", "description": "Creatures that lack the capacity "
                              "for rational thought don't have alignments.", "pages": [22]}]),
    }




# ================================================================ L02 rule entries

from entrylib import entry, md, write_entry, sidebar as sidebar_nodes, table_nodes  # noqa: E402

SYS = None


def S(pointer):
    return f"{SYS_REF}#{pointer}"


def R(path, rid):
    """Pointer to the item with id `rid` in the list at `path` of system.json."""
    cur = SYS
    for part in path.strip("/").split("/"):
        cur = cur[int(part)] if isinstance(cur, list) else cur[part]
    idx = next(i for i, x in enumerate(cur) if x.get("id") == rid)
    return S(f"{path}/{idx}")


def inv_ref(name, kind=None):
    hits = [e["ref"] for e in INV if e["name"] == name and (kind is None or e["kind"] == kind)]
    if len(hits) != 1:
        raise KeyError(f"no unique inventory ref for {name!r}: {hits}")
    return hits[0]


SEE_ALSO_SECTIONS = {  # "See also" targets that are chapter sections, by the rule-entry slug convention
    "Playing the Game (The Six Abilities)": "dnd5e/rule/the-six-abilities",
    "Character Creation (Create Your Character)": "dnd5e/rule/create-your-character",
    "Character Creation": "dnd5e/rule/create-your-character",
    "Level Advancement": "dnd5e/rule/level-advancement",
    "Playing the Game (Combat)": "dnd5e/rule/combat",
    "Gameplay Toolbox (Combat Encounters)": "dnd5e/rule/combat-encounters",
    "Playing the Game (Proficiency)": "dnd5e/rule/playing-the-game-proficiency",
    "Playing the Game (Actions)": "dnd5e/rule/actions",
    "Monsters": "dnd5e/rule/monsters",
}


def glossary_entry(name, plan, **kw):
    page = inv_page(name, "rule")[0]
    nodes = section(name, 4, page)
    return entry("rule", slugify(name), name, nodes, LOT, f"Rules Glossary/Rules Definitions/{name}", plan,
                 facets={"glossary": True}, **kw)


def build_entries(system):
    global SYS
    SYS = system
    E = []
    cr = lambda rid: R("/core_rules", rid)  # noqa: E731

    # ---------------------------------------------------------------- glossary (27)
    E.append(glossary_entry("Ability Score and Modifier", [
        (None, "structured", [S("/abilities"), S("/ability_scores/modifier_table")]),
        ("*See also*", "shared_rule", [SEE_ALSO_SECTIONS["Playing the Game (The Six Abilities)"]])]))
    E.append(glossary_entry("Adventure", [
        (None, "descriptive", None), ("*See also*", "shared_rule", [inv_ref("Encounter")])]))
    E.append(glossary_entry("Alignment", [
        (None, "structured", [S("/registries/alignments")]),
        ("*See also*", "shared_rule", [SEE_ALSO_SECTIONS["Character Creation (Create Your Character)"]])]))
    E.append(glossary_entry("Ally", [(None, "structured", [cr("ally")])]))
    E.append(glossary_entry("Campaign", [
        (None, "descriptive", None), ("*See also*", "shared_rule", [inv_ref("Adventure")])]))
    E.append(glossary_entry("Challenge Rating", [
        (None, "structured", [S("/registries/variables/6"), S("/proficiency_bonus/by_challenge_rating")]),
        ("Compare a monster’s CR", "shared_rule", [SEE_ALSO_SECTIONS["Gameplay Toolbox (Combat Encounters)"]]),
        ("*See also*", "shared_rule", [inv_ref("Stat Block")])]))
    E.append(glossary_entry("Character Sheet", [
        (None, "descriptive", None), ("*See also*", "shared_rule", [SEE_ALSO_SECTIONS["Character Creation"]])]))
    E.append(glossary_entry("Creature", [
        (None, "descriptive", None), ("*See also*", "shared_rule", [inv_ref("Creature Type", "rule")])]))
    E.append(glossary_entry("Creature Type", [
        (None, "structured", [S("/registries/creature_types")]),
        ("The types don’t have rules themselves", "structured", [S("/registries/predicates/2")])]))
    E.append(glossary_entry("Enemy", [(None, "structured", [cr("enemy")])]))
    E.append(glossary_entry("Experience Points", [
        (None, "structured", [S("/levels/advancement"), R("/levels/rules", "level.threshold")]),
        ("*See also*", "shared_rule", [SEE_ALSO_SECTIONS["Level Advancement"]])]))
    E.append(glossary_entry("Illusions", [
        (None, "descriptive", None),
        ("If an illusion manifests in space", "structured", [cr("illusions")]),
        ("For example, a visual illusion", "descriptive", None)]))
    E.append(glossary_entry("Magical Effect", [(None, "structured", [cr("magical_effect")])]))
    E.append(glossary_entry("Monster", [
        (None, "structured", [cr("monster")]),
        ("*See also*", "shared_rule", [inv_ref("Creature"), inv_ref("Nonplayer Character")])]))
    E.append(glossary_entry("Nonplayer Character", [
        (None, "structured", [cr("nonplayer_character")]),
        ("*See also*", "shared_rule", [inv_ref("Monster")])]))
    E.append(glossary_entry("Object", [
        (None, "descriptive", None), ("*See also*", "shared_rule", [inv_ref("Breaking Objects")])]))
    E.append(glossary_entry("Per Day", [(None, "structured", [cr("per_day"), S("/registries/frequencies/4")])]))
    E.append(glossary_entry("Player Character", [
        (None, "structured", [cr("player_character")]),
        ("*See also*", "shared_rule", [SEE_ALSO_SECTIONS["Character Creation"]])]))
    E.append(glossary_entry("Possession", [
        (None, "master_decision", ["md:possession"]),
        ("Possession can be prevented", "shared_rule", ["dnd5e/spell/protection-from-evil-and-good",
                                                        "dnd5e/spell/dispel-evil-and-good"])],
        master_decisions=[md("possession", "A possessing effect defines how the possession operates: apply "
                             "the specific effect's rules for this possession.",
                             "Some effects cause a creature to be possessed by another creature or entity. A "
                             "possessing effect defines how the possession operates.", reason="not_automatable",
                             pages=inv_page("Possession"))]))
    E.append(glossary_entry("Round Down", [(None, "structured", [cr("round_down")])]))
    E.append(glossary_entry("Shape-Shifting", [
        (None, "shared_rule", ["dnd5e/feature/druid-wild-shape", "dnd5e/spell/polymorph"]),
        ("Unless that description says otherwise", "structured", [cr("shape_shifting")])]))
    E.append(glossary_entry("Simultaneous Effects", [(None, "structured", [cr("simultaneous_effects")])]))
    E.append(glossary_entry("Size", [
        (None, "structured", [S("/registries/sizes")]),
        ("An object’s size affects its Hit Points.", "shared_rule", [inv_ref("Breaking Objects")]),
        ("*See also*", "shared_rule", [inv_ref("Breaking Objects"), SEE_ALSO_SECTIONS["Playing the Game (Combat)"]])]))
    E.append(glossary_entry("Speed", [
        (None, "structured", [S("/registries/movement_modes/0"), S("/units/distance")]),
        ("*See also*", "shared_rule", [inv_ref("Climbing"), inv_ref("Crawling"), inv_ref("Flying"),
                                       inv_ref("Jumping"), inv_ref("Swimming"),
                                       SEE_ALSO_SECTIONS["Playing the Game (Combat)"]]),
        ("***Special Speeds.***", "structured", ["/data/rules/0"]),
        ("***Changes to Your Speeds.***", "structured", ["/data/rules/1"])],
        data={"rules": [
            {"id": "special_speeds.switch", "mechanic": {"choose_speed_per_move": True, "switch_during_move": True,
                                                          "remaining": "new_speed_minus_distance_moved",
                                                          "zero_or_less": "cannot_use_new_speed_this_move"}},
            {"id": "special_speeds.changes", "mechanic": {"special_speeds_follow_speed_changes": True,
                                                           "applies_to": ["increase", "decrease", "halve",
                                                                          "set_to_zero"]}}]}))
    stat_plan = [(None, "descriptive", None)]
    for label in ("Size", "Creature Type", "Alignment", "AC, Initiative, and HP", "Speed", "Ability Scores",
                  "Skills", "Resistances and Vulnerabilities", "Immunities", "Gear", "Senses", "Languages",
                  "CR", "Traits", "Actions", "Bonus Actions", "Reactions", "Attack Notation",
                  "Saving Throw Effect Notation", "Damage Notation"):
        by = {"Alignment": ("master_decision", ["md:monster_alignment"]),
              "Attack Notation": ("structured", [cr("stat_block.attack_targets")]),
              "Damage Notation": ("structured", [cr("stat_block.damage_notation")])}.get(
            label, ("structured", ["dnd5e/rule/parts-of-a-stat-block"]))
        stat_plan.append((f"***{label}.***", by[0], by[1]))
    E.append(glossary_entry("Stat Block", stat_plan, master_decisions=[
        md("monster_alignment", "Choose the monster's actual alignment (the stat block only suggests one).",
           "An alignment is suggested for the monster, with the GM determining its actual alignment.",
           when="on_gain", pages=inv_page("Stat Block"))]))
    E.append(glossary_entry("Telepathy", [
        (None, "descriptive", None),
        ("Unless a rule states otherwise", "structured", [cr("telepathy.language")]),
        ("A telepath doesn’t need to see", "structured", [cr("telepathy.contact")]),
        ("A creature without telepathy", "structured", [cr("telepathy.non_telepath")])]))
    E.append(glossary_entry("Teleportation", [
        (None, "descriptive", None),
        ("If you teleport, you disappear", "structured", [cr("teleportation.movement")]),
        ("When you teleport, all the equipment", "structured", [cr("teleportation.passengers")]),
        ("If the destination space", "structured", [cr("teleportation.blocked")]),
        ("The description of a teleportation effect", "shared_rule", ["dnd5e/rule/teleportation"])]))

    E += section_entries(cr)
    return E


def table_data(nodes, caption):
    """{id, caption, columns, rows} for the captioned table inside `nodes` (header rows dropped)."""
    k = next(i for i, n in enumerate(nodes) if n.type == "h" and n.level == 5 and n.text == caption)
    rows, columns = [], None
    for n in nodes[k + 1:]:
        if n.type == "t":
            if n.text.startswith("| **"):
                columns = columns or n.cells
                continue
            rows.append(n.cells)
        elif n.type == "p" and re.fullmatch(r"[A-Z][A-Za-z’ ]+", n.text) and rows and len(rows[-1]) == 2 \
                and columns and len(columns) == 2 and rows[-1][1]:
            rows.append([n.text, ""])  # a lone cell the layout printed as text (e.g. "Infernal")
        elif n.type == "h" or (n.type == "p" and not re.match(r"^\*[^*].*\*$", n.text)):
            break
    return {"id": slugify(caption).replace("-", "_"), "caption": caption, "columns": columns, "rows": rows}


def sec(title, level, page=None, **kw):
    return section(title, level, page, **kw)


def section_entries(cr):
    E = []
    side = lambda title, slug, plan, path: entry(  # noqa: E731
        "rule", slug, title, sidebar_nodes(title), LOT, path, plan, facets={"sidebar": True})

    E.append(side("Exceptions Supersede General Rules", "sidebar-exceptions-supersede-general-rules", [
        (None, "structured", [cr("general_rules")]),
        ("The game also includes elements", "structured", [cr("exceptions_supersede")])], "Playing the Game"))
    E.append(side("Round Down", "sidebar-round-down", [(None, "structured", [cr("round_down")])], "Playing the Game"))
    E.append(side("Unaligned Creatures", "sidebar-unaligned-creatures", [
        (None, "structured", [R("/registries/alignments", "unaligned")])],
        "Character Creation/Create Your Character/Step 4: Alignment"))

    nodes = sec("Rhythm of Play", 2, 5)
    E.append(entry("rule", "rhythm-of-play", "Rhythm of Play", nodes, LOT, "Playing the Game/Rhythm of Play", [
        (None, "descriptive", None),
        ("Outside combat, the GM ensures", "master_decision", ["md:resolve_activity"]),
        ("In combat, the characters take turns.", "shared_rule", [SEE_ALSO_SECTIONS["Playing the Game (Combat)"]]),
        ("**3: The GM Narrates", "descriptive", None),
        ("In those cases, the GM might ask the player to roll a die", "master_decision", ["md:resolve_activity"]),
        ("Describing the results often leads", "descriptive", None)],
        master_decisions=[md("resolve_activity", "Decide how to resolve the characters' activity, and whether a "
                             "roll is needed to determine what happens.",
                             "Outside combat, the GM ensures that every character has a chance to act and decides "
                             "how to resolve their activity.", pages=[5])]))

    nodes = sec("The Six Abilities", 2, 5)
    E.append(entry("rule", "the-six-abilities", "The Six Abilities", nodes, LOT, "Playing the Game/The Six Abilities", [
        (None, "structured", [S("/abilities")]),
        ("### Ability Scores", "structured", [S("/ability_scores/descriptors"), S("/ability_scores/min"),
                                              S("/ability_scores/max")]),
        ("### Ability Modifiers", "structured", [S("/ability_scores/modifier_table")])]))

    nodes = sec("Choose a Character Sheet", 2, 19)
    E.append(entry("rule", "choose-a-character-sheet", "Choose a Character Sheet", nodes, LOT,
                   "Character Creation/Choose a Character Sheet", [(None, "descriptive", None)]))

    steps = [("choose_class", "dnd5e/rule/character-creation-step-1-choose-class"),
             ("determine_origin", "dnd5e/rule/character-creation-step-2-character-origin"),
             ("determine_ability_scores", "dnd5e/rule/character-creation-step-3-ability-scores"),
             ("choose_alignment", "dnd5e/rule/character-creation-step-4-alignment"),
             ("fill_in_details", "dnd5e/rule/character-creation-step-5-character-creation-details")]
    nodes = sec("Create Your Character", 2, 19, stop_titles=("Step 1: Choose Class",))
    E.append(entry("rule", "create-your-character", "Create Your Character", nodes, LOT,
                   "Character Creation/Create Your Character", [
                       (None, "structured", ["/data/procedure"]),
                       ("**1: Choose a Class.**", "shared_rule", [steps[0][1]]),
                       ("**2: Determine Origin.**", "shared_rule", [steps[1][1]]),
                       ("**3: Determine Ability Scores.**", "shared_rule", [steps[2][1]]),
                       ("**4: Choose an Alignment.**", "shared_rule", [steps[3][1]]),
                       ("**5: Fill in Details.**", "shared_rule", [steps[4][1]])],
                   data={"procedure": [{"step": i + 1, "id": sid, "rule": ref} for i, (sid, ref) in enumerate(steps)]}))

    # step 1
    nodes = sec("Step 1: Choose Class", 3)
    E.append(entry("rule", "character-creation-step-1-choose-class", "Step 1: Choose Class", nodes, LOT,
                   "Character Creation/Create Your Character/Step 1: Choose Class", [
                       (None, "structured", ["/data/tables/0"]),
                       ("#### Write Your Level", "structured", [R("/levels/rules", "level.start_xp")]),
                       ("***Starting at a Higher Level.***", "master_decision", ["md:starting_level"]),
                       ("If you start at level 3 or higher", "structured", ["/data/rules/0"]),
                       ("See the “Starting at Higher Levels” section", "shared_rule",
                        ["dnd5e/rule/starting-at-higher-levels"]),
                       ("#### Note Armor Training", "shared_rule", [inv_ref("Armor Training")])],
                   data={"tables": [table_data(nodes, "Class Overview")],
                         "rules": [{"id": "subclass_at_level_3", "mechanic": {"record_subclass_if_start_level_gte": 3}}]},
                   master_decisions=[md("starting_level", "Choose the level at which the characters start.",
                                        "Your GM might start you at a higher level.", when="campaign_setup",
                                        pages=[19])]))

    # step 2
    nodes = sec("Step 2: Character Origin", 3)
    species = ["Dragonborn", "Dwarf", "Elf", "Gnome", "Goliath", "Halfling", "Human", "Orc", "Tiefling"]
    E.append(entry("rule", "character-creation-step-2-character-origin", "Step 2: Character Origin", nodes, LOT,
                   "Character Creation/Create Your Character/Step 2: Character Origin", [
                       (None, "structured", ["/data/rules/0"]),
                       ("A character’s background represents", "descriptive", None),
                       ("#### Choose a Background", "shared_rule", [e["ref"] for e in INV if e["kind"] == "background"]),
                       ("and your GM might offer additional backgrounds", "master_decision", ["md:extra_backgrounds"]),
                       ("The background you choose influences step 3", "structured", ["/data/tables/0"]),
                       ("***Record Your Feat.***", "shared_rule", ["dnd5e/rule/feat-descriptions"]),
                       ("***Note Proficiencies.***", "structured", ["/data/rules/1"]),
                       ("Your class also gives proficiencies.", "shared_rule", [e["ref"] for e in INV if e["kind"] == "class"]),
                       ("The features table in your class description", "structured",
                        [S("/proficiency_bonus/by_level/1")]),
                       ("#### Choose Starting Equipment", "structured", ["/data/rules/2"]),
                       ("#### Choose a Species", "shared_rule", [inv_ref(n, "species") for n in species]),
                       ("Your character’s size and Speed are determined", "shared_rule",
                        [inv_ref(n, "species") for n in species]),
                       ("#### Imagine Your Past and Present", "descriptive", None),
                       ("#### Choose Languages", "structured", ["/data/rules/3", S("/languages")]),
                       ("The Standard Languages table lists", "structured", [S("/languages")])],
                   data={"tables": [table_data(nodes, "Ability Scores and Backgrounds")],
                         "rules": [
                             {"id": "origin_parts", "mechanic": {"choose": ["background", "species"], "languages": 2}},
                             {"id": "background_proficiencies", "mechanic": {"skills": 2, "tools": 1}},
                             {"id": "starting_coins_spendable", "mechanic": {"spend_coins_on": "equipment_chapter"}},
                             {"id": "starting_languages", "mechanic": {"always": ["common"], "choose": 2,
                                                                      "from": "standard", "method": ["roll_1d12", "choose"],
                                                                      "minimum_known": 3}}]},
                   master_decisions=[md("extra_backgrounds", "Offer backgrounds beyond those in Character Origins?",
                                        "your GM might offer additional backgrounds as options.",
                                        when="campaign_setup", pages=[19])]))

    # step 3
    nodes = sec("Step 3: Ability Scores", 3)
    E.append(entry("rule", "character-creation-step-3-ability-scores", "Step 3: Ability Scores", nodes, LOT,
                   "Character Creation/Create Your Character/Step 3: Ability Scores", [
                       (None, "structured", ["/data/rules/0"]),
                       ("Your GM might prefer you to use a particular one.", "master_decision", ["md:generation_method"]),
                       ("***Standard Array.***", "structured", ["/data/rules/1"]),
                       ("***Random Generation.***", "structured", ["/data/rules/2"]),
                       ("***Point Cost.***", "structured", ["/data/rules/3", "/data/tables/0"]),
                       ("#### Assign Ability Scores", "structured", ["/data/rules/4", "/data/tables/1"]),
                       ("#### Adjust Ability Scores", "structured", ["/data/rules/5"]),
                       ("Some players like to increase", "descriptive", None),
                       ("#### Determine Ability Modifiers", "structured", [S("/ability_scores/modifier_table")])],
                   data={"tables": [table_data(nodes, "Ability Score Point Costs"),
                                    table_data(nodes, "Standard Array by Class")],
                         "rules": [
                             {"id": "generate_then_assign", "mechanic": {"scores": 6, "assign_to": "abilities"}},
                             {"id": "standard_array", "mechanic": {"scores": [15, 14, 13, 12, 10, 8]}},
                             {"id": "random_generation", "mechanic": {"roll": "4d6", "keep_highest": 3, "repeat": 6}},
                             {"id": "point_cost", "mechanic": {"points": 27, "cost_table": "ability_score_point_costs"}},
                             {"id": "assign", "mechanic": {"suggestion_table": "standard_array_by_class"}},
                             {"id": "background_adjustment", "mechanic": {
                                 "options": [{"plus_2": 1, "plus_1": 1, "distinct": True}, {"plus_1": 3}],
                                 "from": "background_abilities", "max_score": 20}}]},
                   master_decisions=[md("generation_method", "Require a particular ability score generation method?",
                                        "Your GM might prefer you to use a particular one.",
                                        options=[{"id": "standard_array", "label": "Standard Array"},
                                                 {"id": "random_generation", "label": "Random Generation"},
                                                 {"id": "point_cost", "label": "Point Cost"}],
                                        when="campaign_setup", pages=[21])]))

    # step 4
    nodes = sec("Step 4: Alignment", 3)
    E.append(entry("rule", "character-creation-step-4-alignment", "Step 4: Alignment", nodes, LOT,
                   "Character Creation/Create Your Character/Step 4: Alignment", [
                       (None, "structured", [S("/registries/alignments")]),
                       ("The game assumes that player characters aren’t of an evil alignment.", "master_decision",
                        ["md:evil_alignment"]),
                       ("#### The Nine Alignments", "structured", [S("/registries/alignments")]),
                       ("The summaries of the alignments below", "descriptive", None)],
                   master_decisions=[md("evil_alignment", "Allow this player character to have an evil alignment?",
                                        "The game assumes that player characters aren’t of an evil alignment. Check "
                                        "with your GM before making an evil character.", when="on_gain", pages=[21])]))

    # step 5
    nodes = sec("Step 5: Character Creation Details", 3)
    lr = lambda rid: R("/levels/rules", rid)  # noqa: E731
    E.append(entry("rule", "character-creation-step-5-character-creation-details",
                   "Step 5: Character Creation Details", nodes, LOT,
                   "Character Creation/Create Your Character/Step 5: Character Creation Details", [
                       (None, "descriptive", None),
                       ("#### Record Class Features", "shared_rule", [e["ref"] for e in INV if e["kind"] == "class"]),
                       ("#### Fill In Numbers", "descriptive", None),
                       ("***Saving Throws.***", "structured", ["/data/rules/0"]),
                       ("***Skills.***", "structured", ["/data/rules/1"]),
                       ("***Passive Perception.***", "structured", [lr("passive_perception")]),
                       ("***Hit Points.***", "structured", ["/data/tables/0"]),
                       ("The character sheet includes room", "descriptive", None),
                       ("***Hit Point Dice.***", "structured", [lr("level.start_hit_dice")]),
                       ("You can spend Hit Dice during a Short Rest", "shared_rule", [inv_ref("Short Rest")]),
                       ("***Initiative.***", "structured", [S("/initiative/check")]),
                       ("***Armor Class.***", "structured", [lr("base_ac")]),
                       ("If your starting equipment includes armor", "shared_rule", ["dnd5e/rule/armor"]),
                       ("***Attacks.***", "structured", [lr("melee_attack_bonus"), lr("ranged_attack_bonus")]),
                       ("Look up the damage and properties", "structured", ["/data/rules/2"]),
                       ("***Spellcasting.***", "structured", [lr("spell_save_dc"), lr("spell_attack_bonus")]),
                       ("***Spell Slots, Cantrips, and Prepared Spells.***", "shared_rule",
                        [e["ref"] for e in INV if e["kind"] == "class"])],
                   data={"tables": [table_data(nodes, "Level 1 Hit Points by Class")],
                         "rules": [
                             {"id": "saving_throw_mod", "mechanic": {"formula": {"op": "add", "args": [
                                 {"var": "ability_mod.<ability>"}, {"var": "proficiency_bonus"}]},
                                 "proficient_only": True}},
                             {"id": "skill_mod", "mechanic": {"formula": {"op": "add", "args": [
                                 {"var": "ability_mod.<skill_ability>"}, {"var": "proficiency_bonus"}]},
                                 "proficient_only": True}},
                             {"id": "weapon_damage_ability", "mechanic": {"damage_adds": "attack_ability_modifier"}}]}))

    # level advancement
    nodes = sec("Level Advancement", 2)
    E.append(entry("rule", "level-advancement", "Level Advancement", nodes, LOT, "Character Creation/Level Advancement", [
        (None, "structured", [S("/levels/advancement"), lr("level.threshold")]),
        ("### Gaining a Level", "structured", ["/data/procedure"]),
        ("**1: Choose a Class.**", "shared_rule", ["dnd5e/rule/multiclassing"]),
        ("**2: Adjust Hit Points and Hit Point Dice.**", "structured", [lr("level.hit_points"), "/data/tables/0"]),
        ("**3: Record New Class Features.**", "shared_rule", [e["ref"] for e in INV if e["kind"] == "class"]),
        ("**4: Adjust Proficiency Bonus.**", "structured", [S("/proficiency_bonus/by_level")]),
        ("**5: Adjust Ability Modifiers.**", "structured", [lr("level.ability_modifier_change"),
                                                          lr("level.con_retroactive")]),
        ("### Tiers of Play", "descriptive", None),
        ("#### Tier 1 (Levels 1–4)", "structured", [R("/levels/tiers", "tier_1")]),
        ("#### Tier 2 (Levels 5–10)", "structured", [R("/levels/tiers", "tier_2")]),
        ("#### Tier 3 (Levels 11–16)", "structured", [R("/levels/tiers", "tier_3")]),
        ("#### Tier 4 (Levels 17–20)", "structured", [R("/levels/tiers", "tier_4")])],
        data={"tables": [table_data(nodes, "Fixed Hit Points by Class")],
              "procedure": [{"step": 1, "id": "choose_class"}, {"step": 2, "id": "adjust_hit_points_and_hit_dice"},
                            {"step": 3, "id": "record_new_class_features"}, {"step": 4, "id": "adjust_proficiency_bonus"},
                            {"step": 5, "id": "adjust_ability_modifiers"}]}))

    # starting at higher levels (its table is printed inside "Multiclassing")
    table = table_nodes("Starting Equipment at Higher Levels")
    nodes = sec("Starting at Higher Levels", 2, extra=table)
    E.append(entry("rule", "starting-at-higher-levels", "Starting at Higher Levels", nodes, LOT,
                   "Character Creation/Starting at Higher Levels", [
                       (None, "master_decision", ["md:starting_level"]),
                       ("It is particularly recommended", "structured", ["/data/rules/0"]),
                       ("### Creating Your Character", "structured", [R("/levels/rules", "start_higher.xp")]),
                       ("### Starting Equipment", "master_decision", ["md:starting_equipment"]),
                       ("Also, check with your GM", "master_decision", ["md:equipment_availability"]),
                       ("##### Starting Equipment at Higher Levels", "structured", ["/data/tables/0"])],
                   data={"tables": [table_data(nodes, "Starting Equipment at Higher Levels")],
                         "rules": [{"id": "recommended_start", "mechanic": {"recommended_level": 3,
                                                                           "when": "seasoned_players"}}]},
                   master_decisions=[
                       md("starting_level", "Choose the level at which the characters start.",
                          "Your GM might start your group’s characters at a level higher than 1.",
                          when="campaign_setup", pages=[24]),
                       md("starting_equipment", "Decide whether characters starting above level 1 get more than the "
                          "standard equipment (the table is a guide).",
                          "The GM decides whether your character starts with more than the standard equipment for a "
                          "level 1 character, possibly even one or more magic items.", when="campaign_setup",
                          pages=[24]),
                       md("equipment_availability", "Decide which equipment is available to buy with starting money.",
                          "Also, check with your GM about what equipment is available for you to buy with your "
                          "starting money.", when="campaign_setup", pages=[24])]))

    nodes = sec("Rules Definitions", 2)
    nodes = nodes[:next(i for i, n in enumerate(nodes) if n.type == "h")]
    E.append(entry("rule", "rules-definitions", "Rules Definitions", nodes, LOT, "Rules Glossary/Rules Definitions",
                   [(None, "descriptive", None)]))

    # glossary conventions
    nodes = sec("Glossary Conventions", 2)
    E.append(entry("rule", "glossary-conventions", "Glossary Conventions", nodes, LOT, "Rules Glossary/Glossary Conventions", [
        (None, "descriptive", None),
        ("**Tags in Brackets.**", "structured", ["/data/rules/0"]),
        ("**“You.”**", "descriptive", None),
        ("**Abbreviations.**", "structured", [S("/abbreviations")])],
        data={"rules": [{"id": "glossary_tags", "mechanic": {"tags": {
            "Action": "action", "Area of Effect": "area", "Attitude": "attitude", "Condition": "condition",
            "Hazard": "hazard"}}}]}))
    return E


if __name__ == "__main__":
    system = build_system()
    path = write_json("system.json", system)
    print(f"wrote {path.relative_to(ROOT)}")
    entries = build_entries(system)
    for e in entries:
        write_entry(e)
    print(f"wrote {len(entries)} entries")
