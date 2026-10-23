"""Registry names introduced by the magic item lots (L31, L32). Item effects use the
argument {"item": "this"} for the item that carries the effect."""


def _p(i, d, pages, params=None):
    x = {"id": i, "description": d, "type": "predicate", "pages": pages}
    if params:
        x["params"] = params
    return x


def _e(i, d, pages, params=None):
    x = {"id": i, "description": d, "type": "event", "pages": pages}
    if params:
        x["params"] = params
    return x


def _v(i, d, pages, t="number", params=None):
    x = {"id": i, "description": d, "type": t, "pages": pages}
    if params:
        x["params"] = params
    return x


REGISTRY = {
    "events": [
        _e("dawn", "The next dawn: magic items regain charges and daily properties.", [206]),
        _e("unequips_item", "The creature stops wearing or wielding the item (param: item).", [210], ["item"]),
        _e("hood_lowered", "The wearer pulls the item's hood down (no action required).", [215]),
        _e("deals_damage_with_item", "A creature takes damage from the item (param: item).", [209], ["item"]),
        _e("ranged_attack_against_creature_within_feet", "An attacker makes a ranged attack roll against a target within N feet of the creature (param: feet).", [211], ["feet"]),
        _e("draws_item", "The creature draws the item (param: item).", [223], ["item"]),
        _e("moved_against_will_along_ground", "An effect moves the creature against its will along the ground.", [219]),
        _e("hour_elapsed", "An hour passes (end of each hour).", [227]),
        _e("reads_item", "The creature attempts to read the item (param: item).", [229], ["item"]),
        _e("sees_reflection", "A creature sees its reflection in the item (param: item).", [230], ["item"]),
        _e("minutes_elapsed", "Every 10 minutes pass.", [238]),
        _e("succeeds_saving_throw", "The creature succeeds on a saving throw.", [239]),
        _e("targeted_by_attack_or_area", "The creature (or an ally within range) is targeted by an attack or saves against an area of effect.", [243]),
        _e("expends_last_charge", "The item's last charge is expended.", [206]),
    ],
    "predicates": [
        _p("attuned_to_item", "The creature is attuned to the item (param: item).", [102], ["item"]),
        _p("possesses_item", "The item is in the creature's possession (param: item).", [213], ["item"]),
        _p("within_feet_of_item", "The creature is within N feet of the item (params: feet, item).", [214], ["feet", "item"]),
        _p("riding_item", "The creature rides the item, e.g. astride a broom (param: item).", [214], ["item"]),
        _p("gripping_item", "The creature grips the item's edges, e.g. a cloak used to fly (param: item).", [216], ["item"]),
        _p("in_item_light", "The creature is within the light the item sheds (param: item).", [214], ["item"]),
        _p("attack_is_ranged", "The attack roll is a ranged attack (weapon, spell or other).", [211]),
        _p("class_is", "The creature has a level in one of these classes (param: classes).", [214], ["classes"]),
        _p("spell_level_is", "The spell being cast is of this level (param: level).", [214], ["level"]),
        _p("is_species", "The creature is of one of these species or kinds (param: species).", [213], ["species"]),
        _p("interacting_with", "The check is made to interact with these creatures (param: creatures).", [213], ["creatures"]),
        _p("terrain_from", "The Difficult Terrain is created by these (param: source).", [214], ["source"]),
        _p("check_for_movement", "The check is made to move in one of these modes, e.g. climb or swim (param: modes).", [224], ["modes"]),
        _p("has_sense", "The creature has this sense (param: sense).", [224], ["sense"]),
        _p("creature_has_tag", "The target has one of these creature tags, e.g. Demon (param: tags).", [218], ["tags"]),
        _p("source_has_tag", "The effect's source has one of these creature tags (param: tags).", [218], ["tags"]),
        _p("controls_item", "The creature controls the item (an Artifact such as a Dragon Orb) (param: item).", [218], ["item"]),
        _p("attuned_giant_item", "The creature wears and is attuned to a Belt of Giant Strength or Gauntlets of Ogre Power.", [224]),
        _p("on_vessel", "The creature is on a boat or ship.", [221]),
        _p("can_use_item", "The creature meets the item's requirements to use it (param: item).", [229], ["item"]),
        _p("failed_save_against_spell", "The damage results from failing a saving throw against a spell.", [225]),
        _p("hp_at_most", "The target has at most N Hit Points (param: hp).", [229], ["hp"]),
        _p("hp_below", "The target has fewer than N Hit Points (param: hp).", [233], ["hp"]),
        _p("item_has_gem", "The item still has at least one gem of this type (param: gem).", [225], ["gem"]),
        _p("item_orbiting", "The Ioun Stone orbits the creature's head (param: item).", [227], ["item"]),
        _p("save_against_spell_or_magic", "The saving throw is against a spell or other magical effect.", [226]),
        _p("damage_from_falling", "The damage comes from a fall.", [238]),
        _p("has_marked_target", "The creature has a living sworn enemy or other marked target from the item.", [233]),
        _p("item_form_in", "The item is in one of these forms (param: forms).", [237], ["forms"]),
        _p("item_variant_is", "The item is of this variant or linked type (param: variant).", [237], ["variant"]),
        _p("playing_item", "The creature is playing the instrument (param: item).", [234], ["item"]),
        _p("spell_level_at_most", "The spell is of level N or lower (param: level).", [239], ["level"]),
        _p("spell_targeted_only_you", "The spell targets only the creature and creates no area of effect.", [239]),
        _p("attack_is_spell", "The attack roll is a spell attack.", [244]),
        _p("on_slippery_surface", "The creature is on a slippery surface, such as ice or oil.", [244]),
        _p("target_is_object", "The target is an object.", [248]),
        _p("touching_item", "The creature touches the item (param: item).", [243], ["item"]),
        _p("check_to_control_item", "The check is made to control this item (param: item).", [249], ["item"]),
        _p("has_head", "The creature has at least one head.", [250]),
        _p("took_damage_since_turn_start", "The creature took damage since the start of its last turn.", [215]),
    ],
    "variables": [
        _v("item_bonus", "The +N of the item's variant (data.item.rarity[].bonus).", [205]),
        _v("item_variant_score", "Ability score granted by the item's variant (data.item.variants[].score).", [213]),
        _v("item_variant_fly_speed", "Fly Speed of the item's variant (its table).", [215]),
        _v("charges_spent", "Charges the user chooses to expend on this activation.", [221]),
        _v("weapon_damage_type", "Damage type of the weapon used.", [219], t="identifier"),
        _v("item_gems", "Number of gems remaining in the item.", [225]),
        _v("item_variant_spirits", "Spirits summoned by the item's variant (its table).", [226]),
        _v("item_spheres_damage", "Lightning damage by the number of spheres created (Ring of Shooting Stars table).", [238]),
        _v("creatures_present", "Number of creatures present in the demiplane.", [242]),
        _v("weapon_damage_max", "Maximum result of the weapon's damage dice.", [248]),
        _v("item_ability_mod", "Ability modifier of a sentient item (param: ability).", [207], params=["ability"]),
        _v("shield_ac_bonus", "Armor Class bonus a wielded Shield grants (base 2 plus magic bonus).", [92, 209]),
    ],
    "senses": [
        {"id": "xray_vision", "description": "X-ray vision: solid objects within range appear transparent.", "pages": [239]},
        {"id": "telepathy", "description": "Telepathic communication within a range.", "pages": [226]},
    ],
    "stats": [
        {"id": "armor_stealth_disadvantage", "description": "The worn armor imposes Disadvantage on Dexterity (Stealth) checks (1) or not (0).", "pages": [231]},
        {"id": "armor_strength_requirement", "description": "Strength score the worn armor requires (0 = none).", "pages": [231]},
        {"id": "breathe_any_environment", "description": "The creature can breathe normally in any environment (1) or not (0).", "pages": [232]},
        {"id": "spell_slot_cost", "description": "Spell slots a casting expends (0 = cast without expending a slot).", "pages": [214]},
    ],
    "frequencies": [
        {"id": "hour", "description": "Can't be used again for 1 hour.", "pages": [218]},
    ],
    "restrictions": [
        {"id": "half_cover_against_spell_attacks", "description": "Half Cover applies against your spell attack rolls.", "pages": [251]},
        {"id": "resistance_to_slashing_applies", "description": "The target's Resistance to Slashing damage applies to this weapon's damage.", "pages": [250]},
        {"id": "cover_benefit_half_three_quarters", "description": "Benefit from Half Cover or Three-Quarters Cover against the attack.", "pages": [233]},
        {"id": "long_range_disadvantage", "description": "Suffer Disadvantage due to long range.", "pages": [233]},
        {"id": "read_thoughts_or_lie_detection_by_magic", "description": "Be affected by magic that reads thoughts, detects lies, or reveals alignment or creature type.", "pages": [238]},
        {"id": "actions_other_than_dash_or_escape", "description": "Take actions other than Dash or trying to escape an effect that prevents movement (Dodge if it can't move).", "pages": [229]},
        {"id": "need_food_or_drink", "description": "Need to eat or drink.", "pages": [228]},
        {"id": "end_attunement_voluntarily", "description": "Voluntarily end Attunement to the item.", "pages": [218]},
        {"id": "speed_reduced_by_encumbrance_or_heavy_armor", "description": "Speed reduced by carrying weight over capacity or wearing Heavy Armor.", "pages": [214]},
        {"id": "caught_in_webs", "description": "Be caught in webs of any sort.", "pages": [215]},
    ],
}
