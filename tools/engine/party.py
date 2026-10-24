"""Player decisions for any class (the 'chooser'), starting gear, and the party's inventory.

Everything a rule decides comes from the catalog; this module only makes the choices a player
would make (which skill, which spell, which option), equips the best gear the character is
proficient with, and shares out treasure.
"""
from .engine import Ctx, slug

S = "dnd5e/spell/"

# Ability priorities per class (player choice: where the background and ASI points go).
PRIORITY = {
    "barbarian": ["str", "con", "dex"], "bard": ["cha", "dex", "con"], "cleric": ["wis", "con", "str"],
    "druid": ["wis", "con", "dex"], "fighter": ["str", "con", "dex"], "monk": ["dex", "wis", "con"],
    "paladin": ["str", "cha", "con"], "ranger": ["dex", "wis", "con"], "rogue": ["dex", "con", "int"],
    "sorcerer": ["cha", "con", "dex"], "warlock": ["cha", "con", "dex"], "wizard": ["int", "con", "dex"],
}
SKILLS = ["perception", "stealth", "athletics", "insight", "survival", "arcana", "religion", "medicine",
          "persuasion", "acrobatics", "investigation", "nature", "history", "intimidation", "deception",
          "animal_handling", "sleight_of_hand", "performance"]
# Choice ids -> preferred option (player taste); anything else takes the first option.
CHOICES = {
    "divine_order": "protector", "primal_order": "warden", "land_type": "temperate",
    "hunters_prey": "colossus_slayer", "fighting_style": "feat", "draconic_ancestry": "red",
    "lineage": "wood_elf", "legacy": "infernal", "wild_companion_cost": "spell_slot",
    "cunning_strike": "trip", "fast_hands": "use_an_object", "technique": "topple",
    "unarmed_strike": "damage", "divine_spark_mode": "heal", "asi": "plus_two",
}
FIGHTING_STYLE = {"fighter": "dnd5e/feat/great-weapon-fighting", "paladin": "dnd5e/feat/defense",
                  "ranger": "dnd5e/feat/archery"}
INVOCATIONS = ["agonizing-blast", "armor-of-shadows", "eldritch-mind", "repelling-blast", "devils-sight",
               "pact-of-the-blade", "fiendish-vigor", "misty-visions"]
# Spells a player of the class would favour, best first; the rest are scored from their effects.
FAVOURITES = {
    "bard": ["vicious-mockery", "starry-wisp", "healing-word", "dissonant-whispers", "faerie-fire", "cure-wounds",
             "shatter", "hold-person", "heat-metal", "hypnotic-pattern", "fear", "mass-healing-word"],
    "cleric": ["sacred-flame", "toll-the-dead", "guidance", "bless", "guiding-bolt", "healing-word", "cure-wounds",
               "shield-of-faith", "spiritual-weapon", "aid", "hold-person", "spirit-guardians", "revivify",
               "mass-healing-word"],
    "druid": ["produce-flame", "starry-wisp", "shillelagh", "healing-word", "cure-wounds", "thunderwave", "entangle",
              "moonbeam", "flaming-sphere", "call-lightning", "conjure-animals"],
    "paladin": ["bless", "cure-wounds", "shield-of-faith", "heroism", "aid", "find-steed"],
    "ranger": ["hunters-mark", "cure-wounds", "goodberry", "ensnaring-strike", "pass-without-trace", "spike-growth"],
    "sorcerer": ["fire-bolt", "ray-of-frost", "shocking-grasp", "mage-hand", "chromatic-orb", "magic-missile", "shield",
                 "burning-hands", "scorching-ray", "hold-person", "fireball", "lightning-bolt"],
    "warlock": ["eldritch-blast", "chill-touch", "hex", "hellish-rebuke", "armor-of-agathys", "hold-person",
                "misty-step", "hunger-of-hadar", "fireball"],
    "wizard": ["fire-bolt", "ray-of-frost", "mage-hand", "light", "magic-missile", "shield", "sleep", "mage-armor",
               "thunderwave", "burning-hands", "scorching-ray", "misty-step", "hold-person", "shatter", "fireball",
               "lightning-bolt", "haste"],
}
MASTERY = {"fighter": ["greatsword", "flail", "javelin", "longsword", "handaxe"],
           "barbarian": ["greataxe", "handaxe", "battleaxe"], "paladin": ["longsword", "javelin", "warhammer"],
           "ranger": ["longbow", "scimitar", "shortsword"], "rogue": ["shortsword", "shortbow", "dagger", "rapier"],
           "monk": []}


