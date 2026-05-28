"""routes/assessment.py"""
import uuid
import json
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import User, Assessment, Answer, Question, AssessmentResult, RecommendationSet, Notification, log_event
from utils.classifier import classify_responses
from utils.recommendations import generate_recommendations

assessment_bp = Blueprint("assessment", __name__)


# ── Get all questions (served to the frontend to run the assessment) ──────────
@assessment_bp.get("/questions")
@jwt_required()
def get_questions():
    """Returns the full question bank sorted by domain."""
    questions = Question.query.filter_by(is_active=True).all()
    ordered_domains = ["mathematics", "grammar", "reading", "memory", "reasoning"]
    questions.sort(key=lambda q: ordered_domains.index(q.domain) if q.domain in ordered_domains else 99)
    return jsonify([q.to_dict() for q in questions]), 200


# ── Start a new assessment session ───────────────────────────────────────────
@assessment_bp.post("/start")
@jwt_required()
def start_assessment():
    user_id = get_jwt_identity()
    user    = User.query.get(user_id)
    if not user or user.role != "student":
        return jsonify({"error": "Only students can start assessments"}), 403

    # Mark any in-progress assessment as abandoned
    Assessment.query.filter_by(student_id=user_id, status="in_progress").update({"status": "abandoned"})
    db.session.commit()

    assessment = Assessment(
        id=str(uuid.uuid4()),
        student_id=user_id,
        status="in_progress",
        started_at=datetime.now(timezone.utc),
    )
    db.session.add(assessment)
    log_event(user, "Assessment started", level="info",
              ip=request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip())
    db.session.commit()
    return jsonify({"assessmentId": assessment.id}), 201


# ── Submit completed assessment → run classifier → save results ───────────────
@assessment_bp.post("/<assessment_id>/submit")
@jwt_required()
def submit_assessment(assessment_id):
    user_id = get_jwt_identity()
    assessment = Assessment.query.filter_by(id=assessment_id, student_id=user_id).first()

    if not assessment:
        return jsonify({"error": "Assessment not found"}), 404
    if assessment.status not in ("in_progress", "pending"):
        return jsonify({"error": "Assessment already submitted"}), 400

    data    = request.get_json()
    answers = data.get("answers", {})   # { questionId: { answer, responseTime, isCorrect, skipped } }

    if not answers:
        return jsonify({"error": "No answers provided"}), 400

    # Persist answers
    Answer.query.filter_by(assessment_id=assessment_id).delete()
    for qid, a in answers.items():
        question = Question.query.get(qid)
        if not question:
            continue
        is_correct = (a.get("answer") == question.correct_answer) if a.get("answer") else False
        db.session.add(Answer(
            assessment_id=assessment_id,
            question_id=qid,
            answer=a.get("answer"),
            response_time=int(a.get("responseTime", 0)),
            is_correct=is_correct,
            skipped=bool(a.get("skipped", False)),
        ))

    assessment.status       = "analysing"
    assessment.completed_at = datetime.now(timezone.utc)
    db.session.commit()

    # ── Run classification ────────────────────────────────────────────────────
    db_answers = Answer.query.filter_by(assessment_id=assessment_id).all()
    classification = classify_responses(db_answers)

    time_spent = int((assessment.completed_at - assessment.started_at).total_seconds())

    # Build domain scores for the result
    domain_scores = _build_domain_scores(db_answers)
    overall_score = round(sum(d["accuracy"] for d in domain_scores) / len(domain_scores), 1) if domain_scores else 0

    strengths  = [d["domain"] for d in domain_scores if d["accuracy"] >= 75]
    weaknesses = [d["domain"] for d in domain_scores if d["accuracy"] < 60]

    # ── Save result ───────────────────────────────────────────────────────────
    result = AssessmentResult(
        id=str(uuid.uuid4()),
        assessment_id=assessment_id,
        student_id=user_id,
        completed_at=datetime.now(timezone.utc),
        overall_score=overall_score,
        time_spent=time_spent,
        primary_difficulty=classification["primaryDifficulty"],
        confidence_score=classification["confidenceScore"],
        risk_level=classification["riskLevel"],
        strengths=json.dumps(strengths),
        weaknesses=json.dumps(weaknesses),
        summary=classification["summary"],
        detailed_analysis=classification["detailedAnalysis"],
        recommendations=json.dumps(classification["recommendations"]),
    )
    result.domain_scores = domain_scores
    db.session.add(result)

    assessment.status = "completed"

    # ── Generate recommendations ──────────────────────────────────────────────
    materials = generate_recommendations(
        primary_difficulty=classification["primaryDifficulty"],
        weaknesses=weaknesses,
        student_id=user_id,
    )
    primary_focus = weaknesses[0] if weaknesses else (domain_scores[0]["domain"] if domain_scores else "reading")
    rec_set = RecommendationSet(
        id=str(uuid.uuid4()),
        student_id=user_id,
        assessment_result_id=result.id,
        primary_focus=primary_focus,
    )
    rec_set.material_ids = [m.id for m in materials]
    db.session.add(rec_set)

    # ── Notify student ────────────────────────────────────────────────────────
    db.session.add(Notification(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title="Assessment Complete",
        message="Your latest assessment has been analysed. View your results now.",
        type="success",
        link="/student/results",
    ))
    db.session.add(Notification(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title="New Recommendations",
        message=f"{len(materials)} new learning materials have been recommended for you.",
        type="info",
        link="/student/recommendations",
    ))

    # Audit log
    log_event(
        assessment.student,
        "Assessment completed",
        level="success",
        ip=request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip(),
        detail=f"Score: {overall_score}% | Classification: {classification['primaryDifficulty']}",
    )

    db.session.commit()
    return jsonify({"resultId": result.id, "message": "Assessment submitted"}), 200


