"""Next steps for recovering a deposit, built from the dossier's facts."""

from leaseguard.constants import NOTICE_REPLY_DAYS
from leaseguard.dossier.models import Dossier, EventKind
from leaseguard.dossier.timeline import first_of
from leaseguard.steps import FREE_LEGAL_AID, Step

CERTIFICATE_STEP = Step(
    "Complete the Section 63 certificate",
    "Fill in and sign Part A, and have an expert complete Part B. Keep the hash report with it, and do not edit "
    "the original files: any change alters their SHA-256 fingerprint.",
)
LOK_ADALAT_STEP = Step(
    "Try a free pre-litigation Lok Adalat",
    "Your District Legal Services Authority can take up the dispute before any case is filed. There is no court "
    "fee, and a settlement there is final and binding.",
)


def demand_step(dossier: Dossier) -> Step:
    """Send the demand notice, or keep proof of the one already sent.

    Args:
        dossier: The dossier.

    Returns:
        The step.
    """
    sent = first_of(dossier.events, EventKind.DEMAND)
    if sent and sent.when:
        return Step(
            "Keep proof of your demand",
            f"You asked for a refund on {sent.when:%d %B %Y} "
            f"(Annexure {sent.annexure}). Send the formal notice too, and keep the postal receipt.",
        )
    return Step(
        "Send the demand notice",
        f"Send the draft notice by registered post or speed post with "
        f"acknowledgement, and allow {NOTICE_REPLY_DAYS} days for a reply.",
    )


def forum_step(dossier: Dossier) -> Step:
    """Point to the right forum and the time limit.

    Args:
        dossier: The dossier.

    Returns:
        The step.
    """
    deadline = dossier.limitation_deadline
    limit = f" File well before about {deadline:%d %B %Y}." if deadline else ""
    return Step(
        "If there is no refund, choose the forum with a lawyer",
        "Deposit disputes with a private landlord "
        "usually go to the Rent Authority under your state's law or to a civil court, not the consumer "
        f"commission.{limit}",
    )


def dossier_steps(dossier: Dossier) -> list[Step]:
    """Build the ordered action plan for recovering the deposit.

    Args:
        dossier: The dossier.

    Returns:
        Steps in order: fix gaps, demand, certificate, free mediation, forum, free legal aid.
    """
    fix = [Step("Fill the gaps in your evidence", " ".join(dossier.checklist))] if dossier.checklist else []
    return [*fix, demand_step(dossier), CERTIFICATE_STEP, LOK_ADALAT_STEP, forum_step(dossier), FREE_LEGAL_AID]
