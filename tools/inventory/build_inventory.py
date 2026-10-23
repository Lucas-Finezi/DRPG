#!/usr/bin/env python3
"""L00 — Build the source inventory of the SRD 5.2.1.

Reads only extraction/SRD_CC_v5.2.1.md (derived from source/SRD_CC_v5.2.1.pdf) and writes
inventory/dnd5e/srd-5.2.1/:
  source.json    identity, hash, license and attribution of the source
  outline.json   every section heading (levels 1-4) with page span and owning lot
  tables.json    every table with caption, page, header, row count and owning lot
  entries.json   every expected catalog entry, with ref, kind, page, lot and facets
  lots.json      the lot plan (phases L00-L46) with expected entry counts per lot
  README.md      human summary

The inventory is the contract that L46 audits against: every entry and every section
listed here must be covered by the generated catalog, or be recorded as a gap.

Usage: python3 -I tools/inventory/build_inventory.py
"""
import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from srdmd import load, slugify, strip_md  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
MD = ROOT / "extraction" / "SRD_CC_v5.2.1.md"
REPORT = ROOT / "extraction" / "extraction_report.json"
OUT = ROOT / "inventory" / "dnd5e" / "srd-5.2.1"
SYSTEM = "dnd5e"

# ---------------------------------------------------------------- lot plan

LOTS = [
    ("L00", 0, "Inventário da fonte", "Mapear capítulos, seções, páginas, tabelas, apêndices e licença; gerar inventário de todas as entradas esperadas."),
    ("L01", 0, "Contrato base", "JSON Schemas de system, catalog_entry, effect, source, duration, target, expression e master_decision, com exemplos válidos."),
    ("L02", 0, "Sistema D&D 5e", "Identidade do sistema, atributos, d20, proficiência, economia de ação, iniciativa, descansos, níveis, idiomas, moedas e unidades."),
    ("L03", 1, "Condições", "Todas as condições, efeitos, imunidades, durações, formas de remoção e interações."),
    ("L04", 1, "Regras de combate", "Ordem de combate, movimento, ações, ação bônus, reação, ataque, dano, cura, queda, cobertura, oculto, morte e estabilização."),
    ("L05", 1, "Testes e proficiências", "Testes de atributo, testes de resistência, proficiências, perícias, vantagem, desvantagem, inspiração e DC."),
    ("L06", 1, "Dano, cura e resistências", "Tipos de dano, resistência, vulnerabilidade, imunidade, PV temporários, queda, cura e estabilização."),
    ("L07", 1, "Recursos e descansos", "Recursos, usos, recarga, descanso curto, descanso longo, exaustão e recuperação."),
    ("L08", 1, "Regras de equipamento", "Moedas, peso, capacidade, porte, armas, armaduras, escudos, ferramentas, montarias, serviços, compra e venda."),
    ("L09", 1, "Regras de magia", "Espaços de magia, preparo, componentes, concentração, alvos, áreas, duração, escalonamento, rituais, truques."),
    ("L10", 2, "Espécies", "Todas as espécies, traços, tamanhos, deslocamentos, idiomas, escolhas e variantes da fonte."),
    ("L11", 2, "Antecedentes", "Antecedentes, atributos, talento, proficiências, equipamentos iniciais e criação de antecedente."),
    ("L12", 2, "Classes", "Cada classe: proficiências, PV, equipamentos, recursos e progressão por nível."),
    ("L13", 2, "Subclasses", "Todas as subclasses nível a nível, preservando herança das classes-base."),
    ("L14", 2, "Features e progressões", "Todas as features de classe, subclasse, espécie e opções (metamagia, invocações), com gatilhos, custos e escolhas."),
    ("L15", 2, "Talentos", "Todos os talentos, pré-requisitos, benefícios, repetições e restrições."),
    ("L16", 2, "Multiclasse", "Regras de multiclasse, requisitos, PV, proficiências, espaços de magia e progressões combinadas."),
    ("L17", 3, "Truques", "Todos os truques (nível 0)."),
    ("L18", 3, "Magias de círculo 1", "Todas as magias de nível 1 com escalonamento."),
    ("L19", 3, "Magias de círculo 2", "Todas as magias de nível 2 com escalonamento."),
    ("L20", 3, "Magias de círculo 3", "Todas as magias de nível 3 com escalonamento."),
    ("L21", 3, "Magias de círculo 4", "Todas as magias de nível 4 com escalonamento."),
    ("L22", 3, "Magias de círculo 5", "Todas as magias de nível 5 com escalonamento."),
    ("L23", 3, "Magias de círculo 6", "Todas as magias de nível 6 com escalonamento."),
    ("L24", 3, "Magias de círculo 7", "Todas as magias de nível 7 com escalonamento."),
    ("L25", 3, "Magias de círculo 8", "Todas as magias de nível 8 com escalonamento."),
    ("L26", 3, "Magias de círculo 9", "Todas as magias de nível 9 com escalonamento."),
    ("L27", 3, "Listas de magia", "Listas de magia por classe e listas de subclasse, incluindo exceções."),
    ("L28", 4, "Armas", "Armas simples e marciais, propriedades, maestrias, dano, alcance."),
    ("L29", 4, "Armaduras e escudos", "Categorias, CA, requisito de Força, penalidade de furtividade, vestir/despir."),
    ("L30", 4, "Equipamento de aventura", "Itens, ferramentas, kits, munições, focos, montarias, veículos, estilo de vida, serviços e bugigangas."),
    ("L31", 4, "Itens mágicos", "Todos os itens mágicos (exceto poções e pergaminhos) e regras de itens mágicos."),
    ("L32", 4, "Poções, pergaminhos e consumíveis", "Poções, pergaminhos e venenos, referenciando magias quando aplicável."),
    ("L33", 5, "Bestiário A–C", "Criaturas de A a C e regras de bloco de estatísticas."),
    ("L34", 5, "Bestiário D–F", "Criaturas de D a F."),
    ("L35", 5, "Bestiário G–I", "Criaturas de G a I."),
    ("L36", 5, "Bestiário J–L", "Criaturas de J a L."),
    ("L37", 5, "Bestiário M–O", "Criaturas de M a O."),
    ("L38", 5, "Bestiário P–R", "Criaturas de P a R."),
    ("L39", 5, "Bestiário S–T", "Criaturas de S a T."),
    ("L40", 5, "Bestiário U–Z", "Criaturas de U a Z."),
    ("L41", 5, "Regras de exploração e encontros", "Exploração, viagem, ambiente, perigos, armadilhas, maldições, contágios, medo e estresse."),
    ("L42", 5, "Encontros de combate", "Dificuldade de encontro, orçamento de XP e ajustes (somente o que existe na fonte)."),
    ("L43", 6, "Grafo de referências", "Validar todos os refs entre entradas."),
    ("L44", 6, "Manifest global", "Índice completo por sistema, tipo, nome, facetas, tier e arquivo."),
    ("L45", 6, "Testes de comportamento", "Cenários de combate, magia, descanso, nível, recursos, condições."),
    ("L46", 6, "Auditoria final", "Comparar inventário esperado e entradas geradas; lacunas, duplicatas e pendências."),
]
PHASES = {0: "Fundações", 1: "Regras compartilhadas", 2: "Catálogos de personagem", 3: "Magias",
          4: "Equipamentos e itens", 5: "Criaturas e encontros", 6: "Integração e auditoria"}

