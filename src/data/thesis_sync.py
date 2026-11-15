"""
Thesis sync check: which entries of the thesis draft rest on a source that
changed after the entry was last checked, and which findings of the
"Masterarbeit" card are cited in the text.

The thesis draft marks every entry with comment lines (convention in the
head of kapitel/04_system.tex):

    % Quelle: mvp_auto.yaml Z. 734-802; ADR 027 (10 % + 5 %)
    % Stand: 02.11.2026 neu
    % Befund: schaltwechsel (Stichtag 14.11.2026)
    % Befund: protokoll (Stichtag 14.11.2026, ohne Zahlen)

From these comments alone, without a language model, this module derives:

  - ``replaced``: the entry cites an ADR that a later ADR replaces
    (``**Ersetzt teilweise:** ADR 028`` in its head line). Strong signal.
  - ``changed``: a cited repo file changed after the entry's Stand date.
    Weak signal: the cited lines may be untouched, but line numbers in
    "Z. 734-802" are likely off. The ADR file itself is checked per ADR.
  - ``befunde``: per card note, where the text cites it, and whether its
    wording (numbers) differs from the snapshot of the cited Stichtag.
    With ", ohne Zahlen" the text took over only the statements, not the
    running counters: digits and dates are masked before comparing, so the
    finding counts as changed only when its statement changes.

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
_BEFUND = re.compile(
    r"([a-z0-9_]+)(?:\s*\(Stichtag\s+(\d{1,2}\.\d{1,2}\.\d{4})"
    r"(\s*,\s*ohne\s+Zahlen)?\))?"
)
# Digits and dates of a finding, masked for "ohne Zahlen" (14.11.2026,
# 1.234,5 kWh, 23 %, 03:50).
_NUMBERS = re.compile(r"\d+(?:[.,:]\d+)*")


def without_numbers(text: str) -> str:
    """Text with every number and date replaced by "#"."""
    return _NUMBERS.sub("#", text)


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
    # Befund ids cited "ohne Zahlen" (all their markers in this block).
    ohne_zahlen: set[str] = field(default_factory=set)


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
                for bid, stichtag, plain in _BEFUND.findall(value):
                    iso = de_to_iso(stichtag)[0] if stichtag else None
                    old = next((b for b in block.befunde if b[0] == bid), None)
                    if old is None:
                        block.befunde.append((bid, iso))
                        if plain:
                            block.ohne_zahlen.add(bid)
                        continue
                    # The same finding twice in one block is one place: the
                    # newest Stichtag counts, "ohne Zahlen" only if every
                    # marker says so (15.11.2026, reported once).
                    newest = (
                        max(d for d in (old[1], iso) if d) if (old[1] or iso) else None
                    )
                    block.befunde[block.befunde.index(old)] = (bid, newest)
                    if not plain:
                        block.ohne_zahlen.discard(bid)
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
            place: dict[str, Any] = {"file": e.file, "line": e.line, "stichtag": when}
            if bid in e.ohne_zahlen:
                place["ohne_zahlen"] = True
            if bid not in by_id:
                unknown.append({"id": bid, **place})
                continue
            snap = {n.get("id"): n for n in snapshots.get(when or "", [])}
            if not when or when not in snapshots:
                place["state"] = "ohne_abzug"
            elif bid not in snap:
                place["state"] = "neu_seit_stichtag"
            elif (
                without_numbers(snap[bid]["text"])
                != without_numbers(by_id[bid]["text"])
                if bid in e.ohne_zahlen
                else snap[bid]["text"] != by_id[bid]["text"]
            ):
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
    "Prof.": "wallach",
    "Prüfungsamt": "fristen",
    "Literatur": "literatur",
    "Auswertung": "freeze",
}
# Card group -> chapter the finding belongs to (thesis_notes "Einordnung").
# Rule of Artur (14.11.2026), relaxed 15.11.2026: measured values belong into
# chapter 4 (system description) only where a design decision follows from
# them (group "Systementwurf"); all other production figures go to methods (5),
# results (6) and limitations (7).
# Artur, 15.11.2026 (variant b): the production plant is context only, no
# result strand of its own, so its findings go to the discussion (7), not to
# the results (6). The finding "datenbasis" is done for chapter 5 (stimulus
# data base, sec:stimulus); its rest (whole period, quality) is an \offen in
# sec:limitationen and needs no second finding marker.
GROUP_CHAPTER = {
    "Systementwurf (Messwerte hinter Designentscheidungen)": 4,
    "Befunde aus den Produktivdaten": 7,
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


_LABEL = re.compile(r"\\label\{((?:chap|anhang):[^}]*)\}")


def label_units(texts: dict[str, str]) -> dict[str, str]:
    """Chapter and appendix labels -> "Kap. N" / "Anhang X", taken from the
    file the label sits in (kapitel/06_... -> Kap. 6, anhang/h_... -> Anhang H)."""
    out: dict[str, str] = {}
    for file, text in texts.items():
        ch = _chapter_of(file)
        m = re.match(r"anhang/([a-z])_", file)
        unit = f"Kap. {ch}" if ch else f"Anhang {m.group(1).upper()}" if m else None
        if unit:
            for lab in _LABEL.findall(text):
                out[lab] = unit
    return out


def _plain(tex: str, labels: dict[str, str] | None = None) -> str:
    """Rough LaTeX -> text for a one-line preview (not for the thesis).
    ``labels`` resolves \\cref to a known chapter or appendix."""
    if labels:
        tex = re.sub(
            r"\\[cC]?ref\{([^},]*)\}",
            lambda m: labels.get(m.group(1), m.group(0)),
            tex,
        )
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
    text: str,
    file: str,
    today: date | None = None,
    labels: dict[str, str] | None = None,
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
                "text": _plain(body, labels),
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


def release_check(
    status: dict[str, Any] | None, drift: bool, hints: list[str] | None = None
) -> dict[str, Any]:
    """State of the step "Prüfen, kompilieren, committen" from read-only facts.

    "erledigt" only if check_tex has 0 findings, the sync check shows no drift
    (``drift``), nothing is uncommitted, nothing is unpushed (against overleaf,
    where the pushes go) and GitHub, read only, has the same commit. Each unmet
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
    unpushed = status.get("unpushed")
    if unpushed is None:
        lines.append("Push-Stand (overleaf) nicht lesbar")
    elif unpushed:
        lines.append(f"{unpushed} Commits nicht gepusht")
    if status.get("github_differs"):
        lines.append("GitHub-Stand weicht ab")
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
    if hints:
        note = " ".join([note] + [f"Hinweis, blockiert nicht: {h}." for h in hints])
    if note:
        out["note"] = note.strip()
    return out


# Words in a point that mean it waits for something outside the writing
# (Artur, 14.11.2026). First match wins; checked in this order.
WAIT_REASONS = {
    "Wallach": "Wallach",
    "Nachtrag": "Wallach",
    "Transkript": "Daten",
    "Wer codiert": "Person",
    "Rater benennen": "Person",
    # 15.11.2026: "\offen{... nach dem Datenfreeze ...}" waits for the data,
    # not for Artur ("vor dem Datenfreeze" does not match).
    "nach dem Datenfreeze": "Datenfreeze",
}


# Points that belong to another step than their section says (Artur,
# 14.11.2026): the analysis is prepared now on synthetic data, not after the
# data freeze. First match wins.
ITEM_ROUTE: list[tuple[str, str]] = [
    ("study_analysis", "auswertung_vorb"),
    ("Antwortcodes SUS und TiA", "auswertung_vorb"),
]
# Points of the SoSci section that need the SoSci data, which only Annika can
# download (the project is in her account).
NEEDS_SOSCI_DATA: tuple[str, ...] = (
    "Datum der Korrektur von Aufgabe 1",
    "Finale Fragebogen-PDF",
)
# Points of the SoSci section that are a question for Wallach (15.11.2026:
# the index was not given to VP01 to VP04, whether to drop it is his call).
NEEDS_WALLACH: tuple[str, ...] = ("Index für Textverständnis",)
# Groups of the step "Parallel: Erhebung", in display order.
GROUP_LAB = "Lab-Export (16./17.11.)"
_EXPORT_DAYS = re.compile(r"\d{1,2}\.(?:\s*[/–-]\s*\d{1,2}\.)?\d{1,2}\.(?:\d{4})?")
GROUP_SOSCI = "SoSci (über Annika)"
GROUP_MEDIA = "Fotos und Screenshots"
MEDIA_WORDS = ("Screenshot", "Foto")

# Points of the section "Prüfungsamt und Hochschule" that have a step of their
# own (Artur, 15.11.2026). Matched on the start of the point, and only in that
# section: the Wallach section also starts a point with "Extended Summary".
FRISTEN_ROUTE: list[tuple[str, str]] = [
    ("Extended Summary", "summary"),
    ("Kolloquium", "kolloquium"),
    ("Anlagen", "anlagen"),
    ("Anhang J", "anhang_j"),
]
# Appendices and front matter without a step of their own (their markers go
# to the step "Weitere Anhänge und Formalia").
OTHER_APPENDICES = ("B", "C", "D", "E", "G", "I")
FRONT_MATTER = ("titelseite", "eid")
_FIG_BOX = re.compile(r"^- \[ \] (.+)$")
_FIG_ROW = re.compile(r"^\|([^|]*)\|([^|]*)\|([^|]*)\|.*\|\s*offen\s*\|\s*$")


def figure_points(md: str) -> list[dict[str, str]]:
    """Open points of notizen/abbildungsliste.md: unchecked boxes and table
    rows whose status column is "offen"."""
    out: list[dict[str, str]] = []
    for line in md.splitlines():
        box = _FIG_BOX.match(line.strip())
        if box:
            out.append(
                {
                    "text": re.sub(r"[*`]", "", box.group(1)).strip(),
                    "where": "Fotoliste",
                }
            )
            continue
        row = _FIG_ROW.match(line.strip())
        if row:
            label, chapter, what = (c.strip().strip("`") for c in row.groups())
            out.append(
                {
                    "text": (
                        f"{what} {label}"
                        if label.startswith("(")
                        else f"{what} ({label})"
                    ),
                    "where": (
                        f"Kap. {chapter}" if chapter.isdigit() else f"Anh. {chapter}"
                    ),
                }
            )
    return out


