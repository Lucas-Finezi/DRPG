#!/usr/bin/env python3
"""L31 — Magic item rules: "Magic Items" in Equipment (identifying, attunement, wearing and
wielding) and the "Magic Items" chapter (categories, rarity and values, activation, the next
dawn, curses, resilience, crafting, sentient items), plus the Magic Item Rules sidebar.

Usage: python3 -I tools/build/l31_sections.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import build, extend_registries, md, section, sidebar, table_rows, write_entry  # noqa: E402
from magiclib import SP  # noqa: E402
from l31_registry import REGISTRY  # noqa: E402

LOT = "L31"
SENT = {"op": "reference", "rule": "dnd5e/rule/sentient-magic-item-traits"}


def R(slug, name, nodes, path, items):
    return build("rule", slug, name, nodes, LOT, path, items)


def tab(caption, columns, nodes, tid=None):
    return {"id": tid or caption.lower().replace("’", "").replace(" ", "_"), "caption": caption, "columns": columns,
            "rows": table_rows(nodes)}


def caption_nodes(nodes, caption):
    k = next(i for i, n in enumerate(nodes) if n.type == "h" and n.text == caption)
    out = []
    for n in nodes[k + 1:]:
        if n.type != "t":
            break
        out.append(n)
    return out


def entries():
    E = []
    E.append(R("using-magic-items", "Magic Items (Equipment)", section("Magic Items", 2, page=102, stop_titles=("Identifying a Magic Item",)),
               "Equipment/Magic Items", [(None, "ref", ["dnd5e/rule/magic-items"])]))
    E.append(R("identifying-a-magic-item", "Identifying a Magic Item", section("Identifying a Magic Item", 3, page=102), "Equipment/Magic Items/Identifying a Magic Item", [
        (None, "rule", {"id": "sense", "handling_reveals_extraordinary": True, "properties_automatic": False}),
        ("The *Identify* spell", "rule", {"id": "identify", "spell": SP("Identify"), "short_rest_focus": {"contact": True, "reveals": "properties and use",
                                                                                                      "reveals_curse": False}}),
        ("Sometimes a magic item carries a clue", "desc", None),
        ("Wearing or experimenting", "rule", {"id": "experiment", "potion_taste_reveals": True}),
        ("Wearing or experimenting", "md", md("experiment_hints", "What hints does experimenting with the item give?",
                                              "Other items might require more experimentation."))]))
    E.append(R("magic-item-attunement", "Attunement (Magic Items)", section("Attunement", 3, page=102), "Equipment/Magic Items/Attunement", [
        (None, "rule", {"id": "unattuned", "only_nonmagical_benefits": True}),
        (None, "ref", ["dnd5e/rule/attunement"]),
        ("#### Attune during a Short Rest", "rule", {"id": "attune", "rest": "dnd5e/rule/short-rest", "focus_only_item": True, "contact": True,
                                                     "not_same_rest_as_identify": True, "interrupted": "fails"}),
        ("#### No More Than Three Items", "fx", {"op": "modifier", "stat": "max_attuned_items", "mode": "set", "value": 3}),
        ("#### No More Than Three Items", "rule", {"id": "limit", "max": 3, "fourth_fails": True, "one_copy_per_item": True}),
        ("#### Ending Attunement", "rule", {"id": "ending", "ends_on": ["prerequisites_unmet", "item_100_feet_away_24_hours", "you_die",
                                                                       "another_creature_attunes"],
                                            "voluntary": {"rest": "dnd5e/rule/short-rest", "not_if_cursed": True}})]))
    E.append(R("wearing-and-wielding-items", "Wearing and Wielding Items", section("Wearing and Wielding Items", 3, page=103),
               "Equipment/Magic Items/Wearing and Wielding Items", [
                   (None, "rule", {"id": "use", "worn_as_intended": True, "weapon_held": True}),
                   ("In most cases", "rule", {"id": "fit", "adjusts_to_wearer": True}),
                   ("#### Multiple Items of the Same Kind", "rule", {"id": "one_each", "slots": ["footwear", "gloves_or_gauntlets", "bracers",
                                                                                               "armor", "headwear", "cloak"]}),
                   ("#### Multiple Items of the Same Kind", "md", md("multiple_exceptions", "Allow an exception to the one-of-each-kind rule?", "The GM might make exceptions.")),
                   ("#### Paired Items", "rule", {"id": "pairs", "both_worn_required": True})]))
    mi = section("Magic Items", 1, page=204, stop_titles=("Magic Item Categories",))
    E.append(R("magic-items", "Magic Items", mi, "Magic Items", [(None, "desc", None)]))
    cats = section("Magic Item Categories", 2, page=204, stop_titles=("Armor",))
    E.append(R("magic-item-categories", "Magic Item Categories", cats, "Magic Items/Magic Item Categories", [
        (None, "rule", {"id": "categories", "count": 9}),
        ("##### Magic Item Categories", "table", tab("Magic Item Categories", ["Category", "Examples"], cats))]))
    cat_items = {
        "Armor": [(None, "rule", {"id": "worn", "must_be_worn": True}), ("Some suits", "rule", {"id": "unspecified_type", "choose_or_random": True})],
        "Rings": [(None, "rule", {"id": "worn", "on": "finger or similar digit"})],
        "Rods": [(None, "rule", {"id": "rod", "weight_lb": [2, 5]}), ("Unless its description", "rule", {"id": "focus", "arcane_focus": True})],
        "Scrolls": [(None, "desc", None), ("***Using a Scroll.***", "rule", {"id": "use", "consumable": True, "read_to_activate": True}),
                    ("Any creature that can understand", "rule", {"id": "readers", "requires": "understand a written language"})],
        "Staffs": [(None, "rule", {"id": "staff", "weight_lb": [2, 7]}),
                   ("Unless its description", "rule", {"id": "uses", "as": ["dnd5e/weapon/quarterstaff", "dnd5e/gear/arcane-focus"]})],
        "Wands": [(None, "rule", {"id": "wand", "length_inches": [12, 15]}), ("Unless its description", "rule", {"id": "focus", "arcane_focus": True})],
        "Weapons": [(None, "rule", {"id": "unspecified_type", "choose_or_random": True}),
                    ("***Ammunition.***", "rule", {"id": "ammunition", "fired_ammunition_is_magical": True})],
        "Wondrous Items": [(None, "desc", None)],
    }
    for title, items in cat_items.items():
        E.append(R(f"magic-item-category-{title.lower().replace(' ', '-')}", f"{title} (Magic Item Category)", section(title, 3, page=204 if title in ("Armor", "Rings", "Rods") else 205),
                   f"Magic Items/Magic Item Categories/{title}", items))
    pots = section("Potions", 3, page=204)
    E.append(R("magic-item-category-potions", "Potions (Magic Item Category)", pots, "Magic Items/Magic Item Categories/Potions", [
        (None, "rule", {"id": "potion", "volume_ounces": 1}),
        ("***Using a Potion.***", "rule", {"id": "use", "consumable": True, "drink_or_administer": "bonus_action", "oil": "per description",
                                           "takes_effect": "immediately"}),
        ("***Mixing Potions.***", "rule", {"id": "mixing", "table": "potion_miscibility", "each_extra_potion_rolls_again": True}),
        ("***Mixing Potions.***", "md", md("miscibility_reveal", "When are the mixed effects revealed?",
                                           "Unless the effects are immediately obvious, reveal them only when they become evident.")),
        ("##### Potion Miscibility", "table", tab("Potion Miscibility", ["1d100", "Result"], pots))]))
    E.append(R("magic-item-rarity", "Magic Item Rarity", section("Magic Item Rarity", 2, page=205, stop_titles=("Magic Item Values by Rarity",)),
               "Magic Items/Magic Item Rarity", [
                   (None, "rule", {"id": "rarities", "values": ["common", "uncommon", "rare", "very_rare", "legendary", "artifact"]})]))
    vals = section("Magic Item Values by Rarity", 3, page=205)
    E.append(R("magic-item-values-by-rarity", "Magic Item Values by Rarity", vals, "Magic Items/Magic Item Rarity/Magic Item Values by Rarity", [
        (None, "rule", {"id": "availability", "common": "town or city", "uncommon_rare": "cities", "rarer": "wondrous locations"}),
        ("If a magic item incorporates", "rule", {"id": "base_item_cost", "add_equipment_cost": True}),
        ("##### Magic Item Rarities and Values", "table", {"id": "magic_item_values", "caption": "Magic Item Rarities and Values",
                                                           "columns": ["Rarity", "Value"],
                                                           "rows": [["Common", "100 GP"], ["Uncommon", "400 GP"], ["Rare", "4,000 GP"],
                                                                    ["Very Rare", "40,000 GP"], ["Legendary", "200,000 GP"], ["Artifact", "Priceless"]]}),
        ("\\*Halve the value", "rule", {"id": "consumables", "half_value": True, "except": "dnd5e/magic-item/spell-scroll",
                                        "spell_scroll_value": "double scribing cost"})]))
    E.append(R("activating-a-magic-item", "Activating a Magic Item", section("Activating a Magic Item", 2, page=206, stop_titles=("Command Word",)),
               "Magic Items/Activating a Magic Item", [(None, "rule", {"id": "activation", "default": "dnd5e/action/magic"})]))
    E.append(R("command-word", "Command Word", section("Command Word", 3, page=206), "Magic Items/Activating a Magic Item/Command Word", [
        (None, "rule", {"id": "command_word", "spoken_or_signed": True, "spoken_needs_sound": True, "example": SP("Silence")})]))
    E.append(R("consumable-items", "Consumable Items", section("Consumable Items", 3, page=206), "Magic Items/Activating a Magic Item/Consumable Items", [
        (None, "rule", {"id": "consumed", "loses_magic_after_use": True}),
        ("#### Spells Cast from Items", "rule", {"id": "spells_from_items", "lowest_spell_and_caster_level": True, "slot": "none", "components": "none",
                                                 "normal_casting_time_range_duration": True, "concentration_as_normal": True,
                                                 "potions_confer_effect": True}),
        ("A magic item may require the user", "rule", {"id": "own_ability", "multiple": "user chooses", "none": {"modifier": 0, "add_proficiency_bonus": True}}),
        ("#### Charges", "rule", {"id": "charges", "identify_reveals_remaining": SP("Identify"), "attuned_knows": True})]))
    E.append(R("the-next-dawn", "“The Next Dawn”", section("“The Next Dawn”", 2, page=206), "Magic Items/“The Next Dawn”", [
        (None, "rule", {"id": "recharge", "at": "dawn"}),
        (None, "md", md("no_dawn", "When does the item recharge where dawn doesn't occur?",
                        "If such an item is on a world or plane of existence where the specified event doesn’t occur, the GM determines when the item recharges."))]))
    E.append(R("cursed-items", "Cursed Items", section("Cursed Items", 2, page=206), "Magic Items/Cursed Items", [
        (None, "rule", {"id": "curse", "identify_reveals": False}),
        ("Attunement to a cursed item", "rule", {"id": "attunement", "voluntary_end": False, "until": "curse broken", "example": SP("Remove Curse")})]))
    E.append(R("magic-item-resilience", "Magic Item Resilience", section("Magic Item Resilience", 2, page=206), "Magic Items/Magic Item Resilience", [
        (None, "rule", {"id": "resilience", "at_least_nonmagical": True, "resistance_all_damage": True, "except": ["potion", "scroll"]}),
        ("An Artifact can be destroyed", "rule", {"id": "artifact", "impervious_except_special_way": True}),
        ("An Artifact can be destroyed", "md", md("artifact_destruction", "How can this Artifact be destroyed?",
                                                 "Learning how to destroy an Artifact usually requires research or the completion of a quest."))]))
    E.append(R("crafting-magic-items", "Crafting Magic Items", section("Crafting Magic Items", 2, page=206, stop_titles=("Arcana Proficiency",)),
               "Magic Items/Crafting Magic Items", [
                   (None, "ref", ["dnd5e/rule/brewing-potions-of-healing", "dnd5e/rule/scribing-spell-scrolls"])]))
    E.append(R("crafting-arcana-proficiency", "Arcana Proficiency (Crafting)", section("Arcana Proficiency", 3, page=206),
               "Magic Items/Crafting Magic Items/Arcana Proficiency", [(None, "rule", {"id": "arcana", "crafter_and_assistants": "arcana"})]))
    tools = section("Tools", 3, page=206)
    E.append(R("crafting-magic-item-tools", "Tools (Magic Item Crafting)", tools, "Magic Items/Crafting Magic Items/Tools", [
        (None, "rule", {"id": "tools", "required_and_proficient": True, "assistants_proficient": True}),
        ("##### Magic Item Tools", "table", tab("Magic Item Tools", ["Item Category", "Required Tool"], tools))]))
    E.append(R("crafting-magic-item-spells", "Spells (Magic Item Crafting)", section("Spells", 3, page=207),
               "Magic Items/Crafting Magic Items/Spells", [(None, "rule", {"id": "spells", "prepared_every_crafting_day": True})]))
    tc = section("Time and Cost", 3, page=207)
    E.append(R("crafting-magic-item-time-and-cost", "Time and Cost (Magic Item Crafting)", tc, "Magic Items/Crafting Magic Items/Time and Cost", [
        (None, "rule", {"id": "by_rarity", "table": "magic_item_crafting"}),
        ("***Work per Day.***", "rule", {"id": "work_day", "hours": 8, "consecutive": False}),
        ("***Assistants.***", "rule", {"id": "assistants", "time_divided_by_workers": True, "max_assistants": 1}),
        ("***Assistants.***", "md", md("more_assistants", "Allow more than one assistant?", "Normally, only one other character can assist you, but the GM might allow more assistants.")),
        ("***Raw Materials.***", "rule", {"id": "materials", "city_chance_percent": 75, "settlement_chance_percent": 25, "retry_days": 7}),
        ("***Raw Materials.***", "md", md("materials_available", "Are the raw materials available?", "The GM determines whether appropriate raw materials are available.")),
        ("If a magic item incorporates", "rule", {"id": "base_item", "pay_or_craft": "dnd5e/rule/crafting-nonmagical-items"}),
        ("##### Magic Item Crafting Time and Cost", "table", tab("Magic Item Crafting Time and Cost", ["Item Rarity", "Time", "Cost"], tc, "magic_item_crafting")),
        ("\\*The time and cost are halved", "rule", {"id": "consumables", "halved": True, "except": "dnd5e/magic-item/spell-scroll"})]))
    E.append(R("sentient-magic-items", "Sentient Magic Items", section("Sentient Magic Items", 2, page=207, stop_titles=("Sentient Magic Item Traits",)),
               "Magic Items/Sentient Magic Items", [
                   (None, "desc", None),
                   ("Most sentient items are weapons", "rule", {"id": "never_sentient", "categories": ["potion", "scroll"]}),
                   ("The GM controls", "md", md("sentient_control", "How does the sentient item act and use its properties?",
                                                "The GM controls sentient magic items and their activated properties.", reason="narrative"))]))
    tr = section("Sentient Magic Item Traits", 3, page=207)
    E.append(R("sentient-magic-item-traits", "Sentient Magic Item Traits", tr, "Magic Items/Sentient Magic Items/Sentient Magic Item Traits", [
        (None, "rule", {"id": "persona", "like_npc": True}),
        ("#### Abilities", "rule", {"id": "abilities", "scores": ["int", "wis", "cha"], "random": "4d6 drop lowest"}),
        ("#### Alignment", "rule", {"id": "alignment", "table": "sentient_items_alignment"}),
        ("#### Communication", "rule", {"id": "communication", "table": "sentient_items_communication"}),
        ("#### Senses", "rule", {"id": "senses", "table": "sentient_items_senses"}),
        ("#### Special Purpose", "rule", {"id": "purpose", "table": "sentient_items_special_purpose", "deviation": "conflict"}),
        ("##### Sentient Item’s Alignment", "table", tab("Sentient Item’s Alignment", ["1d100", "Alignment", "1d100", "Alignment"],
                                                         caption_nodes(tr, "Sentient Item’s Alignment"), "sentient_items_alignment")),
        ("##### Sentient Item’s Communication", "table", tab("Sentient Item’s Communication", ["1d10", "Communication"],
                                                             caption_nodes(tr, "Sentient Item’s Communication"), "sentient_items_communication")),
        ("##### Sentient Item’s Senses", "table", tab("Sentient Item’s Senses", ["1d4", "Senses"], caption_nodes(tr, "Sentient Item’s Senses"), "sentient_items_senses")),
        ("##### Sentient Item’s Special Purpose", "table", tab("Sentient Item’s Special Purpose", ["1d10", "Special Purpose"],
                                                               caption_nodes(tr, "Sentient Item’s Special Purpose"), "sentient_items_special_purpose")),
        ("#### Conflict", "fx", {"op": "save", "ability": "cha", "dc": {"op": "add", "args": [12, {"var": "item_ability_mod.cha"}]},
                                 "on_fail": [{"op": "choice", "id": "demand", "choose": 1, "chooser": "gm", "options": [
                                     {"id": "chase", "label": "Chase My Dreams", "effects": [SENT]}, {"id": "get_rid", "label": "Get Rid of It", "effects": [SENT]},
                                     {"id": "change", "label": "It’s Time for a Change", "effects": [SENT]}, {"id": "close", "label": "Keep Me Close", "effects": [SENT]}]}]}),
        ("**Chase My Dreams.**", "sys", ["/effects/0"]),
        ("**Get Rid of It.**", "sys", ["/effects/0"]),
        ("**It’s Time for a Change.**", "sys", ["/effects/0"]),
        ("**Keep Me Close.**", "sys", ["/effects/0"]),
        ("If its bearer refuses", "fx", {"op": "choice", "id": "refusal", "choose": 1, "chooser": "gm", "options": [
            {"id": "no_attune", "label": "Make attunement impossible", "effects": [SENT]}, {"id": "suppress", "label": "Suppress activated properties", "effects": [SENT]},
            {"id": "control", "label": "Take control", "effects": [{"op": "save", "ability": "cha",
                                                                    "dc": {"op": "add", "args": [12, {"var": "item_ability_mod.cha"}]},
                                                                    "on_fail": [{"op": "apply_condition", "condition": "dnd5e/condition/charmed",
                                                                                 "duration": {"kind": "hours", "amount": "1d12", "ends_on": [{"event": "damage_taken"}]},
                                                                                 "note": "Follows the item's commands; repeats the save when it takes damage. Once per dawn."}]}]}]}),
        ("- Make it impossible", "sys", ["/effects/1"]),
        ("- Suppress one or more", "sys", ["/effects/1"]),
        ("- Attempt to take control", "sys", ["/effects/1"])]))
    E.append(R("magic-items-a-z", "Magic Items A–Z", section("Magic Items A–Z", 2, page=209, stop_titles=("Adamantine Armor",)), "Magic Items/Magic Items A–Z", [
        (None, "rule", {"id": "order", "alphabetical": True}),
        ("If a magic item description", "ref", ["dnd5e/rule/monsters"])]))
    E.append(build("rule", "magic-item-rules", "Magic Item Rules", sidebar("Magic Item Rules", 205), LOT, "Magic Items/Magic Item Rules (sidebar)", [
        (None, "ref", ["dnd5e/rule/using-magic-items"]),
        ("***Attunement Prerequisites.***", "rule", {"id": "prerequisites", "class_member": True, "spellcaster": "casts at least one spell from traits or features"}),
        ("***Items Made for Specific Creatures.***", "md", md("fit", "Does this item adjust its size to fit any wearer?",
                                                              "However, you can decide that a magic item doesn’t adjust its size to fit any wearer.")),
        ("***Unusual Anatomy.***", "md", md("anatomy", "Can this creature wear an item not made for its anatomy?",
                                            "Use your discretion to decide whether a creature can wear an item not made for its anatomy.")),
        ("***Paired Items.***", "md", md("paired_exception", "Allow an exception to the paired-items rule?",
                                         "You can allow exceptions to the rule that paired items must both be worn."))]))
    return E


if __name__ == "__main__":
    extend_registries(REGISTRY, LOT)
    out = entries()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
