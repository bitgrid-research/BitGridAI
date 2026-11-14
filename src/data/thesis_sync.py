"""
Thesis sync check: which entries of the thesis draft rest on a source that
changed after the entry was last checked, and which findings of the
"Masterarbeit" card are cited in the text.

The thesis draft marks every entry with comment lines (convention in the
head of kapitel/04_system.tex):

    % Quelle: mvp_auto.yaml Z. 734-802; ADR 027 (10 % + 5 %)
    % Stand: 02.11.2026 neu
    % Befund: schaltwechsel (Stichtag 14.11.2026)

From these comments alone, without a language model, this module derives:

  - ``replaced``: the entry cites an ADR that a later ADR replaces
    (``**Ersetzt teilweise:** ADR 028`` in its head line). Strong signal.
  - ``changed``: a cited repo file changed after the entry's Stand date.
    Weak signal: the cited lines may be untouched, but line numbers in
    "Z. 734-802" are likely off. The ADR file itself is checked per ADR.
  - ``befunde``: per card note, where the text cites it, and whether its
    wording (numbers) differs from the snapshot of the cited Stichtag.

Re-checking an entry means writing a new Stand line; then it drops out.
Pure functions; file and git access live in scripts/thesis_open_export.py.
Quality axis: Reproduzierbarkeit (every number in the thesis traceable to a
dated source) and Transparenz.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Callable

ADR_FILE = "091_adr_de.md"
# Card groups whose notes belong into the text (the others are guidance
# for the author or open work on the system).
TEXT_GROUPS = (
    "Befunde aus den Produktivdaten",
    "Datenbasis und Methodik",
    "Limitationen, die genannt werden müssen",
    "Erklärschicht (Sprachmodell)",
)

_DATE = re.compile(r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b")
_ADR_REF = re.compile(r"\bADRs?\s+(\d{3})((?:\s*(?:/|,|und|bis)\s*\d{3})*)")
_ADR_HEAD = re.compile(r"^## ADR (\d{3})\b\s*[—-]?\s*(.*)$")
_ADR_REPLACES = re.compile(r"\*\*Ersetzt(?: teilweise)?:\*\*\s*ADR\s+(\d{3})")
_ADR_DATE = re.compile(r"\*\*Datum:\*\*\s*(\d{1,2}\.\d{1,2}\.\d{4})")
_FILE = re.compile(
    r"(?<![\w/.-])([\w./-]*[\w-]\.(?:py|yaml|yml|md|js|json|txt|tex|sql))\b"
)
_SECTION = re.compile(r"\\(chapter|section|subsection|subsubsection)\*?\{([^}]*)\}")
_KEY = re.compile(r"^%\s*(Quelle|Stand|Befund)n?\b[^:]*:\s*(.*)$")
_BEFUND = re.compile(r"([a-z0-9_]+)(?:\s*\(Stichtag\s+(\d{1,2}\.\d{1,2}\.\d{4})\))?")


def de_to_iso(text: str) -> list[str]:
    """All dd.mm.yyyy dates in ``text`` as ISO strings (invalid ones skipped)."""
    out = []
    for d, m, y in _DATE.findall(text):
        try:
            out.append(date(int(y), int(m), int(d)).isoformat())
        except ValueError:
            continue
    return out


def iso_to_de(iso: str | None) -> str:
    if not iso:
        return "?"
    y, m, d = iso[:10].split("-")
    return f"{d}.{m}.{y}"


def parse_adrs(text: str) -> dict[int, dict[str, Any]]:
    """ADR number -> {title, date (ISO or None), replaces: [numbers]}.

    Only the head line of each ADR counts for ``date`` and ``replaces``, so
    a sentence that merely discusses an older ADR is no replacement.
    """
    adrs: dict[int, dict[str, Any]] = {}
    current: dict[str, Any] | None = None
    head_lines = 0
    for line in text.splitlines():
        head = _ADR_HEAD.match(line)
        if head:
            current = {
                "title": head.group(2).replace("(Detail)", "").strip(),
                "date": None,
                "replaces": [],
            }
            adrs[int(head.group(1))] = current
            head_lines = 0
            continue
        if current is None or head_lines > 4:
            continue
        if line.strip():
            head_lines += 1
        m = _ADR_DATE.search(line)
        if m:
            current["date"] = de_to_iso(m.group(1))[0]
        current["replaces"] += [int(n) for n in _ADR_REPLACES.findall(line)]
    return adrs


def adr_refs(text: str) -> list[int]:
    """ADR numbers cited in a comment, incl. "ADR 027/028" and "ADR 027 und 028"."""
    out: list[int] = []
    for first, rest in _ADR_REF.findall(text):
        for n in [first] + re.findall(r"\d{3}", rest):
            if int(n) not in out:
                out.append(int(n))
    return out


def file_refs(text: str) -> list[str]:
    """File names or paths cited in a comment (globs and URLs left out)."""
    out = []
    for token in _FILE.findall(text.replace("\\", "/")):
        if "*" in token or token.startswith(("http", "www.")):
            continue
        if token not in out:
            out.append(token)
    return out


@dataclass
class Entry:
    """One comment block of the draft."""

    file: str
    line: int
    section: str
    sources: str = ""
    stand: str | None = None
    befunde: list[tuple[str, str | None]] = field(default_factory=list)


def parse_tex(text: str, file: str) -> list[Entry]:
    """Comment blocks with a Quelle, Stand or Befund line, after \\chapter.

    The head of a chapter explains the convention with example lines; it
    comes before \\chapter and is skipped.
    """
    entries: list[Entry] = []
    section = ""
    started = False
    block: Entry | None = None
    last_key = ""
    for no, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        sec = _SECTION.search(line)
        if sec and not line.startswith("%"):
            started = True
            section = sec.group(2).strip()
        if not line.startswith("%"):
            if block is not None:
                entries.append(block)
                block = None
            continue
        if not started:
            continue
        key = _KEY.match(line)
        if key:
            if block is None:
                block = Entry(file=file, line=no, section=section)
            last_key = key.group(1)
            value = key.group(2)
            if last_key == "Quelle":
                block.sources += " " + value
            elif last_key == "Stand":
                dates = de_to_iso(value)
                if dates:
                    best = max(dates + ([block.stand] if block.stand else []))
                    block.stand = best
            else:
                for bid, stichtag in _BEFUND.findall(value):
                    iso = de_to_iso(stichtag)[0] if stichtag else None
                    block.befunde.append((bid, iso))
        elif block is not None and last_key == "Quelle":
            # Continuation line of a long Quelle comment.
            block.sources += " " + line.lstrip("% ")
    if block is not None:
        entries.append(block)
    return entries


def check(
    entries: list[Entry],
    adrs: dict[int, dict[str, Any]],
    resolve: Callable[[str], str | None],
    changed_on: Callable[[str], str | None],
) -> dict[str, Any]:
    """Drift lists. ``resolve`` maps a cited name to a repo path (or None),
    ``changed_on`` gives the ISO date of a repo path's last change."""
    replaced_by: dict[int, list[int]] = {}
    for num, adr in adrs.items():
        for old in adr["replaces"]:
            replaced_by.setdefault(old, []).append(num)

    replaced: list[dict[str, Any]] = []
    changed: dict[str, dict[str, Any]] = {}
    unresolved: set[str] = set()
    cited_adrs: set[int] = set()
    for e in entries:
        if not e.sources:
            continue
        refs = adr_refs(e.sources)
        cited_adrs.update(refs)
        for num in refs:
            for newer in replaced_by.get(num, []):
                if newer in refs:
                    continue  # the entry already cites the replacement
                when = adrs[newer]["date"]
                if e.stand and when and when <= e.stand:
                    continue
                replaced.append(
                    {
                        "file": e.file,
                        "line": e.line,
                        "section": e.section,
                        "stand": e.stand,
                        "adr": num,
                        "by": newer,
                        "by_title": adrs[newer]["title"],
                        "by_date": when,
                    }
                )
        for name in file_refs(e.sources):
            path = resolve(name)
            if path is None:
                unresolved.add(name)
                continue
            if path.endswith(ADR_FILE):
                continue  # checked per ADR above
            when = changed_on(path)
            if not e.stand or not when or when <= e.stand:
                continue  # without a Stand there is no "after"
            item = changed.setdefault(
                path, {"path": path, "changed": when, "entries": []}
            )
            item["entries"].append(
                {
                    "file": e.file,
                    "line": e.line,
                    "section": e.section,
                    "stand": e.stand,
                }
            )
    no_stand = [
        {"file": e.file, "line": e.line, "section": e.section}
        for e in entries
        if e.sources and not e.stand
    ]
    uncited = [
        {"adr": n, "title": a["title"], "date": a["date"]}
        for n, a in sorted(adrs.items())
        if n >= 20 and n not in cited_adrs
    ]
    return {
        "replaced": replaced,
        "changed": sorted(changed.values(), key=lambda c: -len(c["entries"])),
        "no_stand": no_stand,
        "unresolved": sorted(unresolved),
        "adr_uncited": uncited,
    }


