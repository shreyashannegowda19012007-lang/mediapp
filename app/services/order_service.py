"""
Order Lifecycle and State Machine Service for MediApp.
Authoritative orchestrator for order placement, state transitions, stock reservation,
role-based permissions, and immutable audit history.
"""
import sqlite3
import json
import secrets
from datetime import datetime, timezone
from typing import Sequence, Mapping, Any
from app.database import get_db, query_db, transaction
from app.services.pricing_service import PricingService
from app.services.inventory_service import InventoryService

class OrderStateMachine:
    """Explicit state machine defining allowed transitions per role."""
    TRANSITIONS = {
        "PLACED": {
            "allowed_next": ["ACCEPTED", "AWAITING_PRESCRIPTION", "CANCELLED"],
            "permitted_roles": {
                "ACCEPTED": ["pharmacy", "admin"],
                "AWAITING_PRESCRIPTION": ["customer", "pharmacy", "admin"],
                "CANCELLED": ["customer", "pharmacy", "admin"]
            }
        },
        "AWAITING_PRESCRIPTION": {
            "allowed_next": ["PRESCRIPTION_VERIFIED", "CANCELLED"],
            "permitted_roles": {
                "PRESCRIPTION_VERIFIED": ["pharmacy", "admin"],
                "CANCELLED": ["customer", "pharmacy", "admin"]
            }
        },
        "PRESCRIPTION_VERIFIED": {
            "allowed_next": ["ACCEPTED", "CANCELLED"],
            "permitted_roles": {
                "ACCEPTED": ["pharmacy", "admin"],
                "CANCELLED": ["pharmacy", "admin"]
            }
        },
        "ACCEPTED": {
            "allowed_next": ["PREPARING", "CANCELLED"],
            "permitted_roles": {
                "PREPARING": ["pharmacy", "admin"],
                "CANCELLED": ["pharmacy", "admin"]
            }
        },
        "PREPARING": {
            "allowed_next": ["READY_FOR_PICKUP", "CANCELLED"],
            "permitted_roles": {
                "READY_FOR_PICKUP": ["pharmacy", "admin"],
                "CANCELLED": ["pharmacy", "admin"]
            }
        },
        "READY_FOR_PICKUP": {
            "allowed_next": ["DELIVERY_ASSIGNED", "PICKED_UP", "CANCELLED"],
            "permitted_roles": {
                "DELIVERY_ASSIGNED": ["delivery", "pharmacy", "admin"],
                "PICKED_UP": ["delivery", "admin"],
                "CANCELLED": ["pharmacy", "admin"]
            }
        },
        "DELIVERY_ASSIGNED": {
            "allowed_next": ["PICKED_UP", "CANCELLED"],
            "permitted_roles": {
                "PICKED_UP": ["delivery", "admin"],
                "CANCELLED": ["delivery", "pharmacy", "admin"]
            }
        },
        "PICKED_UP": {
            "allowed_next": ["IN_TRANSIT", "DELIVERY_FAILED"],
            "permitted_roles": {
                "IN_TRANSIT": ["delivery", "admin"],
                "DELIVERY_FAILED": ["delivery", "admin"]
            }
        },
        "IN_TRANSIT": {
            "allowed_next": ["DELIVERED", "DELIVERY_FAILED"],
            "permitted_roles": {
                "DELIVERED": ["delivery", "admin"],
                "DELIVERY_FAILED": ["delivery", "admin"]
            }
        },
        "DELIVERY_FAILED": {
            "allowed_next": ["READY_FOR_PICKUP", "CANCELLED"],
            "permitted_roles": {
                "READY_FOR_PICKUP": ["delivery", "pharmacy", "admin"],
                "CANCELLED": ["pharmacy", "admin"]
            }
        },
        "DELIVERED": {
            "allowed_next": [],
            "permitted_roles": {}
        },
        "CANCELLED": {
            "allowed_next": [],
            "permitted_roles": {}
        }
    }

    @classmethod
    def validate_transition(cls, current_status: str, target_status: str, user_role: str):
        """Validates if target status is allowed from current status by user role."""
        rule = cls.TRANSITIONS.get(current_status)
        if not rule:
            raise ValueError(f"Unknown current order status '{current_status}'.")
            
        if target_status not in rule["allowed_next"]:
            raise ValueError(
                f"Invalid transition from '{current_status}' to '{target_status}'. Allowed transitions: {rule['allowed_next']}."
            )
            
        allowed_roles = rule["permitted_roles"].get(target_status, [])
        if user_role not in allowed_roles:
            raise PermissionError(
                f"Role '{user_role}' is not authorized to transition order to '{target_status}'. Required roles: {allowed_roles}."
            )


