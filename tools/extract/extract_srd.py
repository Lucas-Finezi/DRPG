#!/usr/bin/env python3
"""Extract the SRD 5.2.1 PDF into auditable text artifacts.

Outputs (under extraction/):
  text/pdftotext/page-NNN.txt  raw text, poppler pdftotext (independent tool)
  text/pymupdf/page-NNN.txt    raw text, PyMuPDF story order; table cells tab-separated
  SRD_CC_v5.2.1.md             structured markdown with <!-- page N --> markers
  extraction_report.json       hashes, tool versions, per-page cross-validation
  dehyphenation_log.json       every line-end hyphen decision taken for the markdown

The PDF is never modified. The markdown is derived only from PyMuPDF spans; the
cross-validation compares the multiset of alphanumeric characters per page across
all three outputs, so any dropped or invented character is reported.

Usage: python3 -I tools/extract/extract_srd.py source/SRD_CC_v5.2.1.pdf extraction
"""
import collections
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pymupdf

FOOTER_Y = 735          # every page carries "N  System Reference Document 5.2.1" below this
ROW_TOL = 2.5          # baseline tolerance (pt) for cells of the same table row
INDENT = 4.0           # first-cell indentation (pt) that marks a sub-item row
ROW_GAP = 14.0         # max vertical distance (pt) from a row to the wrapped line of one of its cells
CELL_MAX_WIDTH = 160.0 # a table cell line is narrower than a text column
SIDEBAR_MIN_SIZE = 8.5  # table footnotes are set at 8 pt and are not sidebars
SIDEBAR_MAX_SIZE = 9.4  # sidebar body text is set at 9 pt (main text: 10 pt Cambria)
SIDEBAR_MIN_WIDTH = 150.0  # and runs as prose lines, wider than table cells
CELL_GAP = 6.0          # horizontal gap (pt) between spans that marks a table cell boundary
BODY_FONTS = ("Cambria", "Optima", "ScalaSans")
DEHY = None             # set in main(); used to rejoin hyphenated words inside folded table cells
INVISIBLE = {"­": "", "​": ""}

