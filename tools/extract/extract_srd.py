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
CELL_GAP = 6.0          # horizontal gap (pt) between spans that marks a table cell boundary
BODY_FONTS = ("Cambria", "Optima", "ScalaSans")
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
    return text


# ---------------------------------------------------------------- span model

def span_style(span):
    font = span["font"]
    bold = "Bold" in font or "SemiBold" in font
    italic = "Italic" in font
    return bold, italic


def split_cells(spans):
    """Split x-sorted spans into cells wherever the horizontal gap exceeds CELL_GAP."""
    cells, cur, prev_x1 = [], [], None
    for s in spans:
        if prev_x1 is not None and s["bbox"][0] - prev_x1 > CELL_GAP and "".join(x["text"] for x in cur).strip():
            cells.append(cur)
            cur = []
        cur.append(s)
        prev_x1 = s["bbox"][2]
    cells.append(cur)
    return [c for c in cells if "".join(s["text"] for s in c).strip()]


def merge_rows(raw_lines):
    """Merge consecutive lines sharing a baseline and not overlapping horizontally (table rows)."""
    rows = []
    for l in raw_lines:
        if (rows and abs(rows[-1]["y"] - l["y"]) < ROW_TOL
                and all(l["x0"] >= r[1] - 1 or l["x1"] <= r[0] + 1 for r in rows[-1]["xr"])):
            rows[-1]["spans"].extend(l["spans"])
            rows[-1]["xr"].append((l["x0"], l["x1"]))
        else:
            rows.append({"y": l["y"], "spans": list(l["spans"]), "xr": [(l["x0"], l["x1"])]})
    for r in rows:
        r["spans"].sort(key=lambda s: s["bbox"][0])
    return rows


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
            return True
        return False

    for lines in blocks:
        first = True
        for cells in lines:
            lvl = heading_level(cells)
            if lvl:
                paras.append(("heading", "#" * lvl + " " + render_spans(cells[0]).strip().replace("**", "")))
                first = True
                continue
            xs = [c[0]["bbox"][0] for c in cells]
            if not first and paras and paras[-1][0] == "table":
                prev_cells, prev_xs = paras[-1][1], paras[-1][2]
                slots = [next((k for k in range(1, len(prev_xs)) if abs(prev_xs[k] - x) < 3), None) for x in xs]
                if all(k is not None for k in slots):
                    # wrapped text of non-first cells of the previous row
                    for k, c in zip(slots, cells):
                        prev_cells[k] = dehy.join(prev_cells[k], render_spans(c, escape_pipes=True).strip(), pno)
                    continue
            if len(cells) > 1:
                paras.append(("table", [render_spans(c, escape_pipes=True).strip() for c in cells], xs))
                first = False
                continue
            text = render_spans(cells[0])
            stripped = text.lstrip()
            if stripped.startswith("•"):
                text = "- " + stripped[1:].lstrip()
            if is_new_para(cells, first) or not paras or paras[-1][0] != "para":
                paras.append(("para", text.strip()))
            else:
                paras[-1] = ("para", dehy.join(paras[-1][1], text, pno))
            first = False
        # column/block continuation on the same page: previous paragraph ends with a
        # hyphen and this block starts with a lowercase word -> merge
    paras = [("table", "| " + " | ".join(p[1]) + " |") if p[0] == "table" else p for p in paras]
    merged = []
    for kind, text in paras:
        if (merged and kind == "para" and merged[-1][0] == "para"
                and re.search(r"[A-Za-z]-\**$", merged[-1][1]) and re.match(r"\**[a-z]", text)):
            merged[-1] = ("para", dehy.join(merged[-1][1], text, pno))
        else:
            merged.append((kind, text))
    out = []
    prev = None
    for kind, text in merged:
        if out and not (kind == "table" and prev == "table"):
            out.append("")
        out.append(text)
        prev = kind
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
        c_pt, c_mu, c_md = alnum_counter(clean(pt_body)), alnum_counter(clean(raw_mu)), alnum_counter(md)
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
