"""
Integration tests for AI Ailment Assistant.
Verifies emergency red-flag triage, non-diagnostic OTC guidance, and demo fallback disclaimers.
"""
def test_ai_emergency_triage_alert(client):
    res = client.post("/api/ai/consult", json={
        "query": "I am having sudden crushing chest pain and shortness of breath"
    })
    assert res.status_code == 200
    result = res.json["result"]
    assert result["is_emergency"] is True
    assert "CRITICAL ALERT" in result["response"]
    assert "112 / 911" in result["response"]

def test_ai_anaphylaxis_and_morphological_variants_alert(client):
    """Verifies that anaphylaxis, anaphylactic shock, and related acute allergic emergencies trigger red-flag alert and 0 medicines."""
    test_queries = [
        "anaphylactic shock after peanut intake",
        "severe anaphylactic reaction to insect sting",
        "throat closing and facial swelling",
        "anaphylaxis symptoms from penicillin"
    ]
    for q in test_queries:
        res = client.post("/api/ai/consult", json={"query": q})
        assert res.status_code == 200
        result = res.json["result"]
        assert result["is_emergency"] is True, f"Failed on {q}"
        assert result.get("emergency") is True
        assert "CRITICAL ALERT" in result["response"]
        assert "112 / 911" in result["response"]
        assert len(result.get("recommended_medicines", [])) == 0

def test_ai_otc_clinical_guidance(client):
    res = client.post("/api/ai/consult", json={
        "query": "What should I take for a mild headache?"
    })
    assert res.status_code == 200
    result = res.json["result"]
    assert result["is_emergency"] is False
    assert "Paracetamol" in result["response"]
    assert "disclaimer" in result
