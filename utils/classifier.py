"""
utils/classifier.py
────────────────────
Loads the trained ML model and classifies a student's assessment answers.
Maps between the frontend's domain/difficulty naming and the model's naming.
"""
import os
import math
import numpy as np

# ── Model label mapping ───────────────────────────────────────────────────────
# Model was trained with these labels
MODEL_LABELS = [
    "no_difficulty",
    "dyscalculia",
    "dyslexia",
    "memory_impairment",
    "reasoning_deficit",
    "language_disorder",
]

# Map to frontend DifficultyType values
MODEL_TO_FRONTEND = {
    "no_difficulty":     "no_significant_difficulty",
    "dyscalculia":       "dyscalculia_related",
    "dyslexia":          "dyslexia_related",
    "memory_impairment": "memory_related",
    "reasoning_deficit": "reasoning_related",
    "language_disorder": "dyslexia_related",   # language disorder also mapped to dyslexia-related
}

# Frontend domain → model domain
DOMAIN_MAP = {
    "mathematics": "math",
    "grammar":     "grammar",
    "reading":     "reading",
    "memory":      "memory",
    "reasoning":   "reasoning",
}

DOMAINS_MODEL = ["grammar", "reasoning", "reading", "math", "memory"]

ERROR_MAP = {
    "none": 0, "careless": 1, "misread": 2, "timeout": 3,
    "conceptual": 4, "procedural": 5, "phonological": 6,
    "visual_confuse": 7, "recall_fail": 8, "interference": 9,
    "partial": 10, "inference_fail": 11, "literal_error": 12,
    "syntactic": 13, "morphological": 14,
}

MATH_ERR   = {"conceptual", "procedural"}
PHON_ERR   = {"phonological", "visual_confuse"}
RECALL_ERR = {"recall_fail", "interference", "partial"}
INFER_ERR  = {"inference_fail", "literal_error"}
SYNTAX_ERR = {"syntactic", "morphological"}

_model = None

def _load_model():
    global _model
    if _model is not None:
        return _model
    # Try to find the model file
    candidates = [
        os.path.join(os.path.dirname(__file__), "..", "ml_model", "best_model_real.joblib"),
        os.path.join(os.path.dirname(__file__), "..", "models_ml", "best_model_real.joblib"),
        os.path.join(os.path.dirname(__file__), "..", "..", "ml_pipeline", "models", "best_model_real.joblib"),
        "best_model_real.joblib",
    ]
    for path in candidates:
        if os.path.exists(path):
            import joblib
            _model = joblib.load(path)
            print(f"[classifier] Loaded model from: {path}")
            return _model

    print("[classifier] WARNING: No ML model found. Using rule-based fallback.")
    return None


def _extract_features(answers_by_domain: dict) -> np.ndarray:
    """
    Build the 55-feature vector matching training:
    10 features per domain × 5 domains + 5 domain one-hot flags
    """
    feature_vector = []

    for domain in DOMAINS_MODEL:
        items = answers_by_domain.get(domain, [])

        if not items:
            feature_vector.extend([0.0] * 10)
            continue

        corrects    = [int(a["correct"]) for a in items]
        latencies   = [max(200, int(a.get("latency_ms", 2500))) for a in items]
        error_types = [a.get("error_type", "none").lower() for a in items]

        log_lats    = [math.log(l) for l in latencies]
        error_codes = [ERROR_MAP.get(e, 0) for e in error_types]

        n = len(items)
        accuracy       = np.mean(corrects)
        log_lat_mean   = np.mean(log_lats)
        log_lat_std    = float(np.std(log_lats)) if len(log_lats) > 1 else 0.0
        accuracy_std   = float(np.std(corrects)) if len(corrects) > 1 else 0.0
        error_mean     = np.mean(error_codes)
        math_err_rate   = sum(1 for e in error_types if e in MATH_ERR)   / n
        phon_err_rate   = sum(1 for e in error_types if e in PHON_ERR)   / n
        recall_err_rate = sum(1 for e in error_types if e in RECALL_ERR) / n
        infer_err_rate  = sum(1 for e in error_types if e in INFER_ERR)  / n
        syntax_err_rate = sum(1 for e in error_types if e in SYNTAX_ERR) / n

        feature_vector.extend([
            accuracy, log_lat_mean, log_lat_std, accuracy_std, error_mean,
            math_err_rate, phon_err_rate, recall_err_rate, infer_err_rate, syntax_err_rate,
        ])

    # One-hot for assessed domains
    assessed = {d for d in DOMAINS_MODEL if answers_by_domain.get(d)}
    for d in DOMAINS_MODEL:
        feature_vector.append(1.0 if d in assessed else 0.0)

    return np.array(feature_vector, dtype=float)