class Chooser:
    """Player decisions for one character, consulted by the Builder."""

    def __init__(self, eng, cls):
        self.eng, self.cls = eng, cls

    # -- proficiencies, options, grants ---------------------------------------------------------
    def proficiencies(self, c, ref, cat, pool, fx):
        if cat == "skill":
            if fx.get("expertise"):
                return [s for s in SKILLS if s in c.prof["skill"]]
            if pool == ["any"] or not pool:
                return [s for s in SKILLS if s not in c.prof["skill"]]
            return sorted(pool, key=lambda s: SKILLS.index(s) if s in SKILLS else 99)
        return list(pool or [])

    def choice(self, c, ref, fx, k):
        ids = [o["id"] for o in fx["options"]]
        if k == "ability_scores":
            return None
        want = CHOICES.get(k) if isinstance(k, str) else None
        if want in ids:
            return want
        if slug(ref) == "goliath-giant-ancestry":
            return "stones_endurance"
        if slug(ref) == "gnome-gnomish-lineage":
            return "forest_gnome"
        if slug(ref) == "skilled":
            return ["skill"] * fx.get("choose", 1)
        if k in ("spell_list",):
            return {"sorcerer": "wizard", "warlock": "wizard", "bard": "wizard"}.get(self.cls, "cleric")
        if k == "spellcasting_ability":
            return PRIORITY[self.cls][0] if PRIORITY[self.cls][0] in ("int", "wis", "cha") else "wis"
        return None

    def grant(self, c, ref, refs, n):
        if any("/feat/" in r for r in refs) and FIGHTING_STYLE.get(self.cls) in refs:
            return [FIGHTING_STYLE[self.cls]]
        if any("/feat/" in r for r in refs) and "dnd5e/feat/alert" in refs:
            return ["dnd5e/feat/alert"]
        return refs[:n]

    def invocations(self, c, pool, n):
        lvl = c.class_levels.get("warlock", 1)
        out = []
        for name in INVOCATIONS:
            r = f"dnd5e/feature/warlock-invocation-{name}"
            if r not in pool:
                continue
            pre = self.eng.cat.rule(r, "prerequisite") or {}
            if pre.get("warlock_level", 0) <= lvl:
                out.append(r)
        if "dnd5e/feature/warlock-invocation-agonizing-blast" in out:
            c.chosen_spells["agonizing_blast"] = S + "eldritch-blast"
        have = [r for r in c.features if r in pool]
        return (have + [r for r in out if r not in have])[:n]

    def asi(self, c):
        pr = [a for a in PRIORITY[self.cls] if self.eng.score(c, a) < 20]
        return (pr + ["con", "dex"])[:2]

    def masteries(self, c, n):
        have = [slug(it["ref"]) for it in c.items if "/weapon/" in it["ref"]]
        pref = [w for w in MASTERY.get(self.cls, []) if w in have] + [w for w in have if w not in MASTERY.get(self.cls, [])]
        return list(dict.fromkeys(pref))[:n]

    # -- spells -------------------------------------------------------------------------------
    def score_spell(self, c, sref):
        sp = self.eng.cat.get(sref)
        if sp is None:
            return -1
        fav = FAVOURITES.get(self.cls, [])
        if slug(sref) in fav:
            return 1000 - fav.index(slug(sref))
        v = 0.0
        stack = list(sp.get("effects") or [])
        while stack:
            fx = stack.pop()
            if not isinstance(fx, dict):
                continue
            op = fx.get("op")
            if op == "damage":
                v += 6
            elif op == "heal":
                v += 5
            elif op == "apply_condition":
                v += 4
            elif op in ("save", "attack"):
                v += 2
            for k in ("then", "on_hit", "on_fail", "on_success", "effects"):
                stack.extend(fx.get(k) or [])
        if sp["facets"].get("concentration"):
            v -= 1
        if not sp.get("effects"):
            v -= 5
        return v

    def cantrips(self, c, listing, n):
        pool = [s for s in listing if self.eng.cat.get(s) and self.eng.cat.get(s)["facets"]["level"] == 0]
        return sorted(pool, key=lambda s: -self.score_spell(c, s))[:n]

    def prepared(self, c, listing, max_lvl, n):
        pool = [s for s in listing if self.eng.cat.get(s) and 0 < self.eng.cat.get(s)["facets"]["level"] <= max_lvl
                and s not in c.always]
        ranked = sorted(pool, key=lambda s: -self.score_spell(c, s))
        # keep a spread: at least one spell of the highest level when possible
        top = [s for s in ranked if self.eng.cat.get(s)["facets"]["level"] == max_lvl][:2]
        return list(dict.fromkeys(top + ranked))[:n]

    def spellbook(self, c, listing, max_lvl, size):
        return self.prepared(c, listing, max_lvl, size + 4)

    def free_spells(self, c, rule):
        pool = [s for s in self.eng.cat.get(rule["from"])["data"].get("spells", [])
                if self.eng.cat.get(s)["facets"]["school"] == rule["school"]
                and 0 < self.eng.cat.get(s)["facets"]["level"] <= rule["max_level"] and s not in c.spellbook]
        return sorted(pool, key=lambda s: -self.score_spell(c, s))[:rule["count"]]


