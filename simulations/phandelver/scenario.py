"""Scenario: the Lost Mine of Phandelver, as a sequence of scenes for tools/engine/campaign.py.

SIMULATION ONLY. This file is built from the adventure PDF the project owner supplied for the
simulation; it is not part of the knowledge base (knowledge/) and nothing in the build reads it.
It keeps only what a simulation needs: which creatures each area holds, the XP the book awards,
the treasure, the traps' DCs and the book's level milestones.

Creatures the SRD 5.2.1 does not have are played by the closest SRD stat block (same role and
challenge), listed in SUBSTITUTES. Named magic items map to their SRD item (Talon -> Weapon +1,
longsword); items without an SRD entry are kept in the inventory by name.
"""
C = "dnd5e/creature/"
MI = "dnd5e/magic-item/"
SP = "dnd5e/spell/"
COND = "dnd5e/condition/"

SUBSTITUTES = {
    "Goblin": "goblin-warrior", "Goblin leader (Yeemik, Yegg, Lhupo)": "goblin-boss",
    "Bugbear (Klarg, Mosk, Nezznar's guards)": "bugbear-warrior", "King Grol (old bugbear)": "bugbear-stalker",
    "Redbrand ruffian": "tough", "Nothic": "gibbering-mouther", "Evil mage (Iarno, Hamun Kost)": "cultist-fanatic",
    "Nezznar, drow spellcaster": "cultist-fanatic", "Twig blight": "awakened-shrub", "Ash zombie": "zombie",
    "Orc": "gnoll-warrior", "Brughor, orc war chief": "tough-boss", "Hobgoblin": "hobgoblin-warrior",
    "Targor (hobgoblin leader)": "hobgoblin-captain", "Flameskull": "wight", "Spectator": "gibbering-mouther",
    "Venomfang": "young-green-dragon", "Mormesk": "wraith",
}

POTION = {"ref": MI + "potions-of-healing", "name": "Potion of Healing", "variant": "Potion of Healing"}


def potions(n):
    return dict(POTION, quantity=n)


def scroll(spell, name):
    return {"ref": MI + "spell-scroll", "name": f"Spell Scroll ({name})", "spell": SP + spell}


def plus1(base, name):
    kind = "weapon" if "/weapon/" in base else "armor"
    ref = MI + ("weapon-plus1-plus2-or-plus3" if kind == "weapon" else "armor-plus1-plus2-or-plus3")
    return {"ref": ref, "name": name, "base": base, "bonus": 1}


def gems(name, gp, n=1):
    return {"name": name, "gp": gp, "quantity": n}


def foe(slug_, count=1, role="melee", **kw):
    return {"ref": C + slug_, "count": count, "role": role, **kw}


def d(n, f, plus=0):
    return lambda rng: sum(rng.randint(1, f) for _ in range(n)) + plus


TRIBOAR = {  # wilderness encounters (d12, day / night)
    "day": [(1, 2, C + "stirge", d(1, 8, 2)), (3, 4, C + "ogre", 1), (5, 6, C + "goblin-warrior", d(1, 6, 3)),
            (7, 8, C + "hobgoblin-warrior", d(1, 4, 2)), (9, 10, C + "gnoll-warrior", d(1, 4, 2)),
            (11, 11, C + "wolf", d(1, 4, 2)), (12, 12, C + "owlbear", 1)],
    "night": [(1, 3, C + "ghoul", d(1, 4, 1)), (4, 4, C + "ogre", 1), (5, 5, C + "hobgoblin-warrior", d(1, 4, 2)),
              (6, 6, C + "gnoll-warrior", d(1, 4, 2)), (7, 8, C + "wolf", d(1, 4, 2)), (9, 10, C + "owlbear", 1),
              (11, 12, C + "stirge", d(1, 8, 2))],
}
WAVE_ECHO = [(1, 3, C + "stirge", d(2, 4)), (4, 5, C + "ghoul", d(1, 4)), (6, 6, C + "grick", d(1, 4)),
             (7, 8, C + "bugbear-warrior", d(1, 4)), (9, 9, C + "skeleton", d(1, 6)), (10, 10, C + "zombie", d(1, 6)),
             (11, 12, C + "ochre-jelly", 1)]


