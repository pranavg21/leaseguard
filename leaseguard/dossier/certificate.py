"""Certificate under Section 63(4)(c), Bharatiya Sakshya Adhiniyam, 2023, in the form of the Schedule.

The wording below follows the Schedule to the Act ("[See section 63(4)(c)]") line by line.
LeaseGuard fills only what software knows exactly: the party's name, the SHA-256 tick box
and the hash report listing each record's hash. Everything else stays blank for the party.

Part B is reproduced blank. Section 63(4)(c) requires the certificate to be signed by the
person in charge "and an expert"; the Supreme Court upheld this, and held that an expert may be
a Section 79A examiner or another person the Court is satisfied has special skill in computer
science and cyber forensics (Pune Bar Association v. Union of India, 22 May 2026).
"""

from dataclasses import dataclass

from leaseguard.dossier.models import EvidenceFile, Parties

BLANK = "____________"
UNTICKED = "[ ]"
TICKED = "[X]"
SOURCE = "THE SCHEDULE [See section 63(4)(c)] - CERTIFICATE"
NOTE = (
    "Wording reproduced from the Schedule to the Bharatiya Sakshya Adhiniyam, 2023. LeaseGuard has filled in only "
    "your name, the SHA-256 box and the hash report. Complete every blank, tick what is true, and sign Part A only "
    "if every statement is true. Part B must be completed and signed by an expert: a Section 79A IT Act examiner, "
    "or a person the Court accepts as having special skill in computer science and cyber forensics (Supreme Court, "
    "Pune Bar Association v. Union of India, 22 May 2026). A certificate is needed each time the record is submitted. "
    "This is not legal advice."
)
DEVICE_LINES = (
    f"Computer / Storage Media {UNTICKED} DVR {UNTICKED} Mobile {UNTICKED} Flash Drive {UNTICKED}",
    f"CD/DVD {UNTICKED} Server {UNTICKED} Cloud {UNTICKED} Other {UNTICKED}",
    f"Other: {BLANK}",
    (
        f"Make & Model: {BLANK} Color: {BLANK} Serial Number: {BLANK} IMEI/UIN/UID/MAC/Cloud ID {BLANK} "
        f"(as applicable) and any other relevant information, if any, about the device/digital record {BLANK} "
        "(specify)."
    ),
)
LAWFUL_CONTROL = (
    "The digital device or the digital record source was under the lawful control for regularly creating, storing "
    "or processing information for the purposes of carrying out regular activities and during this period, the "
    "computer or the communication device was working properly and the relevant information was regularly fed into "
    "the computer during the ordinary course of business."
)
PROPER_OPERATION = (
    "If the computer/digital device at any point of time was not working properly or out of operation, then it has "
    "not affected the electronic/digital record or its accuracy. The digital device or the source of the digital "
    "record is:-"
)
CONTROL_LINE = (
    f"Owned {UNTICKED} Maintained {UNTICKED} Managed {UNTICKED} Operated {UNTICKED} by me (select as applicable)."
)
DATE_LINE = f"Date (DD/MM/YYYY): {BLANK} Time (IST): {BLANK} hours (In 24 hours format) Place: {BLANK}"
STANDARD = "(Legally acceptable standard) (Hash report to be enclosed with the certificate)"


@dataclass(frozen=True)
class CertificatePart:
    """One part of the certificate as ordered lines of text."""

    heading: str
    lines: tuple[str, ...]


@dataclass(frozen=True)
class CertificateDraft:
    """The certificate: both parts, plus the hash report enclosed with it."""

    title: str
    note: str
    part_a: CertificatePart
    part_b: CertificatePart
    records: tuple[tuple[str, str, str, str], ...]


def record_rows(files: list[EvidenceFile]) -> tuple[tuple[str, str, str, str], ...]:
    """Build the hash report: annexure, file name, size and SHA-256 of each record.

    Args:
        files: The evidence files.

    Returns:
        Rows of (annexure, file name, size in bytes, SHA-256).
    """
    return tuple((f.annexure, f.name, str(f.size_bytes), f.sha256) for f in files)


def algorithm_line(sha256_ticked: bool) -> str:
    """Render the algorithm tick boxes.

    Args:
        sha256_ticked: Whether to tick SHA256.

    Returns:
        The line as printed in the Schedule.
    """
    mark = TICKED if sha256_ticked else UNTICKED
    return f"{UNTICKED} SHA1: {mark} SHA256: {UNTICKED} MD5: {UNTICKED} Other {BLANK}"


def hash_statement(files: list[EvidenceFile]) -> str:
    """Render the hash sentence, pointing to the enclosed hash report.

    Args:
        files: The evidence files.

    Returns:
        The sentence, with the hash values referenced by annexure.
    """
    span = f"{files[0].annexure} to {files[-1].annexure}" if len(files) > 1 else (files[0].annexure if files else BLANK)
    return (
        f"I state that the HASH value/s of the electronic/digital record/s is as listed against each record in the "
        f"enclosed hash report (Annexure {span}), obtained through the following algorithm:-"
    )


def _opening(name: str) -> str:
    return (
        f"I, {name} (Name), Son/daughter/spouse of {BLANK} residing/employed at {BLANK} do hereby solemnly affirm "
        "and sincerely state and submit as follows:-"
    )


def part_a(parties: Parties, files: list[EvidenceFile]) -> CertificatePart:
    """Build Part A (to be filled by the party), pre-filled where exact.

    Args:
        parties: Names in the dispute.
        files: The evidence files.

    Returns:
        Part A.
    """
    lines = (
        _opening(parties.tenant or BLANK),
        (
            "I have produced electronic record/output of the digital record taken from the following device/digital "
            "record source (tick mark):-"
        ),
        *DEVICE_LINES,
        LAWFUL_CONTROL,
        PROPER_OPERATION,
        CONTROL_LINE,
        hash_statement(files),
        algorithm_line(sha256_ticked=True),
        STANDARD,
        parties.tenant or BLANK,
        "(Name and signature)",
        DATE_LINE,
    )
    return CertificatePart("PART A (To be filled by the Party)", lines)


def part_b() -> CertificatePart:
    """Build Part B (to be filled by the expert), left blank as the expert must verify independently.

    Returns:
        Part B.
    """
    lines = (
        _opening(BLANK),
        (
            "The produced electronic record/output of the digital record are obtained from the following "
            "device/digital record source (tick mark):-"
        ),
        *DEVICE_LINES,
        (
            f"I state that the HASH value/s of the electronic/digital record/s is {BLANK}, obtained through the "
            "following algorithm:-"
        ),
        algorithm_line(sha256_ticked=False),
        STANDARD,
        "(Name, designation and signature)",
        DATE_LINE,
    )
    return CertificatePart("PART B (To be filled by the Expert)", lines)


def build_certificate(parties: Parties, files: list[EvidenceFile]) -> CertificateDraft:
    """Build the full certificate in the Schedule's form, with its hash report.

    Args:
        parties: Names used in the dispute.
        files: The evidence files, in annexure order.

    Returns:
        The certificate.
    """
    return CertificateDraft(SOURCE, NOTE, part_a(parties, files), part_b(), record_rows(files))
