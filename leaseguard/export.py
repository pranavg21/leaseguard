"""Build the lawyer consultation packet as a PDF."""

import io
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import StyleSheet1, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Flowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer

from leaseguard.constants import PDF_MARGIN_MM
from leaseguard.knowledge import CATEGORY_TITLES
from leaseguard.models import AnalysisReport, Finding, RiskLevel, Step

DISCLAIMER = (
    "LeaseGuard provides information, not legal advice. Please review this packet with a qualified "
    "lawyer before acting on it."
)
_FOOTER_Y_MM = 10
_FOOTER_FONT_SIZE = 8
_GAP_MM = 4


def para(text: str, style: str, styles: StyleSheet1) -> Paragraph:
    """Build an escaped paragraph in a named style.

    Args:
        text: Plain text (escaped here, never treated as markup).
        style: Stylesheet style name.
        styles: ReportLab stylesheet.

    Returns:
        The paragraph.
    """
    return Paragraph(escape(text), styles[style])


def finding_block(finding: Finding, styles: StyleSheet1) -> KeepTogether:
    """Render one flagged finding as a block that never splits across pages.

    Args:
        finding: The finding to render.
        styles: ReportLab stylesheet.

    Returns:
        The flowable block.
    """
    status = "verified quote" if finding.quote_verified else "quote NOT verified"
    title = f"{finding.risk.label.upper()} - {finding.clause.heading} ({CATEGORY_TITLES[finding.category]})"
    return KeepTogether(
        [
            para(title, "Heading3", styles),
            para(f'"{finding.quote}" ({status})', "Italic", styles),
            para(finding.reason, "BodyText", styles),
            para(f"Question for your lawyer: {finding.question_for_lawyer}", "BodyText", styles),
            Spacer(1, _GAP_MM * mm),
        ]
    )


def _sections(report: AnalysisReport, styles: StyleSheet1) -> list[Flowable]:
    flagged = sorted((f for f in report.findings if f.risk is not RiskLevel.FAIR), key=lambda f: -f.risk.rank)
    story: list[Flowable] = [para("Flagged clauses", "Heading2", styles)]
    story += [finding_block(f, styles) for f in flagged] or [para("No clauses were flagged.", "BodyText", styles)]
    gaps = [gap.message for gap in report.gaps]
    if not report.coverage_complete:
        gaps = ["Coverage audit skipped because some clauses could not be evaluated."]
    for heading, lines in (("Missing protections", gaps), ("Notes for your situation", report.context_notes)):
        if lines:
            story += [para(heading, "Heading2", styles), *(para(line, "BodyText", styles) for line in lines)]
    return story


def steps_flowables(steps: list[Step], styles: StyleSheet1) -> list[Flowable]:
    """Render an ordered action plan as numbered paragraphs.

    Args:
        steps: The steps.
        styles: ReportLab stylesheet.

    Returns:
        A heading followed by one paragraph per step.
    """
    lines = [f"{n}. {step.title}: {step.detail}" for n, step in enumerate(steps, start=1)]
    return [para("Your next steps", "Heading2", styles), *(para(line, "BodyText", styles) for line in lines)]


def key_terms_flowables(report: AnalysisReport, styles: StyleSheet1) -> list[Flowable]:
    """Render the key terms at a glance.

    Args:
        report: The analysis report.
        styles: ReportLab stylesheet.

    Returns:
        A heading followed by one line per term.
    """
    lines = [f"{t.label}: {t.value}" + (f' - "{t.quote}"' if t.quote else "") for t in report.key_terms]
    return [para("Key terms at a glance", "Heading2", styles), *(para(line, "BodyText", styles) for line in lines)]


def draw_footer(canvas: Canvas, doc: SimpleDocTemplate) -> None:
    """Draw the page footer with the disclaimer and page number.

    Args:
        canvas: The page canvas.
        doc: The document being built.
    """
    canvas.saveState()
    canvas.setFont("Helvetica", _FOOTER_FONT_SIZE)
    canvas.drawString(PDF_MARGIN_MM * mm, _FOOTER_Y_MM * mm, f"LeaseGuard - information only - page {doc.page}")
    canvas.restoreState()


def render_pdf(story: list[Flowable], title: str) -> bytes:
    """Render flowables to an A4 PDF with metadata and the standard footer.

    Args:
        story: The document content.
        title: PDF title metadata.

    Returns:
        PDF bytes.
    """
    buffer = io.BytesIO()
    margin = PDF_MARGIN_MM * mm
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, title=title, author="LeaseGuard", lang="en-IN", leftMargin=margin, rightMargin=margin
    )
    doc.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)
    return buffer.getvalue()


def build_packet(report: AnalysisReport) -> bytes:
    """Build the consultation packet: flagged clauses worst first, gaps and notes.

    Args:
        report: The analysis report.

    Returns:
        PDF bytes.
    """
    styles = getSampleStyleSheet()
    context = report.context
    header = [
        para("LeaseGuard consultation packet", "Title", styles),
        para(DISCLAIMER, "BodyText", styles),
        para(f"Reviewed as: {context.role.value}. State: {context.state}.", "BodyText", styles),
    ]
    story = [*header, *key_terms_flowables(report, styles), *_sections(report, styles)]
    return render_pdf([*story, *steps_flowables(report.next_steps, styles)], "LeaseGuard consultation packet")
