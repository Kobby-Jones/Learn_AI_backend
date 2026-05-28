"""routes/results.py"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import AssessmentResult, User

results_bp = Blueprint("results", __name__)

@results_bp.get("/latest")
@jwt_required()
def get_latest_result():
    user_id = get_jwt_identity()
    result  = AssessmentResult.query.filter_by(student_id=user_id)\
                .order_by(AssessmentResult.completed_at.desc()).first()
    if not result:
        return jsonify({"error": "No results found"}), 404
    return jsonify(result.to_dict()), 200

@results_bp.get("/")
@jwt_required()
def get_all_results():
    user_id = get_jwt_identity()
    results = AssessmentResult.query.filter_by(student_id=user_id)\
                .order_by(AssessmentResult.completed_at.desc()).all()
    return jsonify([r.to_dict() for r in results]), 200

@results_bp.get("/<result_id>")
@jwt_required()
def get_result(result_id):
    user_id = get_jwt_identity()
    result  = AssessmentResult.query.get(result_id)
    if not result:
        return jsonify({"error": "Not found"}), 404
    user = User.query.get(user_id)
    # Students can only see their own; teachers/admins can see all
    if user.role == "student" and result.student_id != user_id:
        return jsonify({"error": "Forbidden"}), 403
    return jsonify(result.to_dict()), 200
