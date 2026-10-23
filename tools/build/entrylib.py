"""Authoring helpers for lot builders (tools/build/lNN_*.py).

A lot builder never retypes source text: it selects a section of
extraction/SRD_CC_v5.2.1.md, and this module renders that section verbatim as the entry's
`text`. The author supplies only structure (facets, data, effects, master decisions) and a
coverage plan: a list of (anchor, status, by) where each anchor is the exact text a
segment starts with. The module cuts `text` at the anchors, so the coverage always
reproduces the text exactly, and fails loudly if an anchor is missing or out of order.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "inventory"))
from srdmd import load, slugify, strip_md  # noqa: E402,F401

MD_PATH = ROOT / "extraction" / "SRD_CC_v5.2.1.md"
KNOWLEDGE = ROOT / "knowledge"
NODES = load(MD_PATH)

SYSTEM = "dnd5e"
DOCUMENT = "srd-5.2.1"
ATTRIBUTION = ("This work includes material from the System Reference Document 5.2.1 (“SRD 5.2.1”) by "
               "Wizards of the Coast LLC, available at https://www.dndbeyond.com/srd. The SRD 5.2.1 is licensed "
               "under the Creative Commons Attribution 4.0 International License, available at "
               "https://creativecommons.org/licenses/by/4.0/legalcode.")

REF_RE = re.compile(r"^(?:[a-z0-9]+|custom/[A-Za-z0-9_-]+)/[a-z0-9-]+/[a-z0-9]+(?:-[a-z0-9]+)*$")


# ---------------------------------------------------------------- locating source text

def find(title, level, page=None, after=0):
    """Index of the heading `title` at `level` (optionally on `page`)."""
    for i in range(after, len(NODES)):
        n = NODES[i]
        if n.type == "h" and n.level == level and n.text == title and (page is None or n.page == page):
            return i
    raise KeyError(f"heading not found: {'#' * level} {title} (page {page})")


def section(title, level, page=None, include_heading=False, stop_titles=(), skip_tables=(), extra=(),
            keep_sidebars=False):
    """Nodes of a section: from the heading to the next heading of the same or higher level.

    Sidebars printed inside the section are excluded (they are entries of their own) unless
    `keep_sidebars`. `stop_titles`: also stop at a deeper heading with one of these titles.
    `skip_tables`: captions of tables that the PDF's column flow placed here but that belong
    to another section. `extra`: nodes appended at the end (e.g. such a table, given to the
    section it belongs to).
    """
    i = find(title, level, page)
    j = i + 1
    while j < len(NODES) and not (NODES[j].type == "h" and not NODES[j].sidebar
                                  and (NODES[j].level <= level or NODES[j].text in stop_titles)):
        j += 1
    nodes = [n for n in NODES[i if include_heading else i + 1:j] if keep_sidebars or not n.sidebar]
    return drop_tables(nodes, skip_tables) + list(extra)


def table_nodes(caption, page=None):
    """A level-5 caption with its table rows (and italic group labels)."""
    i = find(caption, 5, page)
    out = [NODES[i]]
    for k, n in enumerate(NODES[i + 1:], i + 1):
        if n.type == "t" or (n.type == "p" and re.match(r"^\*[^*].*\*$", n.text)):
            out.append(n)
        elif (n.type == "p" and re.match(r"^\*\*[^*]{1,40}\*\*$", n.text) and k + 1 < len(NODES)
              and NODES[k + 1].type == "t"):  # header fragment split from its table
            out.append(n)
        else:
            break
    return out


def nodes_between(start_title, start_level, end_title, end_level, page=None):
    i = find(start_title, start_level, page)
    j = find(end_title, end_level, None, i + 1)
    return NODES[i:j]


def sidebar(title, page=None):
    """Nodes of a boxed sidebar (its heading excluded)."""
    i = find(title, 5, page)
    out = []
    for n in NODES[i + 1:]:
        if not n.sidebar:
            break
        out.append(n)
    return out


def drop_tables(nodes, captions):
    if not captions:
        return list(nodes)
    out, k = [], 0
    while k < len(nodes):
        n = nodes[k]
        if n.type == "h" and n.level == 5 and n.text in captions:
            k += 1
            while k < len(nodes) and (nodes[k].type == "t" or (
                    nodes[k].type == "p" and re.match(r"^\*[^*].*\*$", nodes[k].text))):
                k += 1
            continue
        out.append(n)
        k += 1
    return out


TERMINAL = re.compile(r"[.:!?)\]”*|]$")


def render(nodes, heading_offset=None):
    """Render nodes back to markdown text.

    Paragraphs are separated by a blank line; consecutive table rows by a newline.
    A paragraph cut by a page break, a sidebar or a misplaced table is rejoined: it has no
    closing punctuation and the next paragraph starts in lowercase, or the two are separated
    in the source by a page change or removed nodes. Headings are kept, re-levelled relative
    to `heading_offset`.
    """
    parts = []
    prev_node = None
    for n in nodes:
        if n.type == "h":
            lvl = n.level if heading_offset is None else max(1, n.level - heading_offset)
            parts.append(("h", "#" * lvl + " " + n.text))
        elif n.type == "t":
            parts.append(("t", n.text))
        else:
            text = n.text
            cut = prev_node is not None and (n.index != prev_node.index + 1 or n.page != prev_node.page)
            last = parts[-1][1].rstrip() if parts and parts[-1][0] == "p" else ""
            # a labelled paragraph ("**Strength.** If the table shows ... in the") whose line wrap
            # the extractor took for a paragraph break: the next line goes on mid-phrase
            label_wrap = (re.match(r"^\*\*[^*]+\*\*", last) and not last.startswith("**Duration:**")
                          and re.match(r"^[A-Z][a-z]*\b(?!\.)", text)
                          and (re.search(r"[,(]$", last) or re.search(r"\s([A-Z][a-z]+|\d+)$", last)
                               or (re.search(r"category:$", last) and re.match(r"^[A-Z][a-z]+, ", text))
                               or (re.search(r"\s[a-z]+$", last) and re.match(r"^\d+ [a-z]", text))
                               or re.search(r"\s(a|an|the|of|in|by|to|and|or|either|with|for|on|at|as|your|its|have)$", last)))
            # any paragraph that stops on a function word ("... equal to your" / "Charisma modifier")
            word_wrap = ((re.search(r"\s(a|an|the|of|in|by|to|and|or|with|for|on|at|as|your|its|their)$", last)
                          and re.match(r"^([A-Z][a-z]|\d)", text))
                         or (re.search(r"\s\d+d\d+$", last) and re.match(r"^[A-Z][a-z]+ damage", text))  # "14d6" / "Necrotic damage"
                         or (last.startswith("- ") and re.match(r"^\d+\+? [a-z]", text)))  # list item cut before a number
            # a labelled header line cut inside a parenthesis or after "or" ("**Components:** V, S, M
            # (a miniature sword worth" / "250+ GP)", "**Casting Time:** Action (Overgrowth) or" / "8 hours")
            header_wrap = (re.match(r"^\*\*[^*]+:\*\*", last)
                           and (last.count("(") > last.count(")") or re.search(r"\sor$", last)))
            if parts and parts[-1][0] == "p" and (header_wrap or not TERMINAL.search(last)) and (
                    re.match(r"^[a-z(]", text) or label_wrap or word_wrap or header_wrap
                    or (cut and re.search(r"[a-z,;]$", last)
                        and not re.match(r"^\*\*(Casting Time|Range|Components?|Duration):\*\*", last))):
                parts[-1] = ("p", parts[-1][1].rstrip() + " " + text)
            else:
                parts.append(("p", text))
        prev_node = n
    out = []
    for k, (kind, text) in enumerate(parts):
        if out:
            out.append("\n" if kind == "t" and parts[k - 1][0] == "t" else "\n\n")
        out.append(text)
    return "".join(out).strip()


def pages_of(nodes):
    return sorted({n.page for n in nodes})


# ---------------------------------------------------------------- coverage

def cover(text, plan):
    """Cut `text` into coverage segments at the given anchors.

    plan: list of (anchor, status, by). The first anchor may be None (= start of text).
    Each anchor must occur after the previous one; the segment runs to the next anchor.
    """
    starts = []
    pos = 0
    for anchor, status, by in plan:
        if anchor is None:
            idx = 0
        else:
            idx = text.find(anchor, pos)
            if idx < 0:
                raise ValueError(f"coverage anchor not found after position {pos}: {anchor!r}")
            if text.find(anchor, pos, idx) >= 0:
                raise ValueError(f"coverage anchor is ambiguous: {anchor!r}")
        if not starts and idx != 0:
            raise ValueError(f"first coverage segment must start the text, got {anchor!r}")
        starts.append((idx, status, by))
        pos = idx + 1
    segs = []
    for k, (idx, status, by) in enumerate(starts):
        end = starts[k + 1][0] if k + 1 < len(starts) else len(text)
        seg = {"text": text[idx:end].strip(), "status": status}
        if by:
            seg["by"] = list(by)
        segs.append(seg)
    return segs


# ---------------------------------------------------------------- entries

def source(pages, section_path, lot):
    return {
        "system": SYSTEM, "document": DOCUMENT, "origin": "official", "pages": pages,
        "section": section_path, "license": {"id": "CC-BY-4.0", "attribution": ATTRIBUTION},
        "extracted_by": lot,
    }


def collect_refs(obj, acc):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("text", "note", "prompt", "source_text", "source"):
                continue
            if isinstance(v, str) and REF_RE.match(v) and k in (
                    "ref", "condition", "rule", "spell", "creature", "into", "table", "extends"):
                acc.add(v)
            collect_refs(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            if isinstance(v, str) and REF_RE.match(v):
                acc.add(v)
            else:
                collect_refs(v, acc)


def entry(kind, slug, name, nodes, lot, section_path, plan, tier=None, facets=None, data=None,
          effects=None, master_decisions=None, inconsistencies=None, text=None):
    """Build a catalog entry dict (not yet written)."""
    text = text if text is not None else render(nodes)
    e = {
        "$schema": "../../../../schema/catalog_entry.schema.json",
        "ref": f"{SYSTEM}/{kind}/{slug}",
        "kind": kind,
        "name": name,
        "schema_version": "1.0",
        "source": source(pages_of(nodes), section_path, lot),
        "tier": 0,
        "text": text,
    }
    if facets:
        e["facets"] = facets
    if data:
        e["data"] = data
    if effects:
        e["effects"] = effects
    if master_decisions:
        e["master_decisions"] = master_decisions
    if inconsistencies:
        e["inconsistencies"] = inconsistencies
    e["coverage"] = cover(text, plan)
    if tier is None:
        tier = 3 if master_decisions else 2 if effects else 1 if (data or facets) else 0
    e["tier"] = tier
    refs = set()
    collect_refs({k: v for k, v in e.items() if k not in ("ref", "coverage")}, refs)
    for seg in e["coverage"]:
        for b in seg.get("by", []):
            if REF_RE.match(b.split("#", 1)[0]) and "#" not in b:
                refs.add(b)
            elif "#" in b and REF_RE.match(b.split("#", 1)[0]):
                refs.add(b.split("#", 1)[0])
    if refs:
        e["refs"] = sorted(refs)
    return e


def write_entry(e):
    kind, slug = e["ref"].split("/")[-2:]
    path = KNOWLEDGE / SYSTEM / "entries" / kind / f"{slug}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():  # never silently replace another lot's entry (slug collision)
        old = json.loads(path.read_text(encoding="utf-8"))["source"]["extracted_by"]
        if old != e["source"]["extracted_by"]:
            raise ValueError(f"{e['ref']} already written by {old}; {e['source']['extracted_by']} needs another slug")
    path.write_text(json.dumps(e, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def write_json(rel, obj):
    path = KNOWLEDGE / SYSTEM / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def table_rows(nodes, header_first=None):
    """Data rows (cells) of the table rows in `nodes`, skipping bold header rows."""
    rows = []
    for n in nodes:
        if n.type != "t":
            continue
        if n.text.startswith("| **") and (header_first is None or n.cells[0] == header_first):
            continue
        rows.append(n.cells)
    return rows


def md(name, prompt, source_text, reason="gm_judgment", options=None, when=None, pages=None):
    d = {"id": name, "reason": reason, "prompt": prompt, "source_text": source_text}
    if when:
        d["when"] = when
    if options:
        d["options"] = options
    if pages:
        d["pages"] = pages
    return d


# ---------------------------------------------------------------- verbatim quotes

def _norm(s):
    return re.sub(r"\s+", " ", s).strip()


_PLAIN = [(n.page, _norm(strip_md(n.text))) for n in NODES if n.type in ("p", "t", "h")]
_OFFSETS = []
_pos = 0
for _page, _t in _PLAIN:
    _OFFSETS.append((_pos, _pos + len(_t), _page))
    _pos += len(_t) + 1
_FULL = " ".join(t for _, t in _PLAIN)


def quote(fragment, rid=None, data=None):
    """Verbatim rule statement for system.json: fails unless the fragment is in the source.

    Returns {"id"?, "text", "pages", "data"?}; pages are those of every source passage the
    fragment occupies, over all its occurrences.
    """
    frag = _norm(fragment)
    pages, start = set(), _FULL.find(frag)
    if start < 0:
        raise ValueError(f"quote not found verbatim in the source: {fragment[:80]!r}")
    while start >= 0:
        end = start + len(frag)
        pages |= {page for a, b, page in _OFFSETS if a < end and b > start}
        start = _FULL.find(frag, start + 1)
    q = {}
    if rid:
        q["id"] = rid
    q["text"] = frag
    q["pages"] = sorted(pages)
    if data is not None:
        q["data"] = data
    return q


# ---------------------------------------------------------------- declarative builder

def build(kind, slug, name, nodes, lot, section_path, items, text=None, **kw):
    """Build an entry from a coverage plan whose items carry their own representation.

    items: list of (anchor, tag, payload). Consecutive items with the same anchor form one
    segment. Tags:
      "desc"  descriptive text, no payload
      "rule"  payload = {"id": ..., ...mechanic} appended to data.rules
      "fx"    payload = effect dict (or list of effects) appended to effects
      "md"    payload = master decision dict (from md())
      "ref"   payload = list of refs (shared rule)
      "sys"   payload = list of "ref#pointer" or "/pointer" strings already in place
      "table" payload = table dict appended to data.tables
    The segment status is master_decision > structured > shared_rule > descriptive.
    """
    data = dict(kw.pop("data", {}) or {})
    effects = list(kw.pop("effects", []) or [])
    mds = list(kw.pop("master_decisions", []) or [])
    text = text if text is not None else render(nodes)
    segments = []  # [anchor, set_of_tags, by]
    for anchor, tag, payload in items:
        if anchor is not None and text.startswith(anchor):
            anchor = None  # an anchor at the very start is the first segment
        if not segments or segments[-1][0] != anchor:
            segments.append([anchor, set(), []])
        seg = segments[-1]
        seg[1].add(tag)
        if tag == "rule":
            data.setdefault("rules", []).append(payload)
            seg[2].append(f"/data/rules/{len(data['rules']) - 1}")
        elif tag == "table":
            data.setdefault("tables", []).append(payload)
            seg[2].append(f"/data/tables/{len(data['tables']) - 1}")
        elif tag == "fx":
            for fx in payload if isinstance(payload, list) else [payload]:
                effects.append(fx)
                seg[2].append(f"/effects/{len(effects) - 1}")
        elif tag == "md":
            if payload["id"] not in [m["id"] for m in mds]:
                mds.append(payload)
            seg[2].append(f"md:{payload['id']}")
        elif tag in ("ref", "sys"):
            seg[2].extend(payload)
        elif tag != "desc":
            raise ValueError(f"unknown tag {tag}")
    plan = []
    for anchor, tags, by in segments:
        if "md" in tags:
            status = "master_decision"
        elif tags & {"rule", "fx", "sys", "table"}:
            status = "structured"
        elif "ref" in tags:
            status = "shared_rule"
        else:
            status = "descriptive"
        seen = []
        for b in by:
            if b not in seen:
                seen.append(b)
        plan.append((anchor, status, seen or None))
    return entry(kind, slug, name, nodes, lot, section_path, plan, data=data or None, effects=effects or None,
                 master_decisions=mds or None, text=text, **kw)


def extend_registries(additions, lot):
    """Add registry names a lot needs to knowledge/<system>/system.json (idempotent)."""
    path = KNOWLEDGE / SYSTEM / "system.json"
    system = json.loads(path.read_text(encoding="utf-8"))
    for reg, items in additions.items():
        current = system["registries"].setdefault(reg, [])
        ids = {i["id"] for i in current}
        for item in items:
            if item["id"] in ids:
                continue
            current.append({**item, "lot": lot})
            ids.add(item["id"])
    path.write_text(json.dumps(system, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return system


def glossary(name, kind, lot, items, slug=None, **kw):
    """Entry for a Rules Glossary term (kind tag in brackets in the heading when not 'rule')."""
    inv = json.loads((ROOT / "inventory/dnd5e/srd-5.2.1/entries.json").read_text(encoding="utf-8"))["entries"]
    hit = [e for e in inv if e["name"] == name and e["kind"] == kind]
    if len(hit) != 1:
        raise KeyError(f"inventory: {name} ({kind}) -> {hit}")
    e = hit[0]
    tag = (e.get("facets") or {}).get("glossary_tag")
    title = f"{name} [{tag}]" if tag else name
    nodes = section(title, 4, e["page"])
    return build(kind, slug or e["ref"].rsplit("/", 1)[1], name, nodes, lot,
                 f"Rules Glossary/Rules Definitions/{title}", items,
                 facets={"glossary": True, **({"glossary_tag": tag} if tag else {})}, **kw)


def ref_of(name, kind=None):
    inv = json.loads((ROOT / "inventory/dnd5e/srd-5.2.1/entries.json").read_text(encoding="utf-8"))["entries"]
    hit = [e["ref"] for e in inv if e["name"] == name and (kind is None or e["kind"] == kind)]
    if len(hit) > 1 and kind is None:  # a glossary rule wins over same-named catalog items
        hit = [h for h in hit if h.split("/")[1] == "rule"] or hit
    if len(hit) != 1:
        raise KeyError(f"inventory ref for {name!r} ({kind}): {hit}")
    return hit[0]
