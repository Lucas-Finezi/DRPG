"""Generic tactics for any character class and any stat block.

Decisions only: every outcome comes from the engine. Each turn a character heals a fallen
ally if it can, uses a buff it has (Rage, Hunter's Mark, Bardic Inspiration...), moves, then
takes the action with the best expected value: a weapon attack (with Extra Attack), a spell,
a wand, a potion. Action Surge repeats the action. Monsters use their stat block: Multiattack
from data.rules, attacks in range, spells and breath weapons.
"""
from .engine import Ctx, slug
from .party import best_weapon

S = "dnd5e/spell/"
MELEE = {"barbarian", "fighter", "paladin", "monk"}
HEALERS = {"cleric", "druid", "bard", "paladin", "ranger"}
CONTROL = {"dnd5e/condition/paralyzed": 3, "dnd5e/condition/unconscious": 3, "dnd5e/condition/incapacitated": 2.5,
           "dnd5e/condition/stunned": 3, "dnd5e/condition/restrained": 1.5, "dnd5e/condition/prone": 0.8,
           "dnd5e/condition/frightened": 1.2, "dnd5e/condition/blinded": 1.5, "dnd5e/condition/charmed": 1.5,
           "dnd5e/condition/poisoned": 0.8, "dnd5e/condition/grappled": 0.5}


def cls_of(c):
    return next(iter(c.class_levels)) if c.class_levels else None