def picks_for(eng, cls, background):
    """Picks dict for Builder.character in automatic mode."""
    bg = eng.cat.rule(f"dnd5e/background/{background}", "ability_scores")["abilities"]
    pr = [a for a in PRIORITY[cls] if a in bg] + [a for a in bg if a not in PRIORITY[cls]]
    return {"chooser": Chooser(eng, cls), "background_increase": (pr[0], pr[1])}


# =============================================================================================
# gear
# =============================================================================================
def weapon_value(eng, c, wref):
    w = eng.cat.get(wref)["data"]
    die = w["damage"]["amount"]
    n, f = (int(x) for x in die.split("d"))
    props = [slug(p["ref"]) for p in w.get("properties", [])]
    ability = "dex" if w["melee_or_ranged"] == "ranged" else ("dex" if "finesse" in props and c.mod("dex") > c.mod("str") else "str")
    prof = eng.weapon_proficient(c, wref)
    return n * (f + 1) / 2 + c.mod(ability) + (3 if prof else -5)


def armor_ac(eng, c, aref):
    a = eng.cat.get(aref)["data"]
    ac = a["armor_class"]
    dex = c.mod("dex")
    if a["category"] == "heavy":
        if c.scores["str"] < (a.get("strength_requirement") or 0):
            return -1
        return ac["base"]
    if ac.get("dex_max") is not None:
        dex = min(dex, ac["dex_max"])
    return ac["base"] + dex


