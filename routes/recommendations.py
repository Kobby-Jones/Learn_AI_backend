"""routes/recommendations.py"""
import uuid
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import RecommendationSet, LearningMaterial, AssessmentResult, Bookmark, MaterialProgress

recommendations_bp = Blueprint("recommendations", __name__)

@recommendations_bp.get("/")
@jwt_required()
def get_recommendations():
    user_id = get_jwt_identity()
    rec_set = RecommendationSet.query.filter_by(student_id=user_id)\
                .order_by(RecommendationSet.generated_at.desc()).first()
    if not rec_set:
        return jsonify({"materials": [], "primaryFocus": None}), 200

    bookmarks = {b.material_id for b in Bookmark.query.filter_by(user_id=user_id).all()}
    progress  = {p.material_id: p.progress_pct for p in MaterialProgress.query.filter_by(user_id=user_id).all()}

    materials = []
    for mid in rec_set.material_ids:
        m = LearningMaterial.query.get(mid)
        if m:
            materials.append(m.to_dict(
                recommendation_score=0.9,
                is_bookmarked=(mid in bookmarks),
                progress_percent=progress.get(mid, 0),
            ))

    return jsonify({
        "id":                  rec_set.id,
        "studentId":           rec_set.student_id,
        "assessmentResultId":  rec_set.assessment_result_id,
        "generatedAt":         rec_set.generated_at.isoformat(),
        "primaryFocus":        rec_set.primary_focus,
        "materials":           materials,
    }), 200


@recommendations_bp.get("/library")
@jwt_required()
def get_library():
    """All available materials (library page)."""
    user_id  = get_jwt_identity()
    domain   = request.args.get("domain")
    fmt      = request.args.get("format")

    query = LearningMaterial.query.filter_by(is_active=True)
    if domain:
        query = query.filter_by(domain=domain)
    if fmt:
        query = query.filter_by(format=fmt)
    materials = query.all()

    bookmarks = {b.material_id for b in Bookmark.query.filter_by(user_id=user_id).all()}
    progress  = {p.material_id: p.progress_pct for p in MaterialProgress.query.filter_by(user_id=user_id).all()}

    return jsonify([m.to_dict(
        is_bookmarked=(m.id in bookmarks),
        progress_percent=progress.get(m.id, 0),
    ) for m in materials]), 200


@recommendations_bp.post("/bookmark/<material_id>")
@jwt_required()
def toggle_bookmark(material_id):
    user_id  = get_jwt_identity()
    existing = Bookmark.query.filter_by(user_id=user_id, material_id=material_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({"bookmarked": False}), 200
    db.session.add(Bookmark(user_id=user_id, material_id=material_id))
    db.session.commit()
    return jsonify({"bookmarked": True}), 200


@recommendations_bp.post("/progress/<material_id>")
@jwt_required()
def update_progress(material_id):
    user_id = get_jwt_identity()
    pct     = request.get_json().get("progressPercent", 0)
    record  = MaterialProgress.query.filter_by(user_id=user_id, material_id=material_id).first()
    if record:
        record.progress_pct = pct
    else:
        db.session.add(MaterialProgress(user_id=user_id, material_id=material_id, progress_pct=pct))
    db.session.commit()
    return jsonify({"progressPercent": pct}), 200