class OrderService:
    @staticmethod
    def generate_order_id() -> str:
        """Generates a unique, non-integer order ID formatted as ORD-YYYYMMDD-XXXX."""
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        rand_suffix = secrets.token_hex(2).upper()
        return f"ORD-{date_str}-{rand_suffix}"

    @classmethod
    def create_order(
        cls,
        customer_id: int,
        pharmacy_id: int,
        items: Sequence[Mapping[str, Any]],
        delivery_address: Mapping[str, Any],
        prescription_id: int | None = None,
        delivery_notes: str | None = None,
        conn: sqlite3.Connection = None
    ) -> Mapping[str, Any]:
        """
        Creates a persistent order, reserves stock, stores item snapshots,
        and initializes order status and payment record inside an atomic transaction.
        """
        if not items:
            raise ValueError("An order must contain at least one item.")
            
        managed_conn = conn or get_db()
        with transaction(managed_conn):
            # 1. Fetch live medicine catalogue details for items
            enriched_items = []
            rx_required_found = False
            
            for it in items:
                med_id = it["medicine_id"]
                qty = it["quantity"]
                if qty <= 0:
                    raise ValueError(f"Quantity must be greater than 0 for medicine ID {med_id}.")
                    
                med_row = query_db(
                    "SELECT * FROM medicines WHERE id = ?",
                    (med_id,),
                    one=True,
                    conn=managed_conn
                )
                if not med_row:
                    raise ValueError(f"Medicine ID {med_id} does not exist.")
                    
                inv_row = query_db(
                    "SELECT unit_price, stock_quantity, is_available FROM pharmacy_inventory WHERE pharmacy_id = ? AND medicine_id = ?",
                    (pharmacy_id, med_id),
                    one=True,
                    conn=managed_conn
                )
                if not inv_row or not inv_row["is_available"]:
                    raise ValueError(f"'{med_row['name']}' is not available at the selected pharmacy.")
                if inv_row["stock_quantity"] < qty:
                    raise ValueError(f"Insufficient stock for '{med_row['name']}'. Requested: {qty}, Available: {inv_row['stock_quantity']}.")
                    
                if med_row["prescription_required"]:
                    rx_required_found = True
                    
                unit_price = inv_row["unit_price"]
                line_total = PricingService.calculate_item_total(unit_price, qty)
                
                enriched_items.append({
                    "medicine_id": med_id,
                    "name": med_row["name"],
                    "generic_name": med_row["generic_name"],
                    "strength": med_row["strength"],
                    "dosage_form": med_row["dosage_form"],
                    "unit_price": unit_price,
                    "quantity": qty,
                    "line_total": float(line_total)
                })

            # 2. Check prescription requirement
            if rx_required_found and not prescription_id:
                raise ValueError("This order contains prescription-only (Rx) medicines. A verified prescription must be attached.")
                
            # If prescription is supplied, verify it belongs to this customer
            if prescription_id:
                rx_check = query_db(
                    "SELECT id, status FROM prescriptions WHERE id = ? AND customer_id = ?",
                    (prescription_id, customer_id),
                    one=True,
                    conn=managed_conn
                )
                if not rx_check:
                    raise ValueError("Invalid prescription attached or unauthorized.")
                if rx_check["status"] == "rejected":
                    raise ValueError(f"Attached prescription #{prescription_id} has been rejected and cannot be used for orders.")

            # 3. Calculate authoritative totals
            totals = PricingService.calculate_order_totals(enriched_items)
            
            # 4. Atomically decrement stock to reserve items
            InventoryService.decrement_stock(pharmacy_id, enriched_items, managed_conn)
            
            # 5. Insert order record
            order_id = cls.generate_order_id()
            initial_status = "AWAITING_PRESCRIPTION" if (rx_required_found and rx_check["status"] != "verified") else "PLACED"
            delivery_otp = f"{secrets.randbelow(900000) + 100000}"
            
            cur = managed_conn.cursor()
            cur.execute("""
                INSERT INTO orders (
                    id, customer_id, pharmacy_id, prescription_id, delivery_address_json,
                    subtotal, tax, delivery_fee, discount, total_amount, currency,
                    payment_status, order_status, delivery_notes, delivery_otp, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'INR', 'pending', ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                order_id,
                customer_id,
                pharmacy_id,
                prescription_id,
                json.dumps(delivery_address),
                totals["subtotal"],
                totals["tax"],
                totals["delivery_fee"],
                totals["discount"],
                totals["total"],
                initial_status,
                delivery_notes,
                delivery_otp
            ))

            # 6. Insert order items snapshot
            for item in enriched_items:
                cur.execute("""
                    INSERT INTO order_items (
                        order_id, medicine_id, medicine_name_snapshot, generic_name_snapshot,
                        strength_snapshot, dosage_form_snapshot, unit_price, quantity, total_price
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    order_id,
                    item["medicine_id"],
                    item["name"],
                    item["generic_name"],
                    item["strength"],
                    item["dosage_form"],
                    item["unit_price"],
                    item["quantity"],
                    item["line_total"]
                ))

            # 7. Record status history
            cur.execute("""
                INSERT INTO order_status_history (order_id, from_status, to_status, changed_by_user_id, role, notes)
                VALUES (?, NULL, ?, ?, 'customer', 'Order placed successfully')
            """, (order_id, initial_status, customer_id))

        return cls.get_order_details(order_id, managed_conn)

    @classmethod
    def transition_order_status(
        cls,
        order_id: str,
        target_status: str,
        user_id: int,
        user_role: str,
        notes: str | None = None,
        conn: sqlite3.Connection = None
    ) -> Mapping[str, Any]:
        """
        Executes a validated state transition.
        Automatically handles stock restoration and refund status if cancelled.
        """
        managed_conn = conn or get_db()
        with transaction(managed_conn):
            order = query_db(
                "SELECT * FROM orders WHERE id = ?",
                (order_id,),
                one=True,
                conn=managed_conn
            )
            if not order:
                raise ValueError(f"Order '{order_id}' not found.")
                
            current_status = order["order_status"]
            OrderStateMachine.validate_transition(current_status, target_status, user_role)

            # Authoritative object-level authorization check
            if user_role == "customer":
                if order["customer_id"] != user_id:
                    raise PermissionError("Access denied. You do not own this order.")
            elif user_role == "pharmacy":
                staff = query_db(
                    "SELECT pharmacy_id FROM pharmacy_staff WHERE user_id = ?",
                    (user_id,),
                    one=True,
                    conn=managed_conn
                )
                pharmacy_id = staff["pharmacy_id"] if staff else None
                if not pharmacy_id or pharmacy_id != order["pharmacy_id"]:
                    raise PermissionError("Access denied. This order belongs to another pharmacy store.")
            elif user_role == "delivery":
                if target_status != "DELIVERY_ASSIGNED" and order["delivery_person_id"] != user_id:
                    raise PermissionError("Access denied. This delivery is not assigned to you.")

            cur = managed_conn.cursor()

            # Handle cancellation: restore inventory, mark assignment cancelled & handle refund if paid
            if target_status == "CANCELLED":
                items = query_db(
                    "SELECT medicine_id, quantity FROM order_items WHERE order_id = ?",
                    (order_id,),
                    conn=managed_conn
                )
                InventoryService.restore_stock(order["pharmacy_id"], items, managed_conn)
                
                # Mark courier assignment as cancelled
                cur.execute(
                    "UPDATE delivery_assignments SET status = 'cancelled' WHERE order_id = ?",
                    (order_id,)
                )
                
                # If payment was completed, set status to refunded
                if order["payment_status"] == "paid":
                    cur.execute(
                        "UPDATE orders SET payment_status = 'refunded', cancellation_reason = ? WHERE id = ?",
                        (notes or "Cancelled by user/operator", order_id)
                    )
                    cur.execute(
                        "UPDATE payments SET status = 'refunded', updated_at = CURRENT_TIMESTAMP WHERE order_id = ?",
                        (order_id,)
                    )
                else:
                    cur.execute(
                        "UPDATE orders SET cancellation_reason = ? WHERE id = ?",
                        (notes or "Cancelled before payment", order_id)
                    )

            # Update order status
            cur.execute("""
                UPDATE orders
                SET order_status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (target_status, order_id))

            # Record status history audit
            cur.execute("""
                INSERT INTO order_status_history (order_id, from_status, to_status, changed_by_user_id, role, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (order_id, current_status, target_status, user_id, user_role, notes))

        return cls.get_order_details(order_id, managed_conn)

    @classmethod
    def get_order_details(cls, order_id: str, conn: sqlite3.Connection = None) -> Mapping[str, Any] | None:
        """Retrieves comprehensive order details with items, customer, pharmacy, delivery, and history."""
        managed_conn = conn or get_db()
        order = query_db(
            """
            SELECT o.*,
                   u.full_name as customer_name, u.email as customer_email, u.phone as customer_phone,
                   p.name as pharmacy_name, p.address as pharmacy_address, p.phone as pharmacy_phone,
                   d.full_name as delivery_person_name, d.phone as delivery_person_phone
            FROM orders o
            JOIN users u ON o.customer_id = u.id
            JOIN pharmacies p ON o.pharmacy_id = p.id
            LEFT JOIN users d ON o.delivery_person_id = d.id
            WHERE o.id = ?
            """,
            (order_id,),
            one=True,
            conn=managed_conn
        )
        if not order:
            return None

        # Items
        items = query_db(
            "SELECT * FROM order_items WHERE order_id = ?",
            (order_id,),
            conn=managed_conn
        )
        
        # Payment details
        payment = query_db(
            "SELECT * FROM payments WHERE order_id = ? ORDER BY id DESC LIMIT 1",
            (order_id,),
            one=True,
            conn=managed_conn
        )

        # Status timeline history
        history = query_db(
            """
            SELECT h.*, u.full_name as changed_by_name
            FROM order_status_history h
            LEFT JOIN users u ON h.changed_by_user_id = u.id
            WHERE h.order_id = ?
            ORDER BY h.id ASC
            """,
            (order_id,),
            conn=managed_conn
        )

        order_dict = dict(order)
        order_dict["items"] = [dict(it) for it in items]
        order_dict["payment"] = dict(payment) if payment else None
        order_dict["timeline"] = [dict(h) for h in history]
        
        # Parse JSON address
        try:
            order_dict["delivery_address"] = json.loads(order_dict["delivery_address_json"])
        except Exception:
            order_dict["delivery_address"] = {}

        return order_dict
