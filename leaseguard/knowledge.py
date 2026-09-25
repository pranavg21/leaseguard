"""The documented fair baseline: what each clause category should look like.

These are market norms for Indian residential rentals plus statutory
benchmarks. They are information, not legal advice.
"""

from types import MappingProxyType
from typing import Final

from leaseguard.models import Category

CATEGORY_TITLES: Final = MappingProxyType(
    {
        Category.DEPOSIT: "Security deposit",
        Category.LOCK_IN: "Lock-in and notice",
        Category.ESCALATION: "Rent escalation",
        Category.ENTRY: "Privacy and entry",
        Category.MAINTENANCE: "Maintenance and repairs",
        Category.JURISDICTION: "Disputes and jurisdiction",
        Category.OTHER: "Other terms",
    }
)

CATEGORY_KEYWORDS: Final = MappingProxyType(
    {
        Category.DEPOSIT: ("security deposit", "deposit", "refundable", "advance"),
        Category.LOCK_IN: ("lock-in", "lock in", "notice period", "terminate", "termination", "vacate"),
        Category.ESCALATION: ("escalat", "increase", "enhance", "revision of rent", "hike"),
        Category.ENTRY: ("entry", "enter", "inspect", "access to the premises", "visit"),
        Category.MAINTENANCE: ("repair", "maintenance", "upkeep", "damage", "wear and tear"),
        Category.JURISDICTION: ("jurisdiction", "arbitrat", "dispute", "courts at"),
    }
)

BASELINE: Final = MappingProxyType(
    {
        Category.DEPOSIT: "Refundable deposit of up to 2 months' rent (the benchmark in the Model Tenancy "
        "Act, 2021), returned within about 30 days of handover minus documented deductions.",
        Category.LOCK_IN: "Lock-in of 6 months or less for both parties; notice of 1-2 months for either side.",
        Category.ESCALATION: "A fixed escalation of 5-10% per year, stated in the agreement.",
        Category.ENTRY: "Landlord entry only with at least 24 hours' written notice, except in emergencies.",
        Category.MAINTENANCE: "Tenant handles minor repairs; landlord handles structural repairs and normal "
        "wear and tear.",
        Category.JURISDICTION: "Disputes go to local courts or a neutral arbitrator where the property is.",
        Category.OTHER: "No one-sided penalties, forfeitures or unilateral rights for either party.",
    }
)

LAWYER_QUESTIONS: Final = MappingProxyType(
    {
        Category.DEPOSIT: "Is this deposit and refund timeline enforceable in my state, and what deductions "
        "can lawfully be made?",
        Category.LOCK_IN: "What happens if I need to leave during the lock-in, and is the penalty enforceable?",
        Category.ESCALATION: "Can the rent be increased beyond what is written here, and how often?",
        Category.ENTRY: "What notice must the landlord give before entering, and what can I do if it is ignored?",
        Category.MAINTENANCE: "Which repairs am I legally responsible for, and which fall on the landlord?",
        Category.JURISDICTION: "Is this dispute clause fair, and can I still approach a local rent authority?",
        Category.OTHER: "Is this clause standard, and is it enforceable as written?",
    }
)

# Protections expected in every agreement; missing ones are reported as gaps.
EXPECTED_CATEGORIES: Final = (
    Category.DEPOSIT,
    Category.LOCK_IN,
    Category.MAINTENANCE,
    Category.ENTRY,
    Category.JURISDICTION,
)

STATES: Final = (
    "Maharashtra",
    "Karnataka",
    "Delhi",
    "Tamil Nadu",
    "Telangana",
    "Uttar Pradesh",
    "West Bengal",
    "Gujarat",
    "Haryana",
    "Kerala",
    "Other",
)