def scenes():
    P1, P2, P3, P4 = "part-1-goblin-arrows", "part-2-phandalin", "part-3-spiders-web", "part-4-wave-echo-cave"
    s = []
    add = s.append
    # ---------------------------------------------------------------- Part 1: Goblin Arrows
    add({"type": "combat", "part": P1, "name": "Goblin ambush on the Triboar Trail",
         "foes": [foe("goblin-warrior", 2), foe("goblin-warrior", 2, "ranged")], "distance": 30})
    add({"type": "trap", "part": P1, "name": "Goblin trail: snare", "notice": 12, "save": "dex", "dc": 10,
         "damage": "1d6", "damage_type": "bludgeoning"})
    add({"type": "trap", "part": P1, "name": "Goblin trail: hidden pit", "notice": 15, "save": "dex", "dc": 10,
         "damage": "1d6", "damage_type": "bludgeoning"})
    add({"type": "reward", "part": P1, "name": "Reach the Cragmaw hideout", "xp_each": 75})
    add({"type": "combat", "part": P1, "name": "Cragmaw hideout 2: goblin lookouts",
         "foes": [foe("goblin-warrior", 2, "ranged")], "distance": 40})
    add({"type": "combat", "part": P1, "name": "Cragmaw hideout 3: kennel", "foes": [foe("wolf", 3)], "distance": 15})
    add({"type": "combat", "part": P1, "name": "Cragmaw hideout 5: bridge sentry",
         "foes": [foe("goblin-warrior", 1, "ranged")], "distance": 30})
    add({"type": "trap", "part": P1, "name": "Cragmaw hideout: flood", "save": "dex", "dc": 10, "who": "all",
         "damage": "1d6", "damage_type": "bludgeoning", "conditions": [COND + "prone"]})
    add({"type": "combat", "part": P1, "name": "Cragmaw hideout 6: goblin den (Yeemik)",
         "foes": [foe("goblin-warrior", 5), foe("goblin-boss", 1, name="Yeemik")], "distance": 30,
         "loot": {"coins": {"sp": 15}, "valuables": [gems("Gold tooth", 1, 3)]}})
    add({"type": "combat", "part": P1, "name": "Cragmaw hideout 7: twin pools",
         "foes": [foe("goblin-warrior", 3)], "distance": 30})
    add({"type": "combat", "part": P1, "name": "Cragmaw hideout 8: Klarg's cave", "boss": True,
         "foes": [foe("bugbear-warrior", 1, name="Klarg"), foe("wolf", 1, name="Ripper"), foe("goblin-warrior", 2)],
         "distance": 25,
         "loot": {"coins": {"cp": 600, "sp": 110}, "items": [potions(2)],
                  "valuables": [gems("Jade frog statuette", 40)]}})
    add({"type": "reward", "part": P1, "name": "Clear the Cragmaw hideout", "xp_each": 275})
    add({"type": "rest", "part": P1, "name": "Rest at the hideout", "kind": "long"})
    add({"type": "reward", "part": P1, "name": "Deliver the wagon to Barthen's (10 gp each) and escort Sildar (50 gp)",
         "loot": {"coins": {"gp": 60 + 50}}})
    # ---------------------------------------------------------------- Part 2: Phandalin
    add({"type": "reward", "part": P2, "name": "Return the Lionshield goods to Linene", "loot": {"coins": {"gp": 50}}})
    add({"type": "rest", "part": P2, "name": "Stonehill Inn", "kind": "long"})
    add({"type": "combat", "part": P2, "name": "Redbrand ruffians in the street", "xp": 400,
         "foes": [foe("tough", 4)], "distance": 20})
    add({"type": "reward", "part": P2, "name": "Tresendar cellar: Iarno's escape bag",
         "loot": {"coins": {"gp": 50}, "items": [potions(1), {"ref": MI + "potion-of-invisibility",
                                                               "name": "Potion of Invisibility"}]}})
    add({"type": "combat", "part": P2, "name": "Redbrand hideout 2: barracks", "xp": 300,
         "foes": [foe("tough", 3)], "distance": 15,
         "loot": {"coins": {"sp": 28, "gp": 12, "ep": 15}, "valuables": [gems("Garnet", 10, 2)]}})
    add({"type": "trap", "part": P2, "name": "Redbrand hideout 3: pit trap", "notice": 15, "save": "dex", "dc": 15,
         "damage": "2d6", "damage_type": "bludgeoning", "conditions": [COND + "prone"], "xp": 100})
    add({"type": "combat", "part": P2, "name": "Redbrand hideout 4: Tresendar crypts", "xp": 150,
         "foes": [foe("skeleton", 3)], "distance": 20, "loot": {"valuables": [gems("Platinum signet ring", 50, 3)]}})
    add({"type": "combat", "part": P2, "name": "Redbrand hideout 5: slave pens", "xp": 200 + 100,
         "foes": [foe("tough", 2)], "distance": 15})
    add({"type": "reward", "part": P2, "name": "Redbrand hideout 7: storeroom", "loot": {"valuables": [gems("Beaver pelt", 2, 30)]}})
    add({"type": "combat", "part": P2, "name": "Redbrand hideout 8: the crevasse guardian", "xp": 450, "boss": True,
         "foes": [foe("gibbering-mouther", 1, name="Nothic")], "distance": 20,
         "loot": {"coins": {"sp": 160, "gp": 120}, "valuables": [gems("Malachite", 15, 5)],
                  "items": [potions(2), scroll("augury", "Augury"),
                            plus1("dnd5e/weapon/longsword", "Talon (+1 longsword)")]}})
    add({"type": "combat", "part": P2, "name": "Redbrand hideout 9: bugbear guards (Mosk)", "xp": 600, "boss": True,
         "foes": [foe("bugbear-warrior", 3)], "distance": 15,
         "loot": {"coins": {"sp": 33}, "valuables": [gems("Jeweled eyepatch", 50)]}})
    add({"type": "combat", "part": P2, "name": "Redbrand hideout 10: common room (drunk)", "xp": 400,
         "foes": [foe("tough", 4, conditions=[COND + "poisoned"])], "distance": 15,
         "loot": {"coins": {"cp": 75, "sp": 55, "ep": 22, "gp": 15}, "valuables": [gems("Ruby earrings", 30)]}})
    add({"type": "reward", "part": P2, "name": "Redbrand hideout 11: wizard's workshop",
         "loot": {"valuables": [gems("Rare reagent", 25, 3)]}})
    add({"type": "combat", "part": P2, "name": "Redbrand hideout 12: Glasstaff", "xp": 200, "boss": True,
         "foes": [foe("cultist-fanatic", 1, "ranged", name="Iarno 'Glasstaff' Albrek")], "distance": 25,
         "loot": {"coins": {"sp": 180, "gp": 130},
                  "valuables": [gems("Carnelian", 10, 5), gems("Peridot", 15, 2), gems("Pearl", 100)],
                  "items": [scroll("charm-person", "Charm Person"), scroll("fireball", "Fireball"),
                            {"name": "Staff of Defense (no SRD entry)", "note": "+1 AC; casts Mage Armor/Shield"}]}})
    add({"type": "reward", "part": P2, "name": "Sildar's reward (200 gp) and Halia's job (100 gp)",
         "loot": {"coins": {"gp": 300}}})
    add({"type": "milestone", "part": P2, "name": "Book: level 3 during Part 2", "level": 3,
         "why": "the book expects level 3 during Part 2"})
    add({"type": "rest", "part": P2, "name": "Stonehill Inn", "kind": "long"})
    # ---------------------------------------------------------------- Part 3: The Spider's Web
    add({"type": "travel", "part": P3, "name": "Triboar Trail to Old Owl Well", "days": 2, "table": TRIBOAR})
    add({"type": "combat", "part": P3, "name": "Old Owl Well: Hamun Kost and his zombies", "xp": 800, "boss": True,
         "foes": [foe("zombie", 12), foe("cultist-fanatic", 1, "ranged", name="Hamun Kost")], "distance": 30,
         "loot": {"coins": {"sp": 35, "ep": 20, "gp": 20, "pp": 5},
                  "valuables": [gems("Pearl", 100), gems("Tiny jewelry box", 25)],
                  "items": [potions(1), scroll("darkness", "Darkness"), {"ref": MI + "ring-of-protection",
                                                                         "name": "Ring of Protection"}]}})
    add({"type": "travel", "part": P3, "name": "Hills to Wyvern Tor", "days": 2, "table": TRIBOAR})
    add({"type": "combat", "part": P3, "name": "Wyvern Tor: orc sentry", "foes": [foe("gnoll-warrior", 1)], "distance": 40})
    add({"type": "combat", "part": P3, "name": "Wyvern Tor: Brughor, the orcs and Gog the ogre", "xp": 1250,
         "boss": True, "foes": [foe("tough-boss", 1, name="Brughor"), foe("gnoll-warrior", 5), foe("ogre", 1, name="Gog")],
         "distance": 25, "loot": {"coins": {"cp": 750, "sp": 180, "ep": 62, "gp": 30},
                                  "valuables": [gems("Perfume vial", 10, 3)]}})
    add({"type": "reward", "part": P3, "name": "Harbin Wester's bounty for the orcs", "loot": {"coins": {"gp": 100}}})
    add({"type": "rest", "part": P3, "name": "Camp", "kind": "long"})
    add({"type": "travel", "part": P3, "name": "Triboar Trail to Conyberry", "days": 1, "table": TRIBOAR})
    add({"type": "check", "part": P3, "name": "Agatha the banshee: ask about Bowgentle's book", "ability": "cha",
         "skill": "persuasion", "dc": 15, "auto": "Sister Garaele's silver comb",
         "on_success": {"xp": 200, "loot": {"items": [potions(3)]}}})
    add({"type": "travel", "part": P3, "name": "Neverwinter Wood to Thundertree", "days": 2, "table": TRIBOAR})
    add({"type": "combat", "part": P3, "name": "Thundertree 1-2: twig blights", "xp": 100,
         "foes": [foe("awakened-shrub", 8)], "distance": 10,
         "loot": {"coins": {"cp": 700, "sp": 160, "gp": 90}}})
    add({"type": "combat", "part": P3, "name": "Thundertree 3: ash zombies in the Brown Horse", "xp": 200,
         "foes": [foe("zombie", 4)], "distance": 15})
    add({"type": "combat", "part": P3, "name": "Thundertree 5: blight farm", "xp": 200,
         "foes": [foe("awakened-shrub", 8)], "distance": 10})
    add({"type": "combat", "part": P3, "name": "Thundertree 6: giant spiders", "xp": 400,
         "foes": [foe("giant-spider", 2)], "distance": 15,
         "loot": {"coins": {"gp": 23, "sp": 35}, "items": [potions(1)]}})
    add({"type": "combat", "part": P3, "name": "Thundertree 8: old smithy", "xp": 100, "foes": [foe("zombie", 2)], "distance": 10})
    add({"type": "check", "part": P3, "name": "Thundertree 9: Mirna's heirloom", "ability": "wis", "skill": "perception",
         "dc": 15, "auto": "Mirna told the party where it is",
         "on_success": {"xp": 200}})
    add({"type": "combat", "part": P3, "name": "Thundertree 11: old garrison", "xp": 250, "foes": [foe("zombie", 5)], "distance": 15})
    add({"type": "combat", "part": P3, "name": "Thundertree 12: weaver's cottage", "xp": 150,
         "foes": [foe("awakened-shrub", 6)], "distance": 10})
    add({"type": "combat", "part": P3, "name": "Thundertree 13: dragon cultists", "xp": 150,
         "foes": [foe("cultist", 6)], "distance": 15,
         "loot": {"valuables": [gems("Diamond", 100, 3)], "items": [{"ref": MI + "potion-of-flying", "name": "Potion of Flying"}]}})
    add({"type": "rest", "part": P3, "name": "Rest before the tower", "kind": "short"})
    add({"type": "combat", "part": P3, "name": "Thundertree 7: Venomfang (driven off at half HP)", "xp": 2000,
         "boss": True, "foes": [foe("young-green-dragon", 1, name="Venomfang", behaviour={"flee_at_half": True})],
         "distance": 30,
         "loot": {"coins": {"sp": 800, "gp": 150}, "valuables": [gems("Silver goblet with moonstones", 60, 4)],
                  "items": [scroll("misty-step", "Misty Step"), scroll("lightning-bolt", "Lightning Bolt"),
                            plus1("dnd5e/weapon/battleaxe", "Hew (+1 battleaxe)")]}})
    add({"type": "rest", "part": P3, "name": "Reidoth's camp", "kind": "long"})
    add({"type": "travel", "part": P3, "name": "Neverwinter Wood to Cragmaw Castle", "days": 2, "table": TRIBOAR})
    add({"type": "combat", "part": P3, "name": "Cragmaw Castle 3: archer posts", "xp": 200,
         "foes": [foe("goblin-warrior", 4, "ranged")], "distance": 40})
    add({"type": "trap", "part": P3, "name": "Cragmaw Castle 2: collapsing ceiling", "notice": 20, "save": "dex",
         "dc": 10, "half": True, "who": "all", "damage": "3d6", "damage_type": "bludgeoning", "xp": 100})
    add({"type": "combat", "part": P3, "name": "Cragmaw Castle 4: ruined barracks", "xp": 150,
         "foes": [foe("goblin-warrior", 3)], "distance": 15})
    add({"type": "combat", "part": P3, "name": "Cragmaw Castle 6: hobgoblin barracks", "xp": 400,
         "foes": [foe("hobgoblin-warrior", 4)], "distance": 15})
    add({"type": "combat", "part": P3, "name": "Cragmaw Castle 7: banquet hall (Yegg)", "xp": 400,
         "foes": [foe("goblin-warrior", 7), foe("goblin-boss", 1, name="Yegg")], "distance": 20})
    add({"type": "combat", "part": P3, "name": "Cragmaw Castle 8: dark hall (grick)", "xp": 450,
         "foes": [foe("grick", 1)], "distance": 10, "loot": {"valuables": [gems("Gold sun-elf statuette", 100)]}})
    add({"type": "combat", "part": P3, "name": "Cragmaw Castle 9: goblin shrine (Lhupo)", "xp": 150,
         "foes": [foe("goblin-boss", 1, name="Lhupo"), foe("goblin-warrior", 2)], "distance": 15,
         "loot": {"valuables": [gems("Golden chalice", 150), gems("Ritual knife", 60), gems("Censer", 120)]}})
    add({"type": "combat", "part": P3, "name": "Cragmaw Castle 12: guard barracks", "xp": 200,
         "foes": [foe("hobgoblin-warrior", 2)], "distance": 15})
    add({"type": "combat", "part": P3, "name": "Cragmaw Castle 13: owlbear tower", "xp": 700, "boss": True,
         "foes": [foe("owlbear", 1)], "distance": 10,
         "loot": {"coins": {"ep": 90, "gp": 120},
                  "items": [potions(1), scroll("silence", "Silence"), scroll("revivify", "Revivify")]}})
    add({"type": "combat", "part": P3, "name": "Cragmaw Castle 14: King Grol and Vyerith", "xp": 950 + 200, "boss": True,
         "foes": [foe("bugbear-stalker", 1, name="King Grol"), foe("wolf", 1, name="Snarl"),
                  foe("doppelganger", 1, name="Vyerith")], "distance": 15,
         "loot": {"coins": {"sp": 220, "ep": 160}, "items": [potions(3)]}})
    add({"type": "combat", "part": P3, "name": "Cragmaw Castle: returning war band (Targor)", "xp": 500,
         "foes": [foe("hobgoblin-captain", 1, name="Targor Bloodsword"), foe("hobgoblin-warrior", 3), foe("wolf", 2)],
         "distance": 30})
    add({"type": "reward", "part": P3, "name": "Sildar's 500 gp for Cragmaw Castle; Gundren pays 25 gp each",
         "loot": {"coins": {"gp": 500 + 150}}})
    add({"type": "milestone", "part": P3, "name": "Book: Part 4 is for level 4+", "level": 4,
         "why": "the book designs Part 4 for characters of at least 4th level (2,700 XP)"})
    add({"type": "rest", "part": P3, "name": "Phandalin", "kind": "long"})
    # ---------------------------------------------------------------- Part 4: Wave Echo Cave
    add({"type": "reward", "part": P4, "name": "Wave Echo 1: Tharden's camp",
         "loot": {"items": [{"ref": MI + "boots-of-striding-and-springing", "name": "Boots of Striding and Springing"}]}})
    add({"type": "combat", "part": P4, "name": "Wave Echo 3: old entrance (stirges)", "xp": "monsters",
         "foes": [foe("stirge", 10)], "distance": 15})
    add({"type": "combat", "part": P4, "name": "Wave Echo 4: old guardroom (skeletons)", "xp": "monsters",
         "foes": [foe("skeleton", 9)], "distance": 10})
    add({"type": "combat", "part": P4, "name": "Wave Echo 2: mine tunnels (ochre jelly)", "xp": "monsters",
         "foes": [foe("ochre-jelly", 1)], "distance": 10})
    add({"type": "check", "part": P4, "name": "Wave Echo 5: locked pay chest", "ability": "dex", "tool": "dnd5e/tool/thieves-tools",
         "dc": 20, "on_success": {"loot": {"coins": {"cp": 600, "sp": 180, "ep": 90, "gp": 60}}}})
    add({"type": "combat", "part": P4, "name": "Wave Echo 6: south barracks (ghouls)", "xp": "monsters",
         "foes": [foe("ghoul", 3)], "distance": 10})
    add({"type": "rest", "part": P4, "name": "Wave Echo 7: storeroom", "kind": "short"})
    add({"type": "combat", "part": P4, "name": "Wave Echo 9: great cavern (ghouls)", "xp": "monsters", "boss": True,
         "foes": [foe("ghoul", 7)], "distance": 20})
    add({"type": "trap", "part": P4, "name": "Wave Echo 8: fungus cavern gas", "save": "con", "dc": 11, "who": "all",
         "damage": "3d6", "damage_type": "poison", "conditions": [COND + "poisoned"],
         "duration": {"kind": "minutes", "amount": 10}})
    add({"type": "reward", "part": P4, "name": "Wave Echo 10: dark pool (wizard's skeleton)",
         "loot": {"valuables": [gems("Platinum ring", 75, 2)],
                  "items": [{"ref": MI + "wand-of-magic-missiles", "name": "Wand of Magic Missiles"}]}})
    add({"type": "combat", "part": P4, "name": "Wave Echo 11: north barracks (bugbears)", "xp": "monsters", "boss": True,
         "foes": [foe("bugbear-warrior", 5)], "distance": 15,
         "loot": {"coins": {"cp": 15, "ep": 13}, "items": [{"ref": MI + "potion-of-vitality", "name": "Potion of Vitality"}]}})
    add({"type": "rest", "part": P4, "name": "Rest in the barricaded barracks", "kind": "long"})
    add({"type": "combat", "part": P4, "name": "Wave Echo 12: smelter (zombies and the flameskull)", "xp": "monsters",
         "boss": True, "foes": [foe("zombie", 8), foe("wight", 1, "ranged", name="Flameskull")], "distance": 15})
    add({"type": "combat", "part": P4, "name": "Wave Echo 14: Mormesk the wraith", "xp": "monsters", "boss": True,
         "foes": [foe("wraith", 1, name="Mormesk")], "distance": 10,
         "loot": {"coins": {"cp": 1100, "sp": 160, "ep": 50}, "valuables": [gems("Diamond", 100, 3), gems("Platinum pipe", 150)]}})
    add({"type": "rest", "part": P4, "name": "Short rest", "kind": "short"})
    add({"type": "combat", "part": P4, "name": "Wave Echo 15: the Forge of Spells (spectator)", "xp": "monsters", "boss": True,
         "foes": [foe("gibbering-mouther", 1, name="Spectator")], "distance": 15,
         "loot": {"items": [plus1("dnd5e/weapon/mace", "Lightbringer (+1 mace)"),
                            plus1("dnd5e/armor/breastplate", "Dragonguard (+1 breastplate)")]}})
    add({"type": "combat", "part": P4, "name": "Wave Echo 18: collapsed cavern (Vhalak)", "xp": "monsters", "boss": True,
         "foes": [foe("bugbear-warrior", 3), foe("doppelganger", 1, name="Vhalak")], "distance": 15})
    add({"type": "check", "part": P4, "name": "Wave Echo 18: search the crevasse", "ability": "wis", "skill": "perception",
         "dc": 20, "on_success": {"loot": {"items": [{"ref": MI + "gauntlets-of-ogre-power", "name": "Gauntlets of Ogre Power"}]}}})
    add({"type": "rest", "part": P4, "name": "Rest before Nezznar", "kind": "long"})
    add({"type": "combat", "part": P4, "name": "Wave Echo 19: Nezznar, the Black Spider", "xp": "monsters", "boss": True,
         "foes": [foe("cultist-fanatic", 1, "ranged", name="Nezznar"), foe("giant-spider", 4), foe("bugbear-warrior", 2)],
         "distance": 25,
         "loot": {"coins": {"ep": 190, "gp": 130, "pp": 15},
                  "valuables": [gems("Small gemstone", 10, 9), gems("Electrum drinking mug", 100)],
                  "items": [potions(1), {"name": "Spider Staff (no SRD entry)", "note": "+1d6 poison; Spider Climb/Web"}]}})
    add({"type": "reward", "part": P4, "name": "Wave Echo 20: rescue Nundro", "xp": 200})
    add({"type": "milestone", "part": P4, "name": "Book: level 5 by the end of the adventure", "level": 5,
         "why": "the book: 'by the end of the adventure the characters should be 5th level'"})
    add({"type": "rest", "part": P4, "name": "Phandalin", "kind": "long"})
    # ------------------------------------------------------------- epilogue: level 5 in play
    add({"type": "travel", "part": "epilogue", "name": "Clearing Wave Echo Cave (wandering monsters)", "days": 2,
         "force": True, "table": {"day": WAVE_ECHO, "night": WAVE_ECHO}})
    return s