# The data freeze as a step: export, back up, record, only then unlock the lab.
# (text, waits for, tip). Done when DATENFREEZE_RECORD exists.
DATENFREEZE_RECORD = "data/study/datenfreeze.txt"
DATENFREEZE_PLAN: tuple[tuple[str, str, str], ...] = (
    (
        "Sitzungsprotokoll nach VP16 aus dem Labornetz exportieren"
        " (export_studie_protokoll.py, zweiter Export)",
        "",
        "Nur im Labornetz möglich; schreibt sitzungen.csv, exposition.csv und"
        " eingaben.csv nach data/study/.",
    ),
    (
        "SoSci-Export aller 16 Personen ziehen (CSV mit Variablenansicht)",
        "Annika",
        "Das Projekt liegt in Annikas Account; MODE und K001 müssen mit drin"
        " sein, sonst fehlen Pretest-Kennung und Reihenfolge.",
    ),
    (
        "Backup der Lab-Datenbank von Home Assistant am selben Tag",
        "",
        "Die Rohdaten hinter dem Sitzungsprotokoll: fällt später beim Export"
        " etwas auf, lässt sich neu exportieren.",
    ),
    (
        "Dateien mit Datum und SHA-256 in " + DATENFREEZE_RECORD + " festhalten,"
        " schreibgeschützt ablegen",
        "",
        "Unter Windows: certutil -hashfile <Datei> SHA256. Datum und Dateiliste"
        " auch in Kap. 5 nennen, dann ist der Freeze nachprüfbar.",
    ),
    (
        "Erst danach die Lab-Sperre aufheben (LAB_LOCK in deploy_ha_lab.py)",
        "",
        "Nur mit deiner ausdrücklichen Freigabe; bis dahin bleibt das Lab auf"
        " dem Stand der Erhebung.",
    ),
)
# Chapters whose prose needs the frozen study data.
RESULT_CHAPTERS = (6,)
SUMMARY_MIN_WORDS = 5000
SUMMARY_TEX = "anhang/a_extended_summary.tex"
# Halves of the Extended Summary as in the schedule (07.–13.12. and
# 21.12.–03.01.); the target words come from the budgets in the file.
SUMMARY_HALVES = ((2, 3, 4, 5), (1, 6, 7, 8))
# The colloquium may take place after two thirds of the time (§ 11 Abs. 1 AMPO).
KOLLOQUIUM_FROM = date(2026, 11, 15)
KOLLOQUIUM_PLAN = (
    "Vortrag 20 Min. gliedern (Frage, System, Studie, Ergebnis, Grenzen)",
    "Befragung 20 Min. vorbereiten",
    "Fragenkatalog aus den Limitationen ableiten (Kap. 7, sec:limitationen)",
    "Termin mit Wallach und Conrad abstimmen",
)
# Cleaned export of the code as appendix of the submission.
ANLAGEN_FRIST = "2027-01-10"
ANLAGEN_PLAN = (
    "BitGridAI-Code exportieren ohne IP-Adressen, Hostnamen und Tokens",
    "keine privaten Hausdaten (bitgrid.db, Grundriss mit Namen, Wallet)",
    "keine Rohdaten der Teilnehmenden (SoSci, Sitzungsexport)",
    "LaTeX-Quellen und erstellte Dokumente beilegen",
)
# Files whose change can make the explanation texts of the thesis stale
# (Kap. 4, Anhang C, docs/thesis/studie/hamster_texte_ab_vergleich.md).
EXPLAIN_SOURCES = (
    "bitgrid_dashboard_v3.yaml",
    "bitgrid_dashboard_v3_3.yaml",
    "mvp_auto.yaml",
    "build_sim_day.py",
    "lab_studie.yaml",
)
# First lab session with v3 texts; the lab stays on that version up to VP16.
LAB_STUDY_START = "2026-10-20"
# Analysis prepared on synthetic data (Artur, 15.11.2026): each part is done
# when its code is in the repository. (label, file, text that proves it,
# words of an open point the part covers.)
AUSWERTUNG_PARTS: tuple[tuple[str, str, str, str], ...] = (
    (
        "study_analysis.py auf within umbauen",
        "src/sim/study_analysis.py",
        "def run_within_tests",
        "auf within umstellen",
    ),
    (
        "Umcodierung SUS/TiA (Codes 1, 3, 4, 5, 2 auf 1 bis 5)",
        "src/sim/study_sosci.py",
        "LIKERT_RECODE",
        "Antwortcodes SUS und TiA",
    ),
    (
        "Power für den gepaarten Test neu rechnen",
        "src/sim/study_analysis.py",
        "def paired_power",
        "Power",
    ),
    (
        "Sensitivität: nur 1. Durchlauf, 8 gegen 8",
        "src/sim/study_analysis.py",
        "Sensitivität: nur 1. Durchlauf",
        "",
    ),
    (
        "Reihenfolgeeffekt (AB gegen BA)",
        "src/sim/study_analysis.py",
        "Reihenfolge: Differenz",
        "",
    ),
)
# Sections of the card (Artur, 15.11.2026: "zu gequetscht").
PHASE_WEEK = "Diese Woche"
PHASE_CHAPTERS = "Kapitel"
PHASE_SIDE = "Nebenher"
PHASE_SUBMIT = "Hochschule und Abgabe"
_SUMMARY_SECTION = re.compile(r"\\section\{([^}]*)\}")
_SUMMARY_BUDGET = re.compile(
    r"Wortbudget ca\.\s*([\d.]+);\s*entspricht \\cref\{(chap:[^}]+)\}"
)
_LIT_OPEN = re.compile(r"Literatur|Quelle|Recherche|Studien")


def _uncomment(tex: str) -> str:
    """TeX without comments (an escaped \\% stays)."""
    return "\n".join(re.split(r"(?<!\\)%", ln)[0] for ln in tex.splitlines())


def summary_parts(
    tex: str,
    chapter_of_label: dict[str, int],
    count: Callable[[str], int] | None = None,
) -> list[dict[str, Any]]:
    """Parts of the Extended Summary: {title, chapter, budget, words}.

    One part per \\section with a comment "Wortbudget ca. N; entspricht
    \\cref{chap:x}". ``count`` is the word count of check_tex.py (body text
    only); without it, whitespace words of the uncommented text.
    """
    count = count or (lambda t: len(_uncomment(t).split()))
    heads = list(_SUMMARY_SECTION.finditer(tex))
    out: list[dict[str, Any]] = []
    for n, h in enumerate(heads):
        end = heads[n + 1].start() if n + 1 < len(heads) else len(tex)
        body = tex[h.end() : end]
        b = _SUMMARY_BUDGET.search(body)
        if b is None:
            continue
        out.append(
            {
                "title": h.group(1),
                "chapter": chapter_of_label.get(b.group(2)),
                "budget": int(b.group(1).replace(".", "")),
                "words": count(body),
            }
        )
    return out


def chapter_labels(texts: dict[str, str]) -> dict[str, int]:
    """chap:x label -> chapter number, from the chapter files."""
    out: dict[str, int] = {}
    for file, text in texts.items():
        ch = _chapter_of(file)
        m = re.search(r"\\label\{(chap:[^}]+)\}", text)
        if ch is not None and m:
            out[m.group(1)] = ch
    return out


def _section_body(text: str, title_start: str) -> str:
    """Text of the \\section whose title starts with ``title_start``."""
    m = re.search(r"\\section\{" + re.escape(title_start), text)
    if m is None:
        return ""
    nxt = re.search(r"\\section\{", text[m.end() :])
    return text[m.start() : m.end() + nxt.start()] if nxt else text[m.start() :]


def literature_gaps(texts: dict[str, str], bib_keys: set[str]) -> list[dict[str, str]]:
    """Where the literature is not done yet (Artur, 15.11.2026).

    Kap. 2 (section on language style, tone and persona) and Kap. 3 each need
    at least one \\cite of a key in references.bib and no \\offen about the
    literature (Literatur, Quelle, Recherche, Studien).
    """
    gaps: list[dict[str, str]] = []
    places = []
    for file, text in texts.items():
        if file.startswith("kapitel/02_"):
            places.append(
                ("Kap. 2, Sprachstil", file, _section_body(text, "Sprachstil"))
            )
        elif file.startswith("kapitel/03_"):
            places.append(("Kap. 3", file, text))
    for label, file, body in places:
        if not body:
            continue
        uncommented = _uncomment(body)
        cited = {
            k.strip()
            for group in re.findall(r"\\cite[a-z]*\{([^}]*)\}", uncommented)
            for k in group.split(",")
        }
        if not cited & bib_keys:
            gaps.append(
                {"text": "zitiert noch keine Quelle aus references.bib", "where": label}
            )
        for item in marker_items(body, file):
            if item.get("kind") == "offen" and _LIT_OPEN.search(str(item["text"])):
                gaps.append({"text": str(item["text"]), "where": label})
    return gaps


def auswertung_status(sources: dict[str, str]) -> list[dict[str, Any]]:
    """Parts of the analysis preparation with done = code is present."""
    return [
        {
            "text": label,
            "where": file.split("/")[-1],
            "done": needle in sources.get(file, ""),
            "covers": covers,
        }
        for label, file, needle, covers in AUSWERTUNG_PARTS
    ]


# "(Frist TT.MM.)" or "..., Frist TT.MM.)": done by that day. Highlighted
# from FRIST_WARN_DAYS before, "überfällig" afterwards.
_FRIST = re.compile(r"Frist[\s~]+(\d{1,2})\.(\d{1,2})\.(\d{4})?")
FRIST_WARN_DAYS = 3


def parse_frist(text: str, today: date) -> date | None:
    """Day by which a point must be done, from "Frist 19.11." in its text.
    Without a year the current one, or the next if it lies more than half a
    year back. None if there is none or the date does not exist."""
    m = _FRIST.search(text)
    if m is None:
        return None
    day, month, year = m.groups()
    try:
        when = date(int(year) if year else today.year, int(month), int(day))
    except ValueError:
        return None
    if not year and when < today - _TERMIN_ROLLOVER:
        when = when.replace(year=when.year + 1)
    return when


def frist_due(item: dict[str, Any], today: date) -> bool:
    """True from FRIST_WARN_DAYS days before the Frist on (and when overdue)."""
    f = item.get("frist")
    return bool(f) and date.fromisoformat(str(f)) - today <= timedelta(
        days=FRIST_WARN_DAYS
    )


# Weekly meeting with Prof. Wallach (Artur, 14.11.2026): Wednesday.
MEETING_WEEKDAY = 2


def next_meeting(today: date) -> date:
    """Next meeting day, today included."""
    return today + timedelta(days=(MEETING_WEEKDAY - today.weekday()) % 7)


def freeze_check(
    data: dict[str, Any], today: date, code_open: list[dict[str, str]] | None = None
) -> dict[str, Any]:
    """What must be decided before the data freeze (Nachtrag 2), and when.

    Deterministic list, no model involved: the open markers of the
    preregistration appendix (anhang/f_...), every open point that names the
    Nachtrag, and the decisions the analysis code still lacks (``code_open``,
    from study_sosci.open_decisions). ``freeze`` is the last day of the
    schedule row that names the data freeze; ``meetings`` are the meeting days
    from today up to it.
    """
    row = next(
        (
            r
            for r in data.get("schedule") or []
            if "Datenfreeze" in str(r.get("parallel"))
        ),
        None,
    )
    freeze = date.fromisoformat(str(row["end"])) if row and row.get("end") else None
    meetings: list[str] = []
    if freeze is not None:
        day = next_meeting(today)
        while day <= freeze:
            meetings.append(day.isoformat())
            day += timedelta(days=7)

    def who(text: str, kind: str = "offen") -> str:
        return wait_reason(text) or ("Artur" if kind == "offen" else "Claude")

    items: list[dict[str, str]] = []
    seen: set[str] = set()
    for m in data.get("marker_items") or []:
        if str(m.get("file", "")).startswith("anhang/f_"):
            text = str(m.get("text"))
            seen.add(text[:60])
            items.append(
                {
                    "text": text,
                    "where": _short(m.get("file"), m.get("line")),
                    "am_zug": who(text, str(m.get("kind"))),
                    "quelle": "Präregistrierung",
                }
            )
    for sec in data.get("sections") or []:
        for raw in sec.get("items") or []:
            text = str(raw)
            if "Nachtrag" in text and text[:60] not in seen:
                seen.add(text[:60])
                section = str(sec.get("section") or "")
                # Naming the Nachtrag alone does not make it Wallach's point.
                wallach = "Wallach" in text or section.startswith("Prof.")
                items.append(
                    {
                        "text": text,
                        "where": section,
                        "am_zug": "Wallach" if wallach else "Artur",
                        "quelle": "offene Punkte",
                    }
                )
    # Decisions that offene_punkte.md does not list yet (list_gaps).
    for gap in data.get("list_gaps") or []:
        if "Nachtrag" in gap["text"] and gap["text"][:60] not in seen:
            items.append(
                {
                    "text": gap["text"],
                    "where": gap["where"],
                    "am_zug": "Wallach",
                    "quelle": "fehlt in offene_punkte.md",
                }
            )
    for c in code_open or []:
        items.append({**c, "am_zug": "Artur", "quelle": "Auswertungscode"})
    return {
        "freeze": freeze.isoformat() if freeze else None,
        "days_left": (freeze - today).days if freeze else None,
        "meetings": meetings,
        "items": items,
    }


def wait_reason(text: str) -> str | None:
    """ "Wallach", "Daten", "Person" or "Datenfreeze" if the point waits for
    that, else None (case-insensitive)."""
    low = text.lower()
    for word, who in WAIT_REASONS.items():
        if word.lower() in low:
            return who
    return None


