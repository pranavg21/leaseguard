"""Deterministic keyword classifier used offline and as the AI fallback."""

from leaseguard.constants import HEADING_KEYWORD_BONUS
from leaseguard.knowledge import CATEGORY_KEYWORDS
from leaseguard.models import Category, Clause


def classify_offline(clause: Clause) -> Category:
    """Assign a clause to the category whose keywords it mentions most.

    A keyword in the heading counts extra, because headings are the strongest
    signal in Indian drafting.

    Args:
        clause: The clause to classify.

    Returns:
        The best category, or ``Category.OTHER`` if no keyword matches.
    """
    body = f"{clause.heading} {clause.text}".lower()
    heading = clause.heading.lower()
    scores = {
        category: sum(body.count(k) for k in keywords)
        + (HEADING_KEYWORD_BONUS if any(k in heading for k in keywords) else 0)
        for category, keywords in CATEGORY_KEYWORDS.items()
    }
    best = max(scores, key=lambda category: scores[category])
    return best if scores[best] > 0 else Category.OTHER


def classify_all(clauses: list[Clause]) -> dict[int, Category]:
    """Classify every clause offline.

    Args:
        clauses: Clauses to classify.

    Returns:
        A mapping from clause index to category.
    """
    return {clause.index: classify_offline(clause) for clause in clauses}
