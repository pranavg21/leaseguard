"""Request schemas for the deposit-recovery dossier endpoints."""

import base64
import binascii

from pydantic import Field

from leaseguard.api.schemas import MAX_BASE64_CHARS, DocumentIn, StrictModel
from leaseguard.constants import MAX_EVIDENCE_FILES, MAX_FILENAME_CHARS, MAX_PARTY_NAME_CHARS
from leaseguard.dossier.models import Parties
from leaseguard.dossier.service import Upload
from leaseguard.errors import IngestError
from leaseguard.models import Language

SHA256_PATTERN = r"^[0-9a-fA-F]{64}$"


class EvidenceIn(StrictModel):
    """One evidence file, base64-encoded, with the hash the browser computed."""

    name: str = Field(min_length=1, max_length=MAX_FILENAME_CHARS)
    content_base64: str = Field(min_length=1, max_length=MAX_BASE64_CHARS)
    client_sha256: str | None = Field(default=None, pattern=SHA256_PATTERN)

    def to_upload(self) -> Upload:
        """Decode the file.

        Returns:
            The upload.

        Raises:
            IngestError: If the content is not valid base64.
        """
        try:
            data = base64.b64decode(self.content_base64, validate=True)
        except (binascii.Error, ValueError) as error:
            raise IngestError(f"{self.name} could not be decoded.") from error
        return Upload(self.name, data, self.client_sha256)


class PartiesIn(StrictModel):
    """Names printed on the certificate and notice; all optional."""

    tenant: str = Field(default="", max_length=MAX_PARTY_NAME_CHARS)
    landlord: str = Field(default="", max_length=MAX_PARTY_NAME_CHARS)
    property_address: str = Field(default="", max_length=MAX_PARTY_NAME_CHARS * 2)

    def to_parties(self) -> Parties:
        """Convert to the domain model.

        Returns:
            The parties.
        """
        return Parties(self.tenant, self.landlord, self.property_address)


class DossierRequest(StrictModel):
    """Body of ``POST /api/dossier`` and ``POST /api/dossier/pdf``."""

    files: list[EvidenceIn] = Field(min_length=1, max_length=MAX_EVIDENCE_FILES)
    lease: DocumentIn | None = None
    parties: PartiesIn = Field(default_factory=PartiesIn)
    language: Language = Language.ENGLISH