BESTIARY = [("ABC", "L33"), ("DEF", "L34"), ("GHI", "L35"), ("JKL", "L36"),
            ("MNO", "L37"), ("PQR", "L38"), ("ST", "L39"), ("UVWXYZ", "L40")]
SPELL_LOT = {lvl: f"L{17 + lvl}" for lvl in range(10)}

# Section ownership. Key = heading path prefix (chapter / level-2 / level-3 ...); the longest
# matching prefix wins. Every heading must resolve to exactly one lot.
SECTION_LOTS = {
    "Legal Information": "L00",
    "Contents": "L00",
    "Index of Stat Blocks": "L00",
    "Playing the Game": "L02",
    "Playing the Game/Rhythm of Play": "L02",
    "Playing the Game/The Six Abilities": "L02",
    "Playing the Game/D20 Tests": "L05",
    "Playing the Game/Proficiency": "L05",
    "Playing the Game/Actions": "L04",
    "Playing the Game/Social Interaction": "L05",
    "Playing the Game/Exploration": "L41",
    "Playing the Game/Combat": "L04",
    "Playing the Game/Damage and Healing": "L06",
    "Character Creation": "L02",
    "Character Creation/Multiclassing": "L16",
    "Character Creation/Trinkets": "L30",
    "Classes": "L12",
    "Character Origins": "L10",
    "Character Origins/Character Backgrounds": "L11",
    "Feats": "L15",
    "Equipment": "L08",
    "Equipment/Weapons": "L28",
    "Equipment/Armor": "L29",
    "Equipment/Tools": "L30",
    "Equipment/Adventuring Gear": "L30",
    "Equipment/Mounts and Vehicles": "L30",
    "Equipment/Lifestyle Expenses": "L30",
    "Equipment/Food, Drink, and Lodging": "L30",
    "Equipment/Hirelings": "L30",
    "Equipment/Spellcasting": "L30",
    "Equipment/Magic Items": "L31",
    "Equipment/Brewing Potions of Healing": "L32",
    "Equipment/Scribing Spell Scrolls": "L32",
    "Spells": "L09",
    "Rules Glossary": "L02",
    "Gameplay Toolbox": "L41",
    "Gameplay Toolbox/Creating a Background": "L11",
    "Gameplay Toolbox/Poison": "L32",
    "Gameplay Toolbox/Combat Encounters": "L42",
    "Magic Items": "L31",
    "Monsters": "L33",
    "Monsters A–Z": "L33",   # overridden per creature by initial letter
    "Animals": "L33",        # idem
}

# Glossary terms without a bracket tag, assigned to the lot whose rules they define.
GLOSSARY_LOTS = {
    "L02": ["Ability Score and Modifier", "Adventure", "Alignment", "Ally", "Campaign", "Character Sheet",
            "Creature", "Creature Type", "Enemy", "Experience Points", "Monster", "Nonplayer Character",
            "Object", "Player Character", "Round Down", "Simultaneous Effects", "Size", "Speed",
            "Stat Block", "Per Day", "Possession", "Shape-Shifting", "Telepathy", "Teleportation",
            "Illusions", "Magical Effect", "Challenge Rating"],
    "L03": ["Condition"],
    "L04": ["Action", "Attack Roll", "Bonus Action", "Critical Hit", "Initiative", "Opportunity Attacks",
            "Reach", "Reaction", "Surprise", "Unarmed Strike", "Weapon Attack", "Cover", "Grappling",
            "Improvised Weapons", "Occupied Space", "Unoccupied Space", "Difficult Terrain", "Climbing",
            "Crawling", "Flying", "Fly Speed", "Hover", "Swimming", "Swim Speed", "Climb Speed",
            "Burrow Speed", "Jumping", "High Jump", "Long Jump", "Knocking Out a Creature", "Target",
            "Breaking Objects"],
    "L05": ["Ability Check", "Advantage", "Disadvantage", "D20 Test", "Difficulty Class", "Expertise",
            "Heroic Inspiration", "Passive Perception", "Proficiency", "Save", "Saving Throw", "Skill",
            "Attitude"],
    "L06": ["Bloodied", "Damage", "Damage Roll", "Damage Threshold", "Damage Types", "Dead",
            "Death Saving Throw", "Healing", "Hit Points", "Immunity", "Resistance", "Stable",
            "Temporary Hit Points", "Vulnerability", "Hazard"],
    "L07": ["Hit Point Dice", "Long Rest", "Short Rest"],
    "L08": ["Armor Class", "Armor Training", "Carrying Capacity", "Weapon", "Attunement"],
    "L09": ["Area of Effect", "Cantrip", "Concentration", "Ritual", "Spell", "Spell Attack",
            "Spellcasting Focus"],
    "L41": ["Blindsight", "Bright Light", "Darkness", "Darkvision", "Dim Light", "Heavily Obscured",
            "Lightly Obscured", "Tremorsense", "Truesight", "Curses", "Encounter"],
}
GLOSSARY_TAG = {  # bracket tag -> (kind, lot)
    "Condition": ("condition", "L03"),
    "Action": ("action", "L04"),
    "Area of Effect": ("area", "L09"),
    "Hazard": ("hazard", "L06"),
    "Attitude": ("attitude", "L05"),
}

