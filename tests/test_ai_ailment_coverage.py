"""
Automated Test Suite for Comprehensive AI Ailment Assistant Coverage:
Verifies that 25+ distinct clinical conditions receive unique, genuine,
and tailored medication plans with live dispensary inventory stock,
and that no query degrades to identical canned boilerplate.
"""
import pytest
from app.services.ai_service import AIService, CURATED_DEMO_KNOWLEDGE

AILMENT_TEST_QUERIES = [
    ("acidity", "Acid reflux and burning chest sensation after dinner"),
    ("fever", "Mild acute fever with body temperature and shivering chills"),
    ("headache", "Tension headache and throbbing temple pain"),
    ("cold", "Common cold with runny nose and frequent sneezing"),
    ("cough", "Dry hacking cough with bronchial tickling"),
    ("pain", "General body ache, lower back stiffness, and joint soreness"),
    ("allergies", "Seasonal allergies with itchy hives and allergic rhinitis"),
    ("diarrhea", "Acute loose motions, watery diarrhea, and stomach bug"),
    ("nausea_vomiting", "Severe nausea, vomiting, and food poisoning queasiness"),
    ("constipation", "Functional constipation and hard stool for three days"),
    ("sore_throat", "Pharyngitis, scratchy sore throat, and painful swallowing"),
    ("mouth_ulcers", "Painful mouth ulcers and burning canker sores on tongue"),
    ("toothache", "Acute toothache, dental sensitivity, and swollen tender gum"),
    ("skin_rash_fungal", "Fungal skin infection with itchy ringworm rash"),
    ("eye_strain_dry", "Dry eyes, burning sensation, and computer vision strain"),
    ("muscle_spasm_sprain", "Twisted ankle ligament sprain and muscle cramp"),
    ("gas_bloating", "Intestinal gas, severe bloating, and flatulence"),
    ("dehydration_heat", "Electrolyte depletion, heat fatigue, and extreme thirst"),
    ("minor_cuts_burns", "Minor kitchen cut and superficial heat burn scrape"),
    ("motion_sickness_vertigo", "Motion sickness, car travel nausea, and dizziness"),
    ("insomnia_sleep", "Trouble sleeping at night and acute mild insomnia"),
    ("ear_discomfort", "Earache, ear fullness, and blocked ear wax"),
    ("acne_breakouts", "Facial acne breakouts, pimples, and oily blemishes"),
    ("urinary_discomfort_mild", "Burning urination sensation and mild dysuria"),
    ("sunburn_heat_rash", "Sunburn with red stinging skin and prickly heat rash"),
]

def test_all_25_ailments_produce_unique_responses(client):
    """Verifies all 25 conditions receive distinct, unique clinical plans with zero duplicates."""
    seen_responses = set()
    
    for topic_id, query_text in AILMENT_TEST_QUERIES:
        res = client.post("/api/ai/consult", json={"query": query_text})
        assert res.status_code == 200, f"Query for {topic_id} failed with {res.status_code}"
        data = res.get_json()["result"]
        
        # 1. Non-emergency for standard queries
        assert data["is_emergency"] is False
        
        # 2. Must not contain the old generic fallback boilerplate
        resp_text = data["response"]
        assert "Thank you for reaching out to the MediApp Health Assistant. For mild everyday symptoms" not in resp_text, \
            f"Query '{query_text}' fell back to generic boilerplate!"
        
        # 3. Must contain the 5-pillar structure
        assert "Clinical Context" in resp_text or "Assessment" in resp_text
        assert "Self-Care" in resp_text
        assert "Recommended Over-The-Counter" in resp_text or "OTC" in resp_text
        assert "Red Flags" in resp_text
        assert "Physician Consultation" in resp_text
        
        # 4. Must be unique across all 25 ailments
        assert resp_text not in seen_responses, f"Duplicate response detected for topic '{topic_id}'"
        seen_responses.add(resp_text)
        
        # 5. Must return recommended medicines matching live stock
        meds = data.get("recommended_medicines", [])
        assert len(meds) > 0, f"No recommended medicines returned for topic '{topic_id}'"
        assert any(m.get("stock_quantity", 0) > 0 for m in meds), f"No in-stock medicines for topic '{topic_id}'"

def test_novel_query_dynamic_tailored_synthesis(client):
    """Verifies that an unmapped, novel medical query generates a dynamic tailored response rather than static boilerplate."""
    res = client.post("/api/ai/consult", json={
        "query": "Mild intermittent fluttering and twitching in my left eyelid for two days"
    })
    assert res.status_code == 200
    data = res.get_json()["result"]
    assert data["is_emergency"] is False
    assert "Thank you for reaching out to the MediApp Health Assistant. For mild everyday symptoms" not in data["response"]
    assert "Tailored Clinical Guidance" in data["response"]
    assert len(data.get("recommended_medicines", [])) > 0

def test_emergency_red_flag_priority(client):
    """Verifies life-threatening symptoms immediately trigger emergency red-flag alert."""
    res = client.post("/api/ai/consult", json={
        "query": "Patient experiencing crushing central chest pain radiating to left jaw and shortness of breath"
    })
    assert res.status_code == 200
    data = res.get_json()["result"]
    assert data["is_emergency"] is True
    assert "CRITICAL ALERT" in data["response"]
    assert "112 / 911" in data["response"]
    assert len(data["recommended_medicines"]) == 0

def test_anaphylactic_shock_red_flag_priority(client):
    """Verifies acute anaphylaxis, anaphylactic shock, and airway emergencies trigger immediate emergency triage with 0 medicines."""
    anaphylaxis_queries = [
        "anaphylactic shock after peanut intake",
        "severe anaphylactic reaction with respiratory distress",
        "patient in anaphylactic shock",
        "acute allergic reaction with swollen tongue and throat closing",
        "angioedema and throat swelling"
    ]
    for q in anaphylaxis_queries:
        res = client.post("/api/ai/consult", json={"query": q})
        assert res.status_code == 200, f"Query '{q}' failed with status {res.status_code}"
        data = res.get_json()["result"]
        assert data["is_emergency"] is True, f"Query '{q}' was not flagged as emergency!"
        assert data.get("emergency") is True, f"Query '{q}' missing emergency=True"
        assert "CRITICAL ALERT" in data["response"], f"Query '{q}' missing CRITICAL ALERT"
        assert "112 / 911" in data["response"], f"Query '{q}' missing emergency numbers"
        assert len(data["recommended_medicines"]) == 0, f"Query '{q}' returned medicines: {data['recommended_medicines']}"

