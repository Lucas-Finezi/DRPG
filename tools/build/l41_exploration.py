#!/usr/bin/env python3
"""L41 — Exploration (Playing the Game), Travel Pace, Curses and Magical Contagions, Environmental
Effects, Fear and Mental Stress, Traps (Gameplay Toolbox), the Marching Order sidebar and the
vision, light and senses terms of the Rules Glossary.

Usage: python3 -I tools/build/l41_exploration.py
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import (NODES, build, extend_registries, find, glossary, md, section, sidebar, table_nodes, table_rows,  # noqa: E402
                      write_entry)

LOT = "L41"
ROOT = Path(__file__).resolve().parents[2]
INV = {(e["kind"], e["name"]): e for e in json.loads((ROOT / "inventory/dnd5e/srd-5.2.1/entries.json").read_text(encoding="utf-8"))["entries"]
       if e["lot"] == LOT}
C = lambda s: f"dnd5e/condition/{s}"  # noqa: E731
SP = lambda s: f"dnd5e/spell/{s}"  # noqa: E731
EXH1 = {"op": "apply_condition", "condition": "dnd5e/condition/exhaustion", "params": {"levels": 1}}
EACH_END = {"on": {"event": "turn_end", "whose": "target", "which": "each"}, "ends": "effect_on_self"}
TERRAIN_NOTE = "\\*Appropriate equipment (such as skis)"


def R(slug, name, nodes, path, items, kind="rule", **kw):
    return build(kind, slug, name, nodes, LOT, path, items, **kw)


def adv(rolls, when, mode="advantage", **kw):
    return {"op": "roll_mode", "mode": mode, "rolls": rolls if isinstance(rolls, list) else [rolls], "when": when, **kw}


def skill(s):
    return {"pred": "check_uses_skill", "args": {"skill": s}}


def save(ab, dc, on_fail, **kw):
    return {"op": "save", "ability": ab, "dc": dc, "on_fail": on_fail if isinstance(on_fail, list) else [on_fail], **kw}


def exploration():
    E = []
    E.append(R("exploration", "Exploration", section("Exploration", 2, page=11, stop_titles=("Adventuring Equipment",)), "Playing the Game/Exploration",
               [(None, "desc", None)]))
    E.append(R("adventuring-equipment", "Adventuring Equipment", section("Adventuring Equipment", 3, page=11), "Playing the Game/Exploration/Adventuring Equipment", [
        (None, "desc", None), ("See “Equipment”", "ref", ["dnd5e/rule/adventuring-gear", "dnd5e/rule/tools"])]))
    E.append(R("vision-and-light", "Vision and Light", section("Vision and Light", 3, page=11), "Playing the Game/Exploration/Vision and Light", [
        (None, "desc", None),
        ("#### Obscured Areas", "fx", adv("ability_check", {"all": [{"pred": "in_lightly_obscured_area"}, skill("perception"), {"pred": "requires_sight"}]}, mode="disadvantage")),
        ("#### Obscured Areas", "ref", ["dnd5e/rule/lightly-obscured"]),
        ("A Heavily Obscured area", "fx", {"op": "apply_condition", "condition": C("blinded"), "when": {"pred": "heavily_obscured"},
                                           "note": "When trying to see something there."}),
        ("A Heavily Obscured area", "ref", ["dnd5e/rule/heavily-obscured"]),
        ("#### Light", "rule", {"id": "illumination", "categories": ["bright_light", "dim_light", "darkness"]}),
        ("***Bright Light.***", "ref", ["dnd5e/rule/bright-light"]),
        ("***Dim Light.***", "rule", {"id": "dim_light", "obscurement": "dnd5e/rule/lightly-obscured", "examples": ["twilight", "dawn", "full moon"]}),
        ("***Darkness.***", "rule", {"id": "darkness", "obscurement": "dnd5e/rule/heavily-obscured"}),
        ("#### Special Senses", "ref", ["dnd5e/rule/blindsight", "dnd5e/rule/darkvision", "dnd5e/rule/tremorsense", "dnd5e/rule/truesight"])]))
    E.append(R("hiding", "Hiding", section("Hiding", 3, page=11), "Playing the Game/Exploration/Hiding", [
        (None, "md", md("hiding_allowed", "Are circumstances appropriate for hiding?", "The Game Master decides when circumstances are appropriate for hiding.")),
        (None, "ref", ["dnd5e/action/hide"])]))
    E.append(R("interacting-with-objects", "Interacting with Objects", section("Interacting with Objects", 3, page=11),
               "Playing the Game/Exploration/Interacting with Objects", [
                   (None, "md", md("object_outcome", "What happens when the character interacts with the object?",
                                   "the GM describes what happens", reason="narrative")),
                   ("#### What Is an Object?", "rule", {"id": "object", "discrete_inanimate": True, "excludes": ["building", "vehicle"]}),
                   ("#### Time-Limited Object Interactions", "rule", {"id": "time_limited", "free_per_turn": 1, "extra": "dnd5e/action/utilize"}),
                   ("#### Finding Hidden Objects", "fx", {"op": "check", "ability": "wis", "skill": "perception",
                                                          "note": "Searching in the hidden object's vicinity; searching elsewhere never reveals it."}),
                   ("#### Carrying Objects", "ref", ["dnd5e/rule/carrying-capacity"]),
                   ("#### Breaking Objects", "rule", {"id": "break_fragile", "cost": "action", "automatic": True, "fragile_nonmagical": True}),
                   ("#### Breaking Objects", "ref", ["dnd5e/rule/breaking-objects"])]))
    hz = section("Hazards", 3, page=12)
    E.append(R("hazards", "Hazards", hz, "Playing the Game/Exploration/Hazards", [
        (None, "ref", ["dnd5e/hazard/burning", "dnd5e/hazard/dehydration", "dnd5e/hazard/falling", "dnd5e/hazard/malnutrition", "dnd5e/hazard/suffocation"])]))
    tr = section("Travel", 3, page=12)
    E.append(R("travel", "Travel", tr, "Playing the Game/Exploration/Travel", [
        (None, "md", md("summarize_travel", "Summarize the travel or use the travel pace rules?",
                        "The GM can summarize this travel without calculating exact distances or travel times, or the GM might have you use the travel pace rules below.")),
        ("If you need to know", "ref", ["dnd5e/rule/movement-and-position"]),
        ("#### Travel Pace", "rule", {"id": "travel_pace", "paces": ["fast", "normal", "slow"], "mounts_double_for_hours": 1,
                                      "mount_rest": ["short_rest", "long_rest"]}),
        ("##### Travel Pace", "table", {"id": "travel_pace", "caption": "Travel Pace", "columns": ["Pace", "Minute", "Hour", "Day"],
                                        "rows": table_rows(tr)}),
        ("***Fast.***", "fx", adv("ability_check", {"any": [skill("perception"), skill("survival"), skill("stealth")]}, mode="disadvantage",
                                  note="Fast pace.")),
        ("***Normal.***", "fx", adv("ability_check", skill("stealth"), mode="disadvantage", note="Normal pace.")),
        ("***Slow.***", "fx", adv("ability_check", {"any": [skill("perception"), skill("survival")]}, note="Slow pace.")),
        ("#### Vehicles", "rule", {"id": "vehicles", "land": "choose pace", "waterborne": "vessel speed", "max_hours_per_day": 24})]))
    return E


def toolbox():
    E = []
    tt = table_nodes("Travel Terrain")
    note = [n for n in NODES if n.text.startswith(TERRAIN_NOTE)]
    tp = section("Travel Pace", 2, page=192) + tt + note
    E.append(R("travel-pace-toolbox", "Travel Pace (Gameplay Toolbox)", tp, "Gameplay Toolbox/Travel Pace", [
        (None, "rule", {"id": "max_pace_by_terrain", "table": "travel_terrain"}),
        ("### Good Roads", "rule", {"id": "good_roads", "max_pace_steps": 1}),
        ("### Slower Travelers", "rule", {"id": "slower_travelers", "pace": "slow", "when": "any member's Speed at half or less"}),
        ("### Extended Travel", "fx", {"op": "trigger", "event": {"event": "hour_elapsed", "which": "each"},
                                       "condition": {"pred": "travel_hours_over", "args": {"hours": 8}},
                                       "then": [save("con", {"op": "add", "args": [10, {"var": "travel_hours_over_8"}]}, EXH1)]}),
        ("### Special Movement", "rule", {"id": "special_movement", "mph": "speed / 10", "miles_per_day": "mph × hours (typically 8)",
                                          "fast": "× 4/3 (round down)", "slow": "× 2/3 (round down)", "ignore_terrain_if_flying": "fast"}),
        ("### Vehicles", "rule", {"id": "vehicles", "rate": "vehicle mph", "no_pace_choice": True}),
        ("##### Travel Terrain", "table", {"id": "travel_terrain", "caption": "Travel Terrain",
                                           "columns": ["Terrain", "Maximum Pace", "Encounter Distance", "Foraging DC", "Navigation DC", "Search DC"],
                                           "rows": table_rows(tt)}),
        ("\\*Appropriate equipment", "rule", {"id": "terrain_notes", "arctic_fast_needs_equipment": True, "waterborne": "dnd5e/rule/vehicles"})]))
    E.append(R("curses-and-magical-contagions", "Curses and Magical Contagions", section("Curses and Magical Contagions", 2, page=193, stop_titles=("Curses",)),
               "Gameplay Toolbox/Curses and Magical Contagions", [
                   (None, "rule", {"id": "definitions", "curse": "magical burden until ended", "contagion": "contagious magical adverse effect"})]))
    E.append(R("curses-toolbox", "Curses (Gameplay Toolbox)", section("Curses", 3, page=193, stop_titles=("Bestow Curse",)),
               "Gameplay Toolbox/Curses and Magical Contagions/Curses", [(None, "ref", ["dnd5e/rule/curses"])]))
    curse_items = {
        "Bestow Curse": [(None, "ref", [SP("bestow-curse"), SP("remove-curse")]),
                         ("*Bestow Curse* provides", "rule", {"id": "benchmark", "one_minute": "level 3 spell", "until_dispelled": "level 9 spell"})],
        "Cursed Creatures": [(None, "desc", None),
                             ("You decide how", "md", md("cursed_origin", "How does Remove Curse affect this creature with accursed origins?",
                                                         "You decide how a spell like *Remove Curse* affects a creature with accursed origins."))],
        "Cursed Magic Items": [(None, "ref", ["dnd5e/rule/cursed-items"])],
        "Narrative Curses": [(None, "md", md("narrative_curse", "What effects does this narrative curse have?",
                                             "Such a curse can have any effects you design", reason="narrative")),
                             ("A creature affected", "rule", {"id": "knowable", "knows_why": True, "can_learn_cure": True}),
                             ("A creature affected", "md", md("remove_curse_narrative", "How does Remove Curse affect this curse?",
                                                              "How a spell like *Remove Curse* affects a curse that’s part of your adventure is up to you"))],
        "Environmental Curses": [(None, "desc", None),
                                 ("***Demonic Possession.***", "desc", None),
                                 ("A creature that becomes the target", "fx", save("cha", 15, {"op": "reference", "rule": "dnd5e/curse/environmental-curses",
                                                                                              "note": "Possessed: on a 1 on a D20 Test the entity takes control; DC 15 Charisma save at the end of each later turn regains control."})),
                                 ("After finishing a Long Rest", "fx", {"op": "trigger", "event": {"event": "long_rest_finished"},
                                                                        "then": [{"op": "save", "ability": "cha", "dc": 15,
                                                                                  "on_success": [{"op": "end_effect", "scope": "this_entry_on_target"}]}],
                                                                        "note": "Dispel Evil and Good or any magic that removes a curse also ends it."})],
    }
    for name, items in curse_items.items():
        e = INV[("curse", name)]
        E.append(R(e["ref"].split("/")[-1], name, section(name, 4, page=193), f"Gameplay Toolbox/Curses and Magical Contagions/Curses/{name}", items, kind="curse"))
    E.append(R("magical-contagions", "Magical Contagions", section("Magical Contagions", 3, page=194, stop_titles=("Cackle Fever",)),
               "Gameplay Toolbox/Curses and Magical Contagions/Magical Contagions", [
                   (None, "desc", None),
                   ("#### Rest and Recuperation", "fx", {"op": "save", "ability": "con", "dc": 15,
                                                         "on_success": [adv("saving_throw", {"pred": "save_against_contagion"}, duration={"kind": "hours", "amount": 24})],
                                                         "note": "After 3 days of recuperation (no activity that would interrupt a Long Rest)."}),
                   ("#### Example Contagions", "md", md("alter_contagion", "Alter this contagion's DCs or effects?",
                                                        "Feel free to alter the saving throw DCs, effects, and other characteristics of these contagions to suit your campaign."))]))
    hum = {"creature_types": ["humanoid"]}
    contagions = {
        "Cackle Fever": [(None, "rule", {"id": "hosts", "creature_types": ["humanoid"], "immune": "gnomes", "onset_days": "1d4"}),
                         ("**Fever.**", "fx", EXH1 | {"note": "Lasts until the contagion ends."}),
                         ("**Uncontrollable Laughter.**", "fx", {"op": "trigger", "event": {"event": "damage_taken", "which": "each"},
                                                                 "condition": {"all": [{"pred": "has_condition", "args": {"condition": "exhaustion"}},
                                                                                       {"not": {"pred": "deals_damage_type", "args": {"type": "psychic"}}}]},
                                                                 "then": [save("con", 13, [{"op": "damage", "amount": "1d10", "damage_type": "psychic"},
                                                                                           {"op": "apply_condition", "condition": C("incapacitated"),
                                                                                            "duration": {"kind": "minutes", "amount": 1}}], repeat=EACH_END)]}),
                         ("***Fighting the Contagion.***", "fx", {"op": "trigger", "event": {"event": "long_rest_finished", "which": "each"},
                                                                  "then": [{"op": "save", "ability": "con", "dc": 13}],
                                                                  "note": "After three successes the contagion ends; immune for 1 year."}),
                         ("***Spreading the Contagion.***", "fx", {"op": "trigger", "event": {"event": "turn_start", "whose": "any", "which": "each"},
                                                                   "then": [save("con", 10, {"op": "reference", "rule": "dnd5e/contagion/cackle-fever", "note": "Infected."},
                                                                                 target={"kind": "area", "area": {"shape": "emanation", "size_feet": 10, "origin": "self"}, "filter": hum},
                                                                                 note="Non-gnome Humanoids; on a success immune to this carrier for 24 hours.")]})],
        "Sewer Plague": [(None, "fx", save("con", 11, {"op": "reference", "rule": "dnd5e/contagion/sewer-plague", "note": "Infected; effects 1d4 days later."},
                                           target={"kind": "creature", "filter": hum}, note="Wounded by a carrier or contact with contaminated filth.")),
                         ("**Fatigue.**", "fx", EXH1),
                         ("**Weakness.**", "fx", {"op": "modifier", "stat": "healing_dice", "mode": "multiply", "value": 0.5,
                                                  "when": {"all": [{"pred": "has_condition", "args": {"condition": "exhaustion"}},
                                                                   {"pred": "roll_is", "args": {"roll": "hit_point_die"}}]}}),
                         ("**Restlessness.**", "fx", {"op": "restrict", "restrictions": ["benefit_from_rest"],
                                                      "when": {"pred": "has_condition", "args": {"condition": "exhaustion"}},
                                                      "note": "A Long Rest restores no Hit Points and doesn't reduce Exhaustion."}),
                         ("***Fighting the Contagion.***", "fx", {"op": "trigger", "event": {"event": "dawn", "which": "each"},
                                                                  "then": [{"op": "save", "ability": "con", "dc": 11, "on_fail": [EXH1],
                                                                            "on_success": [{"op": "remove_condition", "conditions": [C("exhaustion")], "levels": 1}]}],
                                                                  "note": "Ends when Exhaustion reaches 0."})],
        "Sight Rot": [(None, "fx", save("con", 15, {"op": "apply_condition", "condition": C("blinded"), "note": "Until the contagion ends."},
                                        target={"kind": "creature", "filter": {"creature_types": ["beast", "humanoid"]}}, note="Drinks tainted water.")),
                      ("***Fighting the Contagion.***", "rule", {"id": "cure", "spells": [SP("heal"), SP("lesser-restoration")],
                                                                 "ointment": {"tool": "dnd5e/tool/herbalism-kit", "hours": 1, "suppress_hours": 24,
                                                                              "total_hours_to_cure": 72, "doses": 3}}),
                      ("***Spreading the Contagion.***", "fx", save("con", 15, {"op": "reference", "rule": "dnd5e/contagion/sight-rot", "note": "Infected."},
                                                                    target={"kind": "creature", "filter": hum},
                                                                    note="Skin contact with an infected creature; on a success immune to that carrier for 24 hours."))],
    }
    for name, items in contagions.items():
        e = INV[("contagion", name)]
        nodes = section(name, 4, page=194)
        items = [(None, "sys", ["/facets"])] + [((nodes[1].text[:40] if a is None else a), t, p) for a, t, p in items]
        E.append(R(e["ref"].split("/")[-1], name, nodes, f"Gameplay Toolbox/Curses and Magical Contagions/Magical Contagions/{name}", items,
                   kind="contagion", facets={"type": "magical_contagion"}))
    env = {
        "Deep Water": [(None, "fx", {"op": "trigger", "event": {"event": "hour_elapsed", "which": "each"}, "condition": {"not": {"pred": "has_speed", "args": {"mode": "swim"}}},
                                     "then": [save("con", 10, EXH1)], "note": "Swimming in water more than 100 feet deep."})],
        "Extreme Cold": [(None, "fx", {"op": "trigger", "event": {"event": "hour_elapsed", "which": "each"},
                                       "then": [save("con", 10, EXH1, note="Resistance or Immunity to Cold: automatic success.")],
                                       "note": "0 °F or lower, exposed."})],
        "Extreme Heat": [(None, "fx", {"op": "trigger", "event": {"event": "hour_elapsed", "which": "each"},
                                       "then": [save("con", {"op": "add", "args": [4, {"var": "hours_exposed"}]}, EXH1,
                                                     note="DC 5 the first hour, +1 each additional hour; Disadvantage in Medium or Heavy armor; Resistance or Immunity to Fire: automatic success.")],
                                       "note": "100 °F or higher, without drinkable water."})],
        "Frigid Water": [(None, "fx", {"op": "trigger", "event": {"event": "minutes_elapsed", "which": "each"},
                                       "condition": {"pred": "minutes_exceed_con_score"},
                                       "then": [save("con", 10, EXH1, note="Each minute beyond Constitution score minutes; Resistance/Immunity to Cold or adapted: automatic success.")]})],
        "Heavy Precipitation": [(None, "fx", [{"op": "reference", "rule": "dnd5e/rule/lightly-obscured"},
                                              adv("ability_check", skill("perception"), mode="disadvantage")]),
                                (None, "rule", {"id": "rain", "extinguishes_open_flames": True})],
        "High Altitude": [(None, "rule", {"id": "altitude", "min_feet": 10000, "travel_hour_counts_as": 2}),
                          ("Creatures can become acclimated", "rule", {"id": "acclimation", "days": 30, "max_feet": 20000, "natives_exempt": True})],
        "Slippery Ice": [(None, "fx", [{"op": "reference", "rule": "dnd5e/rule/difficult-terrain"},
                                       {"op": "trigger", "event": {"event": "enters_or_starts_turn_in_area", "which": "each"},
                                        "then": [save("dex", 10, {"op": "apply_condition", "condition": C("prone")})]}])],
        "Strong Wind": [(None, "fx", adv("attack_roll", {"pred": "attack_with_ranged_weapon"}, mode="disadvantage")),
                        (None, "rule", {"id": "wind", "extinguishes_open_flames": True, "disperses_fog": True, "flyers_land_or_fall": True}),
                        ("A strong wind in a desert", "fx", adv("ability_check", skill("perception"), mode="disadvantage", note="Sandstorm."))],
        "Thin Ice": [(None, "rule", {"id": "thin_ice", "tolerance_lb_per_10ft_square": "3d10 × 10", "breaks_when_exceeded": True,
                                     "below": "dnd5e/environment/frigid-water"})],
    }
    for name, items in env.items():
        e = INV[("environment", name)]
        E.append(R(e["ref"].split("/")[-1], name, section(name, 3, page=195), f"Gameplay Toolbox/Environmental Effects/{name}", items, kind="environment"))
    E.append(R("fear-and-mental-stress", "Fear and Mental Stress", section("Fear and Mental Stress", 2, page=196, stop_titles=("Fear Effects",)),
               "Gameplay Toolbox/Fear and Mental Stress", [
                   (None, "desc", None),
                   ("If you plan to use", "md", md("use_fear_rules", "Use fear and mental stress rules in this campaign?",
                                                   "If you plan to use any of these rules, discuss them with your players at the start of the campaign.", reason="narrative"))]))
    fe = section("Fear Effects", 3, page=196)
    fear_rows = [["When the characters open a sarcophagus, a harmless yet terrifying apparition appears.", "10"],
                 ["A character triggers a magical trap that creates an illusory manifestation of that character’s worst fears, visible only to that character.", "15"],
                 ["A portal to the Abyss opens, revealing a nightmarish realm of torment and slaughter.", "20"]]
    E.append(R("fear-effects", "Fear Effects", fe, "Gameplay Toolbox/Fear and Mental Stress/Fear Effects", [
        (None, "fx", {"op": "save", "ability": "wis", "dc": {"var": "chosen.fear_dc"}, "on_fail": [{"op": "apply_condition", "condition": C("frightened")}],
                      "repeat": EACH_END}),
        (None, "md", md("fear_dc", "How terrifying is the situation (save DC)?", "with a save DC based on how terrifying the situation is")),
        ("##### Sample Fear DCs", "table", {"id": "sample_fear_dcs", "caption": "Sample Fear DCs", "columns": ["Example", "Save DC"], "rows": fear_rows}),
        ("Typically, a Frightened creature", "sys", ["/effects/0"]),
        ("At your discretion", "md", md("fear_extra", "Apply an extra fear effect while Frightened?",
                                        "At your discretion, a Frightened creature might be subject to other effects as long as the Frightened condition lasts.",
                                        options=[{"id": "dash", "label": "Dash away from the source each turn"},
                                                 {"id": "exposed", "label": "Attack rolls against it have Advantage"},
                                                 {"id": "limited", "label": "Only one of move, action or Bonus Action each turn"}]))]))
    ms = section("Mental Stress Effects", 3, page=196)
    E.append(R("mental-stress-effects", "Mental Stress Effects", ms, "Gameplay Toolbox/Fear and Mental Stress/Mental Stress Effects", [
        (None, "rule", {"id": "psychic", "emulate_with": "psychic"}),
        ("The Sample Mental Stress Effects", "md", md("stress_half", "On a successful save, half damage instead of none?",
                                                      "On a successful save, a character might take half as much damage instead of no damage, at your discretion.")),
        ("##### Sample Mental Stress Effects", "table", {"id": "sample_mental_stress", "caption": "Sample Mental Stress Effects",
                                                         "columns": ["Example", "Save DC", "Psychic Damage"],
                                                         "rows": [r for r in table_rows(ms) if r and r[0] not in ("Example",)]})]))
    E.append(R("traps", "Traps", section("Traps", 2, page=199, stop_titles=("Parts of a Trap",)), "Gameplay Toolbox/Traps", [
        (None, "md", md("trap_use", "Place a trap here?", "Traps should be used sparingly, lest they lose their charm.", reason="narrative"))]))
    E.append(R("parts-of-a-trap", "Parts of a Trap", section("Parts of a Trap", 3, page=199), "Gameplay Toolbox/Traps/Parts of a Trap", [
        (None, "rule", {"id": "parts", "fields": ["severity_and_levels", "trigger", "duration"]}),
        ("**Severity and Levels.**", "rule", {"id": "severity", "values": ["nuisance", "deadly"]}),
        ("**Trigger.**", "rule", {"id": "trigger", "examples": ["pressure_plate", "trip_wire", "doorknob", "wrong_key"]}),
        ("**Duration.**", "rule", {"id": "duration", "inert_after_unless_resets": True}),
        ("Use caution when introducing", "desc", None)]))
    E.append(R("example-traps", "Example Traps", section("Example Traps", 3, page=199, stop_titles=("Collapsing Roof",)), "Gameplay Toolbox/Traps/Example Traps",
               [(None, "rule", {"id": "order", "alphabetical": True})]))
    E += traps()
    E.append(R("marching-order", "Marching Order", sidebar("Marching Order"), "Playing the Game/Exploration/Marching Order (sidebar)", [
        (None, "rule", {"id": "marching_order", "determines": ["traps_affected", "spotting_hidden_enemies", "closest_in_fight"], "change": "outside combat"})]))
    return E


def trap(name, page, items):
    e = INV[("trap", name)]
    nodes = section(name, 4, page=page)
    sev = re.findall(r"(Deadly|Nuisance) Trap \(Levels (\d+)–(\d+)\)", nodes[0].text)
    facets = {"severity": [s.lower() for s, _, _ in sev], "min_level": min(int(a) for _, a, _ in sev)}
    data = {"severity": [{"severity": s.lower(), "levels": [int(a), int(b)]} for s, a, b in sev]}
    plan = [(None, "sys", ["/facets", "/data/severity"]), ("**Trigger:**", "rule", {"id": "trigger", "text": re.sub(r"\*\*Trigger:\*\* ", "", nodes[1].text).split("**")[0].strip()}),
            ("**Duration:**", "rule", {"id": "duration", "text": re.search(r"\*\*Duration:\*\* (.+)$", " ".join(n.text for n in nodes[1:3])).group(1)})]
    return build("trap", e["ref"].split("/")[-1], name, nodes, LOT, f"Gameplay Toolbox/Traps/Example Traps/{name}", plan + items, facets=facets, data=data)


def tab(nodes, cols, tid="higher_levels"):
    return {"id": tid, "caption": "At Higher Levels", "columns": cols, "rows": table_rows(nodes)}


def traps():
    E = []
    detect = lambda ab, sk, dc, note: {"op": "check", "ability": ab, "skill": sk, "dc": dc, "note": note}  # noqa: E731
    cr = section("Collapsing Roof", 4, page=199)
    E.append(trap("Collapsing Roof", 199, [
        ("This trap uses a trip wire", "rule", {"id": "trip_wire", "height_inches": 3}),
        ("The first creature that crosses", "fx", save("dex", 13, {"op": "damage", "amount": "2d10", "damage_type": "bludgeoning"}, half_on_success=True,
                                                         note="Each creature beneath the section; rubble becomes Difficult Terrain.")),
        ("***Detect and Disarm.***", "fx", detect("wis", "perception", 11, "Search action; once detected the wire is cut or avoided without a check.")),
        ("***At Higher Levels.***", "table", tab(cr, ["Levels", "Bludgeoning Damage", "Save DC"]))]))
    E.append(trap("Falling Net", 199, [
        ("A falling net trap", "rule", {"id": "net", "square_feet": 10, "trip_wire_inches": 3, "item": "dnd5e/gear/net"}),
        ("The first creature that crosses", "fx", save("dex", 10, {"op": "apply_condition", "condition": C("restrained")},
                                                        note="Huge or larger succeed automatically; an action and a DC 10 Strength (Athletics) check frees a creature within reach.")),
        ("***Detect and Disarm.***", "fx", detect("wis", "perception", 11, "Search action.")),
        ("***Destroy the Net.***", "ref", ["dnd5e/gear/net"]),
        ("***Set the Trap.***", "fx", {"op": "check", "ability": "dex", "skill": "sleight_of_hand", "dc": 13, "note": "Needs Thieves' Tools and the components; 10 minutes per attempt."}),
        ("***At Higher Levels.***", "rule", {"id": "higher_levels", "dc_by_levels": {"5-10": 12, "11-16": 14, "17-20": 16}})]))
    fc = section("Fire-Casting Statue", 4, page=199)
    E.append(trap("Fire-Casting Statue", 199, [
        ("When a creature moves onto", "fx", save("dex", 15, {"op": "damage", "amount": "2d10", "damage_type": "fire"}, half_on_success=True,
                                                   target={"kind": "area", "area": {"shape": "cone", "size_feet": 15, "origin": "object"}})),
        ("***Detect and Disarm.***", "rule", {"id": "detect", "detect_magic": "evocation aura", "search": {"skill": "perception", "dc": 10},
                                              "study": {"skill": "arcana", "dc": 15}, "disarm": "deface the glyph (action)"}),
        ("As a Search action, a creature can examine the section", "fx", detect("wis", "perception", 15, "Pressure plate; an Iron Spike under it prevents triggering.")),
        ("***At Higher Levels.***", "table", tab(fc, ["Levels", "Fire Damage", "Area of Effect"]))]))
    hp = section("Hidden Pit", 4, page=200)
    E.append(trap("Hidden Pit", 200, [
        ("This 10-foot-deep pit", "rule", {"id": "pit", "depth_feet": 10, "lid_stays_open": True}),
        ("A creature that falls into the pit", "fx", {"op": "damage", "amount": "1d6", "damage_type": "bludgeoning"}),
        ("***Detect and Disarm.***", "fx", detect("int", "investigation", 15, "Study action; an Iron Spike or Arcane Lock keeps the lid shut.")),
        ("***Escape.***", "rule", {"id": "escape", "requires_any": ["climb_speed", "climbing_gear", SP("spider-climb")]}),
        ("***At Higher Levels.***", "table", tab(hp, ["Levels", "Pit Depth", "Bludgeoning Damage"]))]))
    E.append(trap("Poisoned Darts", 200, [
        ("When a creature moves onto", "desc", None),
        ("Each creature in the darts’ path", "fx", save("dex", 13, {"op": "repeat", "times": "1d3", "then": [{"op": "damage", "amount": "1d6", "damage_type": "poison"}],
                                                                    "note": "Struck by 1d3 darts, 1d6 Poison damage each."})),
        ("***Detect and Disarm.***", "fx", detect("wis", "perception", 15, "Search action: the holes; plugging them prevents firing.")),
        ("As a Search action, a creature can examine the section", "fx", detect("wis", "perception", 15, "The pressure plate; an Iron Spike prevents triggering.")),
        ("***At Higher Levels.***", "rule", {"id": "higher_levels", "dart_damage": {"5-10": "2d6", "11-16": "4d6", "17-20": "7d6"}})]))
    pn = section("Poisoned Needle", 4, page=200)
    E.append(trap("Poisoned Needle", 200, [
        ("A poisoned needle is hidden", "fx", save("con", 11, [{"op": "damage", "amount": "1d10", "damage_type": "poison"},
                                                                {"op": "apply_condition", "condition": C("poisoned"), "duration": {"kind": "hours", "amount": 1}}],
                                                    half_on_success=True, note="On a success, half damage only.")),
        ("***Avoid.***", "rule", {"id": "avoid", "knock_bypasses": SP("knock")}),
        ("***Detect and Disarm.***", "fx", [detect("wis", "perception", 15, "Search action."),
                                            {"op": "check", "ability": "dex", "skill": "sleight_of_hand", "dc": 15, "note": "Disarm (action); failure triggers the trap."}]),
        ("***At Higher Levels.***", "table", tab(pn, ["Levels", "Poison Damage", "Save DC"]))]))
    E.append(trap("Rolling Stone", 201, [
        ("When a creature moves onto a hidden", "rule", {"id": "stone", "radius_feet": 5, "initiative_bonus": 8}),
        ("On its turn, the stone moves", "fx", save("dex", 15, [{"op": "damage", "amount": "10d10", "damage_type": "bludgeoning"},
                                                                 {"op": "apply_condition", "condition": C("prone")}],
                                                     note="Moves 60 feet a turn; its space is Difficult Terrain.")),
        ("The stone stops when", "rule", {"id": "stop", "on": "wall or barrier", "no_corners": True}),
        ("***Detect and Disarm.***", "fx", detect("int", "investigation", 15, "Study action; an Iron Spike prevents triggering.")),
        ("***Destroy the Stone.***", "rule", {"id": "object", "size": "large", "ac": 17, "hp": 100, "damage_threshold": 10, "immunities": ["poison", "psychic"]}),
        ("***Slow the Stone.***", "fx", {"op": "check", "ability": "str", "skill": "athletics", "dc": 20, "note": "Action; success reduces its movement by 15 feet."})]))
    spk = section("Spiked Pit", 4, page=201)
    E.append(trap("Spiked Pit", 201, [
        ("A 10-foot-deep pit", "rule", {"id": "pit", "depth_feet": 10, "spikes": True}),
        ("A creature that falls into the pit", "fx", [{"op": "damage", "amount": "1d6", "damage_type": "bludgeoning"},
                                                      {"op": "damage", "amount": "2d8", "damage_type": "piercing"}]),
        ("***Detect and Disarm.***", "fx", detect("int", "investigation", 15, "Study action.")),
        ("***Escape.***", "rule", {"id": "escape", "requires_any": ["climb_speed", "climbing_gear", SP("spider-climb")]}),
        ("***At Higher Levels.***", "table", tab(spk, ["Levels", "Pit Depth", "Damage"]))]))
    return E


def glossary_terms():
    G = lambda n, items, **kw: glossary(n, "rule", LOT, items, **kw)  # noqa: E731
    sight = lambda feet_kind: {"op": "sense", "sense": feet_kind, "range_feet": {"var": "sense_range"}}  # noqa: E731
    return [
        G("Blindsight", [(None, "fx", sight("blindsight")), (None, "rule", {"id": "blindsight", "ignores": ["blinded", "darkness", "invisible"], "blocked_by": "total_cover"})]),
        G("Bright Light", [(None, "rule", {"id": "bright_light", "normal_illumination": True}), ("*See also*", "ref", ["dnd5e/rule/vision-and-light"])]),
        G("Curses", [(None, "rule", {"id": "curses", "removed_by": [SP("remove-curse"), SP("greater-restoration")]})]),
        G("Darkness", [(None, "rule", {"id": "darkness", "obscurement": "dnd5e/rule/heavily-obscured"}), ("*See also*", "ref", ["dnd5e/rule/vision-and-light"])]),
        G("Darkvision", [(None, "fx", sight("darkvision")), (None, "rule", {"id": "darkvision", "dim_as_bright": True, "darkness_as_dim": True, "colors": "gray"}),
                         ("*See also*", "ref", ["dnd5e/rule/vision-and-light"])]),
        G("Dim Light", [(None, "rule", {"id": "dim_light", "obscurement": "dnd5e/rule/lightly-obscured"}), ("*See also*", "ref", ["dnd5e/rule/vision-and-light"])]),
        G("Encounter", [(None, "rule", {"id": "encounter", "pillars": ["social_interaction", "exploration", "combat"]})]),
        G("Heavily Obscured", [(None, "fx", {"op": "apply_condition", "condition": C("blinded"), "when": {"pred": "heavily_obscured"}}),
                               ("*See also*", "ref", ["dnd5e/condition/blinded", "dnd5e/rule/darkness", "dnd5e/rule/vision-and-light"])]),
        G("Lightly Obscured", [(None, "fx", adv("ability_check", {"all": [{"pred": "in_lightly_obscured_area"}, skill("perception"), {"pred": "requires_sight"}]}, mode="disadvantage")),
                               ("*See also*", "ref", ["dnd5e/rule/dim-light", "dnd5e/rule/vision-and-light"])]),
        G("Tremorsense", [(None, "fx", sight("tremorsense")), (None, "rule", {"id": "tremorsense", "same_surface_or_liquid": True}),
                          ("Tremorsense can’t detect", "rule", {"id": "limits", "not_in_air": True, "not_sight": True})]),
        G("Truesight", [(None, "fx", sight("truesight")),
                        ("**Darkness.**", "rule", {"id": "darkness", "sees_in": ["normal_darkness", "magical_darkness"]}),
                        ("**Invisibility.**", "rule", {"id": "invisibility", "sees_invisible": True}),
                        ("**Visual Illusions.**", "rule", {"id": "illusions", "transparent": True, "auto_succeed_saves": True}),
                        ("**Transformations.**", "rule", {"id": "transformations", "true_form": True}),
                        ("**Ethereal Plane.**", "rule", {"id": "ethereal", "sees_into": "ethereal_plane"})]),
    ]


REGISTRY = {
    "predicates": [
        {"id": "in_lightly_obscured_area", "description": "The thing the creature tries to see is in a Lightly Obscured area.", "type": "predicate", "pages": [11]},
        {"id": "travel_hours_over", "description": "The group has traveled more than N hours today (param: hours).", "params": ["hours"], "type": "predicate", "pages": [192]},
        {"id": "save_against_contagion", "description": "The saving throw is made to fight off a magical contagion.", "type": "predicate", "pages": [194]},
        {"id": "minutes_exceed_con_score", "description": "Minutes spent in frigid water exceed the creature's Constitution score.", "type": "predicate", "pages": [195]},
    ],
    "variables": [
        {"id": "travel_hours_over_8", "description": "Hours of travel beyond 8 today.", "type": "number", "pages": [192]},
        {"id": "hours_exposed", "description": "Hours of exposure so far (first hour = 1).", "type": "number", "pages": [195]},
        {"id": "sense_range", "description": "Range in feet of the special sense given in the creature's stat block or feature.", "type": "number", "pages": [177]},
    ],
}

if __name__ == "__main__":
    extend_registries(REGISTRY, LOT)
    out = exploration() + toolbox() + glossary_terms()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
