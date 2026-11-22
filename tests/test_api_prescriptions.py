"""
Integration tests for prescription upload, validation, OCR parsing, and pharmacist verification.
"""
import io

def test_prescription_upload_unsupported_format_rejected(auth_client):
    client = auth_client("customer")
    data = {
        "file": (io.BytesIO(b"fake executable content"), "script.exe")
    }
    res = client.post("/api/prescriptions/upload", data=data, content_type="multipart/form-data")
    assert res.status_code == 400
    assert "Unsupported file type" in res.json["error"]

def test_prescription_upload_valid_file_and_ocr(auth_client):
    client = auth_client("customer")
    sample_text_pdf = b"%PDF-1.4 ... Rx Dr. Arvind Kapoor Telma 40mg Atorva 20mg ... %%EOF"
    data = {
        "file": (io.BytesIO(sample_text_pdf), "dr_kapoor_cardio.pdf")
    }
    res = client.post("/api/prescriptions/upload", data=data, content_type="multipart/form-data")
    assert res.status_code == 201
    rx = res.json["prescription"]
    assert rx["id"] is not None
    assert rx["status"] == "pending"
    assert rx["ocr_confidence"] >= 0.50

def test_pharmacist_prescription_verification(auth_client):
    # Customer uploads
    cust = auth_client("customer")
    data = {"file": (io.BytesIO(b"%PDF-1.4 sample"), "test_rx.pdf")}
    upload_res = cust.post("/api/prescriptions/upload", data=data, content_type="multipart/form-data")
    rx_id = upload_res.json["prescription"]["id"]

    # Pharmacy user verifies
    pharm = auth_client("pharmacy")
    verify_res = pharm.post(f"/api/prescriptions/{rx_id}/verify", json={"decision": "verified"})
    assert verify_res.status_code == 200

    # Customer inspects verified state
    check_res = cust.get(f"/api/prescriptions/{rx_id}")
    assert check_res.json["prescription"]["status"] == "verified"

    # Attempting to re-verify or reject an already verified prescription returns 400
    reverify_res = pharm.post(f"/api/prescriptions/{rx_id}/verify", json={"decision": "verified"})
    assert reverify_res.status_code == 400
    assert "Only pending prescriptions can be reviewed or transitioned" in reverify_res.json["error"]

    reject_res = pharm.post(f"/api/prescriptions/{rx_id}/reject", json={"reason": "Contradictory reject"})
    assert reject_res.status_code == 400
    assert "Only pending prescriptions can be reviewed or transitioned" in reject_res.json["error"]