def _rule_based_classify(domain_accuracies: dict) -> str:
    """Fallback when model is not available."""
    if not domain_accuracies:
        return "no_difficulty"
    worst_domain = min(domain_accuracies, key=domain_accuracies.get)
    worst_acc    = domain_accuracies[worst_domain]
    if worst_acc >= 0.75:
        return "no_difficulty"
    domain_to_label = {
        "math":      "dyscalculia",
        "grammar":   "dyslexia",
        "reading":   "dyslexia",
        "memory":    "memory_impairment",
        "reasoning": "reasoning_deficit",
    }
    return domain_to_label.get(worst_domain, "no_difficulty")


def classify_responses(db_answers) -> dict:
    """
    Takes a list of Answer model instances and returns classification dict
    matching the frontend's ClassificationResult shape.
    """
    # Group answers by model domain
    answers_by_domain: dict = {d: [] for d in DOMAINS_MODEL}
    domain_accuracies: dict = {}

    for a in db_answers:
        if a.skipped or not a.question:
            continue
        frontend_domain = a.question.domain
        model_domain    = DOMAIN_MAP.get(frontend_domain, frontend_domain)
        # Infer error type from correctness + question domain
        error_type = _infer_error_type(a, model_domain)
        answers_by_domain[model_domain].append({
            "correct":    int(a.is_correct or 0),
            "latency_ms": a.response_time or 2500,
            "error_type": error_type,
        })

    # Domain accuracy map for fallback + summaries
    for domain, items in answers_by_domain.items():
        if items:
            domain_accuracies[domain] = sum(i["correct"] for i in items) / len(items)

    # ── Try ML model ──────────────────────────────────────────────────────────
    model = _load_model()
    if model and any(answers_by_domain.values()):
        try:
            features  = _extract_features(answers_by_domain).reshape(1, -1)
            label_idx = int(model.predict(features)[0])
            proba     = model.predict_proba(features)[0]
            model_label  = MODEL_LABELS[label_idx]
            confidence   = float(proba[label_idx])
        except Exception as e:
            print(f"[classifier] Model prediction failed: {e}. Using rule-based.")
            model_label = _rule_based_classify(domain_accuracies)
            confidence  = 0.70
    else:
        model_label = _rule_based_classify(domain_accuracies)
        confidence  = 0.70

    frontend_label = MODEL_TO_FRONTEND.get(model_label, "no_significant_difficulty")
    risk_level     = _get_risk_level(model_label, confidence, domain_accuracies)
    summary, detail, recs = _get_narrative(frontend_label, domain_accuracies)

    return {
        "primaryDifficulty": frontend_label,
        "confidenceScore":   round(confidence, 4),
        "riskLevel":         risk_level,
        "summary":           summary,
        "detailedAnalysis":  detail,
        "recommendations":   recs,
    }


def _infer_error_type(answer, domain: str) -> str:
    if answer.is_correct:
        return "none"
    domain_error_map = {
        "math":      "conceptual",
        "grammar":   "syntactic",
        "reading":   "misread",
        "memory":    "recall_fail",
        "reasoning": "inference_fail",
    }
    return domain_error_map.get(domain, "careless")