# "So gehst du vor" per step: the concrete way for this thesis, as numbered
# steps (Artur, 15.11.2026: "die Lösung, wie ich das mache", checked against
# the thesis CLAUDE.md and notizen/stilleitfaden.md). `code` is shown as code
# on the card. "Thesis-Fenster" = Claude Code in C:\DEV\BitGridAI-Masterarbeit,
# "Dev-Fenster" = Claude Code in C:\DEV\BitGridAI.
STEP_TIPS: dict[str, list[str]] = {
    "veraltet": [
        "Jeder Punkt nennt Datei:Zeile und was sich geändert hat (ersetzte ADR"
        " oder neue Befund-Zahlen).",
        "Im Thesis-Fenster: „Stelle X gegen ADR Y prüfen“. Claude liest die neue"
        " Quelle und passt den Satz an, du prüfst den Diff.",
        "Danach steht `% Stand: TT.MM.JJJJ geprüft` (bei Befunden der neue"
        " Stichtag); beim nächsten Export fällt die Meldung weg.",
        "Übernimmt der Text nur die Aussage, nicht die Zahl: Marker als"
        " `% Befund: ID (Stichtag TT.MM.JJJJ, ohne Zahlen)` setzen, dann gibt es"
        " keinen täglichen Alarm mehr.",
    ],
    "klaeren": [
        "Jeder Punkt ist ein `\\offen{…}`: ein Fakt oder eine Entscheidung, die"
        " nur du kennst.",
        "Im Thesis-Fenster die Antwort als Stichwort geben, z. B. „Exponat:"
        " Anschauungsobjekt, nicht eingebunden“.",
        "Claude schreibt sie ein, setzt `% Quelle:` und `% Stand:` und löscht den"
        " Marker; du prüfst den Diff.",
        "Hängt der Punkt an Wallach, kommt er in die nächste Agenda"
        " (`notizen/wallach_agenda_JJJJ-MM-TT.md`).",
    ],
    "belegen": [
        "Jeder Punkt ist ein `\\pruefen{…}`: der Fakt ist unsicher oder"
        " widersprüchlich.",
        "Claude prüft im Thesis-Fenster gegen die Datei aus `% Quelle:` (Code, ADR,"
        " Studienmaterial) und nennt die Fundstelle.",
        "Stimmt es: Marker weg, `% Stand: … geprüft`. Stimmt es nicht: Satz"
        " korrigieren. Nicht belegbar: abschwächen oder als Limitation nach"
        " Kap. 7.",
        "Du bestätigst im Diff.",
    ],
    "befunde": [
        "IDs und aktuelle Werte: `notizen/abgleich_system.md`, Abschnitt 2, und"
        " Tab Forschung, Karte „Merkliste und offene Punkte“.",
        "Claude setzt an der Stelle `% Befund: ID (Stichtag TT.MM.JJJJ)`; du"
        " entscheidest, ob die Zahl in den Text kommt.",
        "Produktivzahlen nur mit Marker übernehmen, sonst sind sie nicht"
        " nachprüfbar. Produktivbefunde gehören nach Kap. 7 (Artur, 15.11.2026).",
    ],
    "prosa": [
        "Im PDF steht über jedem Entwurf „Muss angepasst werden: PROSA“: den Block"
        " in deinen Worten umschreiben.",
        "Stil: unpersönlich („die vorliegende Arbeit“), Präsens für System und"
        " Aussagen, Präteritum nur für Durchführung und Ergebnisse, Zahlen als"
        " `70\\,\\%`, kein Gedankenstrich mit Leerzeichen.",
        "`\\prosa` löschen. Bleibt eine Formulierung von Claude wörtlich stehen:"
        " eine Zeile in Anhang J.",
        "Kapitelrahmen: Einstieg „Ziel dieses Kapitels ist es, …“, am Ende"
        " Zusammenfassung und Überleitung zum nächsten Kapitel.",
        "Danach im Thesis-Fenster „kompilieren und prüfen“ (Schritt Prüfen).",
    ],
    "prosa_bereit": [
        "Du darfst jetzt anfangen; die Woche im Zeitplan ist nur das Soll.",
        "Zuerst die `\\offen` dieses Kapitels (nur du), parallel belegt Claude die"
        " `\\pruefen` im Thesis-Fenster.",
        "Prosa, wenn die Stichpunkte stehen; ein Entwurf von Claude auf Wunsch"
        " (dann mit `\\prosa` markiert, siehe Kap. 4).",
        "Punkte mit „wartet bis“ hängen an einem Termin, z. B. dem Lab-Export am"
        " 17.11.: bis dahin überspringen.",
    ],
    "pruefen": [
        "Im Thesis-Fenster: „kompilieren und prüfen“. Claude lässt"
        " `werkzeuge/check_tex.py` laufen (Ziel „Befunde: 0“) und kompiliert lokal"
        " mit MiKTeX (pdflatex, biber, zweimal pdflatex).",
        "Erfolg: Exit-Code 0, in `main.log` keine Zeile mit „! “ und kein"
        " „undefined“.",
        "Diff ansehen, committen, `git push overleaf main` (pusht nach Overleaf"
        " und GitHub); die Commit-Nachricht liefert Claude.",
        "Overleaf dabei nicht im Browser bearbeiten; vor der nächsten Sitzung"
        " `git pull`.",
    ],
    "erklaertexte": [
        "In BitGridAI ansehen, was sich geändert hat: `git diff -- <Datei>` (noch"
        " nicht committet) oder `git log -p -- <Datei>`.",
        "Nur Optik, Kommentare oder Produktiv-Teile geändert (z. B. 15.11.:"
        " Gras-Karten entfernt): im Thesis-Fenster die genannten `% Stand:`-Zeilen"
        " auf „geprüft“ setzen lassen, fertig.",
        "Texte, Schwellen oder Bilder der Erklärkarte geändert: Kap. 4, Anhang C"
        " und `docs/thesis/studie/hamster_texte_ab_vergleich.md` nachziehen.",
        "Das Labor nicht anfassen: `deploy_ha_lab.py` ist bis zum Datenfreeze"
        " gesperrt; den Lab-Stand prüfst du am Labortermin mit"
        " `deploy_ha_lab.py --snapshot`.",
    ],
    "wallach": [
        "Je Gespräch eine Agenda `notizen/wallach_agenda_JJJJ-MM-TT.md` (Entwurf"
        " von Claude, Punkte vor dem Datenfreeze vorn); die Punkte darunter sind"
        " alle gesammelten Fragen, die Sammlung vom 04.11. steht in"
        " `notizen/wallach_gliederung.md`.",
        "Vor dem Gespräch die Agenda lesen und kürzen; der Button „Mittwoch mit"
        " Wallach“ (Bitsy) gibt eine zweite Meinung zur Reihenfolge.",
        "Antworten noch am selben Tag unten in die Agenda schreiben; Claude"
        " überträgt sie in die Arbeit, `offene_punkte.md` und den Fahrplan, mit"
        " „(Wallach, TT.MM.)“.",
        "Änderungen am Nachtrag nie rückdatieren.",
    ],
    "naechste": [
        "Marker und Gliederung des nächsten Kapitels einmal lesen.",
        "Fragen früh in die Wallach-Agenda; Befunde für dieses Kapitel schon mit"
        " Stichtag markieren lassen.",
    ],
    "spaeter_befunde": [
        "Wie „Befunde übernehmen“, nur für Kapitel, die nicht diese Woche dran"
        " sind.",
        "Marker jetzt setzen ist erlaubt; in der Schreibwoche den Stichtag"
        " erneuern (der Abgleich meldet geänderte Zahlen).",
        "Produktivanlage ist nur Kontext: Einordnung und Limitationen in Kap. 7,"
        " kein eigenes Ergebnis (Artur, 15.11.2026).",
    ],
    "anhang_fh": [
        "F: Nachtrag 2 entsteht in `notizen/nachtrag2_entwurf.md`; nach der"
        " Abstimmung mit Wallach mit dem echten Datum in Anhang F, nie"
        " rückdatiert, und vor dem Datenfreeze.",
        "H: Rater benennen, bevor codiert wird. Wer die Texte mitgestaltet hat,"
        " codiert nicht verblindet.",
        "Punkte mit „wartet auf …“ hängen an Wallach, Daten oder einer Person:"
        " in die Agenda oder direkt anfragen.",
    ],
    "anhang_j": [
        "Nach jeder Sitzung mit KI-Hilfe eine Zeile in"
        " `anhang/j_ki_werkzeuge.tex`: Werkzeug, Modell, Zeitraum, Zweck, Umfang.",
        "Beispiel: „Claude Code (Opus), 15.11.2026, Entwurf Kap. 5.2 aus"
        " Stichpunkten, von mir überarbeitet“.",
        "Auch hinein: KI-Bilder (Hamster, Icons mit ChatGPT) und Hilfe beim"
        " Englischen der Extended Summary.",
    ],
    "anhaenge": [
        "B Fragebogen und E Einwilligung als PDF mit `\\includepdf` einbinden; das"
        " Fragebogen-PDF kommt aus SoSci (über Annika).",
        "Einwilligung nur als leeres Formular, nie unterschrieben (Namen der"
        " Teilnehmenden). Der Marker in `e_einwilligung.tex` verlangt das"
        " unterschriebene: bitte entscheiden und den Marker anpassen.",
        "I Videoskript: `BitGrid-Video.docx` vom NAS (Pfad in `CLAUDE.local.md`),"
        " Claude gleicht ab. D Sprechtexte und Debriefing stehen nicht auf der"
        " NAS-Liste: Datei liefern oder diktieren.",
        "G Systemdetails: Hardware-Tabelle gegen den heutigen Aufbau prüfen"
        " (Claude, Quelle Repo).",
        "Titelseite und Erklärung erst mit dem endgültigen Deckblatt aus dem"
        " Portal (nach dem Titeleintrag).",
    ],
    "abbildungen": [
        "Fotos am Labortermin bei Tageslicht nach der Shotliste in"
        " `notizen/abbildungsliste.md`.",
        "Vorher prüfen: keine Personen, keine Bildschirme mit IP, Hostname oder"
        " Token; Seriennummer, MAC und QR-Codes abdecken; EXIF und GPS entfernen.",
        "Ablage als `bilder/fotos/k4_….jpg` (nur Präfix k1_ bis k8_ oder anh_"
        " wird versioniert); Claude bindet ein und ersetzt `\\abbplatzhalter`.",
        "Screenshots der Produktivanlage: `scripts/ha_view.py --shot <tab>`"
        " (1280 px wie das Lab-Tablet).",
    ],
    "parallel": [
        "Labortermin 16./17.11.: `export_studie_protokoll.py` im Labornetz (VP01"
        " bis VP10), Fotos und Screenshots am selben Tag, dazu"
        " `deploy_ha_lab.py --snapshot`.",
        "Annika bis 19.11.: Zeitraum verlängern, Rechte für dich, CSV-Sicherung"
        " nach der letzten Sitzung (Text steht im Punkt).",
        "Den SoSci-Live-Link nie öffnen: jeder Aufruf legt einen Fall an.",
        "Die Fragen zum Export beantwortet Claude danach aus `sitzungen.csv`,"
        " `exposition.csv` und `eingaben.csv` und trägt sie in Kap. 5 ein.",
    ],
    "auswertung_vorb": [
        "Im Dev-Fenster den offenen Teil nennen, z. B. „Power für den gepaarten"
        " Test einbauen“; Claude setzt ihn in `src/sim/study_analysis.py` mit Test"
        " um.",
        "Getestet wird nur mit synthetischen Daten (`pytest tests/sim`); die"
        " echten SoSci-Daten erst nach dem Datenfreeze öffnen.",
        "Abgehakt wird ein Teil am Code; danach die Checkbox in"
        " `offene_punkte.md` abhaken.",
    ],
    "summary": [
        "Einen Teil erst schreiben, wenn sein Kapitel fertig ist; der Fahrplan"
        " zeigt dann „bereit“ am Teil.",
        "In `anhang/a_extended_summary.tex` den `\\offen`-Platzhalter des"
        " Abschnitts ersetzen; das Wortbudget steht im Platzhalter selbst"
        " („ca. 600 Wörter“).",
        "Englisch: Dezimalpunkt (12.5 kWh), Tausender mit Komma (5,000); dieselben"
        " Zahlen und `\\cite`-Schlüssel wie im Hauptteil, keine neuen Aussagen.",
        "Eine geschätzte Wortzahl zeigt `check_tex.py`; KI-Hilfe beim Englischen in"
        " Anhang J eintragen.",
    ],
    "literatur_tonalitaet": [
        "Erst im eigenen Korpus suchen: `docs/thesis/literatur/00_KORPUS_INDEX.md`"
        " (BitGridAI).",
        "Neue Quelle: Claude bestätigt Titel, Venue, Jahr und DOI an einer"
        " zweiten Stelle, dann Eintrag in `references.bib`.",
        "Im Text `(vgl.~\\cite{Key})`, nur Schlüssel aus der Bib; den Volltext"
        " lesen, bevor du zitierst.",
        "Erledigt, wenn Kap. 2 (Sprachstil) und Kap. 3 eine Bib-Quelle zitieren"
        " und kein `\\offen` zur Literatur mehr haben.",
    ],
    "literatur": [
        "Checkboxen aus Abschnitt 6 von `offene_punkte.md`; gleiche Regeln wie"
        " bei der Literaturrecherche.",
        "Die Lücken im Text stehen hier nur als „siehe auch“; gezählt und"
        " bearbeitet werden sie im Schritt Literaturrecherche.",
    ],
    "fristen": [
        "Titel: Untertitel mit Wallach klären, dann Antrag im Prüfungsportal"
        " (Genehmigung dauert einige Tage), spätestens Mitte Dezember; danach das"
        " endgültige Deckblatt als `vorspann/deckblatt.pdf`.",
        "Abgabe bis 15.01.2027 elektronisch im Dekanat, gedruckt bis 22.01.2027;"
        " die Erklärung handschriftlich unterschreiben und einscannen.",
        "Punkte mit Frist stehen oben, der Rest kann jederzeit erledigt werden.",
    ],
    "anlagen": [
        "Frischen Clone von BitGridAI anlegen; `.env`, `data/`, Logs und"
        " `secrets.yaml` weglassen.",
        "Vor dem Packen nach IP-Adressen, Hostnamen und Tokens suchen und"
        " Namen im Grundriss schwärzen.",
        "Keine Rohdaten der Teilnehmenden; was aus Stimulus- und Studiendaten mit"
        " darf, entscheiden Einwilligung und Datenschutz.",
        "LaTeX-Quellen aus dem Thesis-Repo dazu; im Dekanat fragen, ob die"
        " gedruckte Fassung einen Datenträger braucht.",
    ],
    "kolloquium": [
        "Termin mit Wallach und Conrad abstimmen; die Bewertung der Arbeit dauert"
        " bis zu sechs Wochen.",
        "Fragenkatalog schon jetzt aus Kap. 7 sammeln: N = 16, Stimulus aus"
        " älterer Regelfassung, Produktivdaten nur Kontext.",
        "Folien erst nach Kap. 6; Probevortrag mit Stoppuhr (20 Min.), danach"
        " 20 Min. Befragung.",
    ],
    "freeze": [
        "Nur auf der eingefrorenen Kopie rechnen, im Dev-Fenster:"
        " `.venv/Scripts/python -m src.sim.study_analysis --sosci"
        " data/study/sosci/<Export>.csv` (läuft erst, wenn"
        " `data/study/datenfreeze.txt` existiert). Ergebnis: `kennwerte.csv`,"
        " `kennwerte.md` und `bericht.txt` in `data/study/auswertung/`.",
        "Vorher zum Üben: `--demo` rechnet alles auf synthetischen Daten.",
        "Ergebnisse in Kap. 6 im Präteritum, immer mit Effektgröße r, 95-%-KI und"
        " N (Stilleitfaden).",
        "Jede Abweichung vom Plan in Kap. 5 (Abweichungen) berichten.",
    ],
    "datenfreeze": [
        "An einem Tag am Stück nach VP16; die fünf Punkte darunter der Reihe" " nach.",
        "Prüfsummen mit `certutil -hashfile <Datei> SHA256` in"
        " `data/study/datenfreeze.txt` (BitGridAI); damit gilt der Schritt als"
        " erledigt.",
        "Ab dann nur mit Kopien arbeiten; jede spätere Änderung ist eine"
        " Abweichung für Kap. 5.",
    ],
    "sonstiges": [
        "Den Punkt in `offene_punkte.md` einem Abschnitt zuordnen, dann landet er"
        " im richtigen Schritt.",
    ],
}

