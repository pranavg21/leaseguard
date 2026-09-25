"""Render the dossier as one PDF: index, list of dates, ledger, checklist, certificate and notice."""

from datetime import date

from reportlab.lib import colors
from reportlab.lib.styles import StyleSheet1, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Flowable, LongTable, PageBreak, TableStyle

from leaseguard.dossier.certificate import CertificatePart, build_certificate
from leaseguard.dossier.models import EVENT_TITLES, Contradiction, Dossier
from leaseguard.dossier.notice import build_notice, rupees
from leaseguard.export import para, render_pdf

DISCLAIMER = "Prepared with LeaseGuard. Information, not legal advice. Verify every entry before relying on it."
_GRID = TableStyle(
    [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
    ]
)


def table(rows: list[list[str]], widths: list[float], styles: StyleSheet1) -> LongTable:
    """Build a bordered table whose cells wrap, with a repeating header row.

    Args:
        rows: Header row first, then data rows.
        widths: Column widths in millimetres.
        styles: ReportLab stylesheet.

    Returns:
        The table.
    """
    cells = [[para(cell, "BodyText", styles) for cell in row] for row in rows]
    return LongTable(cells, colWidths=[w * mm for w in widths], repeatRows=1, style=_GRID)


def annexures(contradiction: Contradiction) -> str:
    """Name the annexures a contradiction relies on, without repeating one.

    Args:
        contradiction: The contradiction.

    Returns:
        For example "A-1" or "A-1 and A-3".
    """
    labels = dict.fromkeys((contradiction.earlier.annexure, contradiction.later.annexure))
    return " and ".join(labels)


def index_section(dossier: Dossier, styles: StyleSheet1) -> list[Flowable]:
    """Index of annexures with SHA-256 hash values."""
    rows = [["Annexure", "File", "Type", "SHA-256"]]
    rows += [[f.annexure, f.name, f.kind.value, f.sha256] for f in dossier.files]
    return [para("Index of annexures", "Heading2", styles), table(rows, [20, 40, 20, 94], styles)]


def dates_section(dossier: Dossier, styles: StyleSheet1) -> list[Flowable]:
    """List of dates and events, each with its verbatim source quote."""
    rows = [["Date", "Event", "By", "Source (verbatim)", "Annexure"]]
    rows += [
        [
            e.when.strftime("%d-%m-%Y") if e.when else "DATE NEEDED",
            EVENT_TITLES[e.kind],
            e.actor or "-",
            e.quote,
            e.annexure,
        ]
        for e in dossier.events
    ]
    return [para("List of dates and events", "Heading2", styles), table(rows, [25, 27, 25, 77, 20], styles)]


def findings_section(dossier: Dossier, styles: StyleSheet1) -> list[Flowable]:
    """Deposit ledger, contradictions, limitation reminder and checklist."""
    ledger = dossier.ledger
    lines = [
        f"Deposit: {rupees(ledger.deposit)} (source: {ledger.deposit_source}).",
        f"Refunded: {rupees(ledger.refunded)}. Deductions claimed: {rupees(ledger.deductions_claimed)}.",
        f"Outstanding before disputed deductions: {rupees(ledger.outstanding)}.",
        *(f"Contradiction: {c.message} (Annexure {annexures(c)})." for c in dossier.contradictions),
    ]
    if dossier.limitation_deadline:
        lines.append(
            f"Reminder: money claims generally must be filed within three years (Limitation Act, 1963). "
            f"Counting from move-out, that is about {dossier.limitation_deadline:%d %B %Y}. Confirm with a lawyer."
        )
    lines += [f"To do: {item}" for item in dossier.checklist]
    return [para("Deposit ledger and findings", "Heading2", styles), *(para(x, "BodyText", styles) for x in lines)]


def certificate_section(dossier: Dossier, styles: StyleSheet1) -> list[Flowable]:
    """Certificate in the form of the BSA Schedule: Part A, the enclosed hash report, then Part B."""
    draft = build_certificate(dossier.parties, dossier.files)
    rows = [["Annexure", "File", "Bytes", "SHA-256"], *(list(row) for row in draft.records)]
    return [
        para(draft.title, "Heading2", styles),
        para(draft.note, "Italic", styles),
        *part_flowables(draft.part_a, styles),
        para("Hash report (enclosed with the certificate)", "Heading3", styles),
        table(rows, [20, 44, 16, 94], styles),
        PageBreak(),
        *part_flowables(draft.part_b, styles),
    ]


def part_flowables(part: CertificatePart, styles: StyleSheet1) -> list[Flowable]:
    """Render one certificate part: its heading, then each line as a paragraph.

    Args:
        part: Part A or Part B.
        styles: ReportLab stylesheet.

    Returns:
        The flowables.
    """
    return [para(part.heading, "Heading3", styles), *(para(line, "BodyText", styles) for line in part.lines)]


def dossier_story(dossier: Dossier, today: date, styles: StyleSheet1) -> list[Flowable]:
    """Assemble every section in filing order.

    Args:
        dossier: The dossier.
        today: Date printed on the demand notice.
        styles: ReportLab stylesheet.

    Returns:
        The flowables for the whole document.
    """
    notice = [para(line, "BodyText", styles) for line in build_notice(dossier, today)]
    return [
        para("Deposit-recovery dossier", "Title", styles),
        para(DISCLAIMER, "Italic", styles),
        *index_section(dossier, styles),
        *dates_section(dossier, styles),
        *findings_section(dossier, styles),
        PageBreak(),
        *certificate_section(dossier, styles),
        PageBreak(),
        para("Demand notice (draft)", "Heading2", styles),
        *notice,
    ]


def build_dossier_pdf(dossier: Dossier, today: date) -> bytes:
    """Render the complete dossier.

    Args:
        dossier: The dossier.
        today: Date printed on the demand notice.

    Returns:
        PDF bytes.
    """
    story = dossier_story(dossier, today, getSampleStyleSheet())
    return render_pdf(story, "LeaseGuard deposit-recovery dossier")
