"""Split an agreement into clauses using common Indian drafting heading styles."""

import re

from leaseguard.constants import MAX_HEADING_CHARS, MIN_CLAUSE_CHARS
from leaseguard.models import Clause

_NUMBERING = r"(?:clause|article|section)\s+\d+[.:)]?|\d{1,2}(?:\.\d{1,2})*[.)]|[IVXLC]{1,6}[.)]"
_HEADING = re.compile(rf"^\s*(?:{_NUMBERING}|[A-Z][A-Za-z &/-]{{2,40}}:)", re.IGNORECASE)
_HEADING_PARTS = re.compile(rf"^\s*({_NUMBERING})?\s*([^:.]{{0,50}})", re.IGNORECASE)
_MIN_HEADED_BLOCKS = 3


def segment_clauses(text: str) -> list[Clause]:
    """Return clauses in document order.

    Headings may be numbered ("1.", "2)", "3.1."), Roman ("IV."), "Clause 4"
    or a short title ending in a colon. Without enough headings, blank-line
    separated paragraphs are used instead.

    Args:
        text: Full agreement text.

    Returns:
        Clauses with sequential indexes, skipping fragments that are too short.
    """
    blocks = _headed_blocks(text)
    if len(blocks) < _MIN_HEADED_BLOCKS:
        blocks = [[p.strip()] for p in re.split(r"\n\s*\n", text) if p.strip()]
    clauses: list[Clause] = []
    for block in blocks:
        body = " ".join(block)
        if len(body) >= MIN_CLAUSE_CHARS:
            clauses.append(Clause(index=len(clauses), heading=heading_of(block[0]), text=body))
    return clauses


def heading_of(first_line: str) -> str:
    """Return a short heading such as "3. Security Deposit".

    Args:
        first_line: The first line of a clause.

    Returns:
        The clause number and title, or "Clause" if none can be found.
    """
    match = _HEADING_PARTS.match(first_line)
    number = (match.group(1) or "").strip() if match else ""
    title = match.group(2).strip() if match else ""
    return f"{number} {title}".strip()[:MAX_HEADING_CHARS] or "Clause"


def _headed_blocks(text: str) -> list[list[str]]:
    blocks: list[list[str]] = []
    for line in (raw.strip() for raw in text.splitlines()):
        if not line:
            continue
        if _HEADING.match(line) or not blocks:
            blocks.append([line])
        else:
            blocks[-1].append(line)
    return blocks