# Level-5 sidebars that hold rules (not table captions, not stat-block sections).
SIDEBAR_LOTS = {
    "Exceptions Supersede General Rules": "L02",
    "Round Down": "L02",
    "Heroic Inspiration": "L05",
    "Marching Order": "L41",
    "Playing on a Grid": "L04",
    "Unseen Attackers and Targets": "L04",
    "Resting": "L07",
    "Knocking Out a Creature": "L04",
    "Unaligned Creatures": "L02",
    "Bonus Feats at Level 20": "L15",
    "Breaking Your Oath": "L12",
    "Expanding and Replacing a Spellbook": "L12",
    "Selling Equipment": "L08",
    "Improvised Weapons": "L28",
    "Casting in Armor": "L09",
    "Identifying an Ongoing Spell": "L09",
    "Magic Item Rules": "L31",
    "Running a Monster": "L33",
}
# Tables the PDF's column flow prints inside another section, with the lot that owns them.
RELOCATED_TABLES = {
    "Skills": "L05",                                 # printed inside "Actions" (p. 9)
    "Starting Equipment at Higher Levels": "L02",    # printed inside "Multiclassing" (p. 24)
    "Travel Terrain": "L41",                         # printed inside "Creating a Background" (p. 192)
}
# paragraphs the PDF's column flow printed inside another section: (page, text prefix) -> owner
RELOCATED_FRAGMENTS = [
    {"page": 131, "prefix": "face a choice of paths along the way there", "printed_in": "Find Steed",
     "belongs_to": "Find the Path", "after": "Whenever you", "lot": "L23"},  # end of Find the Path (p. 132)
    # pp. 108-110: the ends of Antilife Shell and Antipathy/Sympathy were printed inside the
    # neighbouring spells
    {"page": 109, "prefix": "or make attacks with Ranged or Reach weapons", "printed_in": "Animate Objects",
     "belongs_to": "Antilife Shell", "after": "An affected creature can cast spells", "lot": "L22"},
    {"page": 109, "prefix": "If you move so that an affected creature is forced", "printed_in": "Animate Objects",
     "belongs_to": "Antilife Shell", "after": "through the barrier.", "lot": "L22"},
    {"page": 110, "prefix": "Wisdom saving throw to end the effect, as described below.", "printed_in": "Antilife Shell",
     "belongs_to": "Antipathy/Sympathy", "after": "that creature can make a", "lot": "L25"},
    {"page": 110, "prefix": "***Ending the Effect.*** If the Frightened or Charmed", "printed_in": "Antilife Shell",
     "belongs_to": "Antipathy/Sympathy", "after": "as described below.", "lot": "L25"},
]
# defects in the source text itself (also present in the raw page text): kept verbatim, flagged
TEXT_DEFECTS = [
    {"subject": "Telekinesis", "ref": "dnd5e/spell/telekinesis", "lot": "L22", "type": "truncated_text",
     "detail": "the last sentence stops mid-phrase: 'such as manipulating a simple tool,' (p. 168)",
     "resolution": "kept verbatim; the open-ended fine control is a master decision", "pages": [168]},
]
STAT_BLOCK_SECTIONS = {"Traits", "Actions", "Bonus Actions", "Reactions", "Legendary Actions"}

SIZES = ["Tiny", "Small", "Medium", "Large", "Huge", "Gargantuan"]
RARITIES = ["Common", "Uncommon", "Rare", "Very Rare", "Legendary", "Artifact"]
ITEM_CATEGORIES = ["Armor", "Potion", "Ring", "Rod", "Scroll", "Staff", "Wand", "Weapon", "Wondrous Item"]
SCHOOLS = ["Abjuration", "Conjuration", "Divination", "Enchantment", "Evocation", "Illusion",
           "Necromancy", "Transmutation"]


# ---------------------------------------------------------------- helpers

class Builder:
    def __init__(self, nodes):
        self.nodes = nodes
        self.entries = []
        self.refs = collections.Counter()
        self.memberships = []
        self.lot_by_node = {}

    def add(self, kind, name, node, lot, slug=None, **facets):
        slug = slug or slugify(name)
        ref = f"{SYSTEM}/{kind}/{slug}"
        self.refs[ref] += 1
        e = {"ref": ref, "kind": kind, "name": name, "page": node.page, "lot": lot}
        facets = {k: v for k, v in facets.items() if v not in (None, "", [], {})}
        if facets:
            e["facets"] = facets
        self.entries.append(e)
        self.lot_by_node.setdefault(node.index, lot)
        return e

    def section(self, title, level, start=0, stop=None):
        """Return (heading_index, end_index) of the first heading matching title at level."""
        nodes = self.nodes
        for i in range(start, stop if stop is not None else len(nodes)):
            n = nodes[i]
            if n.type == "h" and n.level == level and n.text == title:
                j = i + 1
                while j < len(nodes) and not (nodes[j].type == "h" and nodes[j].level <= level):
                    j += 1
                return i, j
        raise KeyError(f"section not found: {'#' * level} {title}")

    def children(self, start, end, level):
        """Headings at `level` inside [start, end): list of (index, child_end)."""
        out = []
        idx = [i for i in range(start + 1, end) if self.nodes[i].type == "h" and self.nodes[i].level == level]
        for k, i in enumerate(idx):
            j = i + 1
            while j < end and not (self.nodes[j].type == "h" and self.nodes[j].level <= level):
                j += 1
            out.append((i, j))
        return out

    def first_para(self, i, end):
        for j in range(i + 1, end):
            if self.nodes[j].type == "p":
                return self.nodes[j]
            if self.nodes[j].type == "h" and self.nodes[j].level <= 4:
                return None
        return None


def paren_cost(name):
    m = re.match(r"^(.*?) \((.*)\)$", name)
    return (m.group(1), m.group(2)) if m else (name, None)


# ---------------------------------------------------------------- outline

EMBEDDED_IN = ("Spell Descriptions", "Magic Items A–Z")


def build_outline(nodes):
    heads = [n for n in nodes if n.type == "h" and n.level <= 4]
    # effective level: a level-3 stat block printed inside a spell or magic item description
    # nests under that entry (level 5) instead of opening a new section
    levels, stack = [], []
    for h in heads:
        lvl = h.level
        if lvl == 3 and stack and stack[-1][0] == 4 and any(l == 2 and t in EMBEDDED_IN for l, t in stack):
            lvl = 5
        while stack and stack[-1][0] >= lvl:
            stack.pop()
        stack.append((lvl, h.text))
        levels.append(lvl)
    last_page = nodes[-1].page
    outline, stack = [], []
    for k, (h, lvl) in enumerate(zip(heads, levels)):
        while stack and stack[-1][0] >= lvl:
            stack.pop()
        path = "/".join([t for _, t in stack] + [h.text])
        nxt = next((x for x, l in zip(heads[k + 1:], levels[k + 1:]) if l <= lvl), None)
        outline.append({"level": lvl, "title": h.text, "path": path, "page_start": h.page,
                        "page_end": nxt.page if nxt else last_page, "lot": None, "_node": h.index})
        stack.append((lvl, h.text))
    return outline


