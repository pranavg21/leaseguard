"""Request and response schemas. Every request body is validated here."""

import base64
import binascii

from pydantic import BaseModel, ConfigDict, Field, model_validator

from leaseguard.constants import MAX_MONTHLY_RENT, MAX_QUESTION_CHARS, MAX_TEXT_CHARS, MAX_UPLOAD_BYTES
from leaseguard.errors import IngestError
from leaseguard.ingest import extract_text, validate_text
from leaseguard.knowledge import STATES
from leaseguard.models import Language, Role, UserContext

_BASE64_OVERHEAD = 4 / 3
MAX_BASE64_CHARS = int(MAX_UPLOAD_BYTES * _BASE64_OVERHEAD) + 4
RESULT_ID_PATTERN = r"^[0-9a-f]{64}$"


class StrictModel(BaseModel):
    """Base model that rejects unknown fields."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ContextIn(StrictModel):
    """The user's situation."""

    role: Role = Role.TENANT
    state: str = Field(default="Other", max_length=40)
    monthly_rent: int | None = Field(default=None, ge=1, le=MAX_MONTHLY_RENT)
    language: Language = Language.ENGLISH

    @model_validator(mode="after")
    def _known_state(self) -> "ContextIn":
        if self.state not in STATES:
            raise ValueError("state must be one of the supported states")
        return self

    def to_context(self) -> UserContext:
        """Convert to the domain model.

        Returns:
            The user context.
        """
        return UserContext(self.role, self.state, self.monthly_rent, self.language)


class DocumentIn(StrictModel):
    """An agreement supplied as pasted text or as a base64-encoded file."""

    text: str | None = Field(default=None, max_length=MAX_TEXT_CHARS)
    file_base64: str | None = Field(default=None, max_length=MAX_BASE64_CHARS)

    @model_validator(mode="after")
    def _exactly_one(self) -> "DocumentIn":
        if (self.text is None) == (self.file_base64 is None):
            raise ValueError("provide exactly one of 'text' or 'file_base64'")
        return self

    def resolve(self) -> str:
        """Decode and validate the document.

        Returns:
            The agreement text.

        Raises:
            IngestError: If the content is invalid.
        """
        if self.text is not None:
            return validate_text(self.text)
        try:
            data = base64.b64decode(self.file_base64 or "", validate=True)
        except (binascii.Error, ValueError) as error:
            raise IngestError("The file could not be decoded.") from error
        return extract_text(data)


class AnalyzeRequest(StrictModel):
    """Body of ``POST /api/analyze`` and ``POST /api/packet``."""

    document: DocumentIn
    context: ContextIn = Field(default_factory=ContextIn)


class AskRequest(AnalyzeRequest):
    """Body of ``POST /api/ask`` when the agreement is sent again."""

    question: str = Field(min_length=1, max_length=MAX_QUESTION_CHARS)


class ReportRef(StrictModel):
    """Body of ``POST /api/packet`` that refers to a report reviewed earlier instead of re-uploading it."""

    report_id: str = Field(pattern=RESULT_ID_PATTERN)


class AskRef(ReportRef):
    """Body of ``POST /api/ask`` that refers to a report reviewed earlier."""

    question: str = Field(min_length=1, max_length=MAX_QUESTION_CHARS)


class CompareRequest(StrictModel):
    """Body of ``POST /api/compare``."""

    original: DocumentIn
    revised: DocumentIn
    context: ContextIn = Field(default_factory=ContextIn)