def auto_equip(eng, c, cls):
    """Wear the best armor the character is trained in; wield the best weapon; shield if it fits."""
    for it in c.items:
        if it["state"] in ("worn", "wielded", "held"):
            it["state"] = "carried"
    armors = [it for it in c.items if "/armor/" in (it.get("base") or it["ref"])
              and eng.cat.get(it.get("base") or it["ref"])["data"]["category"] != "shield"]
    trained = [a for a in armors if eng.cat.get(a.get("base") or a["ref"])["data"]["category"] in c.prof["armor"]]
    unarmored = 10 + c.mod("dex")
    if cls == "monk":
        trained = []
    best = max(trained, key=lambda a: armor_ac(eng, c, a.get("base") or a["ref"]) + a.get("bonus", 0), default=None)
    mage_armor = 13 + c.mod("dex") if ("dnd5e/spell/mage-armor" in c.prepared + c.always or
                                       "dnd5e/feature/warlock-invocation-armor-of-shadows" in c.features) else 0
    if best and armor_ac(eng, c, best.get("base") or best["ref"]) + best.get("bonus", 0) > max(unarmored, mage_armor) \
            and cls != "barbarian":
        best["state"] = "worn"
    weapons = [it for it in c.items if "/weapon/" in (it.get("base") or it["ref"])]
    melee = [w for w in weapons if eng.cat.get(w.get("base") or w["ref"])["data"]["melee_or_ranged"] == "melee"]
    main = max(melee, key=lambda w: weapon_value(eng, c, w.get("base") or w["ref"]) + 2 * w.get("bonus", 0), default=None)
    if main:
        main["state"] = "wielded"
    two_handed = main and "two-handed" in [slug(p["ref"]) for p in eng.cat.get(main.get("base") or main["ref"])["data"].get("properties", [])]
    shield = next((it for it in c.items if slug(it["ref"]) == "shield"), None)
    if shield and "shield" in c.prof["armor"] and not two_handed and cls not in ("monk",):
        shield["state"] = "wielded"
    for it in c.items:
        if slug(it["ref"]) == "holy-symbol" or "focus" in slug(it["ref"]):
            it["state"] = "held"
        if it.get("attuned") and it["state"] == "carried":
            it["state"] = "worn"
    c.score_items = [it for it in c.items if it.get("attuned") and "ability_score" in str(eng.cat.get(it["ref"]).get("effects"))]


def best_weapon(eng, c, ranged):
    """(weapon ref, item record, thrown?) to attack with at this range."""
    opts = []
    for it in c.items:
        w = it.get("base") or it["ref"]
        if "/weapon/" not in w:
            continue
        d = eng.cat.get(w)["data"]
        props = [slug(p["ref"]) for p in d.get("properties", [])]
        if ranged and d["melee_or_ranged"] == "ranged":
            opts.append((weapon_value(eng, c, w) + 2 * it.get("bonus", 0), w, it, False))
        elif ranged and "thrown" in props and it.get("quantity", 1) > 0:
            opts.append((weapon_value(eng, c, w) - 1 + 2 * it.get("bonus", 0), w, it, True))
        elif not ranged and d["melee_or_ranged"] == "melee":
            opts.append((weapon_value(eng, c, w) + 2 * it.get("bonus", 0) + (1 if it["state"] == "wielded" else 0), w, it, False))
    if not opts:
        return None
    v, w, it, thrown = max(opts, key=lambda o: o[0])
    return w, it, thrown


# =============================================================================================
# treasure
# =============================================================================================
COIN_GP = {"cp": 0.01, "sp": 0.1, "ep": 0.5, "gp": 1, "pp": 10}


def item_record(eng, item):
    """Inventory record for a treasure item: {'ref', 'name', 'quantity', 'base', 'bonus', ...}."""
    rec = {"ref": item["ref"], "name": item.get("name") or eng.cat.get(item["ref"])["name"],
           "quantity": item.get("quantity", 1), "state": "carried"}
    for k in ("base", "bonus", "spell", "variant", "charges", "found_as"):
        if k in item:
            rec[k] = item[k]
    e = eng.cat.get(item["ref"])
    if e and e["facets"].get("attunement"):
        rec["attune"] = True
    if item.get("variant"):
        for v in (e["data"].get("item") or {}).get("variants", []):
            if v.get("variant") == item["variant"]:
                rec["variant_data"] = v
    if e and e["facets"].get("category") == "scroll" and item.get("spell"):
        lvl = eng.cat.get(item["spell"])["facets"]["level"]
        for v in e["data"]["item"]["variants"]:
            if v["spell_level"] == lvl:
                rec["scroll_stats"] = {"save_dc": v["save_dc"], "attack_bonus": v["attack_bonus"]}
    if "charges" not in rec:
        for fx in (e or {}).get("effects") or []:
            if fx["op"] == "resource" and fx["resource"] == "charges":
                rec["charges"] = fx["max"]
    return rec


