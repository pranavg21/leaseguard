"""Endpoints for the deposit-recovery dossier."""

from fastapi import APIRouter, Request
from fastapi.responses import Response

from leaseguard.api.dossier_schemas import DossierRequest
from leaseguard.api.dossier_views import dossier_view
from leaseguard.api.routes import llm_client
from leaseguard.api.views import JsonDict
from leaseguard.dossier.dates import today_ist
from leaseguard.dossier.models import Dossier
from leaseguard.dossier.pdf import build_dossier_pdf
from leaseguard.dossier.service import build_dossier

router = APIRouter(prefix="/api/dossier")


def _build(body: DossierRequest, request: Request) -> Dossier:
    client = llm_client(request)
    lease = body.lease.resolve() if body.lease else None
    uploads = [item.to_upload() for item in body.files]
    return build_dossier(uploads, lease, body.parties.to_parties(), client, body.language)


@router.post("")
def dossier(body: DossierRequest, request: Request) -> JsonDict:
    """Build the dossier and return it for review.

    Args:
        body: The validated request.
        request: The incoming request.

    Returns:
        Evidence index, timeline, ledger, contradictions and checklist.
    """
    return dossier_view(_build(body, request))


@router.post("/pdf")
def dossier_pdf(body: DossierRequest, request: Request) -> Response:
    """Build the dossier PDF with the certificate and demand notice drafts.

    Args:
        body: The validated request.
        request: The incoming request.

    Returns:
        The PDF as an attachment.
    """
    pdf = build_dossier_pdf(_build(body, request), today_ist())
    headers = {"Content-Disposition": 'attachment; filename="leaseguard-dossier.pdf"', "Cache-Control": "no-store"}
    return Response(content=pdf, media_type="application/pdf", headers=headers)
