"""
Unit tests for InventoryService.
Verifies stock availability checks, atomic decrement, overselling prevention, and restoration.
"""
import pytest
from app.services.inventory_service import InventoryService
from app.database import get_db, query_db, transaction

def test_check_availability(app):
    with app.app_context():
        # Check available item
        is_avail, err = InventoryService.check_availability(1, [{"medicine_id": 2, "quantity": 2}])
        assert is_avail is True
        assert err is None

        # Check item exceeding available stock
        is_avail, err = InventoryService.check_availability(1, [{"medicine_id": 2, "quantity": 9999}])
        assert is_avail is False
        assert "Insufficient stock" in err

def test_atomic_decrement_and_restore(app):
    with app.app_context():
        conn = get_db()
        # Initial stock of medicine 2 (Dolo 650mg) at pharmacy 1
        initial = query_db("SELECT stock_quantity FROM pharmacy_inventory WHERE pharmacy_id = 1 AND medicine_id = 2", one=True)
        init_qty = initial["stock_quantity"]

        # Decrement 3 units
        with transaction(conn):
            InventoryService.decrement_stock(1, [{"medicine_id": 2, "quantity": 3}], conn)

        after_dec = query_db("SELECT stock_quantity FROM pharmacy_inventory WHERE pharmacy_id = 1 AND medicine_id = 2", one=True)
        assert after_dec["stock_quantity"] == init_qty - 3

        # Restore 3 units
        with transaction(conn):
            InventoryService.restore_stock(1, [{"medicine_id": 2, "quantity": 3}], conn)

        after_restore = query_db("SELECT stock_quantity FROM pharmacy_inventory WHERE pharmacy_id = 1 AND medicine_id = 2", one=True)
        assert after_restore["stock_quantity"] == init_qty

def test_overselling_raises_value_error(app):
    with app.app_context():
        conn = get_db()
        with pytest.raises(ValueError, match="Stock reduction failed"):
            with transaction(conn):
                InventoryService.decrement_stock(1, [{"medicine_id": 2, "quantity": 999999}], conn)
