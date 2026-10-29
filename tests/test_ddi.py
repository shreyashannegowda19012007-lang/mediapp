"""
Unit tests for DDIService.
Asserts clinical drug interaction detection, severity ranking, and generic matching.
"""
from app.services.ddi_service import DDIService, normalize_substance_name

def test_normalize_substance_name():
    tokens = normalize_substance_name("Amlodipine Besylate 5mg Tablet")
    assert "amlodipine" in tokens

    combo_tokens = normalize_substance_name("Amoxicillin + Clavulanic Acid 625mg")
    assert "amoxicillin" in combo_tokens
    assert "clavulanic" in combo_tokens

def test_detect_contraindicated_interaction():
    # Warfarin + Aspirin
    meds = [
        {"id": 26, "name": "Warf 5mg Tablet", "generic_name": "Warfarin Sodium"},
        {"id": 24, "name": "Ecosprin 75mg Tablet", "generic_name": "Aspirin (Acetylsalicylic Acid)"}
    ]
    res = DDIService.check_interactions_for_medicines(meds)
    assert res["has_interactions"] is True
    assert res["highest_severity"] == "CONTRAINDICATED"
    assert any("Bleeding" in intx["title"] for intx in res["interactions"])

def test_detect_sildenafil_nitrate_interaction():
    # Sildenafil + Isosorbide Dinitrate
    meds = [
        {"id": 40, "name": "Manforce 50mg Tablet", "generic_name": "Sildenafil Citrate"},
        {"id": 27, "name": "Sorbitrate 5mg", "generic_name": "Isosorbide Dinitrate"}
    ]
    res = DDIService.check_interactions_for_medicines(meds)
    assert res["has_interactions"] is True
    assert res["highest_severity"] == "CONTRAINDICATED"
    assert any("Hypotension" in intx["title"] for intx in res["interactions"])

def test_safe_medicines_no_interaction():
    meds = [
        {"id": 1, "name": "Crocin Advance 500mg", "generic_name": "Paracetamol"},
        {"id": 30, "name": "Pan 40 Tablet", "generic_name": "Pantoprazole"}
    ]
    res = DDIService.check_interactions_for_medicines(meds)
    assert res["has_interactions"] is False
    assert res["highest_severity"] == "NONE"

def test_generic_alternatives_matching(app):
    with app.app_context():
        # Dolo 650mg should find generic paracetamol alternatives
        res = DDIService.get_generic_alternatives(1) # Crocin Advance 500mg
        assert res["target_medicine"] is not None
        alts = res["alternatives"]
        # Should have found at least 1 alternative sharing same generic_name
        assert len(alts) >= 1
        cheaper = [a for a in alts if a["is_cheaper"]]
        assert len(cheaper) >= 1