def section_lot(path):
    parts = path.split("/")
    for n in range(len(parts), 0, -1):
        key = "/".join(parts[:n])
        if key in SECTION_LOTS:
            return SECTION_LOTS[key]
    return None


def bestiary_lot(name):
    first = name[0].upper()
    for letters, lot in BESTIARY:
        if first in letters:
            return lot
    raise ValueError(name)


# ---------------------------------------------------------------- catalogs

def classes(b):
    s, e = b.section("Classes", 1)
    class_names = []
    for ci, ce in b.children(s, e, 2):
        cname = b.nodes[ci].text
        class_names.append(cname)
        rows = {n.cells[0]: n.cells[1] for n in b.nodes[ci:ce] if n.type == "t" and len(n.cells) == 2}
        hit_die = re.search(r"D(\d+)", rows.get("Hit Point Die", ""))
        b.add("class", cname, b.nodes[ci], "L12",
              primary_ability=rows.get("Primary Ability"),
              hit_die=f"d{hit_die.group(1)}" if hit_die else None)
        sub = None
        for i in range(ci + 1, ce):
            n = b.nodes[i]
            if n.type != "h":
                continue
            m = re.match(rf"^{cname} Subclass: (.+)$", n.text)
            if n.level == 3 and m:
                sub = m.group(1)
                b.add("subclass", sub, n, "L13", slug=slugify(sub), **{"class": f"{SYSTEM}/class/{slugify(cname)}"})
                continue
            if n.level == 3 and n.text in ("Metamagic Options", "Eldritch Invocation Options"):
                kind = "metamagic" if n.text.startswith("Metamagic") else "invocation"
                _, oe = b.section(n.text, 3, i)
                for oi, _ in b.children(i, oe, 4):
                    o = b.nodes[oi]
                    b.add("feature", o.text, o, "L14", slug=f"{slugify(cname)}-{kind}-{slugify(o.text)}",
                          feature_type="metamagic_option" if kind == "metamagic" else "eldritch_invocation",
                          owner=f"{SYSTEM}/class/{slugify(cname)}")
                continue
            if n.level == 3 and n.text.endswith("Spell List"):
                sub = sub  # spell lists handled in spell_lists()
            fm = re.match(r"^Level (\d+): (.+)$", n.text)
            if n.level == 4 and fm:
                lvl, fname = int(fm.group(1)), fm.group(2)
                owner = f"{SYSTEM}/subclass/{slugify(sub)}" if sub else f"{SYSTEM}/class/{slugify(cname)}"
                prefix = slugify(sub) if sub else slugify(cname)
                b.add("feature", fname, n, "L14", slug=f"{prefix}-{slugify(fname)}",
                      feature_type="subclass_feature" if sub else "class_feature",
                      owner=owner, level=lvl)
    # same feature heading repeated at several levels (e.g. Improved Brutal Strike 13/17):
    # disambiguate every member of the collision with its level
    feats = [x for x in b.entries if x["kind"] == "feature" and "level" in x.get("facets", {})]
    dup = collections.Counter(x["ref"] for x in feats)
    for x in feats:
        if dup[x["ref"]] > 1:
            b.refs[x["ref"]] -= 1
            x["ref"] = f"{x['ref']}-level-{x['facets']['level']}"
            b.refs[x["ref"]] += 1
    return class_names


def spell_lists(b, class_names):
    s, e = b.section("Classes", 1)
    for cname in class_names:
        try:
            li, le = b.section(f"{cname} Spell List", 3, s, e)
        except KeyError:
            continue
        b.add("spell-list", f"{cname} Spell List", b.nodes[li], "L27", slug=slugify(cname),
              **{"class": f"{SYSTEM}/class/{slugify(cname)}"})
        level = None
        for n in b.nodes[li:le]:
            if n.type == "h" and n.level == 5:
                m = re.match(r"^(?:Cantrips \(Level 0|Level (\d+)) ", n.text)
                level = int(m.group(1) or 0) if m else None
            elif n.type == "t" and level is not None and n.cells[0] != "Spell":
                b.memberships.append({"list": f"{SYSTEM}/spell-list/{slugify(cname)}", "spell": n.cells[0],
                                      "spell_ref": f"{SYSTEM}/spell/{slugify(n.cells[0])}", "level": level,
                                      "school": n.cells[1] if len(n.cells) > 1 else None,
                                      "special": n.cells[2] if len(n.cells) > 2 else None, "page": n.page})
    # subclass / feature spell tables (always-prepared lists)
    for i, n in enumerate(b.nodes):
        if n.type == "h" and n.level == 5 and n.page < 83 and (
                n.text.endswith(" Spells") and not re.match(r"^(Cantrips|Level \d)", n.text)
                or n.text in ("Arid Land", "Polar Land", "Temperate Land", "Tropical Land")):
            list_name = n.text if n.text.endswith("Spells") else f"Circle of the Land Spells ({n.text})"
            slug = slugify(list_name)
            b.add("spell-list", list_name, n, "L27", slug=slug, list_type="subclass")
            for t in b.nodes[i + 1:]:
                if t.type == "h":
                    break
                if t.type == "t" and re.match(r"^\d+$", t.cells[0]):
                    for sp in re.split(r",\s*", t.cells[1]):
                        b.memberships.append({"list": f"{SYSTEM}/spell-list/{slug}", "spell": sp,
                                              "spell_ref": f"{SYSTEM}/spell/{slugify(sp)}",
                                              "unlocked_at_level": int(t.cells[0]), "page": t.page})


def origins(b):
    s, e = b.section("Character Origins", 1)
    bi, be = b.section("Background Descriptions", 3, s, e)
    for i, _ in b.children(bi, be, 4):
        b.add("background", b.nodes[i].text, b.nodes[i], "L11")
    si, se = b.section("Species Descriptions", 3, s, e)
    for i, ie in b.children(si, se, 4):
        sp = b.nodes[i]
        fields = {}
        for k in range(i, ie):
            n = b.nodes[k]
            m = re.match(r"^\*\*(Creature Type|Size|Speed):\*\* (.+)$", n.text) if n.type == "p" else None
            if m:
                value = strip_md(m.group(2))
                if value.count("(") > value.count(")"):  # value continues in the next paragraph
                    value += " " + strip_md(b.nodes[k + 1].text)
                fields[m.group(1)] = value
        b.add("species", sp.text, sp, "L10", creature_type=fields.get("Creature Type"),
              size=fields.get("Size"), speed=fields.get("Speed"))
        for n in b.nodes[i:ie]:
            m = re.match(r"^\*\*\*(.+?)\.\*\*\*", n.text) if n.type == "p" else None
            if m:
                b.add("feature", m.group(1), n, "L14", slug=f"{slugify(sp.text)}-{slugify(m.group(1))}",
                      feature_type="species_trait", owner=f"{SYSTEM}/species/{slugify(sp.text)}")


