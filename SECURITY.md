# Security policy

## Data handling
- Agreements are processed in memory for the duration of one request. They are never written to disk, logged or stored.
- Aadhaar numbers, PAN numbers, Indian mobile numbers and email addresses are replaced with placeholders **before** any text is sent to Gemini (`leaseguard/privacy.py`). A test checks this.
- Evidence files are fingerprinted with SHA-256 in the browser (Web Crypto) and again on the server. A mismatch is reported. The API returns hashes and verbatim event quotes, never the full evidence text.
- Evidence types are identified by signature (PDF, PNG, JPEG, WebP or UTF-8 text). File names are stripped of path components before display.
- The optional Firestore metrics contain counts, categories, role and state only. They never contain text, quotes or questions.

## Secrets
- `GEMINI_API_KEY` is read only from the environment. In production it comes from Google Secret Manager.
- `.env` is git-ignored.

## Request handling
| Control | Where |
|---|---|
| Pydantic schemas with `extra="forbid"` and length limits on every body | `leaseguard/api/schemas.py` |
| `Content-Type: application/json` required (415 otherwise) | `leaseguard/api/security.py` |
| 8 MB request limit (413), 5 MB file limit and 5 MB evidence total; files identified by signature | `security.py`, `ingest.py` |
| 30 requests per minute per client (429) | `RateLimiter` in `security.py` |
| CSP, HSTS, `X-Frame-Options`, `nosniff`, Referrer and Permissions policies, COOP and CORP | `SECURITY_HEADERS` in `security.py` |
| Structured errors that never include stack traces or echo input back | `leaseguard/api/app.py` |
| Static pages served from fixed paths; the request cannot choose a file | `_page_handler` in `app.py` |
| `report_id` and `dossier_id` are SHA-256 content hashes (strict 64-hex pattern). They cannot be guessed without the document itself, they point only to results held in a small in-memory cache, and they are never logged | `engine.py`, `dossier/service.py`, `schemas.py` |

## AI safety
- The document is wrapped in `<document>` delimiters, and embedded delimiter tags are neutralised.
- The system instruction treats document text as untrusted data.
- Model output must match a JSON schema and is validated with Pydantic. Any value outside that schema is ignored.
- Risk ratings are computed by deterministic rules, so model output cannot change them.
- Every quote shown to the user must pass `verify_grounding()`.

## Frontend
- There is no `innerHTML`, `eval` or inline script. ESLint and `scripts/audit.py` both enforce this.
- The service worker never caches API calls, so agreements are never stored on the device.

## Reporting a vulnerability
Please open a private security advisory on this repository rather than a public issue.