# Tasks of the schedule and the notes that offene_punkte.md does not list
# (review 15.11.2026). Shown in their step, marked, until a line starting with
# the same words is in the list. (step, section of the list, line, tip)
LIST_GAPS: tuple[tuple[str, str, str, str], ...] = (
    (
        "freeze",
        "7. Auswertung",
        "Teach-Back und lautes Denken codieren, ungewichtetes Cohens Kappa je"
        " Kategorie (Zeitplan 30.11.–06.12.; Anh. H, Kap. 6)",
        "Erst die Rater benennen (Anh. H), dann unabhängig codieren; Schwelle"
        " κ ≥ 0,61 nach Landis und Koch.",
    ),
    (
        "freeze",
        "7. Auswertung",
        "FF2: verblindete Prüfung der Faktengleichheit durch die Rater durchführen"
        " (Anh. H, Kap. 6)",
        "Die Rater sehen nur Textpaare ohne Kennzeichnung A oder B; Prüfschema aus"
        " Anhang H.",
    ),
    (
        "freeze",
        "7. Auswertung",
        # No "study_analysis" in the line: ITEM_ROUTE would move it to the
        # preparation on synthetic data.
        "Auswertung mit echten Daten nach dem Datenfreeze (Skript mit --sosci),"
        " Ergebnisse mit r, 95-%-KI und N in Kap. 6",
        "Das Skript ist mit synthetischen Daten getestet; nach dem Freeze nur den"
        " SoSci-Export als Eingabe tauschen.",
    ),
    (
        "fristen",
        "8. Schreiben",
        "Gesamtentwurf an Wallach (Zeitplan 14.–20.12.)",
        "Als PDF mit kurzer Liste, was sich seit Kap. 4 geändert hat; vorher"
        " check_tex ohne Befund.",
    ),
    (
        "fristen",
        "8. Schreiben",
        "Rückmeldung einarbeiten und Korrektur lesen: Rechtschreibung,"
        " Stilleitfaden, Abbildungs- und Literaturverzeichnis (Zeitplan 04.–10.01.)",
        "Laut vorlesen lassen findet Tippfehler; im Stilleitfaden Gedankenstriche"
        " und Zahlenformat prüfen.",
    ),
    (
        "fristen",
        "5. Prüfungsamt",
        "Druck reservieren (Zeitplan 04.–10.01.); gedruckte Ausfertigung bis"
        " 22.01.2027 nachreichen",
        "Copyshop früh anfragen (Bindung, Dauer); bei Postversand zählt das"
        " Absendedatum.",
    ),
)
_GAP_KEY = 30


def list_gaps(data: dict[str, Any]) -> list[dict[str, str]]:
    """LIST_GAPS whose line is not (yet) in offene_punkte.md, as points."""
    listed = [
        str(i)[:_GAP_KEY]
        for sec in data.get("sections") or []
        for i in sec.get("items") or []
    ]
    return [
        {
            "step": step,
            "text": line,
            "where": f"fehlt in Liste ({section})",
            "tip": tip,
            "fehlt_in_liste": "1",
        }
        for step, section, line, tip in LIST_GAPS
        if line[:_GAP_KEY] not in listed
    ]


