"""Character creation, level advancement and monsters, driven by catalog entries."""
import re

from .engine import Creature, Ctx, slug
from .expr import parse_cell

ABILITIES = ("str", "dex", "con", "int", "wis", "cha")
BUILD_OPS = {"proficiency", "grant", "choice", "reference"}


class Builder:
    def __init__(self, eng):
        self.eng, self.cat, self.log = eng, eng.cat, eng.log

    # =========================================================================================
    # character creation (rule/character-creation-step-1 .. 5)
    # =========================================================================================
    def character(self, name, cls, species, background, picks):
        eng, log = self.eng, self.log
        c = Creature(eng, name, "party", "pc")
        c.picks = picks
        cref = f"dnd5e/class/{cls}"
        # Step 3: ability scores — Standard Array by Class.
        t = self.cat.table_rows("dnd5e/rule/character-creation-step-3-ability-scores", "standard_array_by_class")
        row = next(r for r in t["rows"] if r[0].lower() == cls)
        c.scores = dict(zip(ABILITIES, (int(v) for v in row[1:])))
        log.call("table", "standard_array_by_class", "OK", "dnd5e/rule/character-creation-step-3-ability-scores")
        # Step 2: origin — background ability increases, feat, proficiencies, equipment.
        bref = f"dnd5e/background/{background}"
        self.background_scores(c, bref, picks.get("background_increase"))
        c.class_levels[cls] = 1
        c.level = 1
        sref = f"dnd5e/species/{species}"
        sp = self.cat.get(sref)
        c.speed_base = sp["data"]["speed"]
        log.call("data", "species.speed", "OK", sref)
        for ref in (cref, sref, bref):
            self.apply_entry(c, ref)
        for f in self.class_level_features(cls, 1):
            self.add_feature(c, f)
        self.equip(c, picks.get("equip", {}))
        # Step 5: hit points at level 1.
        die = self.cat.get(cref)["data"]["hit_die"]
        c.hit_dice[cls] = [1, 1, die]
        c.hp_base = self.hp_gain(c, cls, first=True)
        eng.init_resources(c)
        self.setup_spellcasting(c)
        c.hp = eng.hp_max(c)
        log.say(f"{c} created: {cls} 1, {species}, {background}; HP {c.hp}")
        return c

    def background_scores(self, c, bref, pick):
        r = self.cat.rule(bref, "ability_scores")
        if r is None:
            self.log.call("rule", "background.ability_scores", "DATA_GAP", bref)
            return
        abil = r["abilities"]
        plus2, plus1 = pick or sorted(abil, key=lambda a: -c.scores[a])[:2]
        if any(fx["op"] == "choice" and fx.get("id") == "ability_scores" for fx in self.cat.get(bref)["effects"]):
            # The choice effect applies it when the background entry is applied.
            c.picks.setdefault("choice", {})[(bref, "ability_scores")] = f"{plus2}_2_{plus1}_1"
            c.score_cap = r.get("max_score", 20)
            return
        self.log.call("rule", "background.ability_scores", "DATA_GAP", bref,
                      "increase only as rule data (no choice effect the engine can offer)")
        c.scores[plus2] = min(r.get("max_score", 20), c.scores[plus2] + 2)
        c.scores[plus1] = min(r.get("max_score", 20), c.scores[plus1] + 1)

    def class_level_features(self, cls, level):
        e = self.cat.get(f"dnd5e/class/{cls}")
        self.log.call("data", "class.levels.features", "OK", e["ref"], f"level {level}")
        return [f["ref"] for f in e["data"]["levels"][str(level)]["features"]]

    def add_feature(self, c, ref):
        if ref in c.features:
            return
        c.features.append(ref)
        self.apply_entry(c, ref)

    # -- build-time effects ----------------------------------------------------------------------
    def apply_entry(self, c, ref):
        e = self.cat.get(ref)
        if e is None:
            self.log.call("ref", ref, "DATA_GAP", None, "missing entry")
            return
        if ref not in c.features and e["kind"] in ("species", "background", "class", "feat", "feature", "subclass"):
            c.features.append(ref)
        fx_list = e.get("effects") or []
        if not fx_list and not (e.get("data") or {}).get("rules"):
            self.log.call("entry", ref, "DATA_GAP", ref, "feature has neither effects nor rule data")
        for i, fx in enumerate(fx_list):
            self.apply_build(c, ref, fx, i)

    def apply_build(self, c, ref, fx, key):
        op, log, picks = fx["op"], self.log, c.picks
        if fx.get("when") and op == "grant":
            if not self.eng.holds(fx["when"], c, Ctx(c, ref=ref)):
                return
        if op == "proficiency":
            cat = fx["category"]
            if fx.get("items"):
                items = fx["items"]
            elif fx.get("choose"):
                pool = fx.get("from")
                if not pool:
                    log.call("op", "proficiency", "DATA_GAP", ref, "choose without 'from' (options only in a note)")
                    pool = []
                want = picks.get("skills" if cat == "skill" else cat, {}).get(ref) or [x for x in pool if x not in c.prof[cat]]
                if fx.get("expertise"):   # expertise in a skill you are already proficient in
                    want = [x for x in want if x in c.prof[cat] and x not in c.prof["expertise"]]
                else:
                    want = [x for x in want if x not in c.prof[cat] and x != "any"]
                items = want[:fx["choose"]] if isinstance(fx["choose"], int) else want[:1]
                if isinstance(picks.get("skills", {}).get(ref), list) and cat == "skill":
                    picks["skills"][ref] = [x for x in picks["skills"][ref] if x not in items]
            else:
                log.call("op", "proficiency", "DATA_GAP", ref, "neither items nor choose: only a note")
                items = []
            for it in items:
                c.prof["expertise" if fx.get("expertise") else cat].add(it)
            log.call("op", "proficiency", "OK", ref, cat)
        elif op == "grant" and "refs" not in fx:
            for it in fx.get("items", []):
                if it.get("ref"):
                    c.items.append({"ref": it["ref"], "state": "carried", "quantity": it["quantity"]})
                else:
                    log.call("item", it["name"], "OK", ref, "no catalog entry (kept by name)")
            c.gp = getattr(c, "gp", 0) + fx.get("gp", 0)
            log.call("op", "grant", "OK", ref, "equipment")
            c.equipment_granted = True
        elif op == "grant":
            refs = fx["refs"]
            if all("/spell-list/" in r for r in refs):
                return self.grant_spells(c, ref, fx)
            if fx.get("choose"):
                want = picks.get("grant", {}).get(ref)
                refs = [want] if want else refs[:int(fx["choose"])]
            log.call("op", "grant", "OK", ref)
            for r in refs:
                if "/spell/" in r:
                    target = c.cantrips if self.cat.get(r)["facets"]["level"] == 0 else c.always
                    if r not in target:
                        target.append(r)
                elif "/subclass/" in r:
                    self.add_subclass(c, r)
                else:
                    self.add_feature(c, r)
        elif op == "choice":
            k = fx.get("id") or key
            want = picks.get("choice", {}).get((ref, k))
            ids = [o["id"] for o in fx["options"]]
            n = fx.get("choose", 1) if isinstance(fx.get("choose", 1), int) else 1
            chosen = (want if isinstance(want, list) else [want if want in ids else ids[0]] * n)[:n]
            c.choices[(ref, k)] = chosen[0]
            log.call("op", "choice", "OK", ref, str(k))
            for pick in chosen:
                opt = next(o for o in fx["options"] if o["id"] == pick)
                if "value" in opt and fx.get("id"):
                    c.choices[(ref, "value:" + fx["id"])] = opt["value"]
                for j, sub in enumerate(opt["effects"]):
                    self.apply_build(c, ref, sub, f"{k}.{j}")
        elif op == "reference":
            if fx["rule"] == ref or fx["rule"] in (c.features + [f"dnd5e/species/{s}" for s in ()]):
                log.call("op", "reference", "DATA_GAP", ref,
                         "build step only in a note: " + fx.get("note", "")[:70])
            elif self.cat.get(fx["rule"]) and not self.cat.get(fx["rule"]).get("effects"):
                log.call("op", "reference", "DATA_GAP", ref, f"points to {fx['rule']} for a build step in a note")
            else:
                log.call("op", "reference", "OK", ref, fx["rule"])
        elif op == "modifier" and fx["stat"] == "cantrips_known":
            log.call("op", "modifier", "OK", ref, "cantrips_known")
        elif op == "modifier" and fx["stat"].startswith("ability_score."):
            ab = fx["stat"].split(".")[1]
            c.scores[ab] = min(getattr(c, "score_cap", 20), c.scores[ab] + int(fx["value"]))
            log.call("op", "modifier", "OK", ref, fx["stat"])

    def grant_spells(self, c, ref, fx):
        """Grant chosen spells from spell lists (Magic Initiate, lineages)."""
        log = self.log
        flt = fx.get("filter")
        if flt is None:
            log.call("op", "grant", "DATA_GAP", ref,
                     "spells from a list with the level only in a note ('" + fx.get("note", "")[:40] + "')")
        want = c.picks.get("origin_spells", {}).get(ref, [])
        if flt is not None:
            want = [s for s in want if self.cat.get(s)["facets"]["level"] == flt.get("spell_level")]
        for s in want:
            target = c.cantrips if self.cat.get(s)["facets"]["level"] == 0 else c.always
            if s not in target:
                target.append(s)
        log.call("op", "grant", "OK", ref, "spells")

    def equip(self, c, equip):
        """Starting equipment: the class option chosen at creation."""
        for cref in [f for f in c.features if "/class/" in f and not getattr(c, "equipment_granted", False)]:
            e = self.cat.get(cref)
            opt = c.choices.get((cref, 4)) or c.choices.get((cref, 3)) or "a"
            items = next((x for x in e["data"]["starting_equipment"] if x["id"] == opt), None)
            structured = any(fx["op"] == "grant" and fx.get("items") for o in
                             next((fx for fx in e["effects"] if fx["op"] == "choice"), {"options": []})["options"]
                             for fx in o["effects"])
            self.log.call("data", "class.starting_equipment", "OK" if structured else "DATA_GAP", cref,
                          None if structured else "option effect is a placeholder; engine FALLBACK reads data.starting_equipment by option id")
            for it in items["items"] if items else []:
                if it.get("ref"):
                    c.items.append({"ref": it["ref"], "state": "carried", "quantity": it["quantity"]})
        for ref, state in equip.items():
            for it in c.items:
                if it["ref"] == ref:
                    it["state"] = state
                    break
            else:
                c.items.append({"ref": ref, "state": state, "quantity": 1})

    # =========================================================================================
    # hit points (rule/level-advancement, rule/character-creation-step-5)
    # =========================================================================================
    def hp_gain(self, c, cls, first=False):
        cref = f"dnd5e/class/{cls}"
        hp = (self.cat.get(cref)["data"] or {}).get("hit_points")
        ctx = Ctx(c, ref=cref)
        if hp:
            self.log.call("data", "class.hit_points", "OK", cref, "level 1" if first else "fixed per level")
            return int(self.eng.ev(hp["level_1"] if first else hp["per_level"]["fixed"], c, ctx))
        if first:
            tref, tid = "dnd5e/rule/character-creation-step-5-character-creation-details", "level_1_hit_points_by_class"
        else:
            tref, tid = "dnd5e/rule/level-advancement", "fixed_hit_points_by_class"
        t = self.cat.table_rows(tref, tid)
        row = next(r for r in t["rows"] if cls.capitalize() in r[0])
        self.log.call("table", tid, "DATA_GAP", tref,
                      f"cell '{row[1]}' is text; engine parses it (class has no structured hit_points)")
        base = int(re.match(r"(\d+)", row[1]).group(1))
        return max(1, base + c.mod("con"))

    # =========================================================================================
    # spellcasting (feature data.rules)
    # =========================================================================================
    def setup_spellcasting(self, c):
        for ref in c.features:
            e = self.cat.get(ref)
            rules = {r["id"]: r for r in (e.get("data") or {}).get("rules", []) if "id" in r}
            if "spell_slots" not in rules:
                continue
            ctx = Ctx(c, ref=ref)
            for lv, x in rules["spell_slots"]["slots_by_spell_level"].items():
                n = int(self.eng.ev(x, c, ctx))
                if n:
                    cur = c.slots.get(lv, [0, 0])
                    c.slots[lv] = [cur[0] + n - cur[1], n]
            self.log.call("rule", "spellcasting#spell_slots", "OK", ref)
            c.spell_ability = rules["spellcasting_ability"]["ability"]
            self.log.call("rule", "spellcasting#spellcasting_ability", "OK", ref)
            picks = c.picks
            n_cantrips = int(self.eng.ev(rules["cantrips"]["known"], c, ctx))
            n_cantrips += sum(1 for _, fx, _ in c.passives("modifier") if fx["stat"] == "cantrips_known")
            n_prep = int(self.eng.ev(rules["prepared_spells"]["count"], c, ctx))
            self.log.call("rule", "spellcasting#cantrips", "OK", ref, f"{n_cantrips} known")
            self.log.call("rule", "spellcasting#prepared_spells", "OK", ref, f"{n_prep} prepared")
            if "spellbook" in rules:
                sb = rules["spellbook"]
                lvl = c.class_levels[[k for k in c.class_levels][0]]
                size = sb["start_level_1_spells"] + sb["per_level_gained_after_1"] * (lvl - 1)
                free = [s for s in c.spellbook if s in sum(picks.get("free_spells", {}).values(), [])]
                learned = [s for s in c.spellbook if s not in free]
                for s in picks.get("spellbook", []):
                    lv = str(self.cat.get(s)["facets"]["level"])
                    if len(learned) < size and s not in learned and (lv in c.slots or not sb.get("must_have_slot_level")):
                        learned.append(s)
                c.spellbook = learned + free
                self.log.call("rule", "spellcasting#spellbook", "OK", ref, f"{size} spells")
            origin = [s for s in c.cantrips if s not in picks.get("cantrips", [])]
            c.cantrips = origin + [s for s in picks.get("cantrips", []) if s not in origin][:n_cantrips]
            pool = c.spellbook if "spellbook" in rules else None
            prep = [s for s in picks.get("prepared", []) if pool is None or s in pool]
            prep = [s for s in prep if str(self.cat.get(s)["facets"]["level"]) in c.slots]
            c.prepared = [s for s in prep if s not in c.always][:n_prep]

    # =========================================================================================
    # level advancement (rule/level-advancement data.procedure)
    # =========================================================================================
    def level_up(self, c, cls):
        proc = self.cat.get("dnd5e/rule/level-advancement")["data"].get("procedure")
        if not proc:
            self.log.call("rule", "level-advancement#procedure", "DATA_GAP", "dnd5e/rule/level-advancement")
        else:
            self.log.call("rule", "level-advancement#procedure", "OK", "dnd5e/rule/level-advancement",
                          ", ".join(s["id"] for s in proc))
        # 1. choose class (same class)
        c.class_levels[cls] += 1
        c.level += 1
        new = c.class_levels[cls]
        # 2. hit points and hit point dice
        gain = self.hp_gain(c, cls)
        c.hp_base += gain
        c.hit_dice[cls][1] += 1
        c.hit_dice[cls][0] += 1
        # 3. class features of the new level (subclass features included)
        for f in self.class_level_features(cls, new):
            self.add_feature(c, f)
        for sub in c.subclasses.values():
            self.subclass_features(c, sub)
        for ref in list(c.features):
            for i, top in enumerate(self.cat.get(ref).get("effects") or []):
                for r, fx, _ in self.eng.expand_all(c, ref, top, i):
                    if fx["op"] == "grant" and fx.get("when"):
                        self.apply_build(c, r, fx, i)
        # 4./5. proficiency bonus and ability modifiers are derived on demand (system tables).
        self.log.call("data", "proficiency_bonus.by_level", "OK", "system.json")
        self.eng.init_resources(c)
        self.subclass_spells(c)
        self.setup_spellcasting(c)
        before = c.hp
        c.hp = min(self.eng.hp_max(c), c.hp + gain)
        self.log.say(f"{c} reaches {cls} {new}: +{gain} HP (max {self.eng.hp_max(c)}), "
                     f"slots {c.slots}, prepared {[slug(s) for s in c.prepared]}")
        self.eng.emit("level_gained", c, Ctx(c))
        return gain

    def add_subclass(self, c, sref):
        e = self.cat.get(sref)
        cls = slug(e["data"]["class"])
        c.subclasses[cls] = sref
        if sref not in c.features:
            c.features.append(sref)
        self.log.call("op", "grant", "OK", sref, "subclass chosen")
        self.subclass_features(c, sref)

    def subclass_features(self, c, sref):
        e = self.cat.get(sref)
        cls = slug(e["data"]["class"])
        gated = all(fx["op"] != "grant" or fx.get("when") for fx in e["effects"])
        if gated:
            for i, fx in enumerate(e["effects"]):
                if fx["op"] == "grant" and self.eng.holds(fx["when"], c, Ctx(c, ref=sref)):
                    self.log.call("op", "grant", "OK", sref, "subclass features by level")
                    for r in fx["refs"]:
                        self.add_feature(c, r)
            return
        self.log.call("op", "grant", "DATA_GAP", sref, "grants every subclass feature at once; level gate only "
                                                       "in a note (engine FALLBACK uses data.levels)")
        for lv, refs in e["data"]["levels"].items():
            if int(lv) <= c.class_levels[cls]:
                for r in refs:
                    self.add_feature(c, r)

    def subclass_spells(self, c):
        """Data.rules a level-up must apply (Evocation Savant free spells)."""
        for ref in c.features:
            for r in (self.cat.get(ref).get("data") or {}).get("rules", []):
                if r.get("id") == "free_spells" and r.get("to") == "spellbook":
                    want = c.picks.get("free_spells", {}).get(ref, [])[:r["count"]]
                    added = [s for s in want if s not in c.spellbook]
                    c.spellbook += added
                    self.log.call("rule", "evocation-savant#free_spells", "OK", ref, ", ".join(slug(s) for s in added))

    # =========================================================================================
    # monsters (stat blocks)
    # =========================================================================================
    def monster(self, ref, name, x):
        e = self.cat.get(ref)
        d = e["data"]
        c = Creature(self.eng, name, "foes", "monster")
        c.monster = e
        c.scores = {a: v["score"] for a, v in d["abilities"].items()}
        c.save_bonus = {a: v["save"] for a, v in d["abilities"].items()}
        c.ac_fixed = d["ac"]["value"]
        c.hp_base = c.hp = d["hp"]["average"]
        c.speed_base = d["speed"]["walk"]
        c.xp = d["cr"]["xp"]
        c.cr_pb = d["cr"].get("proficiency_bonus") or 2
        c.x = x
        self.log.call("data", "creature.stat_block", "OK", ref)
        return c