# ── Get assessment status (frontend polls this during analysis) ───────────────
@assessment_bp.get("/<assessment_id>/status")
@jwt_required()
def get_status(assessment_id):
    assessment = Assessment.query.get(assessment_id)
    if not assessment:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"status": assessment.status}), 200


# ── Helpers ───────────────────────────────────────────────────────────────────
def _build_domain_scores(answers: list) -> list:
    """Compute per-domain accuracy, avg response time, correct/total, percentile."""
    domain_data: dict = {}
    for a in answers:
        q = a.question
        if not q:
            continue
        d = q.domain
        if d not in domain_data:
            domain_data[d] = {"correct": 0, "total": 0, "times": []}
        if not a.skipped:
            domain_data[d]["total"] += 1
            if a.is_correct:
                domain_data[d]["correct"] += 1
            if a.response_time:
                domain_data[d]["times"].append(a.response_time)

    # Rough percentile norms (based on population averages from methodology)
    NORMS = {"mathematics": 71, "grammar": 68, "reading": 59, "memory": 64, "reasoning": 66}

    scores = []
    for domain, dd in domain_data.items():
        total   = dd["total"] or 1
        correct = dd["correct"]
        accuracy = round((correct / total) * 100, 1)
        avg_rt  = int(sum(dd["times"]) / len(dd["times"])) if dd["times"] else 0
        norm    = NORMS.get(domain, 65)
        # Simple percentile: linear scale relative to norm
        percentile = max(1, min(99, int(50 + (accuracy - norm) * 1.5)))
        scores.append({
            "domain":          domain,
            "accuracy":        accuracy,
            "avgResponseTime": avg_rt,
            "correct":         correct,
            "total":           total,
            "percentile":      percentile,
        })

    ordered = ["mathematics", "grammar", "reading", "memory", "reasoning"]
    scores.sort(key=lambda x: ordered.index(x["domain"]) if x["domain"] in ordered else 99)
    return scores