class Tactics:
    def __init__(self, rng):
        self.rng = rng
        self.encounter = {}         # per-fight info: boss present, round
        self.used_recharge = set()

    # ==========================================================================================
    # hooks the engine calls
    # ==========================================================================================
    def choose(self, eng, c, fx, ctx):
        cid = fx.get("id")
        ids = [o["id"] for o in fx["options"]]
        prefs = {"unarmed_strike": "damage", "technique": "topple", "divine_spark_mode": "heal",
                 "action": "disengage", "cunning_strike": "trip", "hunters_prey": "colossus_slayer"}
        if cid in prefs and prefs[cid] in ids:
            return prefs[cid]
        if cid == "finesse_ability":
            return max(("str", "dex"), key=c.mod)
        return ids[0]

    def use_trigger(self, eng, c, ref, fx, ctx):
        name = slug(ref)
        if name in ("cleave", "horde-breaker") or "horde_breaker" in str(fx.get("then")):
            first = ctx.target
            others = [o for o in eng.creatures if o.up and o.side != c.side and first is not None
                      and o is not first and abs(o.x - first.x) <= 5 and abs(o.x - c.x) <= 5]
            if not others:
                return False
            ctx.target = others[0]
            ctx.attack = dict(ctx.attack or {})
            return True
        if name == "wizard-arcane-recovery":
            return any(s[0] < s[1] for s in c.slots.values())
        if name == "monk-uncanny-metabolism":
            return c.hp < eng.hp_max(c) // 2 or c.resources.get("focus_points", {}).get("cur", 1) == 0
        if name in ("alert", "heroic-inspiration"):
            return False
        if name == "goliath-giant-ancestry":
            return c.resources.get("giant_ancestry", {}).get("cur", 0) > 0
        if name == "bard-bardic-inspiration":
            return ctx.flags.get("margin", 99) <= 6
        if name == "college-of-lore-cutting-words":
            return c.resources.get("bardic_inspiration", {}).get("cur", 0) > 1
        if name in ("oath-of-devotion-sacred-weapon",):
            return c.resources.get("channel_divinity", {}).get("cur", 0) > 0
        if name == "rogue-cunning-strike":
            return False
        if name == "dragonborn-breath-weapon":
            near = [o for o in self.foes(eng, c) if abs(o.x - c.x) <= 15]
            if len(near) >= 2 and c.resources.get("breath_weapon", {}).get("cur", 0) > 0:
                if isinstance(ctx.flags.get("replaced"), dict):
                    ctx.flags["replaced"]["replaced"] = True
                ctx.flags["point"] = c.x
                return True
            return False
        if name == "oath-of-devotion-sacred-weapon":
            return bool(self.encounter.get("boss")) and not any(slug(t["ref"]) == name for t in c.temps)
        if name == "orc-relentless-endurance":
            return c.resources.get("relentless_endurance", {}).get("cur", 0) > 0
        return True

    def react_to_hit(self, eng, t, attacker, ctx, total):
        if t.kind != "pc" or not t.economy.get("reaction"):
            return
        if S + "shield" in t.prepared + t.always and total < eng.ac(t, ctx) + 5:
            slot = self.lowest_slot(eng, t, S + "shield")
            if slot:
                eng.cast(t, S + "shield", slot, [t])

    def after_hit(self, eng, c, t, ctx):
        """Divine Smite after a melee weapon hit (bonus action, a slot)."""
        if c.kind != "pc" or not t.up or not c.economy.get("bonus_action"):
            return
        at = ctx.attack or {}
        if at.get("via") not in ("weapon", "unarmed_strike") or at.get("range") != "melee":
            return
        smite = S + "divine-smite"
        if smite not in c.always + c.prepared:
            return
        big = ctx.crit or t.hp > 12 or self.encounter.get("boss")
        if not big:
            return
        slot = self.lowest_slot(eng, c, smite)
        if slot:
            eng.cast(c, smite, slot, [t], ctx.sub(crit=ctx.crit))

    def damage_type(self, eng, c, options, t):
        return options[0]

    def area_targets(self, eng, c, fx, ctx):
        area = fx["target"]["area"]
        size = area.get("size_feet", 10)
        foes = [o for o in eng.creatures if o.up and o.side != c.side]
        if area["origin"] == "self":
            hit = [o for o in foes if abs(o.x - c.x) <= size]
            if area["shape"] == "emanation" and fx["op"] == "heal":
                return [o for o in eng.creatures if o.side == c.side and abs(o.x - c.x) <= size]
            return hit
        point = ctx.flags.get("point")
        if point is None:
            point = self.best_point(foes, size)
        return [o for o in eng.creatures if o.alive and o.hp > 0 and abs(o.x - point) <= size
                and (o.side != c.side or fx["op"] in ("heal", "temp_hp"))]

    def choose_form(self, eng, c, fx, ctx):
        r = eng.cat.rule("dnd5e/feature/druid-wild-shape", "known_forms") or {}
        forms = [f for f in r.get("recommended", []) if eng.cat.exists(f)]
        return "dnd5e/creature/wolf" if "dnd5e/creature/wolf" in forms else (forms[0] if forms else None)

    # ==========================================================================================
    # helpers
    # ==========================================================================================
    def foes(self, eng, c):
        return [o for o in eng.creatures if o.up and o.side != c.side and not o.behaviour.get("fled")]

    def allies(self, eng, c):
        return [o for o in eng.creatures if o.side == c.side and not o.dead]

    def nearest(self, eng, c, pool=None):
        pool = self.foes(eng, c) if pool is None else pool
        return min(pool, key=lambda o: (abs(o.x - c.x), o.hp)) if pool else None

    def best_point(self, foes, size):
        if not foes:
            return 0
        return max((f.x for f in foes), key=lambda x: sum(1 for g in foes if abs(g.x - x) <= size))

    def lowest_slot(self, eng, c, sref, at_least=None):
        lvl = eng.cat.get(sref)["facets"]["level"]
        if lvl == 0:
            return 0
        if c.pact_level and c.resources.get("pact_magic_slot", {}).get("cur", 0) > 0 and c.pact_level >= lvl and \
                sref in c.prepared + c.always and "warlock" in eng.cat.get(sref)["facets"].get("classes", []):
            return c.pact_level
        for k in sorted(c.slots, key=int):
            if int(k) >= max(lvl, at_least or 0) and c.slots[k][0] > 0:
                return int(k)
        return None

    def approach(self, eng, c, target, stop=5):
        d = abs(target.x - c.x)
        step = min(c.economy.get("movement", 0), max(0, d - stop))
        if step:
            c.x += step if target.x > c.x else -step
            c.economy["movement"] -= step
            c.turn["moved"] = True

    def keep_away(self, eng, c, near, want=25):
        d = abs(near.x - c.x)
        if d >= want:
            return
        step = min(c.economy.get("movement", 0), want - d)
        if step:
            c.x += -step if near.x > c.x else step
            c.economy["movement"] -= step
            c.turn["moved"] = True

    def activation(self, eng, c, ref=None, name=None, ident=None):
        for r, fx in eng.activations(c):
            if (ref is None or r == ref) and (name is None or fx.get("name") == name) and (ident is None or fx.get("id") == ident):
                return r, fx
        return None, None

    def use_action(self, eng, c, aref="dnd5e/action/attack"):
        fx = next(x for x in eng.cat.get(aref)["effects"] if x["op"] == "activation")
        if not c.economy.get(fx["cost"]):
            return False
        c.economy[fx["cost"]] -= 1
        eng.log.call("op", "activation", "OK", aref, fx.get("name"))
        return True

    @staticmethod
    def p_hit(bonus, ac, mode="normal"):
        p = min(0.95, max(0.05, (21 + bonus - ac) / 20))
        return p * p if mode == "disadvantage" else 1 - (1 - p) ** 2 if mode == "advantage" else p

    @staticmethod
    def p_fail(dc, save):
        return min(0.95, max(0.05, (dc - save - 1) / 20))

    def save_bonus(self, f, ab):
        return f.save_bonus.get(ab, f.mod(ab)) if f.monster else f.mod(ab) + (f.pb if ab in f.prof["saving_throw"] else 0)

    def avg(self, eng, c, x, ctx):
        """Expected value of an expression (dice at their average), without rolling."""
        saved = eng.ex.roll
        eng.ex.roll = lambda n, f, crit=False, best_of=1: n * (2 if crit else 1) * (f + 1) / 2
        try:
            return eng.ev(x, c, ctx)
        except Exception:
            return 0
        finally:
            eng.ex.roll = saved

    # ==========================================================================================
    # turns
    # ==========================================================================================
    def turn(self, eng, c):
        if not eng.can_act(c):
            eng.log.say(f"{c} cannot act")
            return
        prone = "dnd5e/condition/prone"
        if prone in c.conditions:
            r, stand = self.activation(eng, c, prone, name="Right yourself")
            if stand:
                cost = int(eng.ev(stand["movement_cost"], c, Ctx(c, ref=prone)))
                if c.economy.get("movement", 0) >= cost and eng.activate(c, prone, stand, c):
                    c.economy["movement"] -= cost
        if c.kind == "pc":
            self.turn_pc(eng, c)
        else:
            self.turn_monster(eng, c)

    # -- player characters --------------------------------------------------------------------
    def turn_pc(self, eng, c):
        if not self.foes(eng, c):
            return
        self.emergency(eng, c)
        self.pre_buff(eng, c)
        self.move(eng, c)
        self.act(eng, c)
        if self.foes(eng, c):
            r, surge = self.activation(eng, c, name="Action Surge")
            if surge and eng.activate(c, r, surge, c):
                self.act(eng, c)
        self.bonus(eng, c)

    def ranged_role(self, eng, c):
        k = cls_of(c)
        if k in MELEE or c.form is not None:
            return False
        if k in ("ranger", "rogue"):
            return best_weapon(eng, c, True) is not None
        return True

    def move(self, eng, c):
        foes = self.foes(eng, c)
        if not foes:
            return
        near = self.nearest(eng, c, foes)
        if self.ranged_role(eng, c):
            far = max(foes, key=lambda o: abs(o.x - c.x))
            if abs(near.x - c.x) <= 5 and cls_of(c) == "rogue":
                r, ca = self.activation(eng, c, name="Cunning Action")
                if ca and eng.activate(c, r, ca, c):
                    pass
            self.keep_away(eng, c, near, 20)
            if abs(far.x - c.x) > 60 and abs(near.x - c.x) > 30:
                self.approach(eng, c, near, stop=30)
        else:
            self.approach(eng, c, near)

    def emergency(self, eng, c):
        allies = self.allies(eng, c)
        down = [a for a in allies if a.hp == 0 and not a.dead]
        hurt = sorted([a for a in allies if 0 < a.hp <= eng.hp_max(a) // 4], key=lambda a: a.hp)
        need = down or hurt
        if not need:
            if c.hp <= eng.hp_max(c) // 2:
                r, sw = self.activation(eng, c, name="Second Wind")
                if sw:
                    eng.activate(c, r, sw, c)
            return
        t = need[0]
        for sref in (S + "healing-word", S + "mass-healing-word"):
            if sref in c.prepared + c.always and c.economy.get("bonus_action"):
                slot = self.lowest_slot(eng, c, sref)
                if slot and eng.cast(c, sref, slot, [t]):
                    return
        r, loh = self.activation(eng, c, name="Lay On Hands")
        if loh and c.resources.get("lay_on_hands", {}).get("cur", 0) > 0 and abs(t.x - c.x) <= 30:
            pts = min(c.resources["lay_on_hands"]["cur"], eng.hp_max(t) - t.hp)
            self.approach(eng, c, t)
            if abs(t.x - c.x) <= 5 and eng.activate(c, r, loh, t, Ctx(c, chosen={"lay_on_hands_points": pts})):
                return
        r, spark = self.activation(eng, c, name="Divine Spark")
        if spark and c.resources.get("channel_divinity", {}).get("cur", 0) > 0 and abs(t.x - c.x) <= 30 and \
                eng.activate(c, r, spark, t, Ctx(c, target=t, flags={"targets": [t]})):
            return
        if t.hp == 0:
            for sref in (S + "cure-wounds",):
                if sref in c.prepared + c.always and c.economy.get("action"):
                    self.approach(eng, c, t)
                    slot = self.lowest_slot(eng, c, sref)
                    if slot and abs(t.x - c.x) <= 5 and eng.cast(c, sref, slot, [t]):
                        return
            pot = next((it for it in c.items if "potions-of-healing" in it["ref"]), None)
            if pot and t is c and c.economy.get("bonus_action"):
                eng.use_item(c, pot, c)

    def pre_buff(self, eng, c):
        foes = self.foes(eng, c)
        k = cls_of(c)
        if not c.economy.get("bonus_action"):
            return
        if k == "barbarian" and not eng.has_rage(c):
            r, rage = self.activation(eng, c, ident="enter_rage")
            if rage and eng.activate(c, r, rage, c):
                return
        if k == "druid" and c.form is None and not any(s[0] for s in c.slots.values()) and \
                abs(self.nearest(eng, c).x - c.x) <= 30:
            r, ws = self.activation(eng, c, name="Wild Shape")
            if ws and eng.activate(c, r, ws, c):
                return
        target = max(foes, key=lambda o: o.hp)
        if k == "ranger" and c.concentration is None:
            r, fe = self.activation(eng, c, ref="dnd5e/feature/ranger-favored-enemy")
            if fe and c.resources.get("favored_enemy", {}).get("cur", 0) > 0 and \
                    eng.activate(c, r, fe, target, Ctx(c, target=target, flags={"targets": [target]})):
                return
            if S + "hunters-mark" in c.always and self.lowest_slot(eng, c, S + "hunters-mark") and \
                    self.encounter.get("boss") and eng.cast(c, S + "hunters-mark", self.lowest_slot(eng, c, S + "hunters-mark"), [target]):
                return
        if k == "warlock" and c.concentration is None and S + "hex" in c.prepared and self.encounter.get("boss"):
            slot = self.lowest_slot(eng, c, S + "hex")
            if slot and eng.cast(c, S + "hex", slot, [target]):
                return
        if k == "sorcerer" and not any(slug(t["ref"]) == "sorcerer-innate-sorcery" for t in c.temps) and \
                self.encounter.get("boss"):
            r, inn = self.activation(eng, c, name="Innate Sorcery")
            if inn and eng.activate(c, r, inn, c):
                return
        if k == "bard":
            mates = [a for a in self.allies(eng, c) if a is not c and a.up and a.kind == "pc"
                     and not any(t.get("grant") for t in a.temps) and cls_of(a) in MELEE]
            r, bi = self.activation(eng, c, name="Bardic Inspiration")
            if bi and mates and c.resources.get("bardic_inspiration", {}).get("cur", 0) > 0:
                eng.activate(c, r, bi, mates[0])
                return
        if k == "cleric" and S + "spiritual-weapon" in c.prepared and c.concentration is None and self.encounter.get("boss"):
            slot = self.lowest_slot(eng, c, S + "spiritual-weapon")
            if slot and eng.cast(c, S + "spiritual-weapon", slot, [self.nearest(eng, c)]):
                return

    # -- the action -------------------------------------------------------------------------------
    def act(self, eng, c):
        if not c.economy.get("action"):
            return
        foes = self.foes(eng, c)
        if not foes:
            return
        if cls_of(c) == "sorcerer" and not any(s[0] for s in c.slots.values()) and \
                c.resources.get("sorcery_points", {}).get("cur", 0) >= 2 and c.economy.get("bonus_action"):
            for r, fx in eng.activations(c):
                if r.endswith("sorcerer-font-of-magic") and fx.get("cost") == "bonus_action":
                    if eng.activate(c, r, fx, c, Ctx(c, chosen={"slot_level": 1})):
                        break
        options = []
        w = self.weapon_option(eng, c, foes)
        if w:
            options.append(w)
        options += self.spell_options(eng, c, foes)
        options += self.item_options(eng, c, foes)
        if not options:
            eng.log.say(f"{c} has nothing useful to do")
            return
        val, kind, payload = max(options, key=lambda o: o[0])
        if kind == "weapon":
            self.do_attacks(eng, c, *payload)
        elif kind == "spell":
            sref, slot, targets, point = payload
            ok = eng.cast(c, sref, slot, targets, Ctx(c, flags={"point": point} if point is not None else {}))
            if not ok and w:
                self.do_attacks(eng, c, *w[2])
        elif kind == "item":
            it, target, charges = payload
            if not eng.use_item(c, it, target, charges=charges) and w:
                self.do_attacks(eng, c, *w[2])

    def weapon_option(self, eng, c, foes):
        near = self.nearest(eng, c, foes)
        adjacent = abs(near.x - c.x) <= 5
        if c.form is not None:
            return (8, "weapon", ("form", near, None, False))
        ranged = not adjacent
        choice = best_weapon(eng, c, ranged)
        if choice is None and not adjacent:
            return None
        if choice is None:
            if cls_of(c) == "monk":
                return (5, "weapon", ("unarmed", near, None, False))
            return None
        wref, item, thrown = choice
        n = int(eng.stat(c, "attacks_per_attack_action", Ctx(c), 1))
        d = eng.cat.get(wref)["data"]
        die = d["damage"]["amount"]
        a, f = (int(x) for x in die.split("d"))
        props = [slug(p["ref"]) for p in d.get("properties", [])]
        ab = "dex" if d["melee_or_ranged"] == "ranged" or ("finesse" in props and c.mod("dex") > c.mod("str")) else "str"
        bonus = c.mod(ab) + (c.pb if eng.weapon_proficient(c, wref) else 0) + (item or {}).get("bonus", 0)
        target = near if adjacent else min(foes, key=lambda o: (o.hp, abs(o.x - c.x)))
        mode = "normal"
        rng = next((p.get("range") for p in d.get("properties", []) if p.get("range")), None)
        dist = abs(target.x - c.x)
        if not adjacent and rng:
            if dist > rng["long_feet"]:
                return None
            if dist > rng["normal_feet"]:
                mode = "disadvantage"
        elif not adjacent and d["melee_or_ranged"] == "melee" and not thrown:
            mode = "normal"
        per = a * (f + 1) / 2 + c.mod(ab) + (item or {}).get("bonus", 0)
        p = self.p_hit(bonus, eng.ac(target, Ctx(target)), mode)
        return (n * per * p, "weapon", (wref, target, item, thrown))

    def do_attacks(self, eng, c, wref, target, item, thrown):
        if not self.use_action(eng, c):
            return
        eng.emit("takes_attack_action", c, Ctx(c, target=target))
        n = int(eng.stat(c, "attacks_per_attack_action", Ctx(c), 1))
        if n > 1:
            eng.log.call("stat", "attacks_per_attack_action", "OK", "dnd5e/action/attack", f"{n} attacks")
        for i in range(n):
            foes = self.foes(eng, c)
            if not foes:
                return
            holder = {}
            eng.emit("attack_action_attack", c, Ctx(c, target=target, flags={"replaced": holder}))
            if holder.get("replaced"):
                continue
            if target is None or not target.up:
                target = self.nearest(eng, c, foes)
            if wref == "form":
                self.form_attack(eng, c, target)
                continue
            if wref == "unarmed":
                self.approach(eng, c, target)
                if abs(target.x - c.x) <= 5:
                    eng.unarmed_strike(c, target)
                continue
            d = eng.cat.get(wref)["data"]
            if d["melee_or_ranged"] == "melee" and not thrown:
                self.approach(eng, c, target)
                if abs(target.x - c.x) > 5:
                    alt = best_weapon(eng, c, True)
                    if not alt:
                        return
                    wref, item, thrown = alt
            eng.weapon_attack(c, wref, target, Ctx(c, flags={"thrown": thrown}), item=item)
            if thrown and item is not None:
                item["thrown_away"] = item.get("thrown_away", 0) + 1

    def form_attack(self, eng, c, target):
        acts = [(r, fx) for r, fx in eng.activations(c) if c.form and r == c.form["ref"] and fx.get("cost") == "action"]
        if not acts:
            return
        self.approach(eng, c, target)
        r, fx = acts[0]
        if abs(target.x - c.x) <= 5:
            c.economy["action"] = c.economy.get("action", 0) + 1
            eng.activate(c, r, fx, target)

    def spell_options(self, eng, c, foes):
        out = []
        boss = self.encounter.get("boss")
        many = len(foes) >= 3
        k = cls_of(c)
        reserve = 1 if k in HEALERS else 0
        slots_left = sum(s[0] for s in c.slots.values()) + c.resources.get("pact_magic_slot", {}).get("cur", 0)
        for sref in list(dict.fromkeys(c.cantrips + c.prepared + c.always)):
            sp = eng.cat.get(sref)
            if sp["data"]["casting_time"].get("cost") != "action":
                continue
            slot = self.lowest_slot(eng, c, sref)
            if slot is None:
                continue
            lvl = sp["facets"]["level"]
            if lvl > 0 and not (boss or many) and slots_left <= reserve + 1:
                continue
            if lvl > 0 and not (boss or many or self.encounter.get("round", 1) <= 1):
                continue
            v, targets, point = self.estimate(eng, c, sref, slot, foes)
            if v <= 0:
                continue
            if lvl > 0:
                v -= 2.5 * lvl * (0.4 if boss else 1)
            out.append((v, "spell", (sref, slot, targets, point)))
        return out

    def estimate(self, eng, c, sref, slot, foes):
        sp = eng.cat.get(sref)
        ctx = Ctx(c, ref=sref, spell={"ref": sref, "slot": slot, "level": sp["facets"]["level"],
                                      "ability": c.spell_ability, "cantrip": sp["facets"]["level"] == 0})
        reach = (sp["data"].get("range") or {}).get("feet") or (5 if (sp["data"].get("range") or {}).get("kind") == "touch" else 60)
        if (sp["data"].get("range") or {}).get("kind") == "self":
            reach = 5
        targetable = [f for f in foes if abs(f.x - c.x) <= max(reach, 15)]
        if not targetable:
            return 0, [], None
        value, n_targets, point = 0.0, 1, None
        stack = [(fx, 1.0) for fx in sp.get("effects") or []]
        area = None
        while stack:
            fx, p = stack.pop()
            if not isinstance(fx, dict):
                continue
            op = fx.get("op")
            t = fx.get("target") or {}
            if t.get("kind") == "area":
                area = t["area"]
            mult = 1.0
            if op == "repeat":
                mult = self.avg(eng, c, fx["times"], ctx) or 1
                stack += [(x, p * mult) for x in fx.get("then", [])]
                continue
            if op == "attack":
                tgt = min(targetable, key=lambda f: f.hp)
                q = self.p_hit(int(eng.var(c, "spell_attack_bonus", ctx)), eng.ac(tgt, Ctx(tgt)))
                stack += [(x, p * q) for x in fx.get("on_hit", [])]
                continue
            if op == "save":
                tgt = min(targetable, key=lambda f: f.hp)
                ab = fx["ability"] if isinstance(fx["ability"], str) else "dex"
                try:
                    dc = int(self.avg(eng, c, fx["dc"], ctx))
                except Exception:
                    dc = 13
                q = self.p_fail(dc, self.save_bonus(tgt, ab))
                stack += [(x, p * q) for x in fx.get("on_fail", [])]
                if fx.get("half_on_success"):
                    stack += [(x, p * (1 - q) * 0.5) for x in fx.get("on_fail", []) if x.get("op") == "damage"]
                continue
            if op == "damage":
                extra = eng.stat(c, "damage_roll", ctx.sub(roll="damage_roll"), 0) if sp["facets"]["level"] == 0 else 0
                value += p * (self.avg(eng, c, fx["amount"], ctx) + extra)
            elif op == "apply_condition":
                value += p * 6 * CONTROL.get(fx.get("condition"), 0.3)
            elif op in ("trigger",) and fx.get("duration"):
                stack += [(x, p * 2) for x in fx.get("then", [])]
        if area:
            size = area.get("size_feet", 10)
            point = self.best_point(targetable, size) if area.get("origin") != "self" else c.x
            hit = [f for f in foes if abs(f.x - point) <= size]
            allies_hit = [a for a in self.allies(eng, c) if abs(a.x - point) <= size and a is not c] \
                if area.get("origin") != "self" else []
            if allies_hit:
                return 0, [], None
            n_targets = len(hit)
            targets = hit
        else:
            count = int(self.avg(eng, c, (sp.get("effects") or [{}])[0].get("target", {}).get("count", 1), ctx) or 1)
            targets = sorted(targetable, key=lambda f: (f.hp, abs(f.x - c.x)))[:max(1, count)]
            # every missile/ray of a repeated spell goes to the weakest target first
            targets = (targets * 4)[:4]
        return value * max(1, n_targets), targets, point

    def item_options(self, eng, c, foes):
        out = []
        for it in c.items:
            if slug(it["ref"]) == "wand-of-magic-missiles" and it.get("charges", 0) > 0:
                charges = min(3, it["charges"]) if self.encounter.get("boss") else 1
                t = min(foes, key=lambda f: f.hp)
                out.append((3.5 * (2 + charges) - 1, "item", (it, t, charges)))
            if "spell-scroll" in it["ref"] and it.get("spell") and self.encounter.get("boss") and \
                    eng.holds({"pred": "spell_on_your_list"}, c, Ctx(c, item=it)):
                v, targets, point = self.estimate(eng, c, it["spell"], eng.cat.get(it["spell"])["facets"]["level"], foes)
                if v > 10:
                    out.append((v, "item", (it, targets[0] if targets else None, 1)))
        return out

    def bonus(self, eng, c):
        if not c.economy.get("bonus_action"):
            return
        foes = self.foes(eng, c)
        if not foes:
            return
        k = cls_of(c)
        near = self.nearest(eng, c, foes)
        if k == "monk" and abs(near.x - c.x) <= 5:
            r, fl = self.activation(eng, c, name="Flurry of Blows")
            if fl and eng.activate(c, r, fl, near):
                return
            r, ma = self.activation(eng, c, name="Bonus Unarmed Strike")
            if ma and eng.activate(c, r, ma, near):
                return
        if c.hp <= eng.hp_max(c) // 2:
            r, sw = self.activation(eng, c, name="Second Wind")
            if sw and eng.activate(c, r, sw, c):
                return
            pot = next((it for it in c.items if "potions-of-healing" in it["ref"]), None)
            if pot and c.hp <= eng.hp_max(c) // 3 and eng.use_item(c, pot, c):
                return
        if S + "healing-word" in c.prepared + c.always:
            hurt = [a for a in self.allies(eng, c) if 0 <= a.hp <= eng.hp_max(a) // 3]
            if hurt:
                slot = self.lowest_slot(eng, c, S + "healing-word")
                if slot and eng.cast(c, S + "healing-word", slot, [hurt[0]]):
                    return
        if k == "rogue" and abs(near.x - c.x) > 5:
            r, sa = self.activation(eng, c, name="Steady Aim")
            if sa and not c.turn.get("moved"):
                eng.activate(c, r, sa, c)
                return
        # Spiritual Weapon already up: its bonus-action attack
        for r, fx in eng.activations(c):
            if fx.get("cost") == "bonus_action" and r == S + "spiritual-weapon" and c.concentration and \
                    c.concentration["ref"] == r:
                eng.activate(c, r, fx, near, Ctx(c, spell={"ref": r, "slot": 2, "level": 2,
                                                           "ability": c.spell_ability}))
                return

    # -- monsters ---------------------------------------------------------------------------------
    def turn_monster(self, eng, c):
        foes = self.foes(eng, c)
        if not foes:
            return
        if c.behaviour.get("flee_at_half") and c.hp <= c.hp_base // 2:
            c.behaviour["fled"] = True
            c.x += 200
            eng.log.say(f"{c} flees the fight")
            return
        acts = [(r, fx) for r, fx in eng.activations(c) if r == c.monster["ref"]]
        multi = eng.cat.rule(c.monster["ref"], "multiattack")
        attack_acts = {fx.get("name"): fx for r, fx in acts if fx.get("cost") == "action"
                       and any(x.get("op") == "attack" for x in fx["then"])}
        near = self.nearest(eng, c, foes)
        # breath weapons / area saves (Recharge only in a note): once per fight
        for r, fx in acts:
            if fx.get("cost") != "action" or "Recharge" not in (fx.get("note") or ""):
                continue
            eng.log.call("note", "activation", "DATA_GAP", r, "Recharge X–Y only in a note; used once per fight (GM)")
            key = (id(c), fx.get("name"))
            if key in self.used_recharge:
                continue
            self.used_recharge.add(key)
            self.approach(eng, c, near, stop=10)
            if eng.activate(c, r, fx, near):
                return
        # spellcasting (stat block spells with uses per day)
        casts = [(r, fx) for r, fx in acts if fx.get("cost") == "action" and
                 any(x.get("op") == "cast_spell" for x in fx["then"]) and
                 slug(next(x for x in fx["then"] if x.get("op") == "cast_spell")["spell"]) in (
                     "hold-person", "command", "sleep", "magic-missile", "fire-bolt", "ray-of-sickness", "web",
                     "burning-hands", "chill-touch", "sacred-flame", "inflict-wounds", "shatter", "scorching-ray")]
        for r, fx in casts:
            freq = fx.get("frequency")
            key = (r, "activation:" + str(fx.get("name")))
            if freq and not eng.freq_ok(c, key, freq):
                continue
            target = max(foes, key=lambda o: o.hp)
            if freq:
                eng.freq_use(c, key, freq)
            if eng.activate(c, r, fx, target, Ctx(c, target=target, flags={"targets": [target]})):
                return
        if multi and multi.get("attacks"):
            eng.log.call("rule", "multiattack", "OK", c.monster["ref"])
            if not c.economy.get("action"):
                return
            c.economy["action"] = 0
            for a in multi["attacks"]:
                fx = attack_acts.get(a["name"])
                if not fx:
                    continue
                for _ in range(a["count"]):
                    foes = self.foes(eng, c)
                    if not foes:
                        return
                    t = self.nearest(eng, c, foes)
                    if not self.in_range(c, fx, t):
                        self.approach(eng, c, t)
                    if self.in_range(c, fx, t):
                        c.economy["action"] = 1
                        eng.activate(c, c.monster["ref"], fx, t)
            return
        # a single attack: melee when adjacent (or able to close), ranged otherwise
        melee = [fx for fx in attack_acts.values() if self.reach(fx) <= 10]
        ranged = [fx for fx in attack_acts.values() if self.reach(fx) > 10]
        if c.behaviour.get("role") == "ranged" and ranged:
            t = min(foes, key=lambda o: (eng.ac(o, Ctx(o)), o.hp))
            if abs(near.x - c.x) <= 5:
                r, ne = next(((r, fx) for r, fx in acts if fx.get("name") == "Nimble Escape"), (None, None))
                if ne:
                    eng.activate(c, r, ne, c)
                self.keep_away(eng, c, near, 30)
            eng.activate(c, c.monster["ref"], ranged[0], t)
            return
        if melee:
            self.approach(eng, c, near)
            if abs(near.x - c.x) <= self.reach(melee[0]):
                eng.activate(c, c.monster["ref"], max(melee, key=lambda fx: self.dmg(eng, c, fx)), near)
                return
        if ranged:
            eng.activate(c, c.monster["ref"], ranged[0], near)

    def reach(self, fx):
        for x in fx["then"]:
            if x.get("op") == "attack":
                t = (x.get("target") or {}).get("range") or {}
                if x["attack_type"].startswith("ranged"):
                    return t.get("feet", 80)
                return t.get("feet", 5)
        return 5

    def in_range(self, c, fx, t):
        return abs(t.x - c.x) <= self.reach(fx)

    def dmg(self, eng, c, fx):
        tot = 0
        for x in fx["then"]:
            for d in x.get("on_hit", []):
                if d.get("op") == "damage":
                    tot += self.avg(eng, c, d["amount"], Ctx(c))
        return tot