def _get_risk_level(model_label: str, confidence: float, domain_accuracies: dict) -> str:
    if model_label == "no_difficulty":
        return "low"
    min_acc = min(domain_accuracies.values()) if domain_accuracies else 1.0
    if confidence >= 0.80 or min_acc < 0.45:
        return "high"
    elif confidence >= 0.60 or min_acc < 0.65:
        return "moderate"
    return "low"


def _get_narrative(frontend_label: str, domain_accuracies: dict) -> tuple:
    """Return (summary, detailed_analysis, recommendations) strings."""

    narratives = {
        "no_significant_difficulty": (
            "No significant learning difficulties were detected.",
            "Assessment results indicate performance within or above expected ranges across all five cognitive domains. Scores reflect strong foundational skills in language, mathematics, memory, and reasoning. Continue with regular learning activities to maintain and build on these strengths.",
            [
                "Continue with grade-level or advanced materials to maintain progress",
                "Explore enrichment activities to deepen understanding in strong domains",
                "Set new learning challenges to stay motivated",
            ]
        ),
        "dyslexia_related": (
            "Assessment indicates possible dyslexia-related patterns affecting reading and language processing.",
            "Results show below-average performance in grammar and/or reading comprehension domains, with elevated response times on text-based tasks. These patterns are consistent with indicators associated with dyslexia-related processing differences, including difficulty with phonological processing, reading fluency, and written language mechanics.",
            [
                "Use text-to-speech tools to support reading comprehension",
                "Break reading passages into shorter segments",
                "Practise phonological awareness exercises daily",
                "Consider structured literacy approaches (e.g. Orton-Gillingham)",
            ]
        ),
        "dyscalculia_related": (
            "Assessment indicates possible dyscalculia-related patterns affecting mathematical processing.",
            "Results show significantly below-average performance in the mathematics domain, with extended response times and a higher rate of conceptual and procedural errors. These patterns are consistent with indicators associated with dyscalculia, including difficulty with number sense, arithmetic operations, and mathematical reasoning.",
            [
                "Use visual and hands-on representations of numbers (e.g. number lines, counters)",
                "Practise basic number facts using spaced repetition",
                "Break multi-step problems into individual steps",
                "Use graph paper to help align numbers in calculations",
            ]
        ),
        "memory_related": (
            "Assessment indicates possible memory-related difficulties affecting information retention.",
            "Results show below-average performance in the memory domain, with lower accuracy on sequential recall and working memory tasks. These patterns suggest difficulties with short-term and working memory capacity, which can affect learning across all subjects.",
            [
                "Use chunking strategies to break information into smaller units",
                "Practise spaced repetition for memorising key facts",
                "Use visual mnemonics and mind maps",
                "Reduce cognitive load by presenting one concept at a time",
            ]
        ),
        "reasoning_related": (
            "Assessment indicates possible reasoning-related difficulties affecting logical and abstract thinking.",
            "Results show below-average performance in the reasoning domain, with difficulty on pattern recognition, logical deduction, and abstract reasoning tasks. Extended response times suggest effortful processing when drawing inferences or identifying relationships.",
            [
                "Practise structured problem-solving using step-by-step approaches",
                "Use visual diagrams to represent logical relationships",
                "Work through analogical reasoning exercises regularly",
                "Play strategy-based games to build pattern recognition skills",
            ]
        ),
        "reading_comprehension": (
            "Assessment indicates difficulty with reading comprehension and inferential understanding.",
            "Results show below-average performance on reading passages, particularly on inference-based questions. Extended response times on text-based tasks suggest difficulty extracting meaning from longer texts and integrating information across sentences.",
            [
                "Practise summarising paragraphs in your own words",
                "Use the SQ3R method (Survey, Question, Read, Recite, Review)",
                "Focus on identifying main ideas and supporting details",
                "Gradually increase text length and complexity",
            ]
        ),
    }

    label = frontend_label if frontend_label in narratives else "no_significant_difficulty"
    return narratives[label]
