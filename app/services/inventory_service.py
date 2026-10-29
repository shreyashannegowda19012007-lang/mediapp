"""
Inventory Service for MediApp.
Enforces atomic stock checks, reservation, stock decrement, and replenishment
with concurrency controls to completely prevent overselling.
"""
import sqlite3
from typing import Sequence, Mapping, Any, Tuple
from app.database import get_db, query_db

class InventoryService:
    @staticmethod
    def get_stock(pharmacy_id: int, medicine_id: int, conn: sqlite3.Connection = None) -> Mapping[str, Any] | None:
        """Retrieves pharmacy inventory record for a specific medicine."""
        return query_db(
            """
            SELECT i.*, m.name, m.generic_name, m.mrp, m.prescription_required
            FROM pharmacy_inventory i
            JOIN medicines m ON i.medicine_id = m.id
            WHERE i.pharmacy_id = ? AND i.medicine_id = ?
            """,
            (pharmacy_id, medicine_id),
            one=True,
            conn=conn
        )

    @staticmethod
    def check_availability(
        pharmacy_id: int,
        items: Sequence[Mapping[str, Any]],
        conn: sqlite3.Connection = None
    ) -> Tuple[bool, str | None]:
        """
        Validates whether all requested items exist and have sufficient stock.
        
        Args:
            pharmacy_id: Target pharmacy ID
            items: Sequence of dicts with 'medicine_id' and 'quantity'
            
        Returns:
            (is_available, error_message)
        """
        c = conn or get_db()
        for item in items:
            med_id = item["medicine_id"]
            requested_qty = item["quantity"]
            
            row = query_db(
                """
                SELECT i.stock_quantity, i.is_available, m.name
                FROM pharmacy_inventory i
                JOIN medicines m ON i.medicine_id = m.id
                WHERE i.pharmacy_id = ? AND i.medicine_id = ?
                """,
                (pharmacy_id, med_id),
                one=True,
                conn=c
            )
            
            if not row:
                return False, f"Medicine ID {med_id} is not stocked by this pharmacy."
            if not row["is_available"]:
                return False, f"'{row['name']}' is currently marked unavailable."
            if row["stock_quantity"] < requested_qty:
                return False, f"Insufficient stock for '{row['name']}'. Requested: {requested_qty}, Available: {row['stock_quantity']}."
                
        return True, None

    @staticmethod
    def decrement_stock(
        pharmacy_id: int,
        items: Sequence[Mapping[str, Any]],
        conn: sqlite3.Connection
    ):
        """
        Atomically decrements inventory for order placement.
        Must be executed within a database transaction.
        Raises ValueError if any item cannot be decremented.
        """
        cur = conn.cursor()
        for item in items:
            med_id = item["medicine_id"]
            qty = item["quantity"]
            
            # Atomic update with WHERE clause ensuring non-negative stock
            cur.execute(
                """
                UPDATE pharmacy_inventory
                SET stock_quantity = stock_quantity - ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE pharmacy_id = ? AND medicine_id = ? AND stock_quantity >= ?
                """,
                (qty, pharmacy_id, med_id, qty)
            )
            
            if cur.rowcount == 0:
                # Concurrent inventory conflict or overselling attempt
                raise ValueError(
                    f"Stock reduction failed for medicine ID {med_id}. Insufficient stock or concurrent order conflict."
                )

    @staticmethod
    def restore_stock(
        pharmacy_id: int,
        items: Sequence[Mapping[str, Any]],
        conn: sqlite3.Connection
    ):
        """Restores inventory when an order is cancelled."""
        cur = conn.cursor()
        for item in items:
            med_id = item["medicine_id"]
            qty = item["quantity"]
            cur.execute(
                """
                UPDATE pharmacy_inventory
                SET stock_quantity = stock_quantity + ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE pharmacy_id = ? AND medicine_id = ?
                """,
                (qty, pharmacy_id, med_id)
            )

    @staticmethod
    def update_stock(
        pharmacy_id: int,
        medicine_id: int,
        quantity: int,
        unit_price: float,
        is_available: bool = True,
        batch_number: str = None,
        expiry_date: str = None,
        conn: sqlite3.Connection = None
    ):
        """Inserts or updates inventory record for a pharmacy."""
        if quantity < 0:
            raise ValueError("Stock quantity cannot be negative.")
        if unit_price < 0:
            raise ValueError("Unit price cannot be negative.")
            
        c = conn or get_db()
        cur = c.cursor()
        cur.execute(
            """
            INSERT INTO pharmacy_inventory (
                pharmacy_id, medicine_id, stock_quantity, unit_price, is_available,
                batch_number, expiry_date, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(pharmacy_id, medicine_id) DO UPDATE SET
                stock_quantity = excluded.stock_quantity,
                unit_price = excluded.unit_price,
                is_available = excluded.is_available,
                batch_number = COALESCE(excluded.batch_number, pharmacy_inventory.batch_number),
                expiry_date = COALESCE(excluded.expiry_date, pharmacy_inventory.expiry_date),
                updated_at = CURRENT_TIMESTAMP
            """,
            (pharmacy_id, medicine_id, quantity, unit_price, 1 if is_available else 0, batch_number, expiry_date)
        )
        c.commit()
