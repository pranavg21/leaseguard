"""API endpoints. Handlers are synchronous so FastAPI runs them in a worker thread."""

from fastapi import APIRouter, Request
from fastapi.responses import Response

from leaseguard import __version__
from leaseguard.ai import LLMClient
from leaseguard.api.schemas import (
    AnalyzeRequest,
    AskRef,
    AskRequest,
    CompareRequest,
    ContextIn,
    DocumentIn,
    ReportRef,
)
from leaseguard.api.views import JsonDict, answer_view, change_view, report_view
from leaseguard.compare import compare_reports
from leaseguard.engine import analyse, cached_report
from leaseguard.export import build_packet
from leaseguard.knowledge import STATES
from leaseguard.models import AnalysisReport, Language, Role
from leaseguard.qa import ask
from leaseguard.sample import SAMPLE_LEASE, SAMPLE_LEASE_REVISED
from leaseguard.sample_evidence import SAMPLE_EVIDENCE
from leaseguard.telemetry import Recorder, analysis_event

router = APIRouter(prefix="/api")


def llm_client(request: Request) -> LLMClient:
    """Return the AI client configured for this app.

    Args:
        request: The incoming request.

    Returns:
        The client stored on the application state.
    """
    client: LLMClient = request.app.state.llm_client
    return client


def _analyse(request: Request, document: DocumentIn, context: ContextIn) -> AnalysisReport:
    client = llm_client(request)
    report = analyse(document.resolve(), context.to_context(), client)
    recorder: Recorder = request.app.state.recorder
    recorder.record(analysis_event(report, client.name))
    return report


def _report_for(request: Request, body: AnalyzeRequest | ReportRef) -> AnalysisReport:
    """Return the report a follow-up request refers to.

    A ``report_id`` reuses the cached report, so the agreement is not uploaded,
    decoded or parsed again. A full body is analysed (a cache hit if unchanged).
    """
    if isinstance(body, ReportRef):
        return cached_report(body.report_id)
    return analyse(body.document.resolve(), body.context.to_context(), llm_client(request))


@router.get("/health")
def health() -> JsonDict:
    """Report liveness for Cloud Run.

    Returns:
        Status and version.
    """
    return {"status": "ok", "version": __version__}


@router.get("/meta")
def meta(request: Request) -> JsonDict:
    """List the options the interface offers, so the frontend hard-codes nothing.

    Args:
        request: The incoming request.

    Returns:
        Roles, states, languages and the active AI mode.
    """
    return {
        "roles": [role.value for role in Role],
        "states": list(STATES),
        "languages": [language.value for language in Language],
        "ai_mode": llm_client(request).name,
    }


@router.get("/sample")
def sample() -> JsonDict:
    """Return built-in sample agreements for trying the app without uploading.

    Returns:
        An original and a revised sample agreement, and sample dispute evidence files.
    """
    return {"original": SAMPLE_LEASE, "revised": SAMPLE_LEASE_REVISED, "evidence": SAMPLE_EVIDENCE}


@router.post("/analyze")
def analyze(body: AnalyzeRequest, request: Request) -> JsonDict:
    """Analyse an agreement.

    Args:
        body: The validated request.
        request: The incoming request.

    Returns:
        The report.
    """
    return report_view(_analyse(request, body.document, body.context))


@router.post("/ask")
def ask_question(body: AskRef | AskRequest, request: Request) -> JsonDict:
    """Answer a question about an agreement with a verified quote.

    Args:
        body: A ``report_id`` from an earlier review, or the agreement itself, plus the question.
        request: The incoming request.

    Returns:
        The grounded answer.
    """
    report = _report_for(request, body)
    clauses = [finding.clause for finding in report.findings]
    return answer_view(ask(body.question, clauses, llm_client(request), report.context.language))


@router.post("/compare")
def compare(body: CompareRequest, request: Request) -> JsonDict:
    """Compare an original and a revised draft.

    Args:
        body: The validated request.
        request: The incoming request.

    Returns:
        One row per category, worst changes first.
    """
    original = _analyse(request, body.original, body.context)
    revised = _analyse(request, body.revised, body.context)
    return {"changes": [change_view(change) for change in compare_reports(original, revised)]}


@router.post("/packet")
def packet(body: ReportRef | AnalyzeRequest, request: Request) -> Response:
    """Build the lawyer consultation packet PDF.

    Args:
        body: A ``report_id`` from an earlier review, or the agreement itself.
        request: The incoming request.

    Returns:
        The PDF as an attachment.
    """
    pdf = build_packet(_report_for(request, body))
    headers = {"Content-Disposition": 'attachment; filename="leaseguard-packet.pdf"', "Cache-Control": "no-store"}
    return Response(content=pdf, media_type="application/pdf", headers=headers)