def befunde(
    entries: list[Entry],
    notes: list[dict[str, Any]],
    snapshots: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Per card note: places in the text and whether it changed since the
    cited Stichtag. ``snapshots`` maps ISO date -> thesis notes of that day."""
    by_id = {n["id"]: n for n in notes if n.get("id")}
    places: dict[str, list[dict[str, Any]]] = {}
    unknown: list[dict[str, Any]] = []
    for e in entries:
        for bid, stichtag in e.befunde:
            when = stichtag or e.stand
            place = {"file": e.file, "line": e.line, "stichtag": when}
            if bid not in by_id:
                unknown.append({"id": bid, **place})
                continue
            snap = {n.get("id"): n for n in snapshots.get(when or "", [])}
            if not when or when not in snapshots:
                place["state"] = "ohne_abzug"
            elif bid not in snap:
                place["state"] = "neu_seit_stichtag"
            elif snap[bid]["text"] != by_id[bid]["text"]:
                place["state"] = "geaendert"
            else:
                place["state"] = "aktuell"
            places.setdefault(bid, []).append(place)
    rows = [
        {
            "id": n["id"],
            "title": n["title"],
            "group": n["group"],
            "needs_text": n["group"] in TEXT_GROUPS,
            "places": places.get(n["id"], []),
        }
        for n in notes
        if n.get("id")
    ]
    return {
        "notes": rows,
        "missing": [r["id"] for r in rows if r["needs_text"] and not r["places"]],
        "unknown": unknown,
    }


def _where(item: dict[str, Any]) -> str:
    name = str(item["file"]).split("/")[-1].replace(".tex", "")
    return f"{name}:{item['line']} ({item.get('section') or 'ohne Abschnitt'})"


def render_markdown(sync: dict[str, Any], exported_at: str) -> str:
    """notizen/abgleich_system.md: what Claude in the thesis window reads first."""
    lines = [
        "# Abgleich Arbeit gegen System",
        "",
        f"Erzeugt {exported_at[:16].replace('T', ' ')} UTC von"
        " `scripts/thesis_open_export.py` im Repo BitGridAI. Nicht von Hand"
        " bearbeiten, wird bei jedem Pull und Commit neu geschrieben.",
        "",
        "Ein Eintrag gilt als geprüft, sobald seine `% Stand:`-Zeile ein Datum"
        " nach der Änderung trägt (zum Beispiel `% Stand: 14.11.2026 geprüft`).",
        "",
    ]
    rep = sync.get("replaced") or []
    lines.append(f"## 1. Zitierte ADR ist ersetzt ({len(rep)})")
    lines.append("")
    lines += [
        f"- {_where(r)}, Stand {iso_to_de(r['stand'])}: zitiert ADR {r['adr']:03d},"
        f" ersetzt durch ADR {r['by']:03d} ({r['by_title']},"
        f" {iso_to_de(r['by_date'])})"
        for r in rep
    ] or ["- keine"]
    lines.append("")
    bf = sync.get("befunde") or {}
    rows = bf.get("notes") or []
    stale = [
        (r, p)
        for r in rows
        for p in r["places"]
        if p["state"] in ("geaendert", "neu_seit_stichtag")
    ]
    lines.append(f"## 2. Befunde der Merkliste ({len(rows)})")
    lines.append("")
    for r in rows:
        if not r["needs_text"] and not r["places"]:
            continue
        where = (
            ", ".join(
                f"{p['file'].split('/')[-1]}:{p['line']}"
                f" (Stichtag {iso_to_de(p['stichtag'])}, {p['state']})"
                for p in r["places"]
            )
            or "**fehlt im Text**"
        )
        lines.append(f"- `{r['id']}` {r['title']}: {where}")
    if stale:
        lines += [
            "",
            "Seit dem Stichtag geänderte Zahlen: Wert im Text gegen den Abzug"
            " des Stichtags prüfen oder Stichtag bewusst neu setzen.",
        ]
    for u in bf.get("unknown") or []:
        lines.append(f"- unbekannte ID `{u['id']}` in {u['file']}:{u['line']}")
    lines.append("")
    ch = sync.get("changed") or []
    lines.append(f"## 3. Zitierte Datei seit dem Stand geändert ({len(ch)} Dateien)")
    lines.append("")
    lines.append(
        "Schwaches Signal: Die zitierten Zeilen können unverändert sein,"
        " Zeilennummern stimmen aber oft nicht mehr."
    )
    lines.append("")
    for c in ch:
        lines.append(
            f"- `{c['path']}` geändert {iso_to_de(c['changed'])}, betrifft"
            f" {len(c['entries'])}: "
            + "; ".join(_where(e) for e in c["entries"][:8])
            + (" …" if len(c["entries"]) > 8 else "")
        )
    if not ch:
        lines.append("- keine")
    lines.append("")
    unc = sync.get("adr_uncited") or []
    lines.append(f"## 4. ADR ab 020, die die Arbeit nirgends zitiert ({len(unc)})")
    lines.append("")
    lines += [
        f"- ADR {u['adr']:03d} {u['title']}"
        + (f" ({iso_to_de(u['date'])})" if u["date"] else "")
        for u in unc
    ] or ["- keine"]
    lines.append("")
    ns = sync.get("no_stand") or []
    if ns:
        lines.append(f"## 5. Quelle ohne Stand-Datum ({len(ns)})")
        lines.append("")
        lines.append(
            "Ohne Stand kann der Abgleich nur ersetzte ADR melden, keine"
            " geänderten Dateien."
        )
        lines.append("")
        per_file: dict[str, list[str]] = {}
        for n in ns:
            name = str(n["file"]).split("/")[-1].replace(".tex", "")
            per_file.setdefault(name, []).append(str(n["line"]))
        lines += [
            f"- {name}: {len(nums)} (Zeilen {', '.join(nums)})"
            for name, nums in per_file.items()
        ]
        lines.append("")
    un = sync.get("unresolved") or []
    if un:
        lines.append(f"## 6. Zitierte Datei nicht eindeutig gefunden ({len(un)})")
        lines.append("")
        lines.append(
            "Weder im Repo BitGridAI (auch ignorierte Dateien) noch im"
            " Thesis-Ordner, oder mehrfach vorhanden: Pfad im Kommentar"
            " vervollständigen, sonst bleibt die Quelle ungeprüft."
        )
        lines.append("")
        lines += [f"- `{u}`" for u in un]
        lines.append("")
    return "\n".join(lines)


# ── Fahrplan: the open work in the order we tackle it ────────────────────
# Order follows the work loop of the thesis CLAUDE.md (Abschnitt 3): stale
# facts first (prose written on them is wasted), then clarify, verify, take
# over findings, write, check. Parallel and later work after that.
# Sections of notizen/offene_punkte.md are matched by their first word.
SECTION_STEP = {
    "Artur": "klaeren",
    "Schreiben": "prosa",
    "Abbildungen": "prosa",
    "Sitzungsprotokoll-Export": "parallel",
    "SoSci-Export": "parallel",
    "Prof.": "naechste",
    "Prüfungsamt": "fristen",
    "Literatur": "literatur",
    "Auswertung": "freeze",
}
# Card group -> chapter the finding belongs to (thesis_notes "Einordnung").
# Rule of Artur (14.11.2026): measured values and production figures do not
# belong into chapter 4 (system description); they go to methods (5), results
# (6) and limitations (7).
GROUP_CHAPTER = {
    "Befunde aus den Produktivdaten": 6,
    "Datenbasis und Methodik": 5,
    "Erklärschicht (Sprachmodell)": 4,
    "Limitationen, die genannt werden müssen": 7,
}
_KAP = re.compile(r"Kap\.\s*(\d)((?:\s*(?:,|und|\+)\s*\d)*)")


def week_chapters(text: str) -> list[int]:
    """Chapter numbers named in a schedule cell ("Kap. 1, 8, Kurzfassung")."""
    out: list[int] = []
    for first, rest in _KAP.findall(text):
        for n in [first] + re.findall(r"\d", rest):
            if int(n) not in out:
                out.append(int(n))
    return out


def _chapter_of(file: str) -> int | None:
    m = re.match(r"kapitel/0?(\d)_", file)
    return int(m.group(1)) if m else None


MARKER_MAX = 180


_SYMBOLS = {
    r"\kappa": "Kappa",
    r"\rightarrow": "->",
    r"\to": "->",
    r"\glqq": "„",
    r"\grqq": "“",
    r"\_": "_",
    r"\%": "%",
    r"\&": "&",
}


def _plain(tex: str) -> str:
    """Rough LaTeX -> text for a one-line preview (not for the thesis)."""
    for raw, plain in _SYMBOLS.items():
        tex = tex.replace(raw, plain)
    # Inline math keeps its content ("$\kappa$" -> "Kappa"), empty "$$" goes.
    tex = re.sub(r"\$([^$]*)\$", r"\1", tex)
    tex = tex.replace("~", " ").replace("\\,", " ").replace("--", "–")
    tex = re.sub(r"\\(?=\s)", " ", tex)  # backslash-space (after "z. B.")
    tex = re.sub(r"\\c?ref\{[^}]*\}", "(Verweis)", tex)
    tex = re.sub(r"\\cite\w*\{[^}]*\}", "(Quelle)", tex)
    for _ in range(3):
        tex = re.sub(r"\\[a-zA-Z]+\*?\{([^{}]*)\}", r"\1", tex)
    tex = re.sub(r"\\[a-zA-Z]+\*?", "", tex)
    tex = re.sub(r"\s+", " ", tex.replace("{", "").replace("}", "")).strip()
    return tex if len(tex) <= MARKER_MAX else tex[: MARKER_MAX - 1].rstrip() + "…"


_TERMIN = re.compile(r"\(\s*Termin[\s~]+([^)]*)\)")
_DAY_MONTH = re.compile(r"(\d{1,2})\.(?:(\d{1,2})\.(?:(\d{4}))?)?")
# Without a year, a Termin further back than this is read as next year's.
_TERMIN_ROLLOVER = timedelta(days=180)


def parse_termin(text: str, today: date) -> date | None:
    """Last day of a note like "(Termin 17.11.)", "(Termin 16./17.11.)" or
    "(Termin 16.-17.11.)" (slash, hyphen or en dash), optionally with a year.

    A day without month takes the month of the date to its right. Without a
    year the current one is used, or the next if that date lies more than half
    a year back (a "Termin 05.01." written in November means January). None if
    there is no such note or the date does not exist.
    """
    note = _TERMIN.search(text)
    if note is None:
        return None
    found: list[date] = []
    month = year = ""
    for day, mo, yr in reversed(_DAY_MONTH.findall(note.group(1))):
        if mo:
            month, year = mo, yr
        if not month:
            return None
        try:
            when = date(int(year) if year else today.year, int(month), int(day))
            if not year and when < today - _TERMIN_ROLLOVER:
                when = when.replace(year=when.year + 1)
        except ValueError:
            return None
        found.append(when)
    return max(found) if found else None


def marker_items(
    text: str, file: str, today: date | None = None
) -> list[dict[str, Any]]:
    """\\offen{...} and \\pruefen{...} with line and plain text, braces
    balanced (markers span lines and contain \\cref{...}). ``termin`` is the
    ISO date of a "(Termin ...)" note, read from the full text: the preview is
    cut after MARKER_MAX characters and would lose a note at the end."""
    out: list[dict[str, Any]] = []
    for m in re.finditer(r"\\(offen|pruefen)\{", text):
        if text.rfind("%", text.rfind("\n", 0, m.start()) + 1, m.start()) != -1:
            continue  # commented out
        depth, i = 1, m.end()
        while i < len(text) and depth:
            depth += {"{": 1, "}": -1}.get(text[i], 0)
            i += 1
        body = text[m.end() : i - 1]
        termin = parse_termin(body, today or date.today())
        out.append(
            {
                "file": file,
                "line": text.count("\n", 0, m.start()) + 1,
                "kind": m.group(1),
                "text": _plain(body),
                "termin": termin.isoformat() if termin else None,
            }
        )
    return out


def _short(file: Any, line: Any) -> str:
    return f"{str(file).split('/')[-1]}:{line}"


# ── Prose per chapter ────────────────────────────────────────────────────
# The "Schreiben" checkboxes of offene_punkte.md bundle several chapters in one
# line ("Kap. 1 Aufbau, Kap. 2 Synthese, ..."). They are split per chapter, and
# each piece waits for the schedule week of its own chapter instead of blocking
# one collective step.
# Appendices that need no results can be written now, independent of the
# schedule week (Artur, 14.11.2026).
PROSA_ANYTIME = ("F", "H")
# Anhang C is finished (Artur, 14.11.2026), although its checkbox is bundled
# with F and H and not ticked. Drop this entry once the checkbox is split and
# ticked.
PROSA_DONE = ("C",)
_UNIT_HEAD = re.compile(
    r"(?:Kap\.\s*(\d)|Anh(?:ang|\.)\s*([A-J])|(Kurzfassung)|(Abstract))(?!\w)"
)


def split_pieces(text: str) -> list[str]:
    """Split a checklist line at the commas or semicolons (outside brackets)
    that are followed by another unit ("Kap. 2", "Anh. F", "Kurzfassung")."""
    parts: list[str] = []
    depth, start = 0, 0
    for i, ch in enumerate(text):
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth = max(0, depth - 1)
        elif ch in ",;" and depth == 0 and _UNIT_HEAD.match(text[i + 1 :].lstrip()):
            parts.append(text[start:i].strip())
            start = i + 1
    parts.append(text[start:].strip())
    return [p for p in parts if p]


def piece_unit(piece: str) -> tuple[str, str, str] | None:
    """(key, label, rest) of the unit a piece starts with, None if it names
    none. Keys: "kap:5", "anh:F", "kurzfassung", "abstract"."""
    m = _UNIT_HEAD.match(piece)
    if m is None:
        return None
    if m.group(1):
        key, label = f"kap:{m.group(1)}", f"Kap. {m.group(1)}"
    elif m.group(2):
        key, label = f"anh:{m.group(2)}", f"Anh. {m.group(2)}"
    elif m.group(3):
        key, label = "kurzfassung", "Kurzfassung"
    else:
        key, label = "abstract", "Abstract"
    return key, label, piece[m.end() :].strip(" ,;:")


def prosa_row_of(key: str, schedule: list[dict[str, Any]]) -> int | None:
    """Index of the schedule row in which a writing unit is due."""
    for i, row in enumerate(schedule):
        write = str(row.get("write"))
        if key.startswith("kap:") and int(key[4:]) in week_chapters(write):
            return i
        if key == "kurzfassung" and "Kurzfassung" in write:
            return i
        if key == "abstract" and "Abstract" in write:
            return i
        if key.startswith("anh:") and "Anhang" in write:
            return i
    return None


def search_questions(md: str, limit: int = 3) -> list[str]:
    """First numbered items under "## Nächste Suchfragen" of the thesis file
    notizen/literatur_recherche.md (the open search questions)."""
    out: list[str] = []
    inside = False
    for line in md.splitlines():
        if line.startswith("## "):
            inside = line.startswith("## Nächste Suchfragen")
            continue
        m = re.match(r"^\s*\d+\.\s+(.+)$", line) if inside else None
        if m:
            out.append(re.sub(r"[*`]", "", m.group(1)).strip())
    return out[:limit]


def release_check(status: dict[str, Any] | None, drift: bool) -> dict[str, Any]:
    """State of the step "Prüfen, kompilieren, committen" from read-only facts.

    "erledigt" only if check_tex has 0 findings, the sync check shows no drift
    (``drift``), nothing is uncommitted and nothing unpushed. Each unmet
    condition becomes one line (``items``). Compilation is judged from main.log
    if there is one (no "! " line, no "undefined"), otherwise it is listed as
    not checked and does not block. Without ``status`` nothing is claimed.
    """
    if not status:
        return {}
    lines: list[str] = []
    found = status.get("check_tex")
    if found is None:
        lines.append("check_tex: nicht auswertbar")
    elif found:
        lines.append(f"check_tex: {found} Befunde")
    if drift:
        lines.append("Abgleich: neue Meldung (ersetzte ADR oder geänderte Zahlen)")
    n_files = len(status.get("uncommitted") or [])
    if n_files:
        lines.append(f"{n_files} Dateien nicht committet")
    for remote, n in sorted((status.get("unpushed") or {}).items()):
        if n is None:
            lines.append(f"{remote}: Stand nicht lesbar")
        elif n:
            lines.append(f"{n} Commits nicht gepusht ({remote})")
    log = status.get("log")
    if log is None:
        note = "Kompilierung ungeprüft (kein main.log)"
    else:
        note = ""
        if log.get("errors"):
            lines.append(f"main.log: {log['errors']} Fehlerzeilen")
        if log.get("undefined"):
            lines.append(f"main.log: {log['undefined']} Zeilen mit undefined")
    out: dict[str, Any] = {
        "items": [{"text": x, "where": "Bedingung"} for x in lines],
        "state": "offen" if lines else "erledigt",
    }
    if note:
        out["note"] = note
    return out


def plan(data: dict[str, Any], today: date) -> list[dict[str, Any]]:
    """Ordered steps: {key, title, who, why, state, items: [{text, where}]}.

    state: "jetzt" (first step of the chapter pipeline with work, plus every
    independent track that is due), "offen", "erledigt", "parallel",
    "spaeter", "gesperrt" (before the data freeze), "wartet" (every point of
    the step waits for a "(Termin ...)" date; the step then carries
    ``wait_until`` and does not count as "jetzt").
    """
    schedule = data.get("schedule") or []
    now = next((r for r in schedule if r.get("now")), None)
    idx = schedule.index(now) if now else -1
    nxt = schedule[idx + 1] if now and idx + 1 < len(schedule) else None
    chapters = week_chapters(str(now.get("write"))) if now else []
    kap = ", ".join(str(c) for c in chapters) or "?"
    freeze_row = next(
        (r for r in schedule if "Datenfreeze" in str(r.get("parallel"))), None
    )
    frozen = bool(freeze_row and today.isoformat() > str(freeze_row["end"]))

    def flag_wait(item: dict[str, str], when: date | None) -> dict[str, str]:
        """Mark a point that waits for a date, up to and including that day;
        afterwards it counts like any other."""
        if when is not None and when >= today:
            item["wartet_bis"] = when.isoformat()
        return item

    by_step: dict[str, list[dict[str, str]]] = {}
    for sec in data.get("sections") or []:
        name = str(sec.get("section") or "")
        step = SECTION_STEP.get(name.split()[0] if name else "", "sonstiges")
        for item in sec.get("items") or []:
            by_step.setdefault(step, []).append(
                flag_wait(
                    {"text": str(item), "where": name},
                    parse_termin(str(item), today),
                )
            )

    # Prose points per chapter (see PROSA_ANYTIME / PROSA_DONE above).
    pieces_by_row: dict[int, list[tuple[str, dict[str, str]]]] = {}
    anytime: list[dict[str, str]] = []
    done_prosa: list[str] = []
    for item in by_step.pop("prosa", []):
        for part in split_pieces(item["text"]):
            unit = piece_unit(part)
            if unit is None:
                by_step.setdefault("sonstiges", []).append(
                    {"text": part, "where": item["where"]}
                )
                continue
            key, label, rest = unit
            entry = flag_wait(
                {"text": rest or label, "where": label}, parse_termin(part, today)
            )
            if key.startswith("anh:") and key[4:] in PROSA_DONE:
                done_prosa.append(label)
            elif key.startswith("anh:") and key[4:] in PROSA_ANYTIME:
                anytime.append(entry)
            else:
                target = prosa_row_of(key, schedule)
                if target is None:
                    by_step.setdefault("sonstiges", []).append(entry)
                else:
                    pieces_by_row.setdefault(target, []).append((key, entry))

    sync = data.get("sync") or {}
    stale = [
        {
            "text": f"zitiert ADR {int(r['adr']):03d}, gilt ADR {int(r['by']):03d}"
            f" ({r['by_title']})",
            "where": _short(r["file"], r["line"]),
        }
        for r in sync.get("replaced") or []
    ]
    bf = sync.get("befunde") or {}
    for row in bf.get("notes") or []:
        for p in row.get("places") or []:
            if p.get("state") in ("geaendert", "neu_seit_stichtag"):
                stale.append(
                    {
                        "text": f"Befund {row['title']}: Zahlen seit Stichtag"
                        f" {iso_to_de(p.get('stichtag'))} geändert",
                        "where": _short(p["file"], p["line"]),
                    }
                )

    in_week = [
        m
        for m in data.get("marker_items") or []
        if _chapter_of(str(m.get("file"))) in chapters
    ]

    def mark_items(kind: str) -> list[dict[str, str]]:
        return [
            flag_wait(
                {"text": str(m["text"]), "where": _short(m["file"], m["line"])},
                date.fromisoformat(m["termin"]) if m.get("termin") else None,
            )
            for m in in_week
            if m.get("kind") == kind
        ]

    def week_of(chapter: int | None) -> str:
        """Week of the schedule in which the chapter is written."""
        for r in schedule:
            if chapter in week_chapters(str(r.get("write"))):
                return str(r.get("week"))
        return ""

    # Figures change daily: a finding is taken over in the week of its own
    # chapter, with the Stichtag valid then. Only this week's chapter and next
    # week's chapter are worked on now; the rest waits in its own step.
    next_chapters = week_chapters(str(nxt.get("write"))) if nxt else []
    missing = set(bf.get("missing") or [])
    findings_now: list[dict[str, str]] = []
    findings_next: list[dict[str, str]] = []
    findings_far: list[dict[str, str]] = []
    for row in bf.get("notes") or []:
        if row["id"] not in missing:
            continue
        target = GROUP_CHAPTER.get(row["group"])
        # The week is only news for chapters that are not this week's.
        week = week_of(target) if target not in chapters else ""
        where = f"Kap. {target}" + (f" · {week}" if week else "") if target else ""
        item = {
            "text": f"{row['title']} (% Befund: {row['id']})",
            "where": where,
        }
        if target in chapters:
            findings_now.append(item)
        elif target in next_chapters:
            findings_next.append(item)
        else:
            findings_far.append(item)

    today_iso = today.isoformat()
    marker_list = data.get("marker_items") or []

    def open_markers(chs: list[int]) -> list[dict[str, Any]]:
        """Markers of the chapters that block them (a point that waits for a
        Termin does not)."""
        return [
            m
            for m in marker_list
            if _chapter_of(str(m.get("file"))) in chs
            and not (m.get("termin") and str(m["termin"]) >= today_iso)
        ]

    def marker_point(m: dict[str, Any]) -> dict[str, str]:
        return flag_wait(
            {
                "text": str(m["text"]),
                "where": _short(m["file"], m["line"]),
                # \offen = a decision only Artur can make, \pruefen = Claude
                # checks against the source.
                "am_zug": "Artur" if m.get("kind") == "offen" else "Claude",
            },
            date.fromisoformat(m["termin"]) if m.get("termin") else None,
        )

    def prosa_drafts(chs: list[int]) -> int:
        """\\prosa marks a draft written by Claude that Artur has to adapt."""
        return sum(
            int(m.get("prosa") or 0)
            for m in data.get("markers") or []
            if _chapter_of(str(m.get("file"))) in chs
        )

    def prosa_step(i: int, row: dict[str, Any]) -> dict[str, Any] | None:
        """Prose step of one schedule row; None if the row names no chapter.

        Done when its chapter files hold no open marker (\\offen or \\pruefen
        without Termin) and no extra unit (Kurzfassung, Abstract, Anhang) is
        left. \\prosa does not count. Before the week of the row the step is
        "spaeter", from then on "jetzt" (the current row follows the order of
        the pipeline).
        """
        write = str(row.get("write"))
        chs = week_chapters(write)
        extras = [w for w in ("Kurzfassung", "Abstract", "Anhang") if w in write]
        if not chs and not extras:
            return None
        current = bool(row.get("now"))
        pieces = pieces_by_row.get(i, [])
        counted = [p for u, p in pieces if not u.startswith("kap:")]
        blocking = open_markers(chs)
        started = today_iso >= str(row.get("start"))
        # Markers of the current chapter belong to the steps before (klaeren,
        # belegen); without points of its own the prose step is rated alone.
        done = started and not counted and (not blocking or (current and not pieces))
        week = str(row.get("week"))
        parts = ([f"Kap. {', '.join(str(c) for c in chs)}"] if chs else []) + extras
        if not started:
            why = (
                f"Ab {iso_to_de(str(row.get('start')))[:6]} laut Zeitplan"
                f" ({week}); bis dahin später."
            )
        else:
            n_off = sum(1 for m in blocking if m.get("kind") == "offen")
            summary = (
                f"{len(blocking)} Marker im Text ({n_off} offen,"
                f" {len(blocking) - n_off} prüfen)"
                if blocking
                else "keine offenen Marker mehr im Text"
            )
            if done and blocking:
                summary = (
                    f"keine eigenen Punkte mehr, {len(blocking)} Marker stehen"
                    " in den Schritten davor"
                )
            why = f"Zeitplan {week}: {summary}."
            drafts = prosa_drafts(chs)
            if drafts:
                why += (
                    f" {drafts} Stellen mit \\prosa (Claude-Entwurf, von dir"
                    " anzupassen) zählen hier nicht."
                )
        stale_boxes = [f"{p['where']} {p['text']}".strip() for u, p in pieces]
        if done and stale_boxes:
            why += (
                " Checkbox in offene_punkte.md noch nicht abgehakt: "
                + "; ".join(stale_boxes)
                + "."
            )
        if not started:
            items = [p for _, p in pieces]
        elif done:
            items = []
        elif current:
            items = [p for _, p in pieces]
        else:
            items = [marker_point(m) for m in blocking] + counted
        step: dict[str, Any] = {
            "key": "prosa" if current else f"prosa_{i}",
            "title": f"{', '.join(parts)}: Prosa schreiben",
            "who": "Artur, auf Wunsch mit Claude-Entwurf",
            "why": why,
            "items": items,
        }
        if done:
            step["state"] = "erledigt"
        elif not started:
            step["state"] = "spaeter"
        elif not current:
            step["state"] = "jetzt"
        # A current row that is not done gets "jetzt" or "offen" below, in the
        # order of the pipeline.
        return step

    row_steps: list[dict[str, Any]] = []
    prosa_now: dict[str, Any] | None = None
    for i, r in enumerate(schedule):
        built = prosa_step(i, r)
        if built is None:
            continue
        if r.get("now"):
            prosa_now = built
        else:
            row_steps.append(built)
    if prosa_now is None:
        prosa_now = {
            "key": "prosa",
            "title": f"Kap. {kap}: Prosa schreiben",
            "who": "Artur, auf Wunsch mit Claude-Entwurf",
            "why": "",
            "items": [],
            "state": "erledigt",
        }

    # Appendices that need no results: due now, whatever the week.
    letters = tuple(f"anhang/{x.lower()}_" for x in PROSA_ANYTIME)
    for it in anytime:
        # A checkbox point whose draft stands waits for Artur's decision.
        it["am_zug"] = "Artur" if "Entwurf steht" in it["text"] else "Claude"
    fh_items = anytime + [
        marker_point(m) for m in marker_list if str(m.get("file")).startswith(letters)
    ]
    fh_why = "Brauchen keine Ergebnisse, daher unabhängig von der Kapitelwoche."
    if done_prosa:
        fh_why += (
            f" {', '.join(done_prosa)} ist erledigt (Artur, 14.11.2026); die"
            " Checkbox in offene_punkte.md ist noch nicht abgehakt."
        )
    fh_step: dict[str, Any] = {
        "key": "anhang_fh",
        "title": f"Anhang {' und '.join(PROSA_ANYTIME)}: Prosa schreiben",
        "who": "Artur, auf Wunsch mit Claude-Entwurf",
        "why": fh_why,
        "items": fh_items,
        "state": "jetzt" if fh_items else "erledigt",
    }
    if fh_items and all(i.get("am_zug") == "Artur" for i in fh_items):
        # Only decisions left, the drafts stand: nothing for Claude to do now.
        fh_step["state"] = "wartet"
        fh_step["wait_who"] = "Artur"

    # Literature research on tone, persona and anthropomorphism (biggest risk):
    # "jetzt" from the schedule row that names it.
    lit_row = next(
        (r for r in schedule if "Literaturrecherche" in str(r.get("parallel"))), None
    )
    lit_items = [
        {"text": q, "where": f"Suchfrage {n}"}
        for n, q in enumerate(data.get("literatur_fragen") or [], start=1)
    ]
    lit_started = lit_row is not None and today_iso >= str(lit_row.get("start"))
    lit_why = (
        "Größtes Risiko, dauert am längsten. Claude prüft Quellen vor Nutzung:"
        " erst nennen, wenn Titel, Venue, Jahr und DOI an einer zweiten Stelle"
        " bestätigt sind."
    )
    if lit_row is not None and not lit_started:
        lit_why += f" Start laut Zeitplan: {iso_to_de(str(lit_row.get('start')))[:6]}"
    lit_step: dict[str, Any] = {
        "key": "literatur_tonalitaet",
        "title": "Literaturrecherche Tonalität, Persona, Anthropomorphismus",
        "who": "Artur mit Claude",
        "why": lit_why,
        "items": lit_items,
        "state": (
            "erledigt" if not lit_items else "jetzt" if lit_started else "spaeter"
        ),
    }

    release_state = release_check(data.get("tex_status"), bool(stale))
    steps: list[dict[str, Any]] = [
        {
            "key": "veraltet",
            "title": "Veraltete Stellen korrigieren",
            "who": "Claude markiert, Artur entscheidet",
            "why": "Wer auf überholten Fakten formuliert, schreibt doppelt.",
            "items": stale,
        },
        {
            "key": "klaeren",
            "title": f"Kap. {kap}: offene Fragen klären",
            "who": "Artur",
            "why": "Fakten und Entscheidungen, die nur du kennst (OFFEN im Text).",
            "items": mark_items("offen") + by_step.get("klaeren", []),
        },
        {
            "key": "belegen",
            "title": f"Kap. {kap}: Stellen belegen",
            "who": "Claude prüft gegen die Quelle, Artur bestätigt",
            "why": "PRÜFEN im Text: erst belegt, dann ausformuliert.",
            "items": mark_items("pruefen"),
        },
        {
            "key": "befunde",
            "title": f"Kap. {kap}: Befunde aus der Forschung übernehmen",
            "who": "Claude setzt Marker, Artur wählt aus",
            "why": "Jede Produktivzahl mit Befund-ID und Stichtag.",
            "items": findings_now,
        },
        prosa_now,
        {
            "key": "pruefen",
            "title": "Prüfen, kompilieren, committen",
            "who": "Claude prüft und kompiliert, Artur committet",
            "why": " ".join(
                [
                    "check_tex.py meldet 0 Befunde, Abgleich ohne neue Meldung,"
                    " alles committet und gepusht.",
                    str(release_state.pop("note", "")),
                ]
            ).strip(),
            "items": [],
            **release_state,
        },
        fh_step,
        {
            "key": "parallel",
            "title": "Parallel: " + (str(now.get("parallel")) if now else "Studie"),
            "who": "Artur",
            "why": "Läuft neben dem Schreiben, muss vor dem Datenfreeze fertig sein.",
            "items": by_step.get("parallel", []),
        },
        lit_step,
        {
            "key": "naechste",
            "title": "Vorbereiten: "
            + (f"{nxt['write']} ({nxt['week']})" if nxt else "nächste Woche"),
            "who": "Artur mit Claude",
            "why": f"Parallel dann: {nxt['parallel']}" if nxt else "",
            "items": by_step.get("naechste", []) + findings_next,
        },
        {
            "key": "literatur",
            "title": "Literatur recherchieren",
            "who": "Artur mit Claude",
            "why": (
                "Kap. 2 und 3 hängen daran; Quellen vor Nutzung prüfen, keine"
                " Quelle zitieren, die nicht nachweislich existiert."
            ),
            "items": by_step.get("literatur", []),
        },
        {
            "key": "spaeter_befunde",
            "title": "Befunde später übernehmen",
            "who": "Claude setzt Marker, Artur wählt aus",
            "why": (
                "Die Zahlen ändern sich täglich: erst in der Woche des Kapitels"
                " übernehmen, mit dem dann gültigen Stichtag."
            ),
            "items": findings_far,
        },
        *row_steps,
        {
            "key": "fristen",
            "title": "Hochschule",
            "who": "Artur",
            "why": "Fristen laut Zeitplan, nichts davon blockiert das Kapitel.",
            "items": by_step.get("fristen", []),
        },
        {
            "key": "freeze",
            "title": "Nach dem Datenfreeze: Auswertung",
            "who": "Artur mit Claude",
            "why": (
                f"Datenfreeze {freeze_row['week']}"
                if freeze_row
                else "Erst mit eingefrorenen Daten."
            ),
            "items": by_step.get("freeze", []),
        },
    ]
    if by_step.get("sonstiges"):
        steps.append(
            {
                "key": "sonstiges",
                "title": "Sonstiges",
                "who": "Artur",
                "why": "",
                "items": by_step["sonstiges"],
            }
        )
    first = True
    for s in steps:
        waits = [i["wartet_bis"] for i in s["items"] if i.get("wartet_bis")]
        if s["key"] == "freeze" and not frozen:
            s["state"] = "gesperrt"
        elif waits and len(waits) == len(s["items"]):
            # Every point waits for a date: no work now, "jetzt" moves on.
            s["state"] = "wartet"
            s["wait_until"] = min(waits)
        elif "state" in s:
            pass  # set by the step itself (prose rows, appendices, research)
        elif s["key"] == "parallel":
            s["state"] = "parallel" if s["items"] else "erledigt"
        elif s["key"] in (
            "naechste",
            "literatur",
            "spaeter_befunde",
            "fristen",
            "sonstiges",
        ):
            s["state"] = "spaeter" if s["items"] else "erledigt"
        elif s["key"] == "pruefen":
            s["state"] = "offen"
        elif s["items"] or s["key"] == "prosa":
            s["state"] = "jetzt" if first else "offen"
            first = False
        else:
            s["state"] = "erledigt"
    return steps