def feats(b):
    s, e = b.section("Feats", 1)
    for ci, ce in b.children(s, e, 3):
        cat = b.nodes[ci].text
        if not cat.endswith("Feats"):
            continue
        for i, ie in b.children(ci, ce, 4):
            line = b.first_para(i, ie)
            label = strip_md(line.text) if line else ""
            prereq = re.search(r"\(Prerequisite: (.+)\)", label)
            b.add("feat", b.nodes[i].text, b.nodes[i], "L15", category=cat[:-len(" Feats")],
                  prerequisite=prereq.group(1) if prereq else None)


def equipment(b):
    s, e = b.section("Equipment", 1)
    pi, pe = b.section("Properties", 3, s, e)
    for i, _ in b.children(pi, pe, 4):
        b.add("weapon-property", b.nodes[i].text, b.nodes[i], "L28")
    mi, me = b.section("Mastery Properties", 3, s, e)
    for i, _ in b.children(mi, me, 4):
        b.add("weapon-mastery", b.nodes[i].text, b.nodes[i], "L28")

    def table_rows(caption, first_cell_header, continued_after=None):
        """Rows of a captioned table. `continued_after`: caption of the table after which the
        PDF's column flow prints the remainder of this one (same header, no caption)."""
        i, _ = b.section(caption, 5, s, e)
        group = None
        nodes = list(b.nodes[i + 1:])
        if continued_after:
            j, _ = b.section(continued_after, 5, s, e)
            rest = b.nodes[j + 1:]
            k = next(x for x, n in enumerate(rest) if n.type == "t" and n.cells[0] == first_cell_header)
            stop = next(x for x, n in enumerate(nodes) if n.type == "h" and n.level <= 5)
            nodes = nodes[:stop] + rest[k:]
        for n in nodes:
            if n.type == "h" and n.level <= 5:
                break
            if n.type == "p" and re.match(r"^\*[^*].*\*$", n.text):
                group = strip_md(n.text)
            elif n.type == "t" and n.cells[0] != first_cell_header:
                if n.text.startswith("| **"):
                    break  # header row of a different table that follows without a caption
                # a group label applies only to the rows printed indented beneath it; it carries
                # over to indented rows at the top of the next table half
                yield n, group if n.indented else None
            elif n.type == "t" and n.cells[0] == first_cell_header:
                continue

    for n, group in table_rows("Weapons", "Name"):
        if len(n.cells) == 6 and re.match(r"^\d+d\d+|^1 ", n.cells[1]):
            b.add("weapon", n.cells[0], n, "L28", category=group, damage=n.cells[1], properties=n.cells[2],
                  mastery=n.cells[3], weight=n.cells[4], cost=n.cells[5])
        elif len(n.cells) >= 3 and re.match(r"^\d+d\d+", n.cells[1]):
            b.add("weapon", n.cells[0], n, "L28", category=group, damage=n.cells[1], properties=n.cells[2],
                  note="row wraps in the PDF; remaining cells on the next line")
    for n, group in table_rows("Armor", "Armor"):
        b.add("armor", n.cells[0], n, "L29", category=group, armor_class=n.cells[1], strength=n.cells[2],
              stealth=n.cells[3], weight=n.cells[4], cost=n.cells[5])

    for parent in ("Artisan’s Tools", "Other Tools"):
        ti, te = b.section(parent, 3, s, e)
        for i, _ in b.children(ti, te, 4):
            name, cost = paren_cost(b.nodes[i].text)
            b.add("tool", name, b.nodes[i], "L30", category=parent, cost=cost)
    gi, ge = b.section("Adventuring Gear", 2, s, e)
    for i, _ in b.children(gi, ge, 4):
        name, cost = paren_cost(b.nodes[i].text)
        b.add("gear", name, b.nodes[i], "L30", cost=cost)
    for caption, header, kind, parent in (("Ammunition", "Type", "gear", "Ammunition"),
                                          ("Arcane Focuses", "Focus", "gear", "Arcane Focus"),
                                          ("Druidic Focuses", "Focus", "gear", "Druidic Focus"),
                                          ("Holy Symbols", "Focus", "gear", "Holy Symbol")):
        for n, _ in table_rows(caption, header):
            b.add(kind, f"{parent}: {n.cells[0]}", n, "L30", slug=f"{slugify(parent)}-{slugify(n.cells[0])}",
                  variant_of=f"{SYSTEM}/gear/{slugify(parent)}", columns=n.cells[1:])
    for n, _ in table_rows("Mounts and Other Animals", "Item"):
        b.add("mount", n.cells[0], n, "L30", carrying_capacity=n.cells[1], cost=n.cells[2])
    for n, group in table_rows("Tack, Harness, and Drawn Vehicles", "Item"):
        name = f"{group}, {n.cells[0]}" if group else n.cells[0]
        b.add("vehicle" if n.cells[0] in ("Carriage", "Cart", "Chariot", "Sled", "Wagon") else
              "service" if n.cells[0] == "Stabling per day" else "gear",
              name, n, "L30", weight=n.cells[1], cost=n.cells[2], table="Tack, Harness, and Drawn Vehicles")
    for n, _ in table_rows("Airborne and Waterborne Vehicles", "Ship"):
        b.add("vehicle", n.cells[0], n, "L30", speed=n.cells[1], crew=n.cells[2], passengers=n.cells[3],
              cargo_tons=n.cells[4], ac=n.cells[5], hp=n.cells[6], damage_threshold=n.cells[7], cost=n.cells[8])
    li, le = b.section("Lifestyle Expenses", 2, s, e)
    for i, _ in b.children(li, le, 3):
        name, cost = paren_cost(b.nodes[i].text)
        b.add("lifestyle", name, b.nodes[i], "L30", cost=cost)
    for n, group in table_rows("Food, Drink, and Lodging", "Item", continued_after="Airborne and Waterborne Vehicles"):
        name = f"{group}: {n.cells[0]}" if group else n.cells[0]
        b.add("service", name, n, "L30", cost=n.cells[1], table="Food, Drink, and Lodging")
    for n, _ in table_rows("Hirelings", "Service"):
        b.add("service", n.cells[0], n, "L30", cost=n.cells[1], table="Hirelings")
    for n, _ in table_rows("Spellcasting Services", "Spell Level"):
        b.add("service", f"Spellcasting: {n.cells[0]}", n, "L30", slug=f"spellcasting-{slugify(n.cells[0])}",
              availability=n.cells[1], cost=n.cells[2], table="Spellcasting Services")


