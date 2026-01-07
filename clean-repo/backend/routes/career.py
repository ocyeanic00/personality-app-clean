from flask import Blueprint, jsonify
from personality_engine.career_data import CAREER_MAP

career_bp = Blueprint("career", __name__, url_prefix="/api/career")

@career_bp.route("/<ptype>")
def get_career(ptype):
    ptype = ptype.upper()

    if ptype not in CAREER_MAP:
        return jsonify({"error": "Career data not found"}), 404

    return jsonify(CAREER_MAP[ptype])