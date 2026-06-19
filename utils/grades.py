"""
utils/grades.py
───────────────
Single source of truth for the school grades (classes) the platform supports.

A "grade" and a "class" are the same thing here: each grade level is one class.
- A question belongs to exactly one grade  → "each grade has its corresponding work".
- A student is fixed to one grade           → set at signup, used to serve questions.
- A teacher is assigned to one or more grades → their lists are scoped to those classes.

Order matters: GRADES is listed from lowest to highest and that order is used
everywhere (dropdowns, sorting, etc.). Keep this in sync with the frontend copy
at  frontend/src/lib/grades.ts.
"""

GRADES = [
    {"value": "basic4", "label": "Basic 4"},
    {"value": "basic5", "label": "Basic 5"},
    {"value": "basic6", "label": "Basic 6"},
    {"value": "jhs1",   "label": "JHS 1"},
    {"value": "jhs2",   "label": "JHS 2"},
    {"value": "jhs3",   "label": "JHS 3"},
]

GRADE_VALUES = [g["value"] for g in GRADES]
GRADE_LABELS = {g["value"]: g["label"] for g in GRADES}


def is_valid_grade(value) -> bool:
    """True if `value` is one of the supported grade codes."""
    return value in GRADE_VALUES


def grade_label(value) -> str:
    """Human label for a grade code, falling back to the raw value."""
    return GRADE_LABELS.get(value, value or "")


def grade_order(value) -> int:
    """Sort key for a grade code (lowest grade first)."""
    return GRADE_VALUES.index(value) if value in GRADE_VALUES else 99


def clean_grade_list(values) -> list:
    """
    Normalise an incoming list of grade codes: keep only valid ones,
    de-duplicate, and return them sorted in canonical grade order.
    """
    if not values:
        return []
    seen = []
    for v in values:
        if is_valid_grade(v) and v not in seen:
            seen.append(v)
    seen.sort(key=grade_order)
    return seen