SPELL_HEAD = re.compile(r"^(?:Level (\d) (\w+)|(\w+) Cantrip) \((.+)\)$")


def spells(b):
    s, e = b.section("Spell Descriptions", 2)
    for i, ie in b.children(s, e, 4):
        n = b.nodes[i]
        line = b.first_para(i, ie)
        m = SPELL_HEAD.match(strip_md(line.text)) if line else None
        if not m:
            raise ValueError(f"spell header not parsed: {n.text} p{n.page}")
        level = int(m.group(1)) if m.group(1) else 0
        school = m.group(2) or m.group(3)
        assert school in SCHOOLS, (n.text, school)
        b.add("spell", n.text, n, SPELL_LOT[level], level=level, school=school,
              classes=[c.strip() for c in m.group(4).split(",")])


def glossary(b):
    s, e = b.section("Rules Definitions", 2)
    untagged = {t: lot for lot, terms in GLOSSARY_LOTS.items() for t in terms}
    for i, _ in b.children(s, e, 4):
        n = b.nodes[i]
        m = re.match(r"^(.+?) \[(.+)\]$", n.text)
        if m:
            kind, lot = GLOSSARY_TAG[m.group(2)]
            b.add(kind, m.group(1), n, lot, glossary_tag=m.group(2))
        else:
            if n.text not in untagged:
                raise KeyError(f"glossary term without lot: {n.text}")
            b.add("rule", n.text, n, untagged[n.text], glossary=True)


def toolbox(b):
    s, e = b.section("Gameplay Toolbox", 1)
    ci, ce = b.section("Curses", 3, s, e)
    for i, _ in b.children(ci, ce, 4):
        b.add("curse", b.nodes[i].text, b.nodes[i], "L41")
    xi, xe = b.section("Example Contagions", 4, s, e)
    for i, _ in b.children(xi, b.section("Environmental Effects", 2, s, e)[0], 4):
        b.add("contagion", b.nodes[i].text, b.nodes[i], "L41")
    ei, ee = b.section("Environmental Effects", 2, s, e)
    for i, _ in b.children(ei, ee, 3):
        b.add("environment", b.nodes[i].text, b.nodes[i], "L41")
    pi, pe = b.section("Sample Poisons", 3, s, e)
    for i, ie in b.children(pi, pe, 4):
        name, cost = paren_cost(b.nodes[i].text)
        line = b.first_para(i, ie)
        b.add("poison", name, b.nodes[i], "L32", cost=cost, poison_type=strip_md(line.text) if line else None)
    ti, te = b.section("Example Traps", 3, s, e)
    for i, _ in b.children(ti, te, 4):
        b.add("trap", b.nodes[i].text, b.nodes[i], "L41")


def magic_items(b):
    s, e = b.section("Magic Items A–Z", 2)
    for i, ie in b.children(s, e, 4):
        n = b.nodes[i]
        line = b.first_para(i, ie)
        label = strip_md(line.text) if line else ""
        category = next((c for c in ITEM_CATEGORIES if label.startswith(c)), None)
        if category is None:
            raise ValueError(f"magic item category not parsed: {n.text}: {label}")
        rarities = [r for r in RARITIES if re.search(rf"\b{r}\b", label)]
        if "Rarity Varies" in label:
            rarities.append("Varies")
        if "Very Rare" in rarities and not re.search(r"(?<!Very )\bRare\b", label):
            rarities.remove("Rare")
        att = re.search(r"\((Requires Attunement[^)]*)\)", label)
        lot = "L32" if category in ("Potion", "Scroll") else "L31"
        b.add("magic-item", n.text, n, lot, category=category, rarity=rarities, type_line=label,
              attunement=att.group(1) if att else None)


STAT_HEAD = re.compile(r"^(.+?) (Aberration|Beast|Celestial|Construct|Dragon|Elemental|Fey|Fiend|Giant|"
                       r"Humanoid|Monstrosity|Ooze|Plant|Undead)(?: \((.+?)\))?, (.+)$")


def parse_stat_head(text):
    head = strip_md(text)
    swarm = re.match(r"^(\w+) Swarm of (\w+) (\w+?)s?, (.+)$", head)
    if swarm:  # "Large Swarm of Tiny Beasts, Unaligned"
        head = f"{swarm.group(1)} {swarm.group(3)} (Swarm of {swarm.group(2)}), {swarm.group(4)}"
    return STAT_HEAD.match(head)


def embedded_creatures(b):
    """Stat blocks printed inside a spell or magic item description (summons, figurines...)."""
    for section, kind in (("Spell Descriptions", "spell"), ("Magic Items A–Z", "magic-item")):
        s, e = b.section(section, 2)
        for i, ie in b.children(s, e, 3):
            n = b.nodes[i]
            # the owner is the entry whose text cites the stat block in bold (e.g. "uses the
            # **Otherworldly Steed** stat block"); the PDF's column layout can print the block
            # after a different entry, so position alone is not reliable
            cite = re.compile(rf"\*\*{re.escape(n.text)}s?\*\*")
            owner = None
            for k in range(s, e):
                if b.nodes[k].type == "h" and b.nodes[k].level == 4:
                    current = b.nodes[k]
                elif b.nodes[k].type == "p" and cite.search(b.nodes[k].text):
                    owner = current
                    break
            if owner is None:
                raise ValueError(f"no entry cites embedded stat block {n.text}")
            owner_entry = next(x for x in b.entries if x["kind"] == kind and x["name"] == owner.text)
            line = b.first_para(i, ie)
            m = parse_stat_head(line.text) if line else None
            if not m:
                raise ValueError(f"embedded stat block header not parsed: {n.text} p{n.page}")
            b.add("creature", n.text, n, owner_entry["lot"], group="embedded", embedded_in=owner_entry["ref"],
                  size=m.group(1), type=m.group(2), subtype=m.group(3), alignment=m.group(4))


