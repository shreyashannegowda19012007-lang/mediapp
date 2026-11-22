import unittest
import json
from app import create_app
from app.database import get_db, query_db

class TestBackendRemediations(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        with self.app.app_context():
            conn = get_db()
            conn.execute("UPDATE pharmacy_inventory SET stock_quantity = 100 WHERE medicine_id = 1 AND stock_quantity < 10")
            conn.commit()

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
        self.login_role("delivery")
        delivery_user = query_db("SELECT id FROM users WHERE email = 'demo.delivery@mediapp.local'", one=True)
        delivery_id = delivery_user["id"] if delivery_user else 4

        conn = get_db()
        c = conn.cursor()
        c.execute("UPDATE orders SET order_status = 'IN_TRANSIT', delivery_person_id = ? WHERE id = ?", (delivery_id, order_id))
        # Also create assignment for delivery rider
        c.execute("""
            INSERT OR REPLACE INTO delivery_assignments (order_id, delivery_person_id, status)
            VALUES (?, ?, 'in_transit')
        """, (order_id, delivery_id))
        conn.commit()

        # Now test delivery completion with invalid OTP as delivery agent
        # (already logged in as delivery)
        
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

    def test_06_def04_medicine_rx_query_defensive_parsing(self):
        # Invalid string parameter returns 400 safely without crashing
        res_invalid = self.client.get("/api/medicines?rx=invalid")
        self.assertEqual(res_invalid.status_code, 400)
        self.assertIn("error", res_invalid.get_json())

        # Boolean strings return filtered results
        res_true = self.client.get("/api/medicines?rx=true")
        self.assertEqual(res_true.status_code, 200)
        for med in res_true.get_json()["medicines"]:
            self.assertEqual(med["prescription_required"], 1)

        res_false = self.client.get("/api/medicines?rx=false")
        self.assertEqual(res_false.status_code, 200)
        for med in res_false.get_json()["medicines"]:
            self.assertEqual(med["prescription_required"], 0)

        # Numeric values 1 and 0
        res_1 = self.client.get("/api/medicines?rx=1")
        self.assertEqual(res_1.status_code, 200)
        for med in res_1.get_json()["medicines"]:
            self.assertEqual(med["prescription_required"], 1)

        res_0 = self.client.get("/api/medicines?rx=0")
        self.assertEqual(res_0.status_code, 200)
        for med in res_0.get_json()["medicines"]:
            self.assertEqual(med["prescription_required"], 0)

    def test_07_def05_customer_registration_string_address(self):
        import uuid
        email = f"test.cust.reg.{uuid.uuid4().hex[:6]}@mediapp.local"
        res = self.client.post("/api/auth/register", json={
            "email": email,
            "password": "Password@123",
            "full_name": "Deepika Padukone",
            "phone": "+91 9111122222",
            "address": "Flat 504, Sobha Silicon Oasis, Hosa Road, Bengaluru 560100"
        })
        self.assertEqual(res.status_code, 201)
        user_id = res.get_json()["user"]["id"]

        addr = query_db("SELECT * FROM customer_addresses WHERE user_id = ?", (user_id,), one=True)
        self.assertIsNotNone(addr)
        self.assertIn("Sobha Silicon Oasis", addr["address_line1"])
        self.assertEqual(addr["is_default"], 1)

    def test_08_def06_courier_available_deliveries_parsed_address(self):
        self.login_role("customer")
        self.client.post("/api/cart/items", json={"medicine_id": 1, "quantity": 1})
        test_addr = "402 Green Glen Layout, Bellandur, Bengaluru 560103"
        order_res = self.client.post("/api/orders", json={"delivery_address": test_addr})
        self.assertEqual(order_res.status_code, 201)
        order_id = order_res.get_json()["order_id"]

        # Advance order to READY_FOR_PICKUP with no assigned courier
        conn = get_db()
        conn.execute("UPDATE orders SET order_status = 'READY_FOR_PICKUP', delivery_person_id = NULL WHERE id = ?", (order_id,))
        conn.commit()

        # Login as delivery and check available orders
        self.login_role("delivery")
        avail_res = self.client.get("/api/delivery/available")
        self.assertEqual(avail_res.status_code, 200)
        available_orders = avail_res.get_json().get("available_orders", [])
        matched = next((o for o in available_orders if o["id"] == order_id), None)
        self.assertIsNotNone(matched)
        self.assertIn("delivery_address", matched)
        self.assertIn("Green Glen", matched["delivery_address"])

    def test_09_def07_ai_emergency_triage_contract(self):
        emergency_query = "Severe chest pain crushing left arm and sweating heavily"
        res = self.client.post("/api/ai/consult", json={"query": emergency_query})
        self.assertEqual(res.status_code, 200)
        result = res.get_json().get("result", {})
        self.assertTrue(result.get("is_emergency"))
        self.assertIn("response", result)
        self.assertIn("emergency_message", result)
        self.assertEqual(result["response"], result["emergency_message"])

    def test_10_def08_delivery_otp_redacted_for_courier(self):
        self.login_role("customer")
        self.client.post("/api/cart/items", json={"medicine_id": 1, "quantity": 1})
        order_res = self.client.post("/api/orders", json={"delivery_address": "402 Green Glen Layout, Bellandur, Bengaluru 560103"})
        self.assertEqual(order_res.status_code, 201)
        order_id = order_res.get_json()["order_id"]

        # Customer must be able to view delivery_otp
        cust_order_res = self.client.get(f"/api/orders/{order_id}")
        self.assertEqual(cust_order_res.status_code, 200)
        cust_otp = cust_order_res.get_json()["order"].get("delivery_otp")
        self.assertIsNotNone(cust_otp)
        self.assertEqual(len(str(cust_otp)), 6)

        # Assign order to demo courier
        rider = query_db("SELECT id FROM users WHERE email = 'demo.delivery@mediapp.local'", one=True)
        rider_id = rider["id"]
        conn = get_db()
        conn.execute("UPDATE orders SET delivery_person_id = ?, order_status = 'IN_TRANSIT' WHERE id = ?", (rider_id, order_id))
        conn.commit()

        # Courier must NOT be able to view delivery_otp in order list or detail
        self.login_role("delivery")
        courier_list_res = self.client.get("/api/orders")
        self.assertEqual(courier_list_res.status_code, 200)
        for ord_item in courier_list_res.get_json().get("orders", []):
            self.assertIsNone(ord_item.get("delivery_otp"))

        courier_detail_res = self.client.get(f"/api/orders/{order_id}")
        self.assertEqual(courier_detail_res.status_code, 200)
        courier_otp = courier_detail_res.get_json()["order"].get("delivery_otp")
        self.assertIsNone(courier_otp)

if __name__ == "__main__":
    unittest.main()
