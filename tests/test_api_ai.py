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

def test_ai_otc_clinical_guidance(client):
    res = client.post("/api/ai/consult", json={
        "query": "What should I take for a mild headache?"
    })
    assert res.status_code == 200
    result = res.json["result"]
    assert result["is_emergency"] is False
    assert "Paracetamol" in result["response"]
    assert "disclaimer" in result
