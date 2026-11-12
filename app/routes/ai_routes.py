"""
AI Ailment Assistant Routes for MediApp.
Dispatches user health symptom queries to the AI service with emergency screening.
"""
from flask import Blueprint, request, jsonify
from app.services.ai_service import AIService

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")

@ai_bp.route("/consult", methods=["POST"])
def consult_assistant():
    data = request.get_json() or {}
    query = data.get("query", "").strip()
    
    if not query:
        return jsonify({"error": "Query string is required."}), 400

    try:
        result = AIService.query_assistant(query)
        return jsonify({"status": "success", "result": result})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 502
    except Exception as e:
        return jsonify({"error": f"AI Assistant service error: {str(e)}"}), 500