# How to solve each point of the plan (Artur, 15.11.2026: "auch die
# Unterpunkte genauer beschreiben, wie ich das löse", checked against the
# thesis as of 15.11.2026). First the points known by their words, then a rule
# per kind of point. `code` is shown as code on the card.
ITEM_TIPS: tuple[tuple[str, str], ...] = (
    # Kapitel 4 and the lab
    (
        "Avalon",
        "Bei Tageslicht nur das Gerät fotografieren, Aufkleber mit Seriennummer"
        " und QR-Code abdecken, EXIF entfernen; als `bilder/fotos/k4_avalon_q.jpg`"
        " ablegen, Claude tauscht das Herstellerbild in Abb. 4.8 (e).",
    ),
    (
        "Prüferansicht",
        "Am Labortermin 16./17.11. die Sim-Steuerung im Konto „BitGridAI-Prüferin“"
        " öffnen und ohne Adresszeile (keine IP, kein echter VP-Code) aufnehmen;"
        " nach `bilder/screenshots/`, Claude ersetzt den Platzhalter"
        " `fig:sim_steuerung`.",
    ),
    (
        "Screenshots der Erklärkarte",
        "Am Lab-Tablet den Replay pausieren, Variante A aufnehmen, auf B schalten"
        " und zur selben Sim-Zeit aufnehmen; beide nach `bilder/screenshots/`,"
        " Claude ersetzt den Platzhalter `fig:erklaerkarte_ab`.",
    ),
    (
        "Abendfassung",
        "Am Labortermin `deploy_ha_lab.py --snapshot` laufen lassen: Ist die Liste"
        " „seit 2026-10-19 geändert“ leer, ist belegt, dass der Stand vom 18.10."
        " unverändert lief. Dann `\\pruefen` durch den Beleg ersetzen lassen.",
    ),
    (
        "Sitzungsexport",
        "Im Labornetz in BitGridAI `.venv/Scripts/python"
        " scripts/export_studie_protokoll.py` starten; die CSVs bleiben in"
        " `data/study/`, nie im Thesis-Repo. Danach im Thesis-Fenster „Export"
        " auswerten“.",
    ),
    # Kapitel 5
    (
        "Labor-Werkzeug ist noch für between",
        "Gilt weiter für den Export: `gruppe` ist dort die zweite Variante. Die"
        " Reihenfolge je Person aus `exposition.csv` nehmen; Claude formuliert"
        " das in Kap. 5 und löscht den Marker.",
    ),
    (
        "Reihenfolge: Belegen",
        "Nach dem Lab-Export: Claude liest die Reihenfolge je Person aus"
        " `exposition.csv` und vergleicht sie mit K001 aus SoSci.",
    ),
    (
        "Variablenansicht vom 14.11.2026",
        "Laut Manual gibt es keinen Gesamtwert: Item 19 gehört nur zu"
        " Reliabilität/Kompetenz. Die primäre AV Vertrauen in Automation (Items 9,"
        " 14) ist in beiden Durchläufen vollständig; R/K wird im Vergleich ohne"
        " Item 19 gerechnet, mit 19 nur beschreibend (Nachtrag 2, Punkt 4).",
    ),
    (
        "Antwortcodes",
        "Die Umcodierung steht im Code (`LIKERT_RECODE` in"
        " `src/sim/study_sosci.py`): Claude belegt den Satz mit dieser Stelle und"
        " löscht den Marker.",
    ),
    (
        "Anlass des Wechsels",
        "Nur du weißt es: wann und warum von Jian et al. auf den TiA gewechselt"
        " wurde. Als Stichwort im Thesis-Fenster nennen.",
    ),
    (
        "Herkunft der deutschen Itemformulierungen",
        "TiA: Claude vergleicht den SoSci-Wortlaut mit dem Fragebogen aus Körber"
        " (2019, `Koerber2019Theoretical`). SUS: eine veröffentlichte deutsche"
        " Fassung recherchieren lassen und vor Nutzung prüfen; gibt es keine"
        " passende, wird es eine Limitation in Kap. 7.",
    ),
    (
        "sucht Dieter raus",
        "„sucht Dieter raus“ ist der Name des Index, kein Auftrag. Frage in der"
        " Wallach-Agenda: Index nicht auswerten, weil VP01 bis VP04 ihn nicht"
        " bekamen, nur als Abweichung nennen.",
    ),
    (
        "Einwilligungsformular",
        "Das Formular ist so verwendet worden und bleibt unverändert. Die echte"
        " Dauer aus `sitzungen.csv` (Beginn und Ende) nennen und die"
        " Abweichungen (Dauer, „anonymisiert“ statt pseudonymisiert) in Kap. 5"
        " offen berichten.",
    ),
    (
        "Läuft der Replay während Aufgabe 1",
        "Beantwortet der Lab-Export: Zeit der Eingaben in Aufgabe 1"
        " (`eingaben.csv`) gegen die Sim-Uhr (`exposition.csv`) und Starts und"
        " Pausen (`sitzungen.csv`); Claude trägt es in Kap. 5 Ablauf ein.",
    ),
    (
        "Power für den gepaarten Test",
        "Steht im Code (`paired_power` in `src/sim/study_analysis.py`, Monte-Carlo,"
        " N = 16, zweiseitig): dz 0,3 rund 18 %, 0,5 rund 43 %, 0,8 rund 82 %."
        " Claude ersetzt in Kap. 5 die 39,5 % aus dem Between-Design; die"
        " Annahmen gehören in Nachtrag 2.",
    ),
    (
        "auf das Within-Design umst",
        "Im Code erledigt (`run_within_tests` in `src/sim/study_analysis.py`):"
        " Claude belegt das in Kap. 5 und löscht den Marker.",
    ),
    (
        "Datum der Korrektur",
        "Annika fragen (sie hat die Änderung gemacht): Datum und erste VP danach;"
        " Claude trägt es in Kap. 5 (Abweichungen) ein.",
    ),
    (
        "Versuchsleitung für VP11",
        "Nach VP16: wer die Sitzungen geleitet hat, als Stichwort nennen.",
    ),
    (
        "Ein- und Ausschlusskriterien",
        "Nach dem Datenfreeze aus dem SoSci-Export (Alter, Geschlecht,"
        " Vorkenntnisse); die Kriterien selbst nennst du jetzt schon.",
    ),
    (
        "Zwei unabhängige Rater",
        "In die Wallach-Agenda: zwei Personen, die die Texte nicht mitgestaltet"
        " haben; Namen kommen nicht in die Arbeit, nur die Rolle.",
    ),
    # Kapitel 2, 3, 7, 1
    (
        "Körber (2019) ist noch nicht",
        "Steht seit 14.11. in der Bib (`Koerber2019Theoretical`): Claude setzt"
        " `\\cite`, gleicht Dimensionen und Items mit dem Original ab und löscht"
        " den Marker.",
    ),
    (
        "Quelle für die Teach-Back-Methode",
        "Steht seit 14.11. in der Bib (`Schillinger2003Closing`): Claude setzt"
        " `\\cite` und löscht den Marker.",
    ),
    (
        "Gegen die Fassung prüfen, die VP01",
        "Nach dem Lab-Export bzw. `--snapshot`: Claude vergleicht den Text mit"
        " der Fassung vom 17./18.10. in"
        " `docs/thesis/studie/hamster_texte_ab_vergleich.md` (BitGridAI).",
    ),
    (
        "Größte Literaturlücke",
        "Kandidaten aus dem Marker (Nass und Moon 2000, Waytz et al. 2014, de"
        " Visser et al. 2016) von Claude prüfen lassen, Volltext lesen, dann"
        " Bib-Eintrag und `\\cite` hier.",
    ),
    (
        "Empirische Studien, die Ton",
        "Suchfrage aus `notizen/literatur_recherche.md`; Claude liefert geprüfte"
        " Kandidaten mit DOI, du wählst nach dem Volltext aus.",
    ),
    (
        "Lücke erst nach der Recherche",
        "Erst wenn die Literatur steht: Vergleichstabelle (Arbeit, Kontext,"
        " Manipulation, Maß, Ergebnis) mit Claude füllen, die Lücke formulierst"
        " du.",
    ),
    (
        "Shajalal",
        "PDF beschaffen und lesen; danach sagst du Claude, welche Aussage belegt"
        " ist.",
    ),
    (
        "Längen der Varianten",
        "Claude zählt Wörter und Zeichen je Zustand aus"
        " `docs/thesis/studie/hamster_texte_ab_vergleich.md` (BitGridAI) und"
        " trägt die Kennzahlen ein.",
    ),
    (
        "Lärm luftgekühlter",
        "Drei Wege aus dem Marker: Herstellerdatenblatt des Avalon Q zitieren,"
        " eigene Messung nennen oder den Halbsatz streichen; ohne Quelle keine"
        " Zahl.",
    ),
    (
        "Rekrutierungsweg",
        "Nur du weißt es: wie VP01 bis VP16 gewonnen wurden (Kurs, Aushang,"
        " persönlich); als Stichwort nennen, Claude trägt es in Kap. 5 und 7 ein.",
    ),
    (
        "Gesetzgebungsstand",
        "Anfang Januar den Stand der BT-Drucksache 21/7867 (EEG 2027) prüfen;"
        " Claude passt den Satz in Kap. 1.1 an.",
    ),
    (
        "Reliabilität (Spearman-Brown",
        "Nach dem Datenfreeze rechnet Claude den Wert im Dev-Fenster; du"
        " übernimmst ihn.",
    ),
    (
        "Synthese: Welche Annahmen",
        "Schreibst du, wenn 2.1 bis 2.4 stehen: zwei bis drei Annahmen zu"
        " Sprachstil, Vertrauen und Verständnis, jede mit Beleg aus dem Kapitel;"
        " der letzte Satz leitet zu Kap. 3 über.",
    ),
    (
        "Erst nach Fertigstellung aller Kapitel",
        "Ganz am Ende schreiben (Aufbau der Arbeit): je Kapitel ein Satz; Claude"
        " liefert auf Wunsch die Liste der Kapitelüberschriften.",
    ),
    (
        "Unterfragen gegen die Instrumente",
        "Gehört in die Wallach-Agenda (Akzeptanz ohne Instrument, Verständnis"
        " fehlt in den Unterfragen); nach der Antwort passt Claude die"
        " Unterfragen in Kap. 1 an.",
    ),
    (
        "Basistext vom 28.10.2026",
        "Erst wenn Kap. 6 steht: den vorletzten Teil auf das heutige Design"
        " umschreiben (zwei feste Erklärvarianten, Within, N = 16); schreibst du,"
        " Claude prüft die Fakten.",
    ),
    (
        "Prosa bitte selbst anpassen",
        "Die nummerierten Punkte im Marker der Reihe nach selbst umformulieren;"
        " danach „kurzfassung.tex prüfen“, Claude gleicht jeden Punkt ab.",
    ),
    (
        "Zeitraum und Umfang angeben",
        "Nur du weißt es: seit wann du welches Werkzeug nutzt und wofür (grob"
        " nach Abschnitten); als Stichwort nennen, Claude trägt es ein.",
    ),
    (
        "Reihenfolge A/B je Person",
        "Claude liest die Variantenfolge je VP aus"
        " `exposition.csv` (Spalte `variante_tablet`); der Abgleich mit K001"
        " folgt mit dem SoSci-Export nach dem Freeze.",
    ),
    (
        "vor Durchlauf 2",
        "`eingaben.csv`, Feld „Eco ab“: Claude prüft je Sitzung,"
        " ob der Wert vor dem zweiten Durchlauf wieder 70 % war.",
    ),
    (
        "Wie lange dauert eine Sitzung",
        "`sitzungen.csv` (Beginn, Ende, `lauf_netto_s`): Claude"
        " rechnet Spanne und Median und trägt sie in Kap. 5 ein.",
    ),
    (
        "Warten auf Sonne",
        "`exposition.csv`, Spalte `hamster`: Claude sucht je"
        " Sitzung diese Zustände und meldet, ob einer vorkam.",
    ),
    # Wallach and the Hochschule
    (
        "Ethikvotum",
        "Wallach fragen, ob für die Laborstudie (pseudonyme Daten, angekündigte"
        " weitere Testperson beim Teach-Back) ein Votum nötig ist.",
    ),
    (
        "Forschungsfragen neu",
        "Vorschlag steht in `notizen/wallach_gliederung.md`, Frage 1; nach dem"
        " Gespräch trägt Claude die Fassung in Kap. 1 ein.",
    ),
    (
        "Endgültigen Titel",
        "Nach Wallachs Zustimmung im Prüfungsportal eintragen, deutsch und"
        " englisch.",
    ),
    (
        "Vor der Abgabe",
        "In der Abgabewoche: Titel steht im Portal, neues Deckblatt als"
        " `vorspann/deckblatt.pdf` ablegen, Erklärung unterschreiben und"
        " einscannen.",
    ),
    (
        "Titel: Jede Änderung",
        "Spätestens Mitte Dezember beantragen; ohne Genehmigung kein endgültiges"
        " Deckblatt. Alternative: Anmeldetitel unverändert übernehmen.",
    ),
    (
        "Untertitel",
        "Zwei Vorschläge mitbringen (`wallach_gliederung.md`, Frage 6); nach der"
        " Zustimmung Antrag im Prüfungsportal.",
    ),
    (
        "Kap. 4 zur Rückmeldung",
        "Sobald die `\\prosa` in Kap. 4 weg sind und kompiliert ist: PDF an"
        " Wallach mit den drei Fragen (Länge, Tiefe, Abbildungen).",
    ),
    (
        "Umfang der Arbeit",
        "Steht in `wallach_gliederung.md`, Frage 5; in die nächste Agenda"
        " übernehmen, die Antwort gilt auch für den Punkt unter Hochschule.",
    ),
    (
        "Pflichtumfang",
        "Wallach am Mittwoch fragen (steht in der Agenda); die Antwort trägt"
        " Claude ein.",
    ),
    (
        "Abgabe nach",
        "PDF mit Anlagen elektronisch ans Dekanat bis 15.01.; die gedruckte"
        " Fassung bis 22.01. (per Post zählt das Absendedatum); Wallach und Conrad"
        " fragen, ob sie ein eigenes Exemplar wollen.",
    ),
    (
        "Vertraulichkeit",
        "Bei der Abgabe angeben: interne Arbeit ohne Unternehmen, kein"
        " Sperrvermerk.",
    ),
    (
        "Nach der Abgabe",
        "Kurzfassung und Abstract ins Portal kopieren; vorher prüfen, dass keine"
        " privaten Daten darin stehen.",
    ),
    (
        "Kolloquium (",
        "Termin über Wallach und Conrad; Gäste nur auf Antrag beim"
        " Prüfungsausschuss. Abhaken, wenn das Kolloquium gehalten ist.",
    ),
    (
        "Anlagen zur elektronischen",
        "Die vier Punkte darüber abarbeiten, dann im Dekanat fragen, ob die"
        " gedruckte Fassung einen Datenträger braucht.",
    ),
    (
        "Anhang J „Einsatz",
        "Die Marker darüber abarbeiten; erledigt, wenn jedes Werkzeug Version,"
        " Zeitraum, Zweck und Umfang hat.",
    ),
    (
        "Extended Summary (Anhang A, mindestens",
        "In die Wallach-Agenda: zählt die Summary zum Umfang, und soll sie die"
        " Kapitel gleich gewichten?",
    ),
    # SoSci and Annika
    (
        "Annika erinnern",
        "Mail an Annika mit den drei Punkten aus dem Text (Zeitraum bis 14.12.,"
        " Rechte für dich, CSV-Sicherung) bis 19.11.; nach ihrer Antwort"
        " abhaken.",
    ),
    (
        "Index für Textverständnis",
        "VP01 bis VP04 bekamen Index und Checkliste nicht (Kap. 5). Frage in der"
        " Wallach-Agenda: nicht auswerten, nur als Abweichung nennen.",
    ),
    (
        "Finale Fragebogen-PDF",
        "Annika um das Fragebogen-PDF bitten; das Videoskript liegt auf dem NAS"
        " (`BitGrid-Video.docx`, Pfad in `CLAUDE.local.md`). Die Sprechtexte"
        " stehen dort nicht: Datei liefern oder diktieren.",
    ),
    (
        "Finale Fassung des Fragebogens",
        "Das PDF kommt von Annika (SoSci); Claude bindet es mit `\\includepdf` ein"
        " und löscht den Marker.",
    ),
    # Appendices
    (
        "unterschriebene Formular",
        "Nicht das unterschriebene Formular (Namen der Teilnehmenden): das leere"
        " Formular einbinden und den Marker im Thesis-Fenster so ändern lassen.",
    ),
    (
        "Bilder der zehn Hamster-Zustände",
        "Einfachste Lösung: auf `fig:hamster_zustaende` in Kap. 4 verweisen statt"
        " die Bilder doppelt zu zeigen; dann ist Anhang C wirklich fertig.",
    ),
    (
        "Sprechtexte der Versuchsleitung",
        "Die Sprechtexte sind nicht auf der NAS-Liste in `CLAUDE.local.md`: Datei"
        " liefern oder diktieren; Claude setzt sie mit dem Debriefing (Auflösung"
        " der „weiteren Testperson“) in Anhang D.",
    ),
    (
        "Aus der Fassung vom Sommer",
        "Claude gleicht Anhang G mit dem heutigen Aufbau ab (Laborplattform,"
        " Hardware); du bestätigst im Diff.",
    ),
    (
        "Am 02.11.2026 an den IST-Zustand",
        "Claude prüft die Hardware-Tabelle gegen den Stand heute und setzt"
        " `% Stand: … geprüft`.",
    ),
    (
        "Endfassung des Videos",
        "Claude gleicht `BitGrid-Video.docx` vom NAS gegen Anhang I ab; die"
        " Länge 2:05 und wer Skript und Grafiken gemacht hat, bestätigst du.",
    ),
    (
        "Ehrenwörtliche Erklärung: mit dem",
        "Nach dem Titeleintrag im Portal das endgültige Deckblatt herunterladen"
        " und `vorspann/deckblatt.pdf` ersetzen.",
    ),
    (
        "Deckblatt ist vorläufig",
        "Nach dem Titeleintrag im Portal das endgültige Deckblatt herunterladen"
        " und `vorspann/deckblatt.pdf` ersetzen.",
    ),
    # Anhang F, H, J
    (
        "Nachtrag",
        "Vorbereitet in `notizen/nachtrag2_entwurf.md`; am Mittwoch mit Wallach"
        " bestätigen, dann mit dem echten Datum in Anhang F, vor dem Datenfreeze.",
    ),
    (
        "Ankerbeispiele",
        "Sobald die ersten Transkripte da sind: je Kategorie ein typisches"
        " Beispiel auswählen und im Thesis-Fenster eintragen lassen.",
    ),
    (
        "Wer codiert",
        "In die Wallach-Agenda; wer die Texte mitgestaltet hat (du), codiert"
        " nicht verblindet.",
    ),
    (
        "Rater benennen",
        "In die Wallach-Agenda: zwei Personen, verblindet; danach je Zustand"
        " urteilen lassen.",
    ),
    (
        "erste Prosa-Fassungen von Claude",
        "Nach dem Überarbeiten von Kap. 4: im Anhang J festhalten, welche"
        " Abschnitte aus Claude-Entwürfen stammen.",
    ),
    (
        "Dashboard-Hintergründe",
        "Nur du weißt, womit die Hintergrundbilder entstanden sind; als Stichwort"
        " nennen.",
    ),
    (
        "Über welche Software",
        "Nur du weißt es (Werkzeug für den Entwurf der Erklärtexte im Oktober);"
        " als Stichwort nennen.",
    ),
    (
        "MakerWorld",
        "Nutzungsbedingungen der Plattform aufrufen und die Lizenz des Modells"
        " notieren; Claude trägt sie ein.",
    ),
    # Figures
    (
        "Prinzip flexible Last",
        "Optional: Claude erstellt einen Entwurf mit"
        " `werkzeuge/excalidraw_entwurf.py` im Stil des Konzepts; du entscheidest,"
        " ob er in Kap. 2 kommt.",
    ),
    (
        "Fragebogen, leere Einwilligung",
        "PDFs liefern (Fragebogen über Annika, Einwilligung leer); Claude bindet"
        " sie in Anhang B und E ein.",
    ),
    # Kolloquium and Anlagen
    (
        "Termin mit Wallach und Conrad",
        "Mail an beide mit einem Zeitraum nach der Bewertung (bis zu sechs Wochen"
        " nach der Abgabe).",
    ),
    (
        "Vortrag 20 Min",
        "Fünf Teile mit je etwa vier Minuten; Claude baut auf Wunsch eine"
        " Foliengliederung aus Kap. 1, 4, 5, 6 und 7.",
    ),
    (
        "Befragung 20 Min",
        "Mit dem Fragenkatalog üben: jede Antwort in einer Minute.",
    ),
    (
        "Fragenkatalog",
        "Claude sammelt aus Kap. 7 die wahrscheinlichen Fragen (Stichprobe,"
        " Stimulus, Produktivdaten); du formulierst die Antworten.",
    ),
    (
        "BitGridAI-Code exportieren",
        "Frischen Clone anlegen, `.env`, `data/`, Logs und `secrets.yaml`"
        " weglassen, dann nach IP-Mustern und Tokens suchen.",
    ),
    (
        "keine privaten Hausdaten",
        "`bitgrid.db` und Grundriss-Namen bleiben draußen; Claude listet vor dem"
        " Packen jede Datei mit Hausdaten.",
    ),
    (
        "keine Rohdaten der Teilnehmenden",
        "SoSci-Export und Sitzungsexport bleiben draußen; höchstens aggregierte"
        " Ergebnisse, wenn Einwilligung und Datenschutz es erlauben.",
    ),
    (
        "LaTeX-Quellen",
        "Das Thesis-Repo als ZIP ohne Hilfsdateien (`.aux`, `.log`); `main.pdf`"
        " ist die Abgabe-PDF.",
    ),
    (
        "Kap. 6 vollständig",
        "Nach der Auswertung: Ergebnisse aus der JSON-Ausgabe von"
        " `study_analysis.py` in Kap. 6, die Deutung in Kap. 7.",
    ),
)


