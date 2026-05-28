"""routes/teacher.py"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, AssessmentResult, Enrollment, MaterialProgress, LearningMaterial, Bookmark
from extensions import db
import json
from sqlalchemy import func

teacher_bp = Blueprint("teacher", __name__)


def _require_teacher(user_id):
    user = User.query.get(user_id)
    if not user or user.role not in ("teacher", "admin"):
        return None
    return user


@teacher_bp.get("/students")
@jwt_required()
def get_students():
    uid = get_jwt_identity()
    if not _require_teacher(uid):
        return jsonify({"error": "Forbidden"}), 403

    enrollments = Enrollment.query.filter_by(teacher_id=uid).all()
    student_ids = [e.student_id for e in enrollments]

    # If no enrollments yet, surface all students (useful for demo)
    if not student_ids:
        students = User.query.filter_by(role="student", is_active=True).all()
    else:
        students = User.query.filter(User.id.in_(student_ids), User.is_active == True).all()

    result = []
    for s in students:
        latest = AssessmentResult.query.filter_by(student_id=s.id)\
                    .order_by(AssessmentResult.completed_at.desc()).first()
        results_all = AssessmentResult.query.filter_by(student_id=s.id)\
                        .order_by(AssessmentResult.completed_at.asc()).all()
        scores = [r.overall_score for r in results_all]
        avg    = round(sum(scores) / len(scores), 1) if scores else 0
        trend  = "stable"
        if len(scores) >= 2:
            trend = "improving" if scores[-1] > scores[-2] else ("declining" if scores[-1] < scores[-2] else "stable")

        result.append({
            "id":               s.id,
            "name":             s.name,
            "email":            s.email,
            "avatar":           s.avatar,
            "lastActivity":     latest.completed_at.isoformat() if latest else s.created_at.isoformat(),
            "totalAssessments": len(scores),
            "averageScore":     avg,
            "primaryDifficulty": latest.primary_difficulty if latest else None,
            "riskLevel":        latest.risk_level if latest else None,
            "trend":            trend,
        })
    return jsonify(result), 200


@teacher_bp.get("/students/<student_id>")
@jwt_required()
def get_student_detail(student_id):
    uid = get_jwt_identity()
    if not _require_teacher(uid):
        return jsonify({"error": "Forbidden"}), 403

    student = User.query.get(student_id)
    if not student or student.role != "student":
        return jsonify({"error": "Student not found"}), 404

    results = AssessmentResult.query.filter_by(student_id=student_id)\
                .order_by(AssessmentResult.completed_at.asc()).all()
    progress_entries = []
    for r in results:
        domain_map = {d["domain"]: d["accuracy"] for d in r.domain_scores}
        progress_entries.append({
            "date":         r.completed_at.strftime("%Y-%m-%d"),
            "overallScore": r.overall_score,
            "mathematics":  domain_map.get("mathematics", 0),
            "grammar":      domain_map.get("grammar", 0),
            "reading":      domain_map.get("reading", 0),
            "memory":       domain_map.get("memory", 0),
            "reasoning":    domain_map.get("reasoning", 0),
        })

    latest = results[-1] if results else None
    return jsonify({
        "student": student.to_dict(),
        "latestResult": latest.to_dict() if latest else None,
        "progress": progress_entries,
        "totalAssessments": len(results),
    }), 200


@teacher_bp.get("/classroom-stats")
@jwt_required()
def classroom_stats():
    uid = get_jwt_identity()
    if not _require_teacher(uid):
        return jsonify({"error": "Forbidden"}), 403

    students     = User.query.filter_by(role="student", is_active=True).all()
    total        = len(students)
    assessed_ids = set()
    all_scores   = []
    difficulty_breakdown = {
        "dyslexia_related": 0, "dyscalculia_related": 0,
        "reading_comprehension": 0, "memory_related": 0,
        "reasoning_related": 0, "no_significant_difficulty": 0,
    }
    recent_activity = []

    for s in students:
        results = AssessmentResult.query.filter_by(student_id=s.id)\
                    .order_by(AssessmentResult.completed_at.desc()).all()
        if results:
            assessed_ids.add(s.id)
            all_scores.append(results[0].overall_score)
            diff = results[0].primary_difficulty
            if diff in difficulty_breakdown:
                difficulty_breakdown[diff] += 1
            recent_activity.append({
                "studentName": s.name,
                "action":      "Completed assessment",
                "time":        results[0].completed_at.isoformat(),
            })

    recent_activity.sort(key=lambda x: x["time"], reverse=True)

    return jsonify({
        "totalStudents":      total,
        "assessedStudents":   len(assessed_ids),
        "averageScore":       round(sum(all_scores) / len(all_scores), 1) if all_scores else 0,
        "difficultyBreakdown": difficulty_breakdown,
        "recentActivity":     recent_activity[:5],
    }), 200


# ── Per-domain class averages (analytics page) ───────────────────────────────
@teacher_bp.get("/analytics")
@jwt_required()
def teacher_analytics():
    uid = get_jwt_identity()
    if not _require_teacher(uid):
        return jsonify({"error": "Forbidden"}), 403

    all_results = AssessmentResult.query.all()
    domain_totals = {"mathematics": [], "grammar": [], "reading": [], "memory": [], "reasoning": []}
    for r in all_results:
        for ds in r.domain_scores:
            d = ds.get("domain")
            if d in domain_totals:
                domain_totals[d].append(ds.get("accuracy", 0))
    domain_averages = [
        {"domain": d.capitalize(), "avg": round(sum(v) / len(v), 1) if v else 0}
        for d, v in domain_totals.items()
    ]

    # Class trend = average overall score per assessment date
    by_date = {}
    for r in all_results:
        key = r.completed_at.strftime("%Y-%m-%d")
        by_date.setdefault(key, []).append(r.overall_score)
    trend = [
        {"date": k, "overallScore": round(sum(v) / len(v), 1)}
        for k, v in sorted(by_date.items())
    ]

    return jsonify({
        "domainAverages": domain_averages,
        "classTrend":     trend,
    }), 200


# ── Material engagement breakdown (recommendations oversight page) ───────────
@teacher_bp.get("/recommendations-engagement")
@jwt_required()
def recommendations_engagement():
    uid = get_jwt_identity()
    if not _require_teacher(uid):
        return jsonify({"error": "Forbidden"}), 403

    students = User.query.filter_by(role="student", is_active=True).all()
    rows = []
    total_assigned = 0
    total_completed = 0

    for s in students:
        # all material progress for this student
        progress_q = MaterialProgress.query.filter_by(user_id=s.id).all()
        completed = sum(1 for p in progress_q if p.progress_pct >= 100)
        total = len(progress_q)
        total_assigned += total
        total_completed += completed
        avg_pct = int(sum(p.progress_pct for p in progress_q) / total) if total else 0
        rows.append({
            "studentId":  s.id,
            "name":       s.name,
            "completed":  completed,
            "total":      total or 0,
            "progressPercent": avg_pct,
        })

    completion_rate = round((total_completed / total_assigned) * 100, 1) if total_assigned else 0

    # Average rating of bookmarked/engaged materials
    avg_rating_row = db.session.query(func.avg(LearningMaterial.rating)).scalar()
    avg_rating = round(float(avg_rating_row), 1) if avg_rating_row else 0

    return jsonify({
        "totalAssigned":   total_assigned,
        "completionRate":  completion_rate,
        "averageRating":   avg_rating,
        "students":        rows,
    }), 200


# ── Generated reports list ───────────────────────────────────────────────────
@teacher_bp.get("/reports")
@jwt_required()
def list_reports():
    """Synthesise a list of reports from real assessment data."""
    uid = get_jwt_identity()
    if not _require_teacher(uid):
        return jsonify({"error": "Forbidden"}), 403

    students = User.query.filter_by(role="student", is_active=True).all()
    reports = []

    # Weekly summary (always present)
    reports.append({
        "title": "Weekly Class Summary",
        "desc":  "Overview of all student activity this week",
        "date":  __import__("datetime").datetime.now().strftime("%Y-%m-%d"),
        "type":  "summary",
    })

    # Per-student latest result (most recent five)
    latest_results = (
        AssessmentResult.query.order_by(AssessmentResult.completed_at.desc()).limit(5).all()
    )
    for r in latest_results:
        student = User.query.get(r.student_id)
        if not student:
            continue
        reports.append({
            "title": f"{student.name} — Assessment Report",
            "desc":  f"Detailed report — {r.primary_difficulty.replace('_', ' ') if r.primary_difficulty else 'no classification'}",
            "date":  r.completed_at.strftime("%Y-%m-%d") if r.completed_at else "—",
            "type":  "individual",
            "resultId": r.id,
        })

    return jsonify(reports), 200
