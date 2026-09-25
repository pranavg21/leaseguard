"""Typed data structures shared across the LeaseGuard pipeline."""

from dataclasses import dataclass, field
from enum import StrEnum


class RiskLevel(StrEnum):
    """Risk rating for a clause. Always shown with text and an icon, never colour alone."""

    FAIR = "FAIR"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

    @property
    def rank(self) -> int:
        """Ordering value: FAIR 0, MEDIUM 1, HIGH 2."""
        return _RANKS[self.value]

    @property
    def label(self) -> str:
        """Human-readable label."""
        return _LABELS[self.value]


_RANKS = {"FAIR": 0, "MEDIUM": 1, "HIGH": 2}
_LABELS = {"FAIR": "Fair", "MEDIUM": "Medium risk", "HIGH": "High risk"}


class Role(StrEnum):
    """The user's side of the agreement."""

    TENANT = "tenant"
    LANDLORD = "landlord"


class Language(StrEnum):
    """Languages available for explanations."""

    ENGLISH = "English"
    HINDI = "Hindi"
    MARATHI = "Marathi"


class Category(StrEnum):
    """Clause categories covered by the fair baseline."""

    DEPOSIT = "deposit"
    LOCK_IN = "lock_in_notice"
    ESCALATION = "rent_escalation"
    ENTRY = "privacy_entry"
    MAINTENANCE = "maintenance"
    JURISDICTION = "jurisdiction"
    OTHER = "other"


@dataclass(frozen=True)
class UserContext:
    """Facts about the user that drive context-dependent rules."""

    role: Role = Role.TENANT
    state: str = "Other"
    monthly_rent: int | None = None
    language: Language = Language.ENGLISH


@dataclass(frozen=True)
class Clause:
    """One segmented clause of the source document."""

    index: int
    heading: str
    text: str


@dataclass(frozen=True)
class RuleResult:
    """Outcome of applying a baseline rule to one clause."""

    risk: RiskLevel
    reason: str
    rule_id: str
    keywords: tuple[str, ...]


@dataclass
class Finding:
    """Assessment of one clause against the baseline."""

    clause: Clause
    category: Category
    risk: RiskLevel
    reason: str
    quote: str
    quote_verified: bool
    question_for_lawyer: str
    rule_id: str


@dataclass(frozen=True)
class CoverageGap:
    """A protection the baseline expects but the document does not contain."""

    category: Category
    message: str


@dataclass(frozen=True)
class KeyTerm:
    """One headline term. ``quote`` is copied from the agreement, or empty if not stated."""

    label: str
    value: str
    quote: str


@dataclass(frozen=True)
class Step:
    """One action the user can take, in plain language."""

    title: str
    detail: str


@dataclass
class AnalysisReport:
    """Complete result of analysing one document.

    ``key_terms`` and ``next_steps`` are derived once when the report is built and
    reused by the web view and the PDF. ``report_id`` is the cache key; it is empty
    when the report was not cached, so later requests must send the document again.
    """

    findings: list[Finding]
    gaps: list[CoverageGap]
    coverage_complete: bool
    context: UserContext
    failed_clauses: list[int] = field(default_factory=list)
    context_notes: list[str] = field(default_factory=list)
    key_terms: list[KeyTerm] = field(default_factory=list)
    next_steps: list[Step] = field(default_factory=list)
    report_id: str = ""

    def counts(self) -> dict[RiskLevel, int]:
        """Return the number of findings at each risk level."""
        result = dict.fromkeys(RiskLevel, 0)
        for finding in self.findings:
            result[finding.risk] += 1
        return result


@dataclass(frozen=True)
class Answer:
    """A grounded answer to a user question."""

    text: str
    quote: str | None
    clause_heading: str | None
    grounded: bool
