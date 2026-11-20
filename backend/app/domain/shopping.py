"""采购清单状态流转规则。

纯规则层：cancelled 为终态；相同状态视为幂等。
"""

SHOPPING_TRANSITIONS: dict[str, frozenset[str]] = {
    "pending": frozenset({"purchased", "cancelled"}),
    "purchased": frozenset({"cancelled"}),
    "cancelled": frozenset(),
}


def can_transition(current: str, target: str) -> bool:
    """Allow a no-op transition and transitions listed for the current status."""
    if current == target:
        return True
    return target in SHOPPING_TRANSITIONS.get(current, frozenset())