def share_out(eng, party, loot, log):
    """Coins split evenly; valuables and items go to whoever uses them best."""
    alive = [c for c in party if not c.dead]
    if not alive:
        return []
    notes = []
    for coin, n in (loot.get("coins") or {}).items():
        each, rest = divmod(n, len(alive))
        for i, c in enumerate(alive):
            c.coins[coin] += each + (1 if i < rest else 0)
    for g in loot.get("valuables", []):
        holder = min(alive, key=lambda c: sum(v.get("gp", 0) for v in c.inventory if "gp" in v))
        holder.inventory.append(dict(g))
        notes.append(f"{g['name']} ({g.get('gp', '?')} gp) -> {holder.name}")
    for it in loot.get("items", []):
        if not it.get("ref"):
            holder = alive[0]
            holder.inventory.append({"name": it["name"], "quantity": it.get("quantity", 1), "note": it.get("note")})
            log.call("item", it["name"], "GM", None, "named item without a catalog entry: kept by name, no mechanics")
            notes.append(f"{it['name']} (no catalog entry) -> {holder.name}")
            continue
        rec = item_record(eng, it)
        holder = pick_holder(eng, alive, rec)
        if rec.get("attune"):
            if sum(1 for x in holder.items if x.get("attuned")) < 3:
                rec["attuned"] = True
                log.call("rule", "attunement", "OK", "dnd5e/rule/attunement", "short rest to attune; max 3")
        holder.items.append(rec)
        auto_equip(eng, holder, next(iter(holder.class_levels)))
        notes.append(f"{rec['name']} -> {holder.name}")
    return notes


def pick_holder(eng, alive, rec):
    cat = eng.cat.get(rec["ref"])["facets"].get("category")
    cls = lambda c: next(iter(c.class_levels))  # noqa: E731
    if cat == "weapon" and rec.get("base"):
        held = lambda c: sum(1 for x in c.items if x.get("bonus") and "/weapon/" in (x.get("base") or ""))  # noqa: E731
        users = sorted(alive, key=lambda c: -(weapon_value(eng, c, rec["base"]) - 4 * held(c)))
        return users[0]
    if cat == "armor" and rec.get("base"):
        a = eng.cat.get(rec["base"])["data"]["category"]
        users = [c for c in alive if a in c.prof["armor"] and cls(c) not in ("monk", "barbarian")]
        return max(users or alive, key=lambda c: armor_ac(eng, c, rec["base"]) - eng.ac(c, Ctx(c)))
    if cat == "potion":
        return min(alive, key=lambda c: (sum(x.get("quantity", 1) for x in c.items if "potion" in x["ref"]),
                                         eng.hp_max(c)))
    if cat == "scroll" and rec.get("spell"):
        classes = eng.cat.get(rec["spell"])["facets"].get("classes", [])
        users = [c for c in alive if any(k in classes for k in c.class_levels)]
        return (users or alive)[0]
    if slug(rec["ref"]) == "gauntlets-of-ogre-power":
        return min(alive, key=lambda c: (c.scores["str"] if PRIORITY[cls(c)][0] == "str" else 99))
    if slug(rec["ref"]) == "ring-of-protection":
        return min(alive, key=lambda c: eng.ac(c, Ctx(c)) - (100 if PRIORITY[cls(c)][0] in ("str", "dex") else 0)
                   + 10 * sum(1 for x in c.items if x.get("attuned")))
    if cat == "wand":
        casters = [c for c in alive if c.slots or c.pact_level]
        return min(casters or alive, key=lambda c: len(c.cantrips))
    return min(alive, key=lambda c: len(c.items))


def wealth(c):
    return round(sum(COIN_GP[k] * v for k, v in c.coins.items()) + sum(v.get("gp", 0) * v.get("quantity", 1)
                                                                       for v in c.inventory if "gp" in v), 2)
