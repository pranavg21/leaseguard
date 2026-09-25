"""Rules that depend on who the user is and where the property is."""

from leaseguard.constants import REGISTRATION_TERM_MONTHS
from leaseguard.models import RiskLevel, Role, UserContext
from leaseguard.parsing import parse_months

_ROLE_ADVICE = {
    Role.TENANT: "As the tenant, this is worth negotiating before you sign.",
    Role.LANDLORD: "As the landlord, expect tenants to push back; a clause this far from the norm may also be "
    "harder to enforce.",
}

MAHARASHTRA_NOTE = (
    "Maharashtra: every leave-and-licence agreement, including 11-month ones, must be in writing and "
    "registered (Maharashtra Rent Control Act, 1999, s.55). The duty to register is on the landlord; if it is "
    "not registered, the licensee's account of the terms is presumed true unless disproved (s.55(2)), and the "
    "landlord can face a penalty (s.55(3))."
)
STAMP_NOTE = (
    "No mention of stamp duty was found. Check that the agreement is on stamp paper of the value "
    "required in your state."
)


def frame_for_role(reason: str, risk: RiskLevel, role: Role) -> str:
    """Add role-specific guidance to a flagged finding.

    Args:
        reason: The rule's explanation.
        risk: The finding's risk level.
        role: The user's side of the agreement.

    Returns:
        The explanation, with guidance appended unless the clause is fair.
    """
    return reason if risk is RiskLevel.FAIR else f"{reason} {_ROLE_ADVICE[role]}"


def registration_note(full_text: str) -> str | None:
    """Return a registration reminder if the agreement term exceeds one year.

    Args:
        full_text: The whole agreement.

    Returns:
        The reminder, or None if the term is 12 months or less or unknown.
    """
    term = parse_months(full_text, "for a period of", "term of", "period of")
    if term is None or term <= REGISTRATION_TERM_MONTHS:
        return None
    return (
        f"The term appears to be {term:g} months. Leases for more than one year must be registered "
        "under the Registration Act, 1908 (s.17(1)(d))."
    )


def context_notes(full_text: str, ctx: UserContext) -> list[str]:
    """Collect notes that depend on the user's state and the agreement as a whole.

    Args:
        full_text: The whole agreement.
        ctx: The user's context.

    Returns:
        Notes in display order; possibly empty.
    """
    notes = [MAHARASHTRA_NOTE] if ctx.state == "Maharashtra" else []
    registration = registration_note(full_text)
    if registration:
        notes.append(registration)
    if "stamp" not in full_text.lower():
        notes.append(STAMP_NOTE)
    return notes