def item_tip(step_key: str, item: dict[str, Any]) -> str | None:
    """How to solve one point (ITEM_TIPS, then a rule per kind of point)."""
    text = str(item.get("text") or "")
    where = str(item.get("where") or "")
    # The keyword that stands first in the text wins: a point often names
    # other topics later ("Lärm luftgekühlter Miner ... Avalon").
    hits = [(text.find(n), k, tip) for k, (n, tip) in enumerate(ITEM_TIPS) if n in text]
    if hits:
        return min(hits)[2]
    tip = _kind_tip(step_key, item, text, where)
    if tip and item.get("wartet_bis"):
        d = str(item["wartet_bis"])
        tip = f"Termin {d[8:10]}.{d[5:7]}.: {tip}"
    return tip


def _kind_tip(step_key: str, item: dict[str, Any], text: str, where: str) -> str | None:
    """Rule per kind of point when no ITEM_TIPS entry matches."""
    who = str(item.get("am_zug") or "")
    befund = re.search(r"% Befund: ([a-z0-9_]+)", text)
    if befund:
        return (
            f"Im Thesis-Fenster: „Befund {befund.group(1)} übernehmen“. Claude"
            " setzt den Marker mit heutigem Stichtag an die passende Stelle und"
            " zeigt dir den Wortlaut; die Zahl übernimmst nur du."
        )
    if step_key == "summary":
        budget = re.search(r"von (\d+) Wörtern", text)
        part = text.split(":")[0]
        return (
            f"Wenn das Kapitel fertig ist: im Thesis-Fenster „Extended Summary,"
            f" {part} entwerfen“ oder selbst schreiben, Grundlage ist {where},"
            f" Budget {budget.group(1) if budget else '?'} Wörter."
        )
    if where.endswith("(Fragen)"):
        return (
            "Beantwortet der Lab-Export (`sitzungen.csv`, `exposition.csv`,"
            " `eingaben.csv`): Claude wertet ihn aus und trägt das Ergebnis in"
            " Kap. 5 ein."
        )
    if where == "Fotoliste":
        return (
            "Am Labortermin nach der Shotliste fotografieren, EXIF entfernen, als"
            " `bilder/fotos/k4_….jpg` ablegen; Claude bindet ein."
        )
    if where == "Bedingung":
        return (
            "Im Thesis-Repo `git status`, Diff prüfen, committen und"
            " `git push overleaf main`."
        )
    if step_key == "auswertung_vorb":
        return (
            f"Im Dev-Fenster: „{text}“. Claude setzt es in"
            " `src/sim/study_analysis.py` mit Test um, nur mit synthetischen"
            " Daten."
        )
    if step_key in ("literatur_tonalitaet", "literatur") and where.startswith(
        "Suchfrage"
    ):
        return (
            "Im Thesis-Fenster „Suchfrage recherchieren“: Claude liefert"
            " geprüfte Kandidaten mit DOI, du wählst nach dem Volltext aus."
        )
    if who == "Datenfreeze":
        return "Nach dem Datenfreeze aus dem SoSci-Export eintragen (Claude)."
    if who == "Wallach" or where.startswith("Prof. Wallach"):
        return (
            "In die nächste Agenda (`notizen/wallach_agenda_JJJJ-MM-TT.md`);"
            " die Antwort dort unten eintragen, Claude überträgt sie."
        )
    if who == "Annika":
        return (
            "Annika fragen (das SoSci-Projekt liegt in ihrem Account); ihre"
            " Antwort im Thesis-Fenster nennen, Claude trägt sie ein."
        )
    if who == "Daten":
        return "Wartet auf Daten (Export, Transkripte); danach im Thesis-Fenster bearbeiten."
    if who == "Person":
        return "Erst die Person benennen (Wallach-Agenda), dann hier eintragen lassen."
    kind = item.get("kind")
    if kind == "pruefen" or (step_key == "belegen" and not kind):
        return (
            f"Im Thesis-Fenster „{where} belegen“: Claude prüft gegen die"
            " `% Quelle:` darüber und meldet Fundstelle oder Korrektur; du"
            " bestätigst im Diff."
        )
    if kind == "offen" or step_key == "klaeren":
        if where.startswith("06_"):
            return "Nach dem Datenfreeze aus der Auswertung schreiben."
        if where.startswith(("07_", "08_", "kurzfassung", "abstract")):
            return (
                "Inhalt zum Schreiben: Stichpunkte im Thesis-Fenster sammeln"
                " lassen, die Prosa schreibst du (auf Wunsch Entwurf mit"
                " `\\prosa`)."
            )
        return (
            f"Fakt oder Entscheidung von dir: im Thesis-Fenster „{where}: …“ als"
            " Stichwort nennen; Claude schreibt es ein und löscht den Marker."
        )
    if step_key.startswith("prosa"):
        return (
            "Schreibst du in der Kapitelwoche (oder früher); Claude liefert auf"
            " Wunsch Stichpunkte oder einen `\\prosa`-Entwurf."
        )
    return None


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
            text = str(item)
            dest = next((s for w, s in ITEM_ROUTE if w in text), step)
            if step == "fristen":
                dest = next((s for w, s in FRISTEN_ROUTE if text.startswith(w)), dest)
            point = flag_wait({"text": text, "where": name}, parse_termin(text, today))
            frist = parse_frist(text, today)
            if frist is not None:
                point["frist"] = frist.isoformat()
            by_step.setdefault(dest, []).append(point)

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
                        "text": f"Befund {row['title']}: "
                        + ("Aussage" if p.get("ohne_zahlen") else "Zahlen")
                        + " seit Stichtag"
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
                {
                    "text": str(m["text"]),
                    "where": _short(m["file"], m["line"]),
                    "kind": kind,
                },
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
                "kind": str(m.get("kind") or ""),
                # \offen = a decision only Artur can make, \pruefen = Claude
                # checks against the source.
                "am_zug": wait_reason(str(m["text"]))
                or ("Artur" if m.get("kind") == "offen" else "Claude"),
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

    def draft_note(n: int) -> str:
        return f" {n} Stellen mit \\prosa (Entwurf, von dir anzupassen)."

    def prosa_step(i: int, row: dict[str, Any]) -> dict[str, Any] | None:
        """Prose step of one schedule row; None if the row names no chapter.

        Done when its chapter files hold no open marker (\\offen or \\pruefen
        without Termin) and no extra unit (Kurzfassung, Abstract, Anhang) is
        left. \\prosa does not count. Before the week of the row the step is
        "bereit" (Artur, 15.11.2026: the schedule is a target week, not a
        lock), a results chapter before the data freeze "gesperrt"; from the
        week on "jetzt" (the current row follows the order of the pipeline).
        """
        write = str(row.get("write"))
        chs = week_chapters(write)
        extras = [w for w in ("Kurzfassung", "Abstract", "Anhang") if w in write]
        if not chs and not extras:
            return None
        current = bool(row.get("now"))
        pieces = pieces_by_row.get(i, [])
        counted = [p for u, p in pieces if not u.startswith("kap:")]
        # Kurzfassung and Abstract live in vorspann/; their markers belong to
        # the row that writes them (15.11.2026: they were in no step).
        extra_files = tuple(
            f"vorspann/{w.lower()}.tex"
            for w in extras
            if w in ("Kurzfassung", "Abstract")
        )
        blocking = open_markers(chs) + [
            m
            for m in marker_list
            if str(m.get("file")) in extra_files
            and not (m.get("termin") and str(m["termin"]) >= today_iso)
        ]
        started = today_iso >= str(row.get("start"))
        # Markers of the current chapter belong to the steps before (klaeren,
        # belegen); without points of its own the prose step is rated alone.
        drafts = prosa_drafts(chs)
        # \prosa = a draft by Claude that Artur still has to revise: the
        # chapter is not done while one is left.
        done = (
            started
            and not counted
            and not drafts
            and (not blocking or (current and not pieces))
        )
        week = str(row.get("week"))
        parts = ([f"Kap. {', '.join(str(c) for c in chs)}"] if chs else []) + extras
        needs_data = bool(set(chs) & set(RESULT_CHAPTERS)) and not frozen
        if not started:
            why = (
                f"Soll-Woche {week}. Braucht die eingefrorenen Daten, erst nach"
                " dem Datenfreeze."
                if needs_data
                else f"Soll-Woche {week}; kann jederzeit angefangen werden."
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
        if drafts:
            why += draft_note(drafts)
        stale_boxes = [f"{p['where']} {p['text']}".strip() for u, p in pieces]
        if done and stale_boxes:
            why += (
                " Checkbox in offene_punkte.md noch nicht abgehakt: "
                + "; ".join(stale_boxes)
                + "."
            )
        if not started:
            # The chapter may start any time ("bereit"), so its open markers
            # are its work list now (15.11.2026: Kap. 5 had 19 markers that no
            # step showed).
            # Points that wait for a Termin are listed too, flagged by
            # marker_point (they do not block, but they are work).
            own_all = [
                m
                for m in marker_list
                if _chapter_of(str(m.get("file"))) in chs
                or str(m.get("file")) in extra_files
            ]
            items = [marker_point(m) for m in own_all] + [p for _, p in pieces]
        elif done:
            items = []
        elif current:
            items = [p for _, p in pieces]
        else:
            items = [marker_point(m) for m in blocking] + counted
        step: dict[str, Any] = {
            "key": "prosa" if current else f"prosa_{i}",
            "title": f"{', '.join(parts)}: "
            + ("Entwurf überarbeiten" if drafts else "Prosa schreiben"),
            "who": "Artur" if drafts else "Artur, auf Wunsch mit Claude-Entwurf",
            "why": why,
            "items": items,
        }
        if drafts:
            # \prosa drafts left, shown next to the open points (Artur,
            # 14.11.2026 and 15.11.2026: both counts, so working off markers
            # shows progress too).
            step["prosa"] = drafts
        step["chapters"] = chs
        # Target end of the schedule week, shown on the card (Artur,
        # 15.11.2026: deadlines visible at a glance).
        step["soll_bis"] = str(row.get("end") or "")
        if done:
            step["state"] = "erledigt"
        elif needs_data:
            step["state"] = "gesperrt"
        elif not started:
            step["state"] = "bereit"
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
        it["am_zug"] = wait_reason(it["text"]) or (
            "Artur" if "Entwurf steht" in it["text"] else "Claude"
        )
    fh_markers = [
        marker_point(m) for m in marker_list if str(m.get("file")).startswith(letters)
    ]
    # A checkbox line that only sums up the markers of its own file is shown
    # as a subtitle, not counted a second time.
    marked = {str(m.get("file")).split("/")[-1][:2] for m in marker_list}
    summary_lines = [it for it in anytime if f"{it['where'][-1].lower()}_" in marked]
    fh_items = [it for it in anytime if it not in summary_lines] + fh_markers
    fh_why = "Brauchen keine Ergebnisse, daher unabhängig von der Kapitelwoche."
    for it in summary_lines:
        fh_why += f" Sammelzeile {it['where']}: {it['text']}."
    if done_prosa:
        fh_why += (
            f" {', '.join(done_prosa)} ist erledigt (Artur, 14.11.2026); die"
            " Checkbox in offene_punkte.md ist noch nicht abgehakt."
        )
    fh_drafts = sum(
        int(m.get("prosa") or 0)
        for m in data.get("markers") or []
        if str(m.get("file")).startswith(letters)
    )
    if fh_drafts:
        fh_why += draft_note(fh_drafts)
    # No writing left (no point for Claude): only decisions remain.
    fh_writing = any(i.get("am_zug") == "Claude" for i in fh_items)
    fh_step: dict[str, Any] = {
        "key": "anhang_fh",
        "title": f"Anhang {' und '.join(PROSA_ANYTIME)}: "
        + ("Prosa schreiben" if fh_writing else "offene Entscheidungen"),
        "who": "Artur, auf Wunsch mit Claude-Entwurf",
        "why": fh_why,
        "items": fh_items,
        "state": "jetzt" if fh_items else "erledigt",
    }
    if fh_items and not fh_writing:
        # Only decisions or outside inputs left: nothing to write now.
        fh_step["state"] = "wartet"
        fh_step["wait_who"] = ", ".join(
            dict.fromkeys(str(i["am_zug"]) for i in fh_items)
        )

    # Literature research: the next search questions of literatur_recherche.md
    # plus the gaps in the text (literature_gaps, from the export). Done only
    # when there are no questions AND Kap. 2 (language style) and Kap. 3 cite
    # the bib without an \offen about literature (Artur, 15.11.2026: before,
    # "erledigt" only meant "no search question left").
    lit_gaps = [dict(g) for g in data.get("literatur_luecken") or []]
    lit_items = [
        {"text": q, "where": f"Suchfrage {n}"}
        for n, q in enumerate(data.get("literatur_fragen") or [], start=1)
    ] + lit_gaps
    lit_why = (
        "Suchfragen aus notizen/literatur_recherche.md (Nächste Suchfragen) und"
        " Lücken im Text: Kap. 2 (Sprachstil, Tonalität, Persona) und Kap. 3"
        " brauchen je eine Quelle aus references.bib und kein \\offen zur"
        " Literatur. Claude prüft Quellen vor Nutzung: erst nennen, wenn Titel,"
        " Venue, Jahr und DOI an einer zweiten Stelle bestätigt sind."
    )
    lit_step: dict[str, Any] = {
        "key": "literatur_tonalitaet",
        "title": "Literaturrecherche",
        "who": "Artur mit Claude",
        "why": lit_why,
        "items": lit_items,
        "state": "bereit" if lit_items else "erledigt",
    }
    # The checkbox list of the literature section; the text gaps above are
    # shown here too, not counted twice.
    lit_box = by_step.get("literatur", [])
    lit_see = [
        {**g, "text": f"{g['text']} (siehe auch Literaturrecherche)", "siehe_auch": "1"}
        for g in lit_gaps
    ]
    literatur_step: dict[str, Any] = {
        "key": "literatur",
        "title": "Literatur recherchieren",
        "who": "Artur mit Claude",
        "why": (
            "Kap. 2 und 3 hängen daran; Quellen vor Nutzung prüfen, keine"
            " Quelle zitieren, die nicht nachweislich existiert."
        ),
        "items": lit_box + lit_see,
        "state": "bereit" if lit_box or lit_gaps else "erledigt",
    }

    # Meeting with Prof. Wallach every Wednesday (Artur, 15.11.2026): the next
    # meeting is the Frist of the agenda; on the day and the day after, the
    # answers are entered instead.
    meet = next_meeting(today)
    after_meeting = (today - timedelta(days=1)).weekday() == MEETING_WEEKDAY
    if today.weekday() == MEETING_WEEKDAY or after_meeting:
        talk = {
            "text": "Antworten aus dem Gespräch in die Arbeit und in"
            " offene_punkte.md eintragen",
            "where": "Gespräch Mi"
            f" {(today if not after_meeting else today - timedelta(days=1)):%d.%m.}",
            "am_zug": "Artur und Claude",
            "tip": "Antworten unten in `notizen/wallach_agenda_"
            f"{(today if not after_meeting else today - timedelta(days=1)).isoformat()}"
            ".md` schreiben; im Thesis-Fenster „Antworten übertragen“, Claude"
            " trägt sie in Arbeit, Nachtrag und offene_punkte.md ein.",
        }
    else:
        talk = {
            "text": "Agenda vorbereiten: Fragen unten nach Dringlichkeit ordnen,"
            " Vor-dem-Datenfreeze-Punkte zuerst",
            "where": f"Gespräch Mi {meet:%d.%m.}",
            "am_zug": "Claude",
            "frist": meet.isoformat(),
            "tip": f"Entwurf in `notizen/wallach_agenda_{meet.isoformat()}.md`"
            " (Claude, im Thesis-Fenster „Agenda für Mittwoch“); du liest und"
            " kürzt ihn vor dem Gespräch.",
        }

    # Extended Summary (Anhang A, Pflicht >= 5.000 Wörter): a part is ready
    # once the prose of its chapter is done.
    chapter_done: dict[int, bool] = {}
    for st in row_steps + [prosa_now]:
        for c in st.get("chapters") or []:
            chapter_done[c] = st.get("state") == "erledigt"
    s_parts = [p for p in data.get("summary_parts") or [] if p.get("chapter")]
    s_total = sum(int(p["words"]) for p in s_parts)
    s_items: list[dict[str, Any]] = []
    for half in SUMMARY_HALVES:
        part_list = [p for p in s_parts if p["chapter"] in half]
        soll = sum(int(p["budget"]) for p in part_list)
        group = (
            f"Teil zu Kap. {half[0]}–{half[-1]} (Soll {soll:,} Wörter)"
            if half == tuple(range(half[0], half[-1] + 1))
            else f"Teil zu Kap. {half[0]} und {half[1]}–{half[-1]}"
            f" (Soll {soll:,} Wörter)"
        ).replace(",", ".")
        for p in part_list:
            words, budget = int(p["words"]), int(p["budget"])
            if words >= budget:
                continue
            ready = chapter_done.get(int(p["chapter"]), False)
            s_items.append(
                {
                    "text": f"{p['title']}: {words} von {budget} Wörtern"
                    + ("" if ready else f" (wartet auf Kap. {p['chapter']})"),
                    "where": f"Kap. {p['chapter']}",
                    "group": group,
                    **({"bereit": "1"} if ready else {}),
                }
            )
    s_box = by_step.get("summary", [])
    summary_step: dict[str, Any] = {
        "key": "summary",
        "title": f"Extended Summary (Anhang A): {s_total:,} von"
        f" {SUMMARY_MIN_WORDS:,} Wörtern".replace(",", "."),
        "who": "Artur, auf Wunsch mit Claude-Entwurf (KI-Hilfe in Anhang J)",
        "why": (
            "Englisch, Pflicht laut Modulbeschreibung. Wörter wie check_tex.py"
            " (nur Fließtext). Ein Teil ist bereit, sobald die Prosa seines"
            " Kapitels fertig ist (keine Marker, kein \\prosa mehr)."
            + (
                " Sammelpunkt in offene_punkte.md (Hochschule) abhaken, wenn"
                " die 5.000 erreicht sind."
                if s_box
                else ""
            )
        ),
        "items": s_items,
    }
    if s_parts and s_total >= SUMMARY_MIN_WORDS and not s_items:
        summary_step["state"] = "erledigt"
    elif any(i.get("bereit") for i in s_items):
        summary_step["state"] = "bereit"
    elif s_items or not s_parts:
        summary_step["state"] = "wartet"
        summary_step["wait_who"] = "Kapitelprosa"
    else:
        summary_step["state"] = "erledigt"

    # Anhang J (KI-Werkzeuge): runs along the whole work.
    j_items = [
        marker_point(m)
        for m in marker_list
        if str(m.get("file")).startswith("anhang/j_")
    ] + by_step.get("anhang_j", [])
    anhang_j_step: dict[str, Any] = {
        "key": "anhang_j",
        "title": "Anhang J: KI-Werkzeuge offenlegen",
        "who": "Artur, Claude trägt Werkzeug und Zweck vor",
        "why": (
            "Läuft mit: nach jeder Sitzung mit KI-Hilfe nachtragen (Werkzeug,"
            " Version, Zeitraum, Zweck, Umfang). Verlangt durch die"
            " Ehrenwörtliche Erklärung."
        ),
        "items": j_items,
        "state": "parallel" if j_items else "erledigt",
    }

    # The other appendices and the front matter (15.11.2026: their markers
    # were in no step). A, F, H, J and Kurzfassung/Abstract have steps.
    other_files = tuple(f"anhang/{x.lower()}_" for x in OTHER_APPENDICES) + tuple(
        f"vorspann/{n}.tex" for n in FRONT_MATTER
    )
    other_items = [
        marker_point(m)
        for m in marker_list
        if str(m.get("file")).startswith(other_files)
    ]
    anhaenge_step: dict[str, Any] = {
        "key": "anhaenge",
        "title": "Weitere Anhänge und Formalia",
        "who": "Artur liefert PDFs und Entscheidungen, Claude gleicht ab",
        "why": (
            f"Marker in Anhang {', '.join(OTHER_APPENDICES)}, Titelseite und"
            " Erklärung; brauchen keine Ergebnisse."
        ),
        "items": other_items,
        "state": "bereit" if other_items else "erledigt",
    }
    if any(str(m.get("file")).startswith("anhang/c_") for m in marker_list):
        anhaenge_step["why"] += (
            " Anhang C gilt laut Liste als fertig (PROSA_DONE), hat aber noch"
            " einen Marker."
        )

    # Figures: open points of notizen/abbildungsliste.md (from the export).
    fig_items = [dict(f) for f in data.get("abbildungen") or []]
    abbildungen_step: dict[str, Any] = {
        "key": "abbildungen",
        "title": "Abbildungen",
        "who": "Artur fotografiert, Claude bindet ein",
        "why": (
            "Offene Punkte aus notizen/abbildungsliste.md (Fotoliste und Tabelle);"
            " Screenshots A/B und Miner-Foto stehen zusätzlich unter Erhebung."
        ),
        "items": fig_items,
        "state": "bereit" if fig_items else "erledigt",
    }

    # Explanation texts against the thesis: a changed source of the texts is
    # work for now, not a weak signal (Artur, 15.11.2026).
    e_items: list[dict[str, Any]] = []
    for ch in sync.get("changed") or []:
        path = str(ch.get("path"))
        if path.split("/")[-1] in EXPLAIN_SOURCES:
            e_items.append(
                {
                    "text": f"geändert am {iso_to_de(str(ch.get('changed')))}:"
                    " Erklärtexte gegen Kap. 4, Anhang C und"
                    " hamster_texte_ab_vergleich.md prüfen, dann % Stand"
                    f" erneuern ({len(ch.get('entries') or [])} Stellen)",
                    "where": path.split("/")[-1],
                    "am_zug": "Claude",
                }
            )
    lab = data.get("lab_guard") or {}
    if lab.get("last_deploy") and str(lab["last_deploy"]) > LAB_STUDY_START:
        e_items.append(
            {
                "text": "Lab-Deploy am"
                f" {iso_to_de(str(lab['last_deploy'])[:10])}, nach dem"
                " Studienstart: Stimulus bis VP16 gegen v3 prüfen und als"
                " Abweichung dokumentieren, falls er sich geändert hat",
                "where": "deploy_ha_lab.py",
                "am_zug": "Artur",
            }
        )
    if lab and not lab.get("locked"):
        e_items.append(
            {
                "text": "Lab-Sperre in deploy_ha_lab.py ist aufgehoben: bis VP16"
                " nichts ins Lab deployen",
                "where": "deploy_ha_lab.py",
                "am_zug": "Artur",
            }
        )
    erklaer_step: dict[str, Any] = {
        "key": "erklaertexte",
        "title": "Erklärtexte gegen die Arbeit prüfen",
        "who": "Claude prüft, Artur bestätigt",
        "why": (
            "Quellen der Erklärtexte geändert (Dashboard, mvp_auto,"
            " build_sim_day, lab_studie). Das Labor bleibt bis VP16 auf v3."
        ),
        "items": e_items,
        "state": "jetzt" if e_items else "erledigt",
    }

    # Analysis preparation in parts, each ticked by its code (Artur,
    # 15.11.2026). An open point that a part covers is not listed twice.
    parts = [dict(p) for p in data.get("auswertung_teile") or []]
    a_items: list[dict[str, Any]] = []
    a_ticks: list[str] = []
    a_rest = list(by_step.get("auswertung_vorb", []))
    for p in parts:
        covers = str(p.pop("covers", ""))
        hit = [i for i in a_rest if covers and covers in i["text"]]
        a_rest = [i for i in a_rest if i not in hit]
        if p.pop("done", False):
            a_items.append({**p, "erledigt": "1"})
            a_ticks += [i["text"][:60] for i in hit]
        else:
            a_items.append(p)
    a_items += a_rest
    a_open = [i for i in a_items if not i.get("erledigt")]
    auswertung_step: dict[str, Any] = {
        "key": "auswertung_vorb",
        "title": "Auswertung vorbereiten (synthetische Daten)",
        "who": "Dev",
        "why": (
            "Kann jetzt mit synthetischen Daten laufen; echte Daten erst nach"
            " dem Datenfreeze. Ein Teil ist abgehakt, sobald sein Code im Repo"
            " steht."
            + (
                " Checkbox in offene_punkte.md noch abhaken: "
                + "; ".join(a_ticks)
                + "."
                if a_ticks
                else ""
            )
        ),
        "items": a_items,
        "state": "bereit" if a_open else "erledigt",
    }

    # Colloquium: possible from 15.11.2026; done with its checkbox.
    k_box = by_step.get("kolloquium", [])
    kolloquium_step: dict[str, Any] = {
        "key": "kolloquium",
        "title": "Kolloquium vorbereiten",
        "who": "Artur mit Claude",
        "why": (
            "20 Min. Vortrag und 20 Min. Befragung, zählt zur Hälfte der"
            " Modulnote; frühestens ab 15.11.2026 (§ 11 Abs. 1 AMPO)."
        ),
        "items": (
            [{"text": t, "where": "Kolloquium"} for t in KOLLOQUIUM_PLAN] + k_box
            if k_box
            else []
        ),
        "state": (
            "erledigt"
            if not k_box
            else "bereit" if today >= KOLLOQUIUM_FROM else "spaeter"
        ),
    }

    # Cleaned code export for the submission, Frist 10.01.2027.
    an_box = by_step.get("anlagen", [])
    anlagen_step: dict[str, Any] = {
        "key": "anlagen",
        "title": "Anlagen zur Abgabe: bereinigter Code-Export",
        "who": "Claude bereitet vor, Artur prüft",
        "why": "LaTeX-Quellen, Dokumente und Programme gehören zur Abgabe.",
        "items": (
            [
                {"text": t, "where": "Anlagen", "frist": ANLAGEN_FRIST}
                for t in ANLAGEN_PLAN
            ]
            + [{**i, "frist": ANLAGEN_FRIST} for i in an_box]
            if an_box
            else []
        ),
        "state": "bereit" if an_box else "erledigt",
    }

    # The data freeze itself (Artur, 15.11.2026): until now the plan only
    # listed what must be decided before it. Done once the record file of the
    # freeze exists (data/study/datenfreeze.txt in BitGridAI, gitignored).
    df_end = str(freeze_row["end"]) if freeze_row else None
    df_start = str(freeze_row["start"]) if freeze_row else None
    df_items: list[dict[str, Any]] = []
    if df_end and not data.get("datenfreeze_done"):
        for text, who, tip in DATENFREEZE_PLAN:
            df_point: dict[str, Any] = {
                "text": text,
                "where": "Datenfreeze",
                "frist": df_end,
                "tip": tip,
            }
            if who:
                df_point["am_zug"] = who
            if df_start and df_start > today_iso:
                df_point["wartet_bis"] = df_start
            df_items.append(df_point)
    datenfreeze_step: dict[str, Any] = {
        "key": "datenfreeze",
        "title": "Datenfreeze durchführen"
        + (f" (bis {iso_to_de(df_end)[:6]})" if df_end else ""),
        "who": "Artur, Claude prüft die Prüfsummen",
        "why": (
            "Nach VP16: Daten exportieren, sichern und ab dann nicht mehr"
            " ändern. Erledigt, sobald " + DATENFREEZE_RECORD + " existiert."
        ),
        "items": df_items,
        "state": "erledigt" if not df_items else "bereit",
    }

    # Hochschule: points with a Frist first, by date.
    fristen_items = sorted(
        by_step.get("fristen", []),
        key=lambda i: (0, i["frist"]) if i.get("frist") else (1, ""),
    )

    n_changed = len(sync.get("changed") or [])
    n_missing = len(bf.get("missing") or [])
    release_state = release_check(
        data.get("tex_status"),
        bool(stale),
        [
            f"{n} {what}"
            for n, what in (
                (n_changed, "zitierte Dateien seit dem Stand geändert"),
                (n_missing, "Befunde fehlen im Text"),
            )
            if n
        ],
    )
    # Questions for Prof. Wallach: only here, never in "Vorbereiten". Points of
    # the Hochschule section that name him are shown too ("siehe auch"), but
    # they stay counted there (``siehe_auch``: not counted here).
    wallach_items = (
        list(by_step.get("wallach", []))
        + [
            {**i, "text": f"{i['text']} (siehe auch Hochschule)", "siehe_auch": "1"}
            for i in by_step.get("fristen", [])
            if "Wallach" in i["text"]
        ]
        + [
            {**i, "text": f"{i['text']} (siehe auch Schritt 7)", "siehe_auch": "1"}
            for i in fh_items
            if i.get("am_zug") == "Wallach"
        ]
    )
    # "Parallel: Erhebung" in groups. The questions of the session export
    # inherit the Termin of the export itself; SoSci points that need the data
    # wait for Annika; points already in another step are shown, not counted.
    par_in = by_step.get("parallel", [])
    export_wait: str | None = None
    for pt in par_in:
        if pt["text"].startswith("Sitzungsexport"):
            # Its date stands in the text without "(Termin ...)":
            # "Mo/Di 16./17.11.2026" counts like "(Termin 16./17.11.2026)".
            m = _EXPORT_DAYS.search(pt["text"])
            when = parse_termin(f"(Termin {m.group(0)})", today) if m else None
            flag_wait(pt, when)
            export_wait = pt.get("wartet_bis")
    par_items: list[dict[str, Any]] = []
    for it in par_in:
        it = dict(it)
        where = str(it.get("where"))
        if where.startswith("SoSci"):
            it["group"] = GROUP_SOSCI
            if it["text"].startswith(NEEDS_SOSCI_DATA):
                it["am_zug"] = "Annika"
            elif it["text"].startswith(NEEDS_WALLACH):
                it["am_zug"] = "Wallach"
            if wait_reason(it["text"]) == "Person":
                it["siehe_auch"] = "1"
                it["text"] += " (siehe auch Schritt 7)"
        elif any(w in it["text"] for w in MEDIA_WORDS):
            it["group"] = GROUP_MEDIA
        else:
            it["group"] = GROUP_LAB
            if where.endswith("(Fragen)") and export_wait and not it.get("wartet_bis"):
                it["wartet_bis"] = export_wait
        par_items.append(it)
    order = {GROUP_LAB: 0, GROUP_SOSCI: 1, GROUP_MEDIA: 2}
    par_items.sort(key=lambda i: order.get(str(i.get("group")), 9))

    def phase(name: str, *group: dict[str, Any]) -> list[dict[str, Any]]:
        for st in group:
            st["phase"] = name
        return list(group)

    # Order (Artur, 15.11.2026): this week's loop, then the prose of the other
    # chapters (they may start any time), then what runs alongside, then the
    # Hochschule. Prose used to stand behind research and findings.
    steps: list[dict[str, Any]] = [
        *phase(
            PHASE_WEEK,
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
                "why": "Fakten und Entscheidungen, die nur du kennst (OFFEN im"
                " Text).",
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
                        (
                            "Erledigt, wenn check_tex 0 Befunde meldet, der"
                            " Abgleich keine neue Meldung hat und alles"
                            " committet und gepusht ist."
                            if release_state.get("state") != "erledigt"
                            else "check_tex 0 Befunde, Abgleich ohne neue"
                            " Meldung, alles committet und gepusht."
                        ),
                        str(release_state.pop("note", "")),
                    ]
                ).strip(),
                "items": [],
                **release_state,
            },
            erklaer_step,
            {
                "key": "wallach",
                "title": f"Gespräch mit Prof. Wallach (Mi {meet:%d.%m.})",
                "who": "Artur mit Prof. Wallach",
                "why": (
                    "Jeden Mittwoch. Bis zum Gespräch die Agenda, danach die"
                    " Antworten in die Arbeit; darunter die gesammelten Fragen."
                ),
                "items": [talk] + wallach_items,
                "state": "jetzt",
            },
        ),
        *phase(
            PHASE_CHAPTERS,
            {
                "key": "naechste",
                "title": "Vorbereiten: "
                + (f"{nxt['write']} ({nxt['week']})" if nxt else "nächste Woche"),
                "who": "Artur mit Claude",
                "why": f"Parallel dann: {nxt['parallel']}" if nxt else "",
                "items": by_step.get("naechste", []) + findings_next,
            },
            *row_steps,
            {
                "key": "spaeter_befunde",
                "title": "Befunde der anderen Kapitel übernehmen",
                "who": "Claude setzt Marker, Artur wählt aus",
                "why": (
                    "Zahlen ändern sich täglich: Stichtag beim Übernehmen"
                    " setzen und in der Schreibwoche erneuern."
                ),
                "items": findings_far,
            },
        ),
        *phase(
            PHASE_SIDE,
            fh_step,
            anhang_j_step,
            anhaenge_step,
            abbildungen_step,
            {
                "key": "parallel",
                "title": "Parallel: " + (str(now.get("parallel")) if now else "Studie"),
                "who": "Artur",
                "why": "Läuft neben dem Schreiben, muss vor dem Datenfreeze"
                " fertig sein.",
                "items": par_items,
            },
            datenfreeze_step,
            auswertung_step,
            summary_step,
            lit_step,
            literatur_step,
        ),
        *phase(
            PHASE_SUBMIT,
            {
                "key": "fristen",
                "title": "Hochschule",
                "who": "Artur",
                "why": "Punkte mit Frist zuerst; der Rest kann jederzeit"
                " erledigt werden.",
                "items": fristen_items,
            },
            anlagen_step,
            kolloquium_step,
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
        ),
    ]
    if by_step.get("sonstiges"):
        steps.append(
            {
                "key": "sonstiges",
                "title": "Sonstiges",
                "who": "Artur",
                "why": "",
                "items": by_step["sonstiges"],
                "phase": PHASE_SUBMIT,
            }
        )
    # Tasks missing in offene_punkte.md go to their step, marked; every step
    # gets its "So gehst du vor" (Artur, 15.11.2026).
    by_key = {st["key"]: st for st in steps}
    # ``list_gaps`` comes from the export (list_gaps(data) there).
    for raw_gap in data.get("list_gaps") or []:
        gap = dict(raw_gap)
        gap_step = by_key.get(str(gap.pop("step", "")))
        if gap_step is not None:
            gap_who = wait_reason(gap["text"])
            if gap_who:
                gap["am_zug"] = gap_who
            gap_step["items"] = list(gap_step["items"]) + [gap]
    for st in steps:
        # Open points of the step: what the card and BitHamster count
        # (copies marked "siehe auch" are counted where they belong).
        st["offen"] = sum(
            1 for it in st["items"] if not (it.get("erledigt") or it.get("siehe_auch"))
        )
        tip_key = "prosa_bereit" if st["key"].startswith("prosa_") else st["key"]
        if tip_key in STEP_TIPS:
            st["tip"] = STEP_TIPS[tip_key]
        for it in st["items"]:
            if it.get("tip") or it.get("erledigt"):
                continue
            solution = item_tip(st["key"], it)
            if solution:
                it["tip"] = solution
    first = True
    for s in steps:
        items = [i for i in s["items"] if not i.get("erledigt")]
        waits = [i["wartet_bis"] for i in items if i.get("wartet_bis")]
        if any(frist_due(i, today) for i in items if not i.get("siehe_auch")):
            # A Frist close or over: this is work for now, whatever else.
            s["state"] = "jetzt"
        elif s["key"] == "freeze" and not frozen:
            s["state"] = "gesperrt"
        elif waits and len(waits) == len(items) and s["key"] != "wallach":
            # Every point waits for a date: no work now, "jetzt" moves on.
            s["state"] = "wartet"
            s["wait_until"] = min(waits)
        elif (
            items
            and "state" not in s
            and all(
                i.get("wartet_bis") or i.get("am_zug") in WAIT_REASONS.values()
                for i in items
            )
        ):
            # Every point waits for a date or an outside input.
            s["state"] = "wartet"
            s["wait_who"] = ", ".join(
                dict.fromkeys(
                    str(i["am_zug"])
                    for i in items
                    if i.get("am_zug") in WAIT_REASONS.values()
                )
            )
        elif "state" in s:
            pass  # set by the step itself
        elif s["key"] == "parallel":
            s["state"] = "parallel" if items else "erledigt"
        elif s["key"] in ("naechste", "spaeter_befunde", "fristen", "sonstiges"):
            # The schedule is a target week, not a lock (Artur, 15.11.2026).
            s["state"] = "bereit" if items else "erledigt"
        elif s["key"] == "pruefen":
            s["state"] = "offen"
        elif items or s["key"] == "prosa":
            s["state"] = "jetzt" if first else "offen"
            first = False
        else:
            s["state"] = "erledigt"
        s.pop("chapters", None)
    return steps


def stamp_done(
    steps: list[dict[str, Any]], ledger: dict[str, str], today: date
) -> dict[str, str]:
    """Give every step its stable number ``nr`` and done steps ``done_at``.

    ``ledger`` maps step key to the ISO day the step was first seen
    "erledigt". The day stays as long as the step stays done; a step that
    reopens loses its entry, so a later completion gets the new day. Returns
    the updated ledger (the caller persists it).
    """
    out: dict[str, str] = {}
    for nr, step in enumerate(steps, start=1):
        step["nr"] = nr
        key = str(step.get("key", ""))
        if step.get("state") == "erledigt" and key:
            out[key] = ledger.get(key) or today.isoformat()
            step["done_at"] = out[key]
    return out