def creatures(b):
    for chapter, group in (("Monsters A–Z", "monster"), ("Animals", "animal")):
        s, e = b.section(chapter, 1)
        for i, ie in b.children(s, e, 3):
            n = b.nodes[i]
            body = b.nodes[i:ie]
            if not any(x.type in ("p", "t") and "**AC**" in x.text for x in body):
                continue
            line = b.first_para(i, ie)
            m = parse_stat_head(line.text) if line else None
            if not m:
                raise ValueError(f"stat block header not parsed: {n.text} p{n.page}: {line and line.text}")
            cr = next((re.search(r"\*\*CR\*\* (\S+)", x.text) for x in body
                       if x.type in ("p", "t") and "**CR**" in x.text), None)
            # nearest level-2 group heading (e.g. "Black Dragons")
            grp = next((b.nodes[k].text for k in range(i - 1, s, -1)
                        if b.nodes[k].type == "h" and b.nodes[k].level == 2), None)
            b.add("creature", n.text, n, bestiary_lot(n.text), group=group,
                  size=m.group(1), type=m.group(2), subtype=m.group(3), alignment=m.group(4),
                  cr=cr.group(1) if cr else None, family=grp if grp and grp != n.text else None)


def spell_consistency(b):
    """Compare each spell's header (level, school, classes) with the class spell lists."""
    spells_by_ref = {x["ref"]: x for x in b.entries if x["kind"] == "spell"}
    on_lists = collections.defaultdict(dict)
    out = []
    for m in b.memberships:
        if "level" not in m:
            continue
        cls = m["list"].rsplit("/", 1)[1]
        on_lists[m["spell_ref"]][cls] = m
        sp = spells_by_ref[m["spell_ref"]]
        if m["school"] != sp["facets"]["school"]:
            out.append({"subject": sp["name"], "ref": sp["ref"], "lot": "L27", "type": "school_mismatch",
                        "resolution": "D-001: the description header is authoritative (school "
                                      f"{sp['facets']['school']})",
                        "detail": f"school '{sp['facets']['school']}' in the description (p. {sp['page']}) "
                                  f"but '{m['school']}' in the {cls.title()} spell list (p. {m['page']})",
                        "pages": [sp["page"], m["page"]]})
    for ref, sp in spells_by_ref.items():
        header = {c.lower() for c in sp["facets"]["classes"]}
        listed = set(on_lists[ref])
        for cls in sorted(header - listed):
            out.append({"subject": sp["name"], "ref": ref, "lot": "L27", "type": "class_not_on_list",
                        "resolution": f"D-001: enabled for {cls.title()} (the description header is authoritative)",
                        "detail": f"description header names {cls.title()} (p. {sp['page']}) but the spell "
                                  f"is absent from the {cls.title()} spell list",
                        "pages": [sp["page"]]})
        for cls in sorted(listed - header):
            out.append({"subject": sp["name"], "ref": ref, "lot": "L27", "type": "list_not_in_header",
                        "resolution": "D-001: the description header is authoritative; needs review",
                        "detail": f"listed on the {cls.title()} spell list (p. {on_lists[ref][cls]['page']}) "
                                  f"but not named in the description header (p. {sp['page']})",
                        "pages": [sp["page"], on_lists[ref][cls]["page"]]})
    return out


def build_sidebars(nodes):
    """Level-5 headings followed by prose: rule sidebars that need an owning lot."""
    out = []
    for i, n in enumerate(nodes):
        if n.type != "h" or n.level != 5 or n.text in STAT_BLOCK_SECTIONS:
            continue
        follow = [m for m in nodes[i + 1:i + 3]]
        if not follow or follow[0].type != "p" or re.match(r"^\*[^*].*\*$|^\*\*[^*]+\*\*$", follow[0].text):
            continue  # table caption (followed by an italic group label or a bold header fragment)
        if n.text not in SIDEBAR_LOTS:
            raise KeyError(f"sidebar without lot: {n.text} p{n.page}")
        out.append({"title": n.text, "page": n.page, "lot": SIDEBAR_LOTS[n.text]})
    return out


# ---------------------------------------------------------------- tables

def build_tables(nodes, outline_lot):
    tables, k = [], 0
    while k < len(nodes):
        if nodes[k].type != "t":
            k += 1
            continue
        start = k
        rows = []
        # a table continues across italic group labels, bold stray header labels and page breaks
        while k < len(nodes) and (nodes[k].type == "t" or (
                nodes[k].type == "p" and re.match(r"^\*[^*].*\*$|^\*\*[^*]+\*\*$", nodes[k].text)
                and k + 1 < len(nodes) and nodes[k + 1].type == "t")):
            if nodes[k].type == "t":
                rows.append(nodes[k])
            k += 1
        cap = next((nodes[j] for j in range(start - 1, max(start - 4, -1), -1)
                    if nodes[j].type == "h"), None)
        header = rows[0].cells if all(c.startswith("**") for c in rows[0].text.strip("| ").split(" | ")) else None
        if rows[0].page >= 258 and any("MOD SAVE" in r.text or r.text.startswith("| **AC**") for r in rows):
            ttype = "stat_block"
        elif cap and cap.text == "Contents" or rows[0].page <= 4:
            ttype = "front_matter"
        else:
            ttype = "data"
        tables.append({"type": ttype, "caption": cap.text if cap and cap.level == 5 else None,
                       "context_heading": cap.text if cap else None,
                       "page_start": rows[0].page, "page_end": rows[-1].page,
                       "rows": len(rows), "header": header,
                       "lot": outline_lot(rows[0].index)})
    return tables


# ---------------------------------------------------------------- main

