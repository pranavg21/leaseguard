"""Tests for leaseguard/dossier/certificate.py against the text of the BSA Schedule."""

import pytest

from leaseguard.dossier.certificate import (
    BLANK,
    TICKED,
    UNTICKED,
    algorithm_line,
    build_certificate,
    hash_statement,
    part_b,
    record_rows,
)
from leaseguard.dossier.models import Parties
from tests.dossier_fixtures import PARTIES, evidence

# Fixed phrases of the Schedule ("[See section 63(4)(c)]"), which the certificate must reproduce exactly.
SCHEDULE_PHRASES = (
    "Son/daughter/spouse of",
    "do hereby solemnly affirm and sincerely state and submit as follows:-",
    (
        "I have produced electronic record/output of the digital record taken from the following device/digital record "
        "source (tick mark):-"
    ),
    f"Computer / Storage Media {UNTICKED} DVR {UNTICKED} Mobile {UNTICKED} Flash Drive {UNTICKED}",
    f"CD/DVD {UNTICKED} Server {UNTICKED} Cloud {UNTICKED} Other {UNTICKED}",
    "IMEI/UIN/UID/MAC/Cloud ID",
    (
        "The digital device or the digital record source was under the lawful control for regularly creating, storing "
        "or processing information for the purposes of carrying out regular activities and during this period, the "
        "computer or the communication device was working properly and the relevant information was regularly fed into "
        "the computer during the ordinary course of business."
    ),
    (
        "If the computer/digital device at any point of time was not working properly or out of operation, then it has "
        "not affected the electronic/digital record or its accuracy."
    ),
    f"Owned {UNTICKED} Maintained {UNTICKED} Managed {UNTICKED} Operated {UNTICKED} by me (select as applicable).",
    "I state that the HASH value/s of the electronic/digital record/s is",
    ", obtained through the following algorithm:-",
    "(Legally acceptable standard) (Hash report to be enclosed with the certificate)",
    "Time (IST):",
    "hours (In 24 hours format) Place:",
)


def text_of(lines: tuple[str, ...]) -> str:
    return "\n".join(lines)


@pytest.mark.parametrize("phrase", SCHEDULE_PHRASES)
def test_part_a_reproduces_schedule_wording(phrase: str) -> None:
    assert phrase in text_of(build_certificate(PARTIES, [evidence("x")]).part_a.lines)


def test_part_a_prefills_only_exact_facts() -> None:
    part = build_certificate(PARTIES, [evidence("x")]).part_a
    assert part.heading == "PART A (To be filled by the Party)"
    assert part.lines[0].startswith("I, Priya (Name)")
    assert f"{TICKED} SHA256:" in text_of(part.lines)
    assert f"Make & Model: {BLANK}" in text_of(part.lines)
    assert part.lines[-2] == "(Name and signature)"


def test_part_b_is_blank_for_the_expert() -> None:
    part = part_b()
    assert part.heading == "PART B (To be filled by the Expert)"
    assert part.lines[0].startswith(f"I, {BLANK} (Name)")
    assert TICKED not in text_of(part.lines)
    assert "(Name, designation and signature)" in part.lines
    assert "The produced electronic record/output of the digital record are obtained from" in part.lines[1]


def test_note_cites_the_supreme_court_on_part_b() -> None:
    note = build_certificate(PARTIES, []).note
    assert "Pune Bar Association v. Union of India, 22 May 2026" in note
    assert "Section 79A" in note


def test_hash_statement_and_report() -> None:
    files = [evidence("a", annexure="A-1"), evidence("b", annexure="A-3")]
    assert "(Annexure A-1 to A-3)" in hash_statement(files)
    assert "(Annexure A-1)" in hash_statement(files[:1])
    assert BLANK in hash_statement([])
    assert record_rows(files)[0] == ("A-1", "f.txt", "1", "0" * 64)
    assert algorithm_line(sha256_ticked=False).count(UNTICKED) == 4


def test_blank_name() -> None:
    assert build_certificate(Parties("", "", ""), []).part_a.lines[0].startswith(f"I, {BLANK} (Name)")
