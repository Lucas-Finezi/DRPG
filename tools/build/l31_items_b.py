#!/usr/bin/env python3
"""L31 — Magic items A–Z, part 2 (Cubic Gate … Hat of Many Spells) and the Giant Fly stat block.

Usage: python3 -I tools/build/l31_items_b.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import NODES, extend_registries, find, write_entry  # noqa: E402
from magiclib import (DIES, ATTUNED, BONUS, CR, DAWN, HOLD, INHERIT, MI, SELF, SP, THIS, WEAR, WIELD, act, adv, area,  # noqa: E402
                      cast, charges, check, cond, creature, dmg, hours, item_nodes, md, mins, mod, ref, resist,
                      rows_of, save, sense, setv, speed, spells_table, tab, trig, until_turn, while_)
from l31_registry import REGISTRY  # noqa: E402
from statblock import creature_entry  # noqa: E402

LOT = "L31"
EACH_END = {"on": {"event": "turn_end", "whose": "target", "which": "each"}, "ends": "effect_on_self"}


def plus_weapon(n):
    return [mod("attack_roll", n, WIELD), mod("damage_roll", n, WIELD)]


def summon(creature_, dur=None, **kw):
    d = {"op": "summon", "creature": CR(creature_), "controller": "summoner", "initiative": "after_summoner"}
    if dur:
        d["duration"] = dur
    d.update(kw)
    return d


def figurine_nodes():
    """The Giant Fly stat block interrupts the figurine descriptions (p. 222): the text goes on after it."""
    i = find("Figurine of Wondrous Power", 4)
    g = find("Giant Fly", 3, 222)
    j = g + 1
    while not NODES[j].text.startswith("**CR**"):
        j += 1
    k = find("Flame Tongue", 4, None, j)
    return [n for n in NODES[i + 1:g] + NODES[j + 1:k] if not n.sidebar]


def entries():
    E = []
    E.append(MI("Cubic Gate", [
        ("^", "rule", {"id": "cube", "size_inches": 3, "sides": 6, "material_plane_side": True}),
        ("^", "md", md("cube_planes", "Which planes are the other five sides keyed to?", "The other sides are linked to planes determined by the GM.")),
        ("The cube has 3 charges", "fx", charges(3, "1d3")),
        ("***Gate.***", "fx", act(cast("Gate", note="Portal to the plane keyed to the pressed side."), uses=1)),
        ("***Plane Shift.***", "fx", act(cast("Plane Shift", note="Pressing a side twice; to the plane keyed to that side."), uses=1))]))
    E.append(MI("Dagger of Venom", [
        ("^", "fx", plus_weapon(1)),
        ("You can take a Bonus Action to magically coat", "fx", act(
            trig("hits_with_attack_roll", save("con", 15, on_fail=[dmg("2d10", "poison"), cond("poisoned", mins(1))], target=INHERIT),
                 duration={"kind": "minutes", "amount": 1, "ends_on": [{"event": "hits_with_attack_roll"}]},
                 condition={"pred": "attack_uses_weapon", "args": THIS}),
            cost="bonus_action", freq=DAWN))]))
    E.append(MI("Dancing Sword", [
        ("^", "fx", act({"op": "attack", "attack_type": "melee_weapon",
                         "note": "The weapon hovers, flies up to 30 feet and attacks one creature within 5 feet of itself; your attack roll and ability modifier."},
                        cost="bonus_action")),
        ("While the weapon hovers", "fx", act({"op": "attack", "attack_type": "melee_weapon",
                                               "note": "Fly up to 30 feet to a spot within 30 feet of you, then attack one creature within 5 feet of it."},
                                              cost="bonus_action", requires={"pred": "effect_active"})),
        ("After the hovering weapon attacks", "rule", {"id": "return", "after_attacks": 4, "no_free_hand": "falls_in_your_space",
                                                       "obstructed": "moves_close_then_falls",
                                                       "stops_hovering": ["you_grasp_it", "more_than_30_feet_away"]})]))
    E.append(MI("Decanter of Endless Water", [
        ("^", "rule", {"id": "decanter", "weight_lb": 2}),
        ("You can take a Magic action to remove", "fx", act({"op": "choice", "id": "command_word", "choose": 1, "options": [
            {"id": "splash", "label": "Splash: 1 gallon", "effects": [ref("dnd5e/magic-item/decanter-of-endless-water", note="1 gallon.")]},
            {"id": "fountain", "label": "Fountain: 5 gallons", "effects": [ref("dnd5e/magic-item/decanter-of-endless-water", note="5 gallons.")]},
            {"id": "geyser", "label": "Geyser: 30 gallons in a Line", "effects": [
                save("str", 13, on_fail=[dmg("1d4", "bludgeoning"), cond("prone")],
                     target={"kind": "creature", "area": {"shape": "line", "size_feet": 30, "width_feet": 1, "origin": "self"}},
                     note="One creature of your choice in the Line; or knock over one unattended object of 200 lb. or less.")]}],
            "note": "Fresh or salt water (your choice); stops pouring at the start of your next turn."})),
        ("**Splash.**", "sys", ["/effects/0"]),
        ("**Fountain.**", "sys", ["/effects/0"]),
        ("**Geyser.**", "sys", ["/effects/0"])]))
    deck = item_nodes("Deck of Illusions")
    E.append(MI("Deck of Illusions", [
        ("^", "rule", {"id": "deck", "cards": 34, "creature_cards": 32, "mirror_cards": 2, "missing_when_found": "1d20 - 1"}),
        ("The magic of the deck functions", "fx", [
            act(ref("dnd5e/magic-item/deck-of-illusions", duration={"kind": "until_dispelled"},
                    note="Draw a random card, throw it within 30 feet: an illusion of the creature from the table forms over it; it can do no harm.")),
            act({"op": "move", "mode": "move", "note": "Move the illusion anywhere within 30 feet of its card."},
                requires={"pred": "within_feet", "args": {"feet": 120}})]),
        ("Any physical interaction", "rule", {"id": "discern", "physical_interaction_reveals": True,
                                              "study": {"action": "dnd5e/action/study", "check": "int.investigation", "dc": 15},
                                              "ends": ["card_moved", "dispelled"], "dispel": SP("Dispel Magic"), "card_used_up": True}),
        ("##### Deck of Illusions", "table", tab("Deck of Illusions", ["1d100", "Illusion"], rows_of(deck))),
        ("\\*Stat blocks", "ref", ["dnd5e/rule/monsters"])]))
    E.append(MI("Defender", [
        ("^", "fx", plus_weapon(3)),
        ("The first time you attack", "fx", trig({"event": "attack_roll_made", "which": "each"},
                                                 {"op": "choice", "id": "transfer", "choose": 1, "options": [
                                                     {"id": f"ac_{k}", "label": f"Transfer {k} to AC",
                                                      "effects": [mod("attack_roll", -k, WIELD, duration=until_turn()),
                                                                  mod("damage_roll", -k, WIELD, duration=until_turn()),
                                                                  mod("ac", k, HOLD, duration=until_turn())]} for k in (0, 1, 2, 3)]},
                                                 condition={"all": [{"pred": "first_attack_this_turn"},
                                                                    {"pred": "attack_uses_weapon", "args": THIS}]},
                                                 optional=True))]))
    E.append(MI("Demon Armor", [
        ("^", "fx", [mod("ac", 1, WEAR),
                     {"op": "proficiency", "category": "language", "items": ["abyssal"], "when": WEAR},
                     setv("weapon_damage_die", "1d8", {"all": [WEAR, {"pred": "attack_is_unarmed_strike"}]}, note="Slashing instead of Bludgeoning."),
                     mod("attack_roll", 1, {"all": [WEAR, {"pred": "attack_is_unarmed_strike"}]}),
                     mod("damage_roll", 1, {"all": [WEAR, {"pred": "attack_is_unarmed_strike"}]})]),
        ("***Curse.***", "ref", ["dnd5e/rule/cursed-items"]),
        ("***Curse.***", "rule", {"id": "curse", "cannot_doff": True, "ends_by": [SP("Remove Curse")]}),
        ("***Curse.***", "fx", [adv("attack_roll", {"all": [WEAR, {"pred": "creature_has_tag", "args": {"tags": ["demon"]}}]}, mode="disadvantage"),
                                adv("saving_throw", {"all": [WEAR, {"pred": "source_has_tag", "args": {"tags": ["demon"]}}]}, mode="disadvantage",
                                    note="Against their spells and special abilities.")])]))
    E.append(MI("Dimensional Shackles", [
        ("^", "fx", act({"op": "restrict", "restrictions": ["teleport_or_planar_travel_in_area"],
                         "target": {"kind": "creature", "filter": {"sizes": ["small", "medium", "large"], "predicate": {"pred": "has_condition", "args": {"condition": "incapacitated"}}}},
                         "note": "Any extradimensional movement; interdimensional portals still work."},
                        cost="action", action="dnd5e/action/utilize")),
        ("You and any creature you designate", "rule", {"id": "removal", "action": "dnd5e/action/utilize", "by": ["you", "designated"],
                                                        "escape": {"every_days": 30, "check": "str.athletics", "dc": 30, "destroys_shackles": True}})]))
    orb = item_nodes("Dragon Orb")
    E.append(MI("Dragon Orb", [
        ("^", "rule", {"id": "orb", "diameter_inches": 10, "used_diameter_inches": 20}),
        ("While attuned to an orb", "fx", act(save("cha", 15, on_success=ref("dnd5e/magic-item/dragon-orb", note="You control the orb while attuned."),
                                                   on_fail=cond("charmed", while_(ATTUNED))), requires=ATTUNED)),
        ("While you are Charmed by the orb", "fx", [{"op": "restrict", "restrictions": ["end_attunement_voluntarily"],
                                                    "when": {"pred": "has_condition_from", "args": {"condition": "charmed", "source": "this"}}},
                                                   cast("Suggestion", dc=18, target=SELF, note="The orb casts it on you at will.")]),
        ("While you are Charmed by the orb", "md", md("orb_goals", "What does the dragon essence in the orb want?",
                                                      "The dragon essence within the orb might want many things: ... or something else the GM decides.")),
        ("***Spells.***", "fx", [charges(7, "1d4 + 3")] + spells_table([("Cure Wounds", 4, 9), ("Daylight", 1), ("Death Ward", 2),
                                                                        ("Detect Magic", 0), ("Scrying", 3)], dc=18)),
        ("| **Spell**", "table", tab("Dragon Orb Spells", ["Spell", "Charge Cost"], rows_of(orb))),
        ("***Call Dragons.***", "fx", act(ref("dnd5e/magic-item/dragon-orb", note="Telepathic call, 40 miles: chromatic dragons feel compelled to come; dragon deities unaffected; they might be Hostile."),
                                          freq={"count": 1, "per": "hour"}, requires={"pred": "controls_item", "args": THIS})),
        ("***Destroying an Orb.***", "rule", {"id": "destruction", "ac": 20,
                                              "destroyed_by": ["dnd5e/magic-item/weapon-plus1-plus2-or-plus3#+3", SP("Disintegrate")],
                                              "otherwise_immune": True})]))
    dsm = item_nodes("Dragon Scale Mail")
    E.append(MI("Dragon Scale Mail", [
        ("^", "desc", None),
        ("While wearing this armor", "fx", [mod("ac", 1, WEAR),
                                           adv("saving_throw", {"all": [WEAR, {"pred": "save_against_effect_of_types", "args": {"effect": "breath_weapon", "types": ["dragon"]}}]}),
                                           resist([{"var": "chosen.dragon_kind"}], WEAR, note="Type from the table, by the dragon that provided the scales.")]),
        ("Additionally, you can focus", "fx", act(ref("dnd5e/magic-item/dragon-scale-mail",
                                                       note="Learn distance and direction to the closest dragon of the armor's type within 30 miles."),
                                                   freq=DAWN, requires=WEAR)),
        ("| **Dragon**", "table", tab("Dragon Scale Mail", ["Dragon", "Resistance", "Dragon", "Resistance"], rows_of(dsm)))]))
    E.append(MI("Dragon Slayer", [
        ("^", "fx", plus_weapon(1)),
        ("The weapon deals an extra", "fx", trig("hits_with_attack_roll", dmg("3d6", {"var": "weapon_damage_type"}, target=INHERIT),
                                                 condition={"all": [{"pred": "attack_uses_weapon", "args": THIS},
                                                                    {"pred": "creature_type_in", "args": {"types": ["dragon"]}}]}))]))
    E.append(MI("Dust of Disappearance", [
        ("^", "fx", act(cond("invisible", {"kind": "minutes", "amount": "2d4",
                                           "ends_on": [{"event": "attacks_deals_damage_or_casts", "whose": "target"}]},
                             target=area("emanation", 10, origin="self"),
                             note="You and each creature and object in the area; same duration for all; ends for a creature right after it attacks, deals damage or casts a spell."),
                        cost="action", action="dnd5e/action/utilize")),
        ("^", "rule", {"id": "single_use", "consumed": True})]))
    E.append(MI("Dust of Dryness", [
        ("^", "rule", {"id": "pinches", "count": "1d6 + 4"}),
        ("^", "fx", act(ref("dnd5e/magic-item/dust-of-dryness", note="Up to a 15-foot Cube of water becomes a marble-sized pellet."),
                        cost="action", action="dnd5e/action/utilize")),
        ("^", "rule", {"id": "pellet", "weight": "negligible", "smash": {"action": "dnd5e/action/utilize", "releases_water": True}}),
        ("As a Utilize action, you can sprinkle a pinch of the dust on an Elemental", "fx", act(
            save("con", 13, on_fail=dmg("10d6", "necrotic"), half=True,
                 target={"kind": "creature", "range": {"kind": "distance", "feet": 5}, "filter": {"creature_types": ["elemental"]}},
                 note="An Elemental composed mostly of water (e.g. Water Elemental)."),
            cost="action", action="dnd5e/action/utilize"))]))
    E.append(MI("Dust of Sneezing and Choking", [
        ("^", "rule", {"id": "disguise", "resembles": "dnd5e/magic-item/dust-of-disappearance", "identify_reveals_as": "dnd5e/magic-item/dust-of-disappearance",
                       "uses": 1}),
        ("As a Utilize action, you can throw", "fx", act(save("con", 15, on_fail=[cond("incapacitated"), ref("dnd5e/hazard/suffocation")],
                                                              target=area("emanation", 30, origin="self", include_self=True), repeat=EACH_END,
                                                              note="Constructs, Elementals, Oozes, Plants and Undead succeed automatically. Lesser Restoration ends it."),
                                                         cost="action", action="dnd5e/action/utilize")),
        ("On a failed save", "sys", ["/effects/0"])]))
    E.append(MI("Dwarven Plate", [
        ("^", "fx", [mod("ac", 2, WEAR),
                     trig({"event": "moved_against_will_along_ground", "which": "each"},
                          ref("dnd5e/magic-item/dwarven-plate", note="Reduce the distance moved by up to 10 feet."),
                          cost="reaction", optional=True, condition=WEAR)])]))
    E.append(MI("Dwarven Thrower", [
        ("^", "fx", plus_weapon(3) + [
            {"op": "grant", "refs": ["dnd5e/weapon-property/thrown"], "when": WIELD, "note": "Normal range 20 feet, long range 60 feet."},
            trig("hits_with_attack_roll", {"op": "choice", "id": "giant", "choose": 1, "options": [
                {"id": "giant", "label": "Target is a Giant", "effects": [dmg("2d8", "force", target=INHERIT)]},
                {"id": "other", "label": "Other target", "effects": [dmg("1d8", "force", target=INHERIT)]}]},
                 condition={"all": [{"pred": "attack_uses_weapon", "args": THIS}, {"pred": "attack_is_ranged"}]})]),
        ("^", "rule", {"id": "returning", "returns_to_hand": "immediately after hitting or missing"})],
        data={"item": {"attunement": {"required": True, "by": "a Dwarf or a Creature Attuned to a Belt of Dwarvenkind",
                                      "species": ["dwarf"], "or_attuned_to": "dnd5e/magic-item/belt-of-dwarvenkind"}}}))
    E.append(MI("Efficient Quiver", [
        ("^", "rule", {"id": "compartments", "max_weight_lb": 2,
                       "short": {"holds": 60, "of": ["dnd5e/gear/ammunition-arrows", "dnd5e/gear/ammunition-bolts"]},
                       "midsize": {"holds": 18, "of": ["dnd5e/weapon/javelin"]},
                       "long": {"holds": 6, "of": ["bows", "dnd5e/weapon/quarterstaff", "dnd5e/weapon/spear"]}}),
        ("You can draw any item", "rule", {"id": "draw", "as_regular_quiver": True})]))
    E.append(MI("Efreeti Bottle", [
        ("^", "fx", act(summon("Efreeti", note="Appears at the end of your turn within 30 feet."))),
        ("The first time the bottle is opened", "md", md("efreeti_roll", "Roll 1d10 the first time the bottle is opened.",
                                                         "The first time the bottle is opened, the GM rolls on the following table to determine what happens.",
                                                         reason="not_automatable")),
        ("| **1d10**", "table", tab("Efreeti Bottle", ["1d10", "Effect"], rows_of(item_nodes("Efreeti Bottle"))))]))
    eg = item_nodes("Elemental Gem")
    E.append(MI("Elemental Gem", [
        ("^", "desc", None),
        ("When you take a Utilize action to break", "fx", act({"op": "choice", "id": "gem", "choose": 1, "note": "The gem's type determines the elemental.",
                                                              "options": [{"id": r[0].lower().replace(" ", "_"), "label": r[0],
                                                                           "effects": [summon(r[1], hours(1))]} for r in rows_of(eg)]},
                                                             cost="action", action="dnd5e/action/utilize")),
        ("When you take a Utilize action to break", "rule", {"id": "elemental", "single_use": True, "dismiss": "bonus_action",
                                                             "ends_on": ["1_hour", "dies", "dismissed"]}),
        ("| **Gem**", "table", tab("Elemental Gem", ["Gem", "Summoned Elemental"], rows_of(eg)))]))
    E.append(MI("Elven Chain", [
        ("^", "fx", [mod("ac", 1, WEAR),
                     {"op": "proficiency", "category": "armor", "items": ["dnd5e/armor/chain-mail", "dnd5e/armor/chain-shirt"],
                      "note": "Considered trained with this armor."}])]))
    E.append(MI("Energy Bow", [
        ("^", "fx", plus_weapon(1)),
        ("^", "rule", {"id": "energy_arrows", "string": False, "arrow_appears_on_draw": True, "damage_type": "force",
                       "replaces": "piercing", "vanishes_after_hit_or_miss": True}),
        ("^", "rule", {"id": "arrow_light", "bright_feet": 20, "dim_feet": 20, "rules": ["dnd5e/rule/bright-light", "dnd5e/rule/dim-light"]}),
        ("This weapon has the following", "desc", None),
        ("***Arrow of Restraint.***", "fx", trig("hits_with_attack_roll", save("str", 15, on_fail=cond("restrained", mins(1)), target=INHERIT,
                                                                               note="Instead of damage. The creature can take an action: DC 20 Strength (Athletics) check ends it."),
                                                 optional=True, condition={"pred": "attack_uses_weapon", "args": THIS})),
        ("***Arrow of Transport.***", "fx", act({"op": "move", "mode": "teleport",
                                                 "target": {"kind": "creature_or_object", "range": {"kind": "distance", "feet": 60}, "must_see": True},
                                                 "note": "Willing Medium or smaller creature, or an unattended object that fits in a 5-foot Cube: to a space you can see within 10 feet of you."})),
        ("***Energy Ladder.***", "fx", act(ref("dnd5e/magic-item/energy-bow", duration=mins(1), note="A ladder up to 60 feet long on a wall up to 60 feet away.")))]))
    E.append(MI("Eversmoking Bottle", [
        ("^", "rule", {"id": "toggle", "open_close": "dnd5e/action/magic"}),
        ("Opening the bottle", "fx", ref("dnd5e/rule/heavily-obscured", target=area("emanation", 60, origin="object"))),
        ("Each minute the bottle", "rule", {"id": "growth", "per_minute_feet": 10, "max_feet": 120}),
        ("Closing the bottle", "rule", {"id": "disperse", "closed_minutes": 10, "strong_wind_minutes": 1, "wind_example": SP("Gust of Wind")})]))
    E.append(MI("Eyes of Charming", [
        ("^", "fx", [charges(3, "all"),
                     act(cast("Charm Person", dc=13, level={"op": "add", "args": [{"var": "charges_spent"}, 0]},
                              note="Level = charges expended (1 charge = level 1)."), uses={"var": "charges_spent"}, requires=WEAR)])]))
    E.append(MI("Eyes of Minute Seeing", [
        ("^", "fx", [sense("darkvision", 1, WEAR),
                     adv("ability_check", {"all": [WEAR, {"pred": "check_uses_skill", "args": {"skill": "investigation"}},
                                                   {"pred": "within_feet", "args": {"feet": 1}}]})])]))
    E.append(MI("Eyes of the Eagle", [
        ("^", "fx", adv("ability_check", {"all": [WEAR, {"pred": "check_uses_skill", "args": {"skill": "perception"}}, {"pred": "requires_sight"}]})),
        ("^", "rule", {"id": "distant_details", "min_size_feet": 2, "requires": "clear_visibility"})]))
    ft = item_nodes("Feather Token")
    E.append(MI("Feather Token", [
        ("^", "md", md("token_kind", "Which kind of feather token is this? (choose or roll on the Feather Tokens table)",
                       "The GM chooses the kind of token or determines it randomly by rolling on the Feather Tokens table.")),
        ("***Anchor (Uncommon).***", "fx", act(ref("dnd5e/magic-item/feather-token", duration=hours(24), note="Anchor: the touched boat or ship can't be moved by any means; touching again ends it; the token disappears."))),
        ("***Bird (Rare).***", "fx", act(summon("Roc", note="Bird: Roc statistics but can't attack; carries 500 lb. at 16 mph (144 miles/day, 1-hour rest every 3 hours) or 1,000 lb. at half speed; dismiss as a Magic action."))),
        ("***Fan (Uncommon).***", "fx", act(ref("dnd5e/magic-item/feather-token", duration=hours(8), note="Fan: one ship's speed +5 mph; dismiss as a Magic action."),
                                            requires={"pred": "on_vessel"})),
        ("***Swan Boat (Rare).***", "fx", act(ref("dnd5e/magic-item/feather-token", duration=hours(24),
                                                  note="Swan Boat: 50 by 20 feet, 6 mph; Magic action to move or turn 90 degrees; dismiss as a Magic action."))),
        ("***Tree (Uncommon).***", "fx", act(ref("dnd5e/magic-item/feather-token", note="Tree: nonmagical oak, 60 feet tall, 5-foot trunk, 20-foot crown radius; outdoors only."))),
        ("***Whip (Rare).***", "fx", [act(ref("dnd5e/magic-item/feather-token", duration=hours(1), note="Whip: floats at a point within 10 feet.")),
                                      act({"op": "attack", "attack_type": "melee_spell", "bonus": 9, "on_hit": [dmg("1d6 + 5", "force")],
                                           "note": "Against a creature within 10 feet of the whip; the whip may first fly up to 20 feet."},
                                          cost="bonus_action", requires={"pred": "effect_active"})]),
        ("As a Bonus Action, you can direct", "rule", {"id": "whip_end", "ends_on": ["1_hour", "dismissed_magic_action", "you_die", "you_incapacitated"]}),
        ("##### Feather Tokens", "table", tab("Feather Tokens", ["1d100", "Token", "Rarity"], rows_of(ft)))]))
    fig = figurine_nodes()

    def fig_fx(name, creature_, hours_, recharge_days, **kw):
        return {"op": "activation", "cost": "action", "action": "dnd5e/action/magic", "name": name,
                "then": [summon(creature_, hours(hours_, up_to=True), **kw)],
                "note": f"Can't be used again until {recharge_days} days have passed."}
    E.append(MI("Figurine of Wondrous Power", [
        ("^", "rule", {"id": "throw", "range_feet": 60, "fails_if_space_occupied_or_too_small": True}),
        ("The creature is Friendly", "rule", {"id": "creature", "attitude": "friendly", "understands_your_languages": True,
                                              "initiative": "after_you", "no_commands": "defends_only"}),
        ("The creature exists for a duration", "rule", {"id": "revert", "on": ["duration_ends", "drops_to_0_hp", "magic_action_while_touching"],
                                                        "recharge": "per figurine"}),
        ("***Bronze Griffon (Rare).***", "fx", fig_fx("Bronze Griffon", "Griffon", 6, 5)),
        ("***Ebony Fly (Rare).***", "fx", fig_fx("Ebony Fly", "Giant Fly", 12, 2, note="Can be ridden as a mount.")),
        ("***Golden Lions (Rare).***", "fx", fig_fx("Golden Lions", "Lion", 1, 7, count=2, note="A pair; use one or both.")),
        ("***Ivory Goats (Rare).***", "desc", None),
        ("**Goat of Terror.**", "fx", [fig_fx("Goat of Terror", "Giant Goat", 3, 15, note="Can't attack; its horns become a +1 Lance and a +2 Longsword (Magic action to remove)."),
                                       trig({"event": "turn_start", "whose": "any", "which": "each"},
                                            save("wis", 15, on_fail=cond("frightened", mins(1)), repeat=EACH_END,
                                                 target={"kind": "creature", "area": {"shape": "emanation", "size_feet": 30, "origin": "point", "moves_with_origin": True},
                                                         "filter": {"enemies_only": True}},
                                                 note="While you ride the goat; a creature that succeeds is immune for 24 hours."),
                                            condition={"pred": "riding_item", "args": THIS})]),
        ("**Goat of Traveling.**", "fx", [fig_fx("Goat of Traveling", "Riding Horse", 24, 7, note="A Large goat with the statistics of a Riding Horse."),
                                          charges(24, note="1 charge per hour or portion in goat form; when empty it reverts and recharges all after 7 days.")]),
        ("**Goat of Travail.**", "fx", fig_fx("Goat of Travail", "Giant Goat", 3, 30)),
        ("***Marble Elephant (Rare).***", "fx", fig_fx("Marble Elephant", "Elephant", 24, 7)),
        ("***Obsidian Steed (Very Rare).***", "fx", fig_fx("Obsidian Steed", "Nightmare", 24, 5, note="Fights only to defend itself.")),
        ("The figurine has a 10 percent chance", "rule", {"id": "obsidian_disobey", "chance_percent": 10,
                                                          "mount_while_disobeying": "both transported to a random location in Hades"}),
        ("***Onyx Dog (Rare).***", "fx", fig_fx("Onyx Dog", "Mastiff", 6, 7, note="Intelligence 8, speaks Common, Blindsight 60 feet.")),
        ("***Serpentine Owl (Rare).***", "fx", fig_fx("Serpentine Owl", "Giant Owl", 8, 2, note="Telepathy with you at any range on the same plane.")),
        ("***Silver Raven (Uncommon).***", "fx", [fig_fx("Silver Raven", "Raven", 12, 2),
                                                  cast("Animal Messenger", note="On the raven, while it is in raven form.")])],
        nodes=fig))
    E.append(creature_entry("Giant Fly", 222, LOT, "Magic Items/Magic Items A–Z/Figurine of Wondrous Power/Giant Fly", end_at_cr=True))
    E.append(MI("Flame Tongue", [
        ("^", "fx", act([trig("hits_with_attack_roll", dmg("2d6", "fire", target=INHERIT), condition={"pred": "attack_uses_weapon", "args": THIS})],
                        cost="bonus_action", requires=HOLD,
                        note="Command word; until you repeat it as a Bonus Action or drop, stow or sheathe the weapon.")),
        ("^", "rule", {"id": "light", "bright_feet": 40, "dim_feet": 40, "rules": ["dnd5e/rule/bright-light", "dnd5e/rule/dim-light"]})]))
    E.append(MI("Folding Boat", [
        ("^", "rule", {"id": "box", "inches": [12, 6, 6], "weight_lb": 4, "floats": True, "storage": True}),
        ("^", "fx", act({"op": "choice", "id": "command_word", "choose": 1, "options": [
            {"id": "first", "label": "Rowboat", "effects": [ref("dnd5e/vehicle/rowboat")]},
            {"id": "second", "label": "Keelboat", "effects": [ref("dnd5e/vehicle/keelboat")]},
            {"id": "third", "label": "Fold back", "effects": [ref("dnd5e/magic-item/folding-boat", note="Only if no creatures are aboard.")]}]})),
        ("**First Command Word.**", "sys", ["/effects/0"]),
        ("**Second Command Word.**", "sys", ["/effects/0"]),
        ("**Third Command Word.**", "sys", ["/effects/0"]),
        ("When the box becomes a vessel", "rule", {"id": "vessel", "weight": "normal_vessel", "stored_items_remain": True}),
        ("Statistics for the Rowboat", "ref", ["dnd5e/vehicle/rowboat", "dnd5e/vehicle/keelboat"]),
        ("Statistics for the Rowboat", "rule", {"id": "destroyed", "vessel_at_0_hp": True})]))
    E.append(MI("Frost Brand", [
        ("^", "fx", [trig("hits_with_attack_roll", dmg("1d6", "cold", target=INHERIT), condition={"pred": "attack_uses_weapon", "args": THIS}),
                     resist("fire", HOLD)]),
        ("In freezing temperatures", "rule", {"id": "light", "bright_feet": 10, "dim_feet": 10, "requires": "freezing_temperatures"}),
        ("When you draw this weapon", "fx", trig({"event": "draws_item", "which": "each"},
                                                 ref("dnd5e/magic-item/frost-brand", note="Extinguish all nonmagical flames within 30 feet."),
                                                 optional=True, frequency={"count": 1, "per": "hour"}))]))
    E.append(MI("Gauntlets of Ogre Power", [("^", "fx", setv("ability_score.str", 19, WEAR, note="No effect if your Strength is already 19 or higher."))]))
    E.append(MI("Gem of Brightness", [
        ("^", "fx", [charges(50), act({"op": "choice", "id": "command_word", "choose": 1, "options": [
            {"id": "first", "label": "Light (no charge)", "effects": [ref("dnd5e/rule/bright-light", note="Bright Light 30 feet, Dim Light 30 more; until repeated as a Bonus Action or another function is used.")]},
            {"id": "second", "label": "Beam (1 charge)", "effects": [
                {"op": "spend", "resource": "charges", "amount": 1},
                save("con", 15, on_fail=cond("blinded", mins(1)), repeat=EACH_END, target=creature(60, must_see=True))]},
            {"id": "third", "label": "Flare (5 charges)", "effects": [
                {"op": "spend", "resource": "charges", "amount": 5},
                save("con", 15, on_fail=cond("blinded", mins(1)), repeat=EACH_END, target=area("cone", 30, origin="self"))]}]},
            requires=HOLD)]),
        ("**First Command Word.**", "sys", ["/effects/1"]),
        ("**Second Command Word.**", "sys", ["/effects/1"]),
        ("**Third Command Word.**", "sys", ["/effects/1"]),
        ("When all of the gem’s charges", "rule", {"id": "spent", "becomes": "nonmagical jewel", "worth_gp": 50})]))
    E.append(MI("Gem of Seeing", [
        ("^", "fx", [charges(3), act(sense("truesight", 120, duration=mins(10), note="When you peer through the gem."), uses=1)]),
        ("The gem regains", "fx", charges(3, "1d3"))]))
    E.append(MI("Giant Slayer", [
        ("^", "fx", plus_weapon(1)),
        ("When you hit a Giant", "fx", trig("hits_with_attack_roll", [dmg("2d6", {"var": "weapon_damage_type"}, target=INHERIT),
                                                                      save("str", 15, on_fail=cond("prone"), target=INHERIT)],
                                            condition={"all": [{"pred": "attack_uses_weapon", "args": THIS},
                                                               {"pred": "creature_type_in", "args": {"types": ["giant"]}}]}))]))
    E.append(MI("Glamoured Studded Leather", [
        ("^", "fx", [mod("ac", 1, WEAR),
                     act(ref("dnd5e/magic-item/glamoured-studded-leather", note="Illusory appearance of clothing or other armor; bulk and weight unchanged; lasts until reused or doffed."),
                         cost="bonus_action", requires=WEAR)])]))
    E.append(MI("Gloves of Missile Snaring", [
        ("^", "fx", trig("hit_by_attack_roll", {"op": "modifier", "stat": "damage_taken", "mode": "add",
                                                "value": {"op": "neg", "args": [{"op": "add", "args": ["1d10", {"var": "ability_mod.dex"}]}]},
                                                "note": "If reduced to 0, catch the ammunition or weapon if small enough to hold."},
                         cost="reaction", optional=True,
                         condition={"all": [WEAR, {"pred": "has_hand_free"}, {"pred": "attack_with_weapon_property", "args": {"property": ["ranged", "thrown"]}}]}))]))
    E.append(MI("Gloves of Swimming and Climbing", [
        ("^", "fx", [speed("climb", 0, mode="equal_to_walk", when=WEAR), speed("swim", 0, mode="equal_to_walk", when=WEAR),
                     mod("ability_check", 5, {"all": [WEAR, {"pred": "check_uses_skill", "args": {"skill": "athletics"}},
                                                      {"pred": "check_for_movement", "args": {"modes": ["climb", "swim"]}}]})])]))
    E.append(MI("Gloves of Thievery", [
        ("^", "rule", {"id": "imperceptible", "while_worn": True}),
        ("^", "fx", mod("ability_check", 5, {"all": [WEAR, {"pred": "check_uses_skill", "args": {"skill": "sleight_of_hand"}}]}))]))
    E.append(MI("Goggles of Night", [
        ("^", "fx", [sense("darkvision", 60, WEAR, mode="max"),
                     sense("darkvision", 60, {"all": [WEAR, {"pred": "has_sense", "args": {"sense": "darkvision"}}]}, mode="add")])]))
    E.append(MI("Hammer of Thunderbolts", [
        ("^", "fx", plus_weapon(1)),
        ("The weapon has 5 charges", "fx", [charges(5, "1d4 + 1"),
                                           act({"op": "attack", "attack_type": "ranged_weapon",
                                                "note": "Hurled as if Thrown (20/60 feet); returns to your hand immediately after hitting or missing.",
                                                "on_hit": [save("con", 17, on_fail=cond("stunned", until_turn("turn_end")),
                                                                target={"kind": "creature", "area": {"shape": "emanation", "size_feet": 30, "origin": "target"},
                                                                        "filter": {"include_self": False}},
                                                                note="The target and every creature within 30 feet of it other than you; thunderclap audible to 300 feet.")]},
                                               cost="action", action="dnd5e/action/attack", uses=1)]),
        ("***Giant’s Bane.***", "desc", None),
        ("**Giants’ Bane.**", "fx", trig("rolls_natural_20_attack", save("con", 17, on_fail=DIES, target=INHERIT),
                                         condition={"all": [ATTUNED, {"pred": "attuned_giant_item"},
                                                            {"pred": "attack_uses_weapon", "args": THIS},
                                                            {"pred": "creature_type_in", "args": {"types": ["giant"]}}]})),
        ("**Might of Giants.**", "fx", mod("ability_score.str", 4, {"all": [ATTUNED, {"pred": "attuned_giant_item"}]},
                                           note="Increases the score bestowed by the belt or gauntlets, to a maximum of 30."))]))
    E.append(MI("Handy Haversack", [
        ("^", "rule", {"id": "pouches", "side": {"count": 2, "max_lb": 200, "max_cubic_feet": 25},
                       "central": {"max_lb": 500, "max_cubic_feet": 64}, "weight_lb": 5}),
        ("Retrieving an item", "rule", {"id": "retrieve", "cost": ["dnd5e/action/utilize", "bonus_action"], "item_on_top": True}),
        ("If any of its pouches", "rule", {"id": "destroyed", "on": ["overloaded", "pierced", "torn"], "contents_lost": True,
                                           "artifacts_turn_up": True, "inside_out": "spills_unharmed"}),
        ("Each pouch of the haversack", "rule", {"id": "air", "minutes": 10, "divided_by_breathers": True}),
        ("Placing the haversack", "rule", {"id": "extradimensional_conflict",
                                           "with": ["dnd5e/magic-item/bag-of-holding", "dnd5e/magic-item/portable-hole"],
                                           "both_destroyed": True, "gate": "astral_plane", "one_way": True}),
        ("Placing the haversack", "fx", {"op": "move", "mode": "teleport", "target": area("emanation", 10, origin="point"),
                                         "when": {"not": {"pred": "behind_cover", "args": {"cover": "total"}}},
                                         "note": "Creatures within 10 feet of the gate and not behind Total Cover go to a random location on the Astral Plane."})]))
    E.append(MI("Hat of Disguise", [("^", "fx", act(cast("Disguise Self", note="Ends if the hat is removed."), requires=WEAR))]))
    hat = item_nodes("Hat of Many Spells")
    E.append(MI("Hat of Many Spells", [
        ("^", "desc", None),
        ("***Spellcasting Focus.***", "fx", setv("spellcasting_focus", 1, {"all": [HOLD, {"pred": "spell_of_class", "args": {"class": "wizard"}}]},
                                                 note="Special Somatic component: pull the spell out of the hat.")),
        ("***Unknown Spell.***", "fx", act([{"op": "spend", "resource": "spell_slot", "amount": 1, "level": {"var": "spell_level"}},
                                            check("int", {"op": "add", "args": [10, {"var": "spell_level"}]}, skill="arcana",
                                                  on_success=ref("dnd5e/magic-item/hat-of-many-spells", note="You cast the spell with its normal casting time."),
                                                  on_fail=ref("dnd5e/magic-item/hat-of-many-spells", note="Random effect: roll 1d100 on the table."))],
                                           cost="none", requires=HOLD,
                                           frequency={"count": 1, "per": "short_rest"},
                                           note="A level 1+ Wizard spell you don't know, of a level you can cast, Material components no more than 1,000 GP; the frequency applies on success.")),
        ("Any spell you cast from the hat", "rule", {"id": "numbers", "save_dc": "spell_save_dc", "attack": "spell_attack_bonus"}),
        ("| **1d100**", "table", tab("Hat of Many Spells", ["1d100", "Effect"], rows_of(hat)))]))
    return E


if __name__ == "__main__":
    extend_registries(REGISTRY, LOT)
    out = entries()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
