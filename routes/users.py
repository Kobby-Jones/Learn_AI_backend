"""routes/users.py"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, AssessmentResult, MaterialProgress
from extensions import db
import json

users_bp = Blueprint("users", __name__)

@users_bp.get("/stats")
@jwt_required()
def get_student_stats():
    user_id  = get_jwt_identity()
    results  = AssessmentResult.query.filter_by(student_id=user_id)\
                .order_by(AssessmentResult.completed_at.asc()).all()
    completed_materials = MaterialProgress.query.filter(
        MaterialProgress.user_id == user_id,
        MaterialProgress.progress_pct >= 100
    ).count()

    scores = [r.overall_score for r in results]
    avg    = round(sum(scores) / len(scores), 1) if scores else 0
    improvement = round(scores[-1] - scores[0], 1) if len(scores) >= 2 else 0
    total_time  = sum(r.time_spent for r in results) // 60  # minutes

    last_date = results[-1].completed_at.isoformat() if results else None
    return jsonify({
        "totalAssessments":   len(results),
        "averageScore":       avg,
        "improvementRate":    improvement,
        "streakDays":         0,  # can be implemented with daily tracking
        "materialsCompleted": completed_materials,
        "totalTimeSpent":     total_time,
        "lastAssessmentDate": last_date,
    }), 200


@users_bp.get("/progress")
@jwt_required()
def get_progress():
    user_id = get_jwt_identity()
    results = AssessmentResult.query.filter_by(student_id=user_id)\
                .order_by(AssessmentResult.completed_at.asc()).all()
    entries = []
    for r in results:
        domain_map = {d["domain"]: d["accuracy"] for d in r.domain_scores}
        entries.append({
            "date":         r.completed_at.strftime("%Y-%m-%d"),
            "overallScore": r.overall_score,
            "mathematics":  domain_map.get("mathematics", 0),
            "grammar":      domain_map.get("grammar", 0),
            "reading":      domain_map.get("reading", 0),
            "memory":       domain_map.get("memory", 0),
            "reasoning":    domain_map.get("reasoning", 0),
        })
    return jsonify(entries), 200
