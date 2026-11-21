import unittest
import json
from app import create_app
from app.database import get_db, query_db

class TestBackendRemediations(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def login_role(self, role):
        res = self.client.post("/api/auth/demo-login", json={"role": role})
        self.assertEqual(res.status_code, 200)

    def test_01_delivery_address_whitespace_rejected(self):
        self.login_role("customer")
        # Ensure cart has an item
        self.client.post("/api/cart/items", json={"medicine_id": 1, "quantity": 1})
        # Try blank/whitespace address
        res = self.client.post("/api/orders", json={"delivery_address": "   \n\t  "})
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn("at least 10 characters", data.get("error", ""))

    def test_02_order_otp_generated_and_handoff_enforced(self):
        self.login_role("customer")
        self.client.post("/api/cart/items", json={"medicine_id": 1, "quantity": 1})
        res = self.client.post("/api/orders", json={"delivery_address": "402 Green Glen Layout, Bellandur, Bengaluru 560103"})
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        order_id = data.get("order_id")
        self.assertIsNotNone(order_id)
        
        # Verify OTP is present in database
        order = query_db("SELECT delivery_otp FROM orders WHERE id = ?", (order_id,), one=True)
        self.assertIsNotNone(order["delivery_otp"])
        self.assertEqual(len(order["delivery_otp"]), 6)
        correct_otp = order["delivery_otp"]

        # Fast forward order states: PLACED -> ACCEPTED -> PREPARING -> READY_FOR_PICKUP
        conn = get_db()
        c = conn.cursor()
        c.execute("UPDATE orders SET order_status = 'IN_TRANSIT', delivery_person_id = 4 WHERE id = ?", (order_id,))
        # Also create assignment for delivery rider (user_id 4)
        c.execute("""
            INSERT OR REPLACE INTO delivery_assignments (order_id, delivery_person_id, status)
            VALUES (?, 4, 'in_transit')
        """, (order_id,))
        conn.commit()

        # Now test delivery completion with invalid OTP as delivery agent
        self.login_role("delivery")
        
        # Try wrong OTP
        res_fail = self.client.post(f"/api/delivery/orders/{order_id}/verify-otp", json={"otp": "000000"})
        self.assertEqual(res_fail.status_code, 400)
        self.assertIn("Invalid delivery OTP", res_fail.get_json().get("error", ""))

        # Try correct OTP
        res_ok = self.client.post(f"/api/delivery/orders/{order_id}/verify-otp", json={"otp": correct_otp})
        self.assertEqual(res_ok.status_code, 200)
        
        # Verify status is now DELIVERED
        final_order = query_db("SELECT order_status FROM orders WHERE id = ?", (order_id,), one=True)
        self.assertEqual(final_order["order_status"], "DELIVERED")

    def test_03_cold_chain_query_filtering(self):
        res_all = self.client.get("/api/medicines?limit=24")
        self.assertEqual(res_all.status_code, 200)
        data_all = res_all.get_json()
        total_all = data_all["pagination"]["total_count"]

        res_cold = self.client.get("/api/medicines?cold_chain=1&limit=24")
        self.assertEqual(res_cold.status_code, 200)
        data_cold = res_cold.get_json()
        total_cold = data_cold["pagination"]["total_count"]

        # Cold chain total count must be strictly less than all medicines and > 0
        self.assertGreater(total_all, total_cold)
        self.assertGreater(total_cold, 0)
        for m in data_cold["medicines"]:
            self.assertEqual(m["requires_cold_chain"], 1)

    def test_04_prescription_verification_stores_notes(self):
        self.login_role("pharmacy")
        # Find a pending prescription
        rx = query_db("SELECT id FROM prescriptions WHERE status = 'pending' LIMIT 1", one=True)
        if rx:
            rx_id = rx["id"]
            approved_meds = [{"medicine_id": 1, "name": "Paracetamol 500mg", "dosage": "1-0-1"}]
            notes = "Dosage verified against clinical guidelines"
            res = self.client.post(f"/api/prescriptions/{rx_id}/verify", json={
                "decision": "verified",
                "approved_medicines": approved_meds,
                "clinical_notes": notes
            })
            self.assertEqual(res.status_code, 200)
            
            # Verify persisted in database
            saved_rx = query_db("SELECT approved_medicines, pharmacist_notes, status FROM prescriptions WHERE id = ?", (rx_id,), one=True)
            self.assertEqual(saved_rx["status"], "verified")
            self.assertEqual(saved_rx["pharmacist_notes"], notes)
            self.assertIn("Paracetamol", saved_rx["approved_medicines"])

    def test_05_customer_order_cancellation(self):
        self.login_role("customer")
        self.client.post("/api/cart/items", json={"medicine_id": 1, "quantity": 1})
        res = self.client.post("/api/orders", json={"delivery_address": "402 Green Glen Layout, Bellandur, Bengaluru 560103"})
        self.assertEqual(res.status_code, 201)
        order_id = res.get_json()["order_id"]

        # Cancel order
        res_cancel = self.client.post(f"/api/orders/{order_id}/cancel", json={"reason": "Customer cancelled order"})
        self.assertEqual(res_cancel.status_code, 200)
        order = query_db("SELECT order_status FROM orders WHERE id = ?", (order_id,), one=True)
        self.assertEqual(order["order_status"], "CANCELLED")

if __name__ == "__main__":
    unittest.main()
