"""routes/meta.py — small public endpoints for reference data the UI needs before login."""
from flask import Blueprint, jsonify
from utils.grades import GRADES

meta_bp = Blueprint("meta", __name__)


@meta_bp.get("/grades")
def list_grades():
    """Public list of grades/classes, used by the registration form."""
    return jsonify(GRADES), 200
