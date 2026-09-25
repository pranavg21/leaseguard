"""Named constants for every limit and threshold used by LeaseGuard.

Keeping them in one module makes the baseline auditable and avoids magic
numbers scattered through the code.
"""

from typing import Final

# Input limits
MAX_UPLOAD_BYTES: Final = 5 * 1024 * 1024
MAX_REQUEST_BYTES: Final = 8 * 1024 * 1024
MAX_PDF_PAGES: Final = 40
MIN_TEXT_CHARS: Final = 500
MAX_TEXT_CHARS: Final = 200_000
MAX_QUESTION_CHARS: Final = 500
MAX_FILENAME_CHARS: Final = 120
MAX_MONTHLY_RENT: Final = 10_000_000
PRINTABLE_RATIO: Final = 0.95

# Segmentation and grounding
MIN_CLAUSE_CHARS: Final = 25
MAX_HEADING_CHARS: Final = 60
MIN_QUOTE_CHARS: Final = 12
MAX_QUOTE_CHARS: Final = 400
MONTH_WINDOW_CHARS: Final = 45
MIN_KEYWORD_CHARS: Final = 4
HEADING_KEYWORD_BONUS: Final = 3

# Baseline thresholds (market norms and statutory benchmarks)
DEPOSIT_CAP_MONTHS: Final = 2.0
DEPOSIT_HIGH_MONTHS: Final = 6.0
LOCK_IN_FAIR_MONTHS: Final = 6.0
LOCK_IN_HIGH_MONTHS: Final = 12.0
NOTICE_MAX_MONTHS: Final = 2.0
ESCALATION_FAIR_PCT: Final = 10.0
ESCALATION_HIGH_PCT: Final = 15.0
REGISTRATION_TERM_MONTHS: Final = 12.0

# AI and caching
LLM_TEMPERATURE: Final = 0.0
LLM_CLAUSE_PREVIEW_CHARS: Final = 600
LLM_EXPLANATION_MAX_CHARS: Final = 600
LLM_SUMMARY_MAX_CHARS: Final = 200
CACHE_SIZE: Final = 32

# HTTP
RATE_LIMIT_REQUESTS: Final = 30
RATE_LIMIT_WINDOW_SECONDS: Final = 60.0
HSTS_MAX_AGE_SECONDS: Final = 63_072_000
PDF_MARGIN_MM: Final = 18

# Deposit-recovery dossier
MAX_EVIDENCE_FILES: Final = 10
MAX_PARTY_NAME_CHARS: Final = 80
LIMITATION_YEARS: Final = 3
NOTICE_REPLY_DAYS: Final = 15
TWO_DIGIT_YEAR_BASE: Final = 2000
TWO_DIGIT_YEAR_LIMIT: Final = 100
HASH_PREVIEW_CHARS: Final = 16
