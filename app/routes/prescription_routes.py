"""
Prescription Document & OCR Verification Routes for MediApp.
Secures uploaded prescriptions, runs multi-tiered OCR analysis,
and facilitates pharmacist/admin review and verification.
"""
import os
import secrets
import json
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, session, send_file
from app.config import Config
from app.services.auth_service import login_required, roles_required
from app.services.ocr_service import OCRService
from app.services.order_service import OrderService
from app.database import query_db, get_db

prescription_bp = Blueprint("prescriptions", __name__, url_prefix="/api/prescriptions")

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@prescription_bp.route("/upload", methods=["POST"])
@login_required
def upload_prescription():
    if "file" not in request.files:
        return jsonify({"error": "No file part in upload request."}), 400
        
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400
        
    if not allowed_file(file.filename):
        return jsonify({
            "error": f"Unsupported file type. Allowed formats: {', '.join(sorted(Config.ALLOWED_EXTENSIONS))}."
        }), 400

    user_id = session["user_id"]
    original_name = secure_filename(file.filename)
    extension = original_name.rsplit(".", 1)[1].lower()
    unique_filename = f"rx_{user_id}_{secrets.token_hex(8)}.{extension}"
    
    upload_folder = Config.UPLOAD_FOLDER
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, unique_filename)
    
    file.save(file_path)
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({"error": "Uploaded file is empty (0 bytes)."}), 400

    mime_type = file.mimetype or "application/octet-stream"

    # Execute OCR extraction pipeline
    try:
        ocr_result = OCRService.process_document(file_path, mime_type)
    except Exception as e:
        ocr_result = {
            "doctor_name": None,
            "patient_name": None,
            "prescription_date": None,
            "extracted_medicines": [],
            "confidence": 0.0,
            "raw_text": f"OCR extraction failed: {str(e)}",
            "provider": "failed"
        }

    # Store prescription record in database
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO prescriptions (
            customer_id, file_path, original_filename, file_size, mime_type,
            doctor_name, patient_name, prescription_date, extracted_text,
            extracted_medicines, ocr_confidence, ocr_provider, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
    """, (
        user_id,
        file_path,
        original_name,
        file_size,
        mime_type,
        ocr_result.get("doctor_name"),
        ocr_result.get("patient_name"),
        ocr_result.get("prescription_date"),
        ocr_result.get("raw_text"),
        json.dumps(ocr_result.get("extracted_medicines", [])),
        ocr_result.get("confidence", 0.0),
        ocr_result.get("provider", "heuristic")
    ))
    conn.commit()
    rx_id = cur.lastrowid

    extracted_meds = ocr_result.get("extracted_medicines", [])
    return jsonify({
        "status": "success",
        "message": "Prescription uploaded and processed.",
        "prescription_id": rx_id,
        "ocr_status": "pending",
        "detected_medicines": extracted_meds,
        "prescription": {
            "id": rx_id,
            "original_filename": original_name,
            "file_size": file_size,
            "status": "pending",
            "doctor_name": ocr_result.get("doctor_name"),
            "patient_name": ocr_result.get("patient_name"),
            "prescription_date": ocr_result.get("prescription_date"),
            "extracted_medicines": extracted_meds,
            "detected_medicines": extracted_meds,
            "ocr_confidence": ocr_result.get("confidence", 0.0),
            "ocr_provider": ocr_result.get("provider")
        }
    }), 201

@prescription_bp.route("", methods=["GET"])
@login_required
def list_prescriptions():
    user_id = session["user_id"]
    role = session["role"]
    
    if role == "delivery":
        return jsonify({"error": "Access denied. Delivery personnel are not authorized to view prescriptions."}), 403
    elif role == "customer":
        rows = query_db("SELECT * FROM prescriptions WHERE customer_id = ? ORDER BY id DESC", (user_id,))
    elif role in ("pharmacy", "admin"):
        # Pharmacy and admin can view pending or all prescriptions
        rows = query_db("""
            SELECT p.*, u.full_name as customer_name, u.email as customer_email
            FROM prescriptions p
            JOIN users u ON p.customer_id = u.id
            ORDER BY p.id DESC
            LIMIT 50
        """)
    else:
        return jsonify({"error": "Unauthorized role."}), 403

    result = []
    for r in rows:
        item = dict(r)
        try:
            item["extracted_medicines"] = json.loads(item["extracted_medicines"]) if item["extracted_medicines"] else []
        except Exception:
            item["extracted_medicines"] = []
        item["detected_medicines"] = item["extracted_medicines"]
        result.append(item)

    return jsonify({"status": "success", "prescriptions": result})

@prescription_bp.route("/<int:rx_id>", methods=["GET"])
@login_required
def get_prescription(rx_id: int):
    user_id = session["user_id"]
    role = session["role"]
    
    if role == "delivery":
        return jsonify({"error": "Access denied. Delivery personnel are not authorized to view patient medical prescriptions."}), 403

    rx = query_db("""
        SELECT p.*, u.full_name as customer_name, u.email as customer_email
        FROM prescriptions p
        JOIN users u ON p.customer_id = u.id
        WHERE p.id = ?
    """, (rx_id,), one=True)
    
    if not rx:
        return jsonify({"error": f"Prescription ID {rx_id} not found."}), 404
        
    if role == "customer" and rx["customer_id"] != user_id:
        return jsonify({"error": "Access denied. You do not own this prescription."}), 403

    if role not in ("customer", "pharmacy", "admin"):
        return jsonify({"error": "Unauthorized role."}), 403

    rx_dict = dict(rx)
    try:
        rx_dict["extracted_medicines"] = json.loads(rx_dict["extracted_medicines"]) if rx_dict["extracted_medicines"] else []
    except Exception:
        rx_dict["extracted_medicines"] = []
    rx_dict["detected_medicines"] = rx_dict["extracted_medicines"]

    return jsonify({"status": "success", "prescription": rx_dict})

@prescription_bp.route("/<int:rx_id>/verify", methods=["POST"])
@login_required
@roles_required("pharmacy", "admin")
def verify_prescription(rx_id: int):
    if session.get("role") == "pharmacy":
        pharm_id = session.get("pharmacy_id")
        if not pharm_id:
            return jsonify({"error": "User is not associated with an approved pharmacy."}), 403
        pharm = query_db("SELECT status FROM pharmacies WHERE id = ?", (pharm_id,), one=True)
        if not pharm or pharm["status"] != "approved":
            return jsonify({"error": "Associated pharmacy is not approved to verify prescriptions."}), 403

    data = request.get_json() or {}
    decision = data.get("decision", "verified") # 'verified' or 'rejected'
    rejection_reason = data.get("rejection_reason") or data.get("reason")
    user_id = session["user_id"]

    if decision not in ("verified", "rejected"):
        return jsonify({"error": "Decision must be 'verified' or 'rejected'."}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE prescriptions
        SET status = ?,
            reviewed_by = ?,
            rejection_reason = ?,
            verified_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (decision, user_id, rejection_reason if decision == "rejected" else None, rx_id))
    if cur.rowcount == 0:
        return jsonify({"error": f"Prescription ID {rx_id} not found."}), 404
    conn.commit()

    # Synchronize any linked orders waiting for this prescription
    user_role = session.get("role", "pharmacy")
    linked_orders = query_db(
        "SELECT id FROM orders WHERE prescription_id = ? AND order_status = 'AWAITING_PRESCRIPTION'",
        (rx_id,),
        conn=conn
    )
    for ord_row in linked_orders:
        oid = ord_row["id"]
        try:
            if decision == "verified":
                OrderService.transition_order_status(
                    order_id=oid,
                    target_status="PRESCRIPTION_VERIFIED",
                    user_id=user_id,
                    user_role=user_role,
                    notes="Prescription verified and approved by licensed pharmacist",
                    conn=conn
                )
            elif decision == "rejected":
                OrderService.transition_order_status(
                    order_id=oid,
                    target_status="CANCELLED",
                    user_id=user_id,
                    user_role=user_role,
                    notes=f"Prescription rejected by pharmacist: {rejection_reason or 'Clinical documentation invalid'}",
                    conn=conn
                )
        except Exception:
            pass

    return jsonify({
        "status": "success",
        "message": f"Prescription has been marked as {decision}."
    })

@prescription_bp.route("/<int:rx_id>/reject", methods=["POST"])
@login_required
@roles_required("pharmacy", "admin")
def reject_prescription(rx_id: int):
    """Convenience endpoint dedicated to prescription rejection matching frontend api.ts."""
    if session.get("role") == "pharmacy":
        pharm_id = session.get("pharmacy_id")
        if not pharm_id:
            return jsonify({"error": "User is not associated with an approved pharmacy."}), 403
        pharm = query_db("SELECT status FROM pharmacies WHERE id = ?", (pharm_id,), one=True)
        if not pharm or pharm["status"] != "approved":
            return jsonify({"error": "Associated pharmacy is not approved to verify prescriptions."}), 403

    data = request.get_json() or {}
    reason = data.get("reason") or data.get("rejection_reason") or "Clinical documentation invalid"
    user_id = session["user_id"]

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE prescriptions
        SET status = 'rejected',
            reviewed_by = ?,
            rejection_reason = ?,
            verified_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (user_id, reason, rx_id))
    if cur.rowcount == 0:
        return jsonify({"error": f"Prescription ID {rx_id} not found."}), 404
    conn.commit()

    user_role = session.get("role", "pharmacy")
    linked_orders = query_db(
        "SELECT id FROM orders WHERE prescription_id = ? AND order_status = 'AWAITING_PRESCRIPTION'",
        (rx_id,),
        conn=conn
    )
    for ord_row in linked_orders:
        oid = ord_row["id"]
        try:
            OrderService.transition_order_status(
                order_id=oid,
                target_status="CANCELLED",
                user_id=user_id,
                user_role=user_role,
                notes=f"Prescription rejected by pharmacist: {reason}",
                conn=conn
            )
        except Exception:
            pass

    return jsonify({
        "status": "success",
        "message": "Prescription has been marked as rejected."
    })

@prescription_bp.route("/<int:rx_id>/file", methods=["GET"])
@login_required
def download_prescription_file(rx_id: int):
    """Secure endpoint for downloading/viewing prescription images with authorization."""
    user_id = session["user_id"]
    role = session["role"]
    
    if role == "delivery":
        return jsonify({"error": "Access denied. Delivery personnel are not authorized to download patient prescriptions."}), 403

    rx = query_db("SELECT customer_id, file_path, original_filename, mime_type FROM prescriptions WHERE id = ?", (rx_id,), one=True)
    if not rx:
        return jsonify({"error": "Prescription not found."}), 404
        
    if role == "customer" and rx["customer_id"] != user_id:
        return jsonify({"error": "Access denied. You do not own this prescription."}), 403

    if role not in ("customer", "pharmacy", "admin"):
        return jsonify({"error": "Unauthorized role."}), 403

    if not os.path.exists(rx["file_path"]):
        return jsonify({"error": "Prescription file does not exist on disk."}), 404

    return send_file(
        rx["file_path"],
        mimetype=rx["mime_type"],
        as_attachment=False,
        download_name=rx["original_filename"]
    )