# Line-end breaks reviewed by hand in dehyphenation_log.json where the vocabulary heuristic
# cannot tell a compound from typesetting hyphenation; these are real compounds.
KEEP_HYPHEN = {"long-dead", "nine-course", "real-world"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def clean(text):
    for k, v in INVISIBLE.items():
        text = text.replace(k, v)
    return re.sub(r"[\x00-\x08\x0b-\x1f]", "", text)  # stray control glyphs (e.g. BEL in "4:\t\x07Choose")


# ---------------------------------------------------------------- span model

def span_style(span):
    font = span["font"]
    bold = "Bold" in font or "SemiBold" in font
    italic = "Italic" in font
    return bold, italic


def split_cells(spans):
    """Split x-sorted spans into cells wherever the horizontal gap exceeds CELL_GAP.

    Whitespace-only spans do not count as content: a wide space span between two cells
    ("Barbarian" + " " + "Battle") must not bridge the gap.
    """
    cells, cur, prev_x1 = [], [], None
    for s in spans:
        if s["text"].strip() and prev_x1 is not None and s["bbox"][0] - prev_x1 > CELL_GAP \
                and "".join(x["text"] for x in cur).strip():
            cells.append(cur)
            cur = []
        cur.append(s)
        if s["text"].strip():
            prev_x1 = s["bbox"][2]
    cells.append(cur)
    return [c for c in cells if "".join(s["text"] for s in c).strip()]


def merge_rows(raw_lines):
    """Merge consecutive lines sharing a baseline and not overlapping horizontally (table rows)."""
    rows = []
    for l in raw_lines:
        if (rows and abs(rows[-1]["y"] - l["y"]) < ROW_TOL
                and all(l["x0"] >= r[1] - 1 or l["x1"] <= r[0] + 1 for r in rows[-1]["xr"])):
            rows[-1]["parts"].append((l["x0"], l["spans"]))
            rows[-1]["xr"].append((l["x0"], l["x1"]))
        else:
            rows.append({"y": l["y"], "parts": [(l["x0"], l["spans"])], "xr": [(l["x0"], l["x1"])]})
    for r in rows:
        # order the merged line segments left to right; spans keep their order inside a
        # segment (a folded multi-line cell starts every line at the same x)
        r["spans"] = [s for _, spans in sorted(r["parts"], key=lambda p: p[0]) for s in spans]
    return rows


def is_prose(line):
    return any(s["font"].startswith("Cambria") for s in line["spans"] if s["text"].strip())


def merge_split_rows(raw_blocks):
    """Reattach trailing table cells that the PDF stores as a separate block.

    A table row whose middle cell wraps (e.g. Light Crossbow's properties) is laid out as one
    block holding the first cells plus the wrapped text, and another block holding the last
    cells on the first line's baseline. Each line of such a block is merged into the line of
    the previous block that shares its baseline and ends to its left. Only non-prose lines
    whose target already has several cells are merged, so prose columns never fuse.
    """
    out = []
    for lines in raw_blocks:
        lines = [{"y": r["y"], "x0": min(a for a, _ in r["xr"]), "x1": max(b for _, b in r["xr"]),
                  "spans": r["spans"]} for r in merge_rows(lines)]
        prev = out[-1] if out else None
        targets = []
        if prev and len(lines) <= 3 and not any(is_prose(l) for l in lines):
            for l in lines:
                t = next((p for p in prev if abs(p["y"] - l["y"]) < ROW_TOL and p["x1"] < l["x0"]
                          and not is_prose(p)), None)
                targets.append(t)
        # the block's first line must continue a table row (2+ cells); later lines are the
        # wrapped second lines of multi-line cells and join the lines sharing their baseline
        if targets and all(targets) and len(split_cells(targets[0]["spans"])) >= 2:
            for l, t in zip(lines, targets):
                t["spans"] = t["spans"] + l["spans"]
                t["x1"] = max(t["x1"], l["x1"])
            continue
        # a one-line cell vertically centred beside a multi-line cell ("Bard, Cleric, Druid," /
        # "Monk, Rogue, or Warlock" | "5 + Con. modifier"): fold the multi-line cell into one
        # line and append the centred cell to it
        plines = sorted(prev, key=lambda x: x["y"]) if prev else []
        if (prev and len(lines) == 1 and 2 <= len(prev) <= 3 and not is_prose(lines[0])
                and not (is_header_block(prev) and is_header_block(lines))
                and all(x["x1"] - x["x0"] < CELL_MAX_WIDTH for x in prev + lines)
                and not any(is_prose(p) for p in prev)
                and all(p["x1"] < lines[0]["x0"] for p in prev)
                and plines[0]["y"] - ROW_TOL < lines[0]["y"] < plines[-1]["y"] - ROW_TOL
                and all(len(split_cells(p["spans"])) == 1 for p in prev)):
            spans = [dict(x) for x in plines[0]["spans"]]
            for p in plines[1:]:
                nxt = [dict(x) for x in p["spans"]]
                left = "".join(x["text"] for x in spans)
                m = re.search(r"([A-Za-z’']+)-$", left.rstrip())
                n = re.match(r"([a-z][A-Za-z’']*)", nxt[0]["text"].lstrip())
                if m and n and DEHY is not None and DEHY.decide(m.group(1), n.group(1)) == "join":
                    spans[-1]["text"] = spans[-1]["text"].rstrip()[:-1]
                    nxt[0]["text"] = nxt[0]["text"].lstrip()
                elif not left.endswith((" ", "-")):
                    nxt[0]["text"] = " " + nxt[0]["text"].lstrip()
                spans += nxt
            out[-1] = [{"y": plines[0]["y"], "x0": min(p["x0"] for p in prev), "x1": lines[0]["x1"],
                        "spans": spans + lines[0]["spans"]}]
            continue
        out.append(lines)
    return out


def is_sidebar_line(cells):
    """Body text of a boxed sidebar: every span in the sans-serif face at about 9 pt."""
    spans = [s for c in cells for s in c if s["text"].strip()]
    if not spans or len(cells) != 1 or not all(
            s["font"].startswith("GillSans") and SIDEBAR_MIN_SIZE < s["size"] < SIDEBAR_MAX_SIZE for s in spans):
        return False
    labelled = spans[0]["font"] == "GillSans-BoldItalic"  # "Only One at a Time." style label
    return labelled or sum(s["bbox"][2] - s["bbox"][0] for s in spans) > SIDEBAR_MIN_WIDTH


def is_header_block(lines):
    spans = [s for l in lines for s in l["spans"] if s["text"].strip()]
    return bool(spans) and all(s["font"].startswith("GillSans-SemiBold") and s["size"] < 10 for s in spans)


def page_lines(page):
    """Return blocks as lists of lines; each line is a list of cells; each cell a list of spans.

    PyMuPDF story order is kept. Table cells, which the PDF stores as separate lines on a
    shared baseline, are merged into one line; consecutive blocks made only of table-header
    labels are pooled and regrouped by baseline so multi-line headers become header rows.
    """
    raw_blocks = []
    for b in page.get_text("dict")["blocks"]:
        if b["type"] != 0:
            continue
        lines = []
        for l in b["lines"]:
            if l["bbox"][1] >= FOOTER_Y:
                continue
            spans = [s for s in l["spans"] if s["text"] != ""]
            if spans:
                lines.append({"y": l["bbox"][1], "x0": l["bbox"][0], "x1": l["bbox"][2], "spans": spans})
        if lines:
            raw_blocks.append(lines)

    raw_blocks = merge_split_rows(raw_blocks)
    pooled = []
    for lines in raw_blocks:
        if pooled and is_header_block(lines) and pooled[-1][0] == "header":
            pooled[-1][1].extend(lines)
        else:
            pooled.append(("header" if is_header_block(lines) else "body", list(lines)))

    blocks = []
    for kind, lines in pooled:
        if kind == "header":
            lines = sorted(lines, key=lambda l: (round(l["y"] / ROW_TOL), l["x0"]))
        out = [split_cells(r["spans"]) for r in merge_rows(lines)]
        out = [c for c in out if c]
        if out:
            blocks.append(out)
    return blocks


def raw_page_text(blocks):
    out = []
    for lines in blocks:
        for cells in lines:
            out.append("\t".join("".join(s["text"] for s in c).strip() for c in cells))
        out.append("")
    return "\n".join(out).rstrip() + "\n"


# ---------------------------------------------------------------- markdown

def heading_level(cells):
    if len(cells) != 1:
        return 0
    spans = [s for s in cells[0] if s["text"].strip()]
    if not spans or not all(s["font"].startswith("GillSans") for s in spans):
        return 0
    size = max(s["size"] for s in spans)
    bold = all(span_style(s)[0] for s in spans)
    if bold:
        if size >= 25:
            return 1
        if size >= 17:
            return 2
        if size >= 13.5:
            return 3
        if size >= 11.5:
            return 4
        if size >= 10.4:
            return 5
        return 0
    if 11.5 <= size < 13:
        return 5  # stat-block section titles (Traits, Actions, ...)
    return 0


def render_spans(spans, escape_pipes=False):
    runs = []
    for s in spans:
        style = span_style(s)
        text = clean(s["text"]).replace("\t", " ")
        text = text.replace("*", "\\*")
        if escape_pipes:
            text = text.replace("|", "\\|")
        if runs and runs[-1][0] == style:
            runs[-1][1] += text
        else:
            runs.append([style, text])
    out = []
    for (bold, italic), text in runs:
        core = text.strip()
        if not core or not (bold or italic):
            out.append(text)
            continue
        mark = "***" if bold and italic else "**" if bold else "*"
        lead = text[: len(text) - len(text.lstrip())]
        trail = text[len(text.rstrip()):]
        out.append(f"{lead}{mark}{core}{mark}{trail}")
    return re.sub(r"[ ]{2,}", " ", "".join(out))


def plain(spans):
    return clean("".join(s["text"] for s in spans))


class Dehyphenator:
    def __init__(self, vocab):
        self.vocab = vocab
        self.log = []

    def decide(self, a, b):
        joined, hyph = (a + b).lower(), f"{a}-{b}".lower()
        cj, ch = self.vocab.get(joined, 0), self.vocab.get(hyph, 0)
        return "keep_hyphen" if ch > cj or hyph in KEEP_HYPHEN else "join"

    def join(self, left, right, page):
        """Join two text fragments that were split at a line end."""
        if re.search(r"\d-\**\s*$", left):  # 10-foot, 100-foot: numeric compounds keep the hyphen
            return left.rstrip() + right.lstrip()
        m = re.search(r"([A-Za-z’']+)-(\**)\s*$", left)
        n = re.match(r"\s*(\**)([a-z][A-Za-z’']*)", right)
        if m and n:
            a, b = m.group(1), n.group(2)
            joined, hyph = (a + b).lower(), f"{a}-{b}".lower()
            cj, ch = self.vocab.get(joined, 0), self.vocab.get(hyph, 0)
            if ch > cj or hyph in KEEP_HYPHEN:
                decision = "keep_hyphen"
            else:
                decision = "join"
            self.log.append({"page": page, "left": a + "-", "right": b, "decision": decision,
                             "joined_count": cj, "hyphenated_count": ch,
                             "ambiguous": (cj == 0 and ch == 0) or (cj > 0 and ch > 0),
                             "manual_override": hyph in KEEP_HYPHEN})
            if decision == "join":
                return left[: m.start(1)] + a + m.group(2) + right.lstrip()
            return left.rstrip() + right.lstrip()
        if re.search(r"[—–/]\**\s*$", left):
            return left.rstrip() + right.lstrip()
        return left.rstrip() + " " + right.lstrip()


def build_vocab(doc):
    """Word counts (lowercase) from text that is NOT split at a line end, including hyphenated compounds."""
    vocab = collections.Counter()
    for page in doc:
        for line in clean(page.get_text()).splitlines():
            line = line.strip()
            if line.endswith("-"):
                line = line[:-1].rsplit(" ", 1)[0] if " " in line else ""
            for w in re.findall(r"[A-Za-z’']+(?:-[A-Za-z’']+)*", line):
                vocab[w.lower()] += 1
                for part in w.split("-"):
                    vocab[part.lower()] += 0
    return vocab


def page_markdown(blocks, pno, dehy):
    paras = []  # list of (kind, text) kind in heading|table|para

    def is_new_para(line_cells, first):
        if first:
            return True
        spans = [s for s in line_cells[0] if s["text"].strip()]
        t = plain(line_cells[0])
        if t.startswith("\t") or t.lstrip().startswith("•"):
            return True
        if spans and span_style(spans[0])[0]:
            if not spans[0]["font"].startswith("Cambria"):
                return True  # stat-block and table labels (Optima / GillSans) always open a line
            # running prose: a bold run opens a paragraph only when it is a label ("Trigger:",
            # "Evasion.") or the previous line closed a sentence; otherwise it is a bold word
            # (e.g. a creature name) that merely wrapped to the start of the line
            first_run = ""
            for x in spans:
                if not span_style(x)[0]:
                    break
                first_run += x["text"]
            prev_text = paras[-1][1] if paras and paras[-1][0] == "para" else ""
            if re.fullmatch(r"\*\*[^*]+\*\*", prev_text.strip()) and not re.search(r"[.:!?]\**$", prev_text.strip()):
                return False  # second line of a bold label wrapped mid-phrase ("... Characters" / "Do.")
            if re.search(r"[.:!?]\**$", first_run.strip()) or re.search(r"[.:!?)”0-9]\**$", prev_text.strip()):
                return True
            return False
        return False

    for bi, lines in enumerate(blocks):
        first = True
        for cells in lines:
            lvl = heading_level(cells)
            if lvl:
                title = render_spans(cells[0]).strip().replace("**", "")
                prev = paras[-1] if paras else None
                if prev and prev[0] == "heading" and (prev[2] == (bi, lvl) or prev[2][1] == lvl == 1) and lvl <= 4:
                    # a heading wrapped onto several lines (e.g. "Curses and" / "Magical Contagions")
                    paras[-1] = ("heading", prev[1] + " " + title, prev[2])
                else:
                    paras.append(("heading", "#" * lvl + " " + title, (bi, lvl)))
                first = True
                continue
            xs = [c[0]["bbox"][0] for c in cells]
            y = min(sp["bbox"][1] for c in cells for sp in c)
            if paras and paras[-1][0] == "table" and (not first or 0 < y - paras[-1][3] < ROW_GAP):
                prev_cells, prev_xs = paras[-1][1], paras[-1][2]
                slots = [next((k for k in range(1, len(prev_xs)) if abs(prev_xs[k] - x) < 3), None) for x in xs]
                if all(k is not None for k in slots):
                    # wrapped text of non-first cells of the previous row (same block, or the
                    # next block when it sits right below the row)
                    for k, c in zip(slots, cells):
                        prev_cells[k] = dehy.join(prev_cells[k], render_spans(c, escape_pipes=True).strip(), pno)
                    paras[-1] = (*paras[-1][:3], y)
                    continue
            if len(cells) > 1:
                paras.append(("table", [render_spans(c, escape_pipes=True).strip() for c in cells], xs, y))
                first = False
                continue
            text = render_spans(cells[0])
            stripped = text.lstrip()
            if stripped.startswith("•"):
                text = "- " + stripped[1:].lstrip()
            if is_new_para(cells, first) or not paras or paras[-1][0] != "para":
                paras.append(("para", text.strip(), is_sidebar_line(cells)))
            else:  # continuation line: same paragraph, same sidebar status
                paras[-1] = ("para", dehy.join(paras[-1][1], text, pno), paras[-1][2])
            first = False
        # column/block continuation on the same page: previous paragraph ends with a
        # hyphen and this block starts with a lowercase word -> merge
    # rows printed indented under an italic group label (e.g. "Saddle" -> Exotic, Military,
    # Riding) keep that membership only through their x position: mark them with "↳ "
    k = 0
    while k < len(paras):
        if paras[k][0] != "table":
            k += 1
            continue
        run, has_label = [], False
        while k < len(paras) and (paras[k][0] == "table" or (
                paras[k][0] == "para" and re.match(r"^\*[^*].*\*$", paras[k][1]))):
            if paras[k][0] == "table":
                run.append(k)
            else:
                has_label = True
            k += 1
        if not has_label:
            continue  # only tables with group labels have sub-item rows
        # indentation is measured against the header row of the same table half (some tables
        # are printed as two side-by-side halves, each with its own header)
        base = min(paras[r][2][0] for r in run)
        for r in run:
            if paras[r][1][0].startswith("**"):
                base = paras[r][2][0]
            elif paras[r][2][0] - base > INDENT:
                paras[r][1][0] = "↳ " + paras[r][1][0]
    paras = [("table", "| " + " | ".join(p[1]) + " |", False) if p[0] == "table"
             else (p[0], p[1], p[2] if p[0] == "para" else False) for p in paras]
    merged = []
    for kind, text, side in paras:
        # a paragraph continued in the next block (column break, hanging indent): the
        # previous one ends without closing punctuation and this one starts in lowercase
        if (merged and kind == "para" and merged[-1][0] == "para" and merged[-1][2] == side
                and not re.search(r"[.:!?)”\]]\**$", merged[-1][1]) and re.match(r"\**[a-z]", text)):
            merged[-1] = ("para", dehy.join(merged[-1][1], text, pno), side)
        else:
            merged.append((kind, text, side))
    # a bold or italic phrase broken across lines yields "**a** **b**": rejoin it
    # and a word hyphenated inside an emphasis run yields "*Suc**cess:*": drop the inner markers
    merged = [(k, re.sub(r"(?<=\w)(?:\*\*)+(?=\w)", "", re.sub(r"(?<=\w)(\*{1,3}) \1(?=\w)", " ", t)), sd)
              if k != "heading" else (k, t, sd) for k, t, sd in merged]
    # sidebars (boxed text set in the sans-serif body face) are wrapped in markers, together
    # with the level-5 heading that introduces them
    out = []
    prev = None
    k = 0
    while k < len(merged):
        kind, text, side = merged[k]
        if side or (kind == "heading" and text.startswith("##### ") and k + 1 < len(merged)
                    and merged[k + 1][2]):
            run = [merged[k]]
            k += 1
            while k < len(merged) and merged[k][2]:
                run.append(merged[k])
                k += 1
            if out:
                out.append("")
            out.append("<!-- sidebar -->")
            for _, t, _ in run:
                out += ["", t]
            out += ["", "<!-- /sidebar -->"]
            prev = "sidebar"
            continue
        if out and not (kind == "table" and prev == "table"):
            out.append("")
        out.append(text)
        prev = kind
        k += 1
    return "\n".join(out)


# ---------------------------------------------------------------- validation

def alnum_counter(text):
    return collections.Counter(ch for ch in text if ch.isalnum())


def counter_diff(a, b):
    missing = a - b
    extra = b - a
    return sum(missing.values()), sum(extra.values()), dict(missing.most_common(10)), dict(extra.most_common(10))


def main(pdf_path, out_dir):
    pdf_path, out = Path(pdf_path), Path(out_dir)
    (out / "text" / "pdftotext").mkdir(parents=True, exist_ok=True)
    (out / "text" / "pymupdf").mkdir(parents=True, exist_ok=True)

    doc = pymupdf.open(pdf_path)
    n = doc.page_count
    vocab = build_vocab(doc)
    dehy = Dehyphenator(vocab)
    global DEHY
    DEHY = dehy

    md_parts = [
        "<!-- Generated by tools/extract/extract_srd.py from source/SRD_CC_v5.2.1.pdf. Do not edit by hand. -->",
        "<!-- Page markers use PDF page numbers, which equal the printed page numbers of the SRD. -->",
    ]
    pages = []
    for i in range(n):
        pno = i + 1
        page = doc[i]
        blocks = page_lines(page)
        raw_mu = raw_page_text(blocks)
        (out / "text" / "pymupdf" / f"page-{pno:03d}.txt").write_text(raw_mu, encoding="utf-8")

        raw_pt = subprocess.run(["pdftotext", "-f", str(pno), "-l", str(pno), "-enc", "UTF-8", str(pdf_path), "-"],
                                check=True, capture_output=True, text=True).stdout
        (out / "text" / "pdftotext" / f"page-{pno:03d}.txt").write_text(raw_pt, encoding="utf-8")

        md = page_markdown(blocks, pno, dehy)
        md_parts.append(f"\n<!-- page {pno} -->\n\n{md}")

        footer = [l for l in page.get_text("dict")["blocks"] if l["type"] == 0 and l["bbox"][1] >= FOOTER_Y]
        footer_text = " ".join("".join(s["text"] for ln in b["lines"] for s in ln["spans"]) for b in footer)
        printed = re.findall(r"\d{1,3}", footer_text.replace("System Reference Document 5.2.1", " "))

        # remove footer from pdftotext before comparing
        footer_at = raw_pt.rfind("System Reference Document 5.2.1")
        pt_body = raw_pt[:footer_at] + raw_pt[footer_at + len("System Reference Document 5.2.1"):]
        pt_body = re.sub(rf"(?m)^\s*{pno}\s*$", "", pt_body, count=1)
        c_pt, c_mu = alnum_counter(clean(pt_body)), alnum_counter(clean(raw_mu))
        c_md = alnum_counter(re.sub(r"<!--.*?-->", "", md))  # structural markers are not content
        mu_vs_pt = counter_diff(c_pt, c_mu)
        md_vs_mu = counter_diff(c_mu, c_md)
        pages.append({
            "page": pno,
            "printed_page": int(printed[0]) if printed else None,
            "alnum_chars": sum(c_mu.values()),
            "images": sum(1 for b in page.get_text("dict")["blocks"] if b["type"] != 0),
            "table_rows": md.count("\n| ") + (1 if md.startswith("| ") else 0),
            "pymupdf_vs_pdftotext": {"missing": mu_vs_pt[0], "extra": mu_vs_pt[1],
                                     "missing_sample": mu_vs_pt[2], "extra_sample": mu_vs_pt[3]},
            "markdown_vs_pymupdf": {"missing": md_vs_mu[0], "extra": md_vs_mu[1],
                                    "missing_sample": md_vs_mu[2], "extra_sample": md_vs_mu[3]},
        })

    md_text = "\n".join(md_parts).rstrip() + "\n"
    md_path = out / "SRD_CC_v5.2.1.md"
    md_path.write_text(md_text, encoding="utf-8")
    (out / "dehyphenation_log.json").write_text(json.dumps(dehy.log, ensure_ascii=False, indent=1), encoding="utf-8")

    pt_version = subprocess.run(["pdftotext", "-v"], capture_output=True, text=True).stderr.splitlines()[0]
    flagged = [p["page"] for p in pages
               if p["pymupdf_vs_pdftotext"]["missing"] or p["pymupdf_vs_pdftotext"]["extra"]
               or p["markdown_vs_pymupdf"]["missing"] or p["markdown_vs_pymupdf"]["extra"]]
    report = {
        "source": {
            "file": str(pdf_path),
            "sha256": sha256(pdf_path),
            "bytes": pdf_path.stat().st_size,
            "pages": n,
            "metadata": {k: v for k, v in doc.metadata.items() if v},
            "license": "CC-BY-4.0",
            "attribution": ("This work includes material from the System Reference Document 5.2.1 (“SRD 5.2.1”) "
                            "by Wizards of the Coast LLC, available at https://www.dndbeyond.com/srd. The SRD 5.2.1 is "
                            "licensed under the Creative Commons Attribution 4.0 International License, available at "
                            "https://creativecommons.org/licenses/by/4.0/legalcode."),
        },
        "tools": {"pymupdf": pymupdf.VersionBind, "pdftotext": pt_version, "python": sys.version.split()[0]},
        "outputs": {"markdown": str(md_path), "markdown_sha256": sha256(md_path)},
        "summary": {
            "pages_total": n,
            "pages_printed_number_matches_pdf_index": sum(1 for p in pages if p["printed_page"] == p["page"]),
            "pages_with_char_mismatch": flagged,
            "alnum_chars_total": sum(p["alnum_chars"] for p in pages),
            "dehyphenation_decisions": len(dehy.log),
            "dehyphenation_ambiguous": sum(1 for d in dehy.log if d["ambiguous"]),
            "dehyphenation_kept_hyphen": sum(1 for d in dehy.log if d["decision"] == "keep_hyphen"),
        },
        "pages": pages,
    }
    (out / "extraction_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(report["summary"], indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:3])
