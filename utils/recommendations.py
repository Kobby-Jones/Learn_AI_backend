"""utils/recommendations.py"""
from models import LearningMaterial, Bookmark, MaterialProgress

DIFFICULTY_TO_DOMAIN = {
    "dyslexia_related":          ["grammar", "reading"],
    "dyscalculia_related":       ["mathematics"],
    "memory_related":            ["memory"],
    "reasoning_related":         ["reasoning"],
    "reading_comprehension":     ["reading"],
    "no_significant_difficulty": ["mathematics", "grammar", "reading", "memory", "reasoning"],
}

def generate_recommendations(primary_difficulty: str, weaknesses: list, student_id: str) -> list:
    """Return list of LearningMaterial objects best suited to the student's difficulty."""
    target_domains = DIFFICULTY_TO_DOMAIN.get(primary_difficulty, [])
    # Add weakness domains
    for w in weaknesses:
        if w not in target_domains:
            target_domains.append(w)

    materials = []
    seen_ids  = set()

    # First: materials targeting the primary difficulty
    primary_mats = LearningMaterial.query.filter(
        LearningMaterial.target_difficulty == primary_difficulty,
        LearningMaterial.is_active == True
    ).limit(4).all()
    for m in primary_mats:
        if m.id not in seen_ids:
            materials.append(m)
            seen_ids.add(m.id)

    # Fill remaining slots by domain
    for domain in target_domains:
        if len(materials) >= 8:
            break
        domain_mats = LearningMaterial.query.filter(
            LearningMaterial.domain == domain,
            LearningMaterial.is_active == True
        ).limit(3).all()
        for m in domain_mats:
            if m.id not in seen_ids and len(materials) < 8:
                materials.append(m)
                seen_ids.add(m.id)

    # Pad with general materials if needed
    if len(materials) < 4:
        general = LearningMaterial.query.filter_by(is_active=True).limit(8).all()
        for m in general:
            if m.id not in seen_ids and len(materials) < 6:
                materials.append(m)
                seen_ids.add(m.id)

    return materials
