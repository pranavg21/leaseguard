"""Shared display formatting."""

_GROUP = 3
_INDIAN_GROUP = 2


def indian_rupees(amount: int) -> str:
    """Format whole rupees with Indian digit grouping, for example ``Rs. 1,50,000``.

    Args:
        amount: Whole rupees.

    Returns:
        The formatted amount.
    """
    digits = str(amount)
    head, tail = digits[:-_GROUP], digits[-_GROUP:]
    groups = [head[max(i - _INDIAN_GROUP, 0) : i] for i in range(len(head), 0, -_INDIAN_GROUP)][::-1]
    return "Rs. " + ",".join([*groups, tail]) if head else f"Rs. {tail}"
