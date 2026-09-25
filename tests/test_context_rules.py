"""Tests for leaseguard/context_rules.py."""

from leaseguard.context_rules import MAHARASHTRA_NOTE, STAMP_NOTE, context_notes, frame_for_role, registration_note
from leaseguard.models import RiskLevel, Role, UserContext


def test_role_framing() -> None:
    tenant = frame_for_role("x.", RiskLevel.HIGH, Role.TENANT)
    landlord = frame_for_role("x.", RiskLevel.MEDIUM, Role.LANDLORD)
    assert "tenant" in tenant
    assert "landlord" in landlord
    assert frame_for_role("x.", RiskLevel.FAIR, Role.TENANT) == "x."


def test_registration_note_only_above_twelve_months() -> None:
    assert "17(1)(d)" in (registration_note("for a period of 24 months") or "")
    assert registration_note("for a period of 11 months") is None
    assert registration_note("no term") is None


def test_context_notes_depend_on_state_and_stamp_duty() -> None:
    maharashtra = context_notes("for a period of 11 months", UserContext(state="Maharashtra"))
    assert maharashtra == [MAHARASHTRA_NOTE, STAMP_NOTE]
    assert "11-month" in MAHARASHTRA_NOTE
    assert "55(2)" in MAHARASHTRA_NOTE
    assert context_notes("executed on stamp paper", UserContext(state="Kerala")) == []


def test_long_term_adds_registration_note() -> None:
    notes = context_notes("stamp paper; for a period of 36 months", UserContext(state="Kerala"))
    assert len(notes) == 1
    assert "36 months" in notes[0]