def main():
    nodes = load(MD)
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    b = Builder(nodes)

    outline = build_outline(nodes)
    for o in outline:
        o["lot"] = section_lot(o["path"])
        if o["path"].startswith(("Monsters A–Z/", "Animals/")) and o["level"] >= 2:
            o["lot"] = bestiary_lot(o["title"])
        if o["lot"] is None:
            raise KeyError(f"section without lot: {o['path']}")
    head_idx = [n.index for n in nodes if n.type == "h" and n.level <= 4]

    def lot_at(index):
        pos = max((k for k, hi in enumerate(head_idx) if hi <= index), default=0)
        return outline[pos]["lot"]

    names = classes(b)
    spell_lists(b, names)
    origins(b)
    feats(b)
    equipment(b)
    spells(b)
    glossary(b)
    toolbox(b)
    magic_items(b)
    creatures(b)
    embedded_creatures(b)
    tables = build_tables(nodes, lot_at)
    # a heading that introduces a catalog entry is owned by that entry's lot; its sub-headings follow
    owner_stack = []
    for o in outline:
        while owner_stack and owner_stack[-1][0] >= o["level"]:
            owner_stack.pop()
        if o["_node"] in b.lot_by_node:
            o["lot"] = b.lot_by_node[o["_node"]]
            owner_stack.append((o["level"], o["lot"]))
        elif owner_stack:
            o["lot"] = owner_stack[-1][1]
        del o["_node"]

    duplicates = sorted(r for r, c in b.refs.items() if c > 1)
    inconsistencies = spell_consistency(b) + TEXT_DEFECTS
    spell_refs = {x["ref"] for x in b.entries if x["kind"] == "spell"}
    unresolved = sorted({m["spell"] for m in b.memberships if m["spell_ref"] not in spell_refs})

    OUT.mkdir(parents=True, exist_ok=True)
    src = report["source"]
    source = {
        "system": SYSTEM, "source_id": "srd-5.2.1", "title": "System Reference Document 5.2.1",
        "publisher": "Wizards of the Coast LLC", "file": "source/SRD_CC_v5.2.1.pdf",
        "sha256": src["sha256"], "bytes": src["bytes"], "pages": src["pages"],
        "page_numbering": "PDF page index equals printed page number (verified on all pages)",
        "license": {"id": "CC-BY-4.0", "url": "https://creativecommons.org/licenses/by/4.0/legalcode",
                    "attribution": src["attribution"], "page": 1,
                    "notes": ["Do not include any other attribution to Wizards or its parent or affiliates.",
                              "A work may state it is “compatible with fifth edition” or “5E compatible.”"]},
        "extraction": {"markdown": "extraction/SRD_CC_v5.2.1.md",
                       "markdown_sha256": report["outputs"]["markdown_sha256"],
                       "report": "extraction/extraction_report.json"},
    }
    chapters = [o for o in outline if o["level"] == 1]
    counts_kind = collections.Counter(x["kind"] for x in b.entries)
    counts_lot = collections.Counter(x["lot"] for x in b.entries)
    lots = []
    for lot, phase, title, desc in LOTS:
        lots.append({"lot": lot, "phase": phase, "phase_name": PHASES[phase], "title": title,
                     "description": desc, "expected_entries": counts_lot.get(lot, 0),
                     "expected_by_kind": dict(sorted(collections.Counter(
                         x["kind"] for x in b.entries if x["lot"] == lot).items())),
                     "sections": [o["path"] for o in outline if o["lot"] == lot and o["level"] <= 3],
                     "sidebars": [x["title"] for x in build_sidebars(nodes) if x["lot"] == lot],
                     "tables": sum(1 for t in tables if t["lot"] == lot and t["type"] == "data")})
    if "L27" in counts_lot:
        next(x for x in lots if x["lot"] == "L27")["expected_memberships"] = len(b.memberships)

    def dump(name, data):
        (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    dump("source.json", source)
    sidebars = build_sidebars(nodes)
    dump("outline.json", {"chapters": [{"title": c["title"], "page_start": c["page_start"],
                                        "page_end": c["page_end"]} for c in chapters], "sections": outline,
                          "sidebars": sidebars,
                          "relocated_tables": [{"caption": c, "lot": l} for c, l in RELOCATED_TABLES.items()],
                          "relocated_fragments": RELOCATED_FRAGMENTS})
    dump("tables.json", {"count": len(tables),
                         "by_type": dict(collections.Counter(t["type"] for t in tables)), "tables": tables})
    dump("entries.json", {"count": len(b.entries), "by_kind": dict(sorted(counts_kind.items())),
                          "duplicate_refs": duplicates, "entries": b.entries,
                          "spell_list_memberships": b.memberships,
                          "spell_list_unresolved_names": unresolved,
                          "source_inconsistencies": inconsistencies})
    dump("lots.json", {"phases": PHASES, "lots": lots})

    lines = ["# Inventário da fonte — SRD 5.2.1 (L00)", "",
             "Gerado por `tools/inventory/build_inventory.py` a partir de `extraction/SRD_CC_v5.2.1.md`. "
             "Não editar à mão.", "",
             f"- Fonte: `{source['file']}` — SHA-256 `{source['sha256']}` — {source['pages']} páginas",
             f"- Licença: {source['license']['id']} (atribuição em `source.json`)",
             f"- Seções mapeadas (níveis 1–4): {len(outline)} — quadros laterais com regras: "
             f"{len(build_sidebars(nodes))} — tabelas: {len(tables)}",
             f"- Entradas esperadas: **{len(b.entries)}** — vínculos de listas de magia: {len(b.memberships)}",
             f"- Refs duplicados: {len(duplicates)} — nomes de magia em listas sem magia correspondente: "
             f"{len(unresolved)}", "", "## Capítulos", "", "| Capítulo | Páginas |", "|---|---|"]
    lines += [f"| {c['title']} | {c['page_start']}–{c['page_end']} |" for c in chapters]
    lines += ["", "## Entradas esperadas por tipo", "", "| Tipo (`kind`) | Quantidade |", "|---|---|"]
    lines += [f"| `{k}` | {v} |" for k, v in sorted(counts_kind.items())]
    lines += ["", "## Plano de lotes", "", "| Lote | Fase | Título | Entradas | Tabelas |", "|---|---|---|---|---|"]
    lines += [f"| {x['lot']} | {x['phase']} — {x['phase_name']} | {x['title']} | {x['expected_entries']} | {x['tables']} |"
              for x in lots]
    if inconsistencies:
        lines += ["", "## Inconsistências da própria fonte", "",
                  "Divergências internas do SRD, confirmadas no texto bruto das duas ferramentas. "
                  "Não são corrigidas aqui: o lote dono registra a divergência e, se preciso, uma "
                  "decisão do mestre (`master_decision`).", ""]
        lines += [f"- **{x['subject']}** ({x['lot']}): {x['detail']} → {x['resolution']}" for x in inconsistencies]
    if duplicates or unresolved:
        lines += ["", "## Pendências", ""]
        lines += [f"- Ref duplicado: `{r}`" for r in duplicates]
        lines += [f"- Lista de magia cita `{n}` sem descrição de magia com esse nome" for n in unresolved]
    (OUT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"entries": len(b.entries), "by_kind": dict(sorted(counts_kind.items())),
                      "tables": len(tables), "sections": len(outline), "memberships": len(b.memberships),
                      "duplicates": duplicates, "unresolved": unresolved}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
