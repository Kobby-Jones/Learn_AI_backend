"""routes/notifications.py"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Notification

notifications_bp = Blueprint("notifications", __name__)

@notifications_bp.get("/")
@jwt_required()
def get_notifications():
    user_id = get_jwt_identity()
    notes   = Notification.query.filter_by(user_id=user_id)\
                .order_by(Notification.created_at.desc()).limit(50).all()
    return jsonify([n.to_dict() for n in notes]), 200

@notifications_bp.post("/<nid>/read")
@jwt_required()
def mark_read(nid):
    user_id = get_jwt_identity()
    note    = Notification.query.filter_by(id=nid, user_id=user_id).first()
    if note:
        note.is_read = True
        db.session.commit()
    return jsonify({"ok": True}), 200

@notifications_bp.post("/read-all")
@jwt_required()
def mark_all_read():
    user_id = get_jwt_identity()
    Notification.query.filter_by(user_id=user_id, is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"ok": True}), 200
