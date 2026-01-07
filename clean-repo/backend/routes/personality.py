from flask import Blueprint, jsonify
from personality_engine.traits_data import TYPE_DESCRIPTIONS

personality_bp = Blueprint("personality", __name__, url_prefix="/api/personality")

@personality_bp.get("/<ptype>")
def get_personality(ptype):
    base = ptype.split("-")[0].upper()

    return jsonify({
        "type": ptype,
        "description": TYPE_DESCRIPTIONS.get(base, {})
    })
