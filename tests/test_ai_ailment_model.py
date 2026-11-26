"""
Test Suite for Model 1: AI Ailment Assistant Trained ML Model Pipeline.
Validates machine learning classification accuracy, probability calibration,
5-pillar clinical structure, live database stock linking, and emergency red-flag triage.
"""
import pytest
import os
import joblib
from app import create_app
from app.services.ai_service import AIService

@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    yield app

def test_ml_model_artifacts_exist():
    """Verify serialized model pipeline and knowledge base exist on disk."""
    model_path = os.path.join("app", "models", "ailment_classifier.joblib")
    knowledge_path = os.path.join("app", "models", "ailment_knowledge.json")
    assert os.path.exists(model_path), f"Missing model at {model_path}"
    assert os.path.exists(knowledge_path), f"Missing knowledge base at {knowledge_path}"

def test_ml_model_pipeline_direct_inference():
    """Verify direct scikit-learn pipeline inference and probability calibration."""
    model_path = os.path.join("app", "models", "ailment_classifier.joblib")
    pipeline = joblib.load(model_path)
    
    test_cases = [
        ("severe acid reflux burning sensation behind breastbone after heavy dinner", "acidity_gerd"),
        ("high temperature 101 fahrenheit feeling warm with shivering chills", "acute_fever"),
        ("tight squeezing headache across temples after long computer screen work", "tension_headache"),
        ("persistent hacking dry cough throat irritation keeping me awake", "acute_bronchial_cough"),
        ("itchy circular red rash on inner thighs spreading outward", "tinea_fungal_infection"),
        ("crushing central chest pain radiating to left shoulder with cold sweats", "cardiovascular_chest_emergency"),
        ("sudden right arm weakness and slurred speech drooping face", "neurological_stroke_emergency"),
    ]
    
    for query, expected_class in test_cases:
        pred = pipeline.predict([query])[0]
        probas = pipeline.predict_proba([query])[0]
        confidence = max(probas)
        assert pred == expected_class, f"Expected {expected_class} for '{query}', got {pred}"
        assert confidence >= 0.20, f"Confidence {confidence} is too low for '{query}'"

def test_ai_service_suggest_medication_plan_with_ml(app):
    """Verify end-to-end AIService.suggest_medication_plan using the ML model."""
    with app.app_context():
        # Test 1: Acidity / GERD
        res = AIService.suggest_medication_plan("I am suffering from intense heartburn and acid burning in my chest after dinner")
        assert not res["is_emergency"]
        assert res["source"] in ("trained_ml_classifier", "clinical_knowledge_engine")
        assert "Clinical Condition Context:" in res["response"] or "Clinical Context" in res["response"]
        assert "Non-Pharmacological Self-Care" in res["response"]
        assert "Recommended Over-The-Counter" in res["response"]
        assert "Red Flags" in res["response"]
        assert "Physician Consultation" in res["response"]
        assert len(res["recommended_medicines"]) > 0
        
        # Test 2: Fever
        res_fever = AIService.suggest_medication_plan("Feeling very hot with fever 101 F, shivering, and body chills")
        assert not res_fever["is_emergency"]
        assert any("Paracetamol" in m["name"] or "Dolo" in m["name"] or "Calpol" in m["name"] for m in res_fever["recommended_medicines"])
        
        # Test 3: Emergency Red-Flag Triage
        res_emergency = AIService.suggest_medication_plan("Crushing chest pain radiating down left arm with profuse cold sweating and breathless")
        assert res_emergency["is_emergency"]
        assert "EMERGENCY" in res_emergency["response"] or "112" in res_emergency["response"]
        assert len(res_emergency["recommended_medicines"]) == 0

def test_ai_service_novel_symptoms_fallback(app):
    """Verify unmapped or novel queries receive safe tailored guidance without crashing."""
    with app.app_context():
        res = AIService.suggest_medication_plan("Mild fluttering sensation and twitching under my left eyelid after long coding")
        assert not res["is_emergency"]
        assert len(res["response"]) > 100
        assert len(res["recommended_medicines"]) > 0
