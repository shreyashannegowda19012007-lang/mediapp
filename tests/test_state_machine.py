"""
Unit tests for OrderStateMachine.
Verifies valid transitions, role permissions, and rejection of invalid state transitions.
"""
import pytest
from app.services.order_service import OrderStateMachine

def test_valid_transitions():
    # Customer/Pharmacy/Admin can cancel placed order
    OrderStateMachine.validate_transition("PLACED", "CANCELLED", "customer")
    OrderStateMachine.validate_transition("PLACED", "CANCELLED", "pharmacy")
    OrderStateMachine.validate_transition("PLACED", "CANCELLED", "admin")

    # Pharmacy can accept placed order
    OrderStateMachine.validate_transition("PLACED", "ACCEPTED", "pharmacy")

    # Pharmacy prepares and marks ready
    OrderStateMachine.validate_transition("ACCEPTED", "PREPARING", "pharmacy")
    OrderStateMachine.validate_transition("PREPARING", "READY_FOR_PICKUP", "pharmacy")

    # Delivery rider picks up and delivers
    OrderStateMachine.validate_transition("READY_FOR_PICKUP", "DELIVERY_ASSIGNED", "delivery")
    OrderStateMachine.validate_transition("DELIVERY_ASSIGNED", "PICKED_UP", "delivery")
    OrderStateMachine.validate_transition("PICKED_UP", "IN_TRANSIT", "delivery")
    OrderStateMachine.validate_transition("IN_TRANSIT", "DELIVERED", "delivery")

def test_invalid_transition_rejection():
    # Cannot jump straight from PLACED to DELIVERED
    with pytest.raises(ValueError, match="Invalid transition"):
        OrderStateMachine.validate_transition("PLACED", "DELIVERED", "customer")

    # Cannot transition from DELIVERED to anything (terminal state)
    with pytest.raises(ValueError, match="Invalid transition"):
        OrderStateMachine.validate_transition("DELIVERED", "CANCELLED", "admin")

    # Cannot transition from CANCELLED to ACCEPTED
    with pytest.raises(ValueError, match="Invalid transition"):
        OrderStateMachine.validate_transition("CANCELLED", "ACCEPTED", "pharmacy")

def test_unauthorized_role_transition():
    # Customer cannot accept an order (only pharmacy/admin)
    with pytest.raises(PermissionError, match="not authorized"):
        OrderStateMachine.validate_transition("PLACED", "ACCEPTED", "customer")

    # Delivery rider cannot cancel a placed order
    with pytest.raises(PermissionError, match="not authorized"):
        OrderStateMachine.validate_transition("PLACED", "CANCELLED", "delivery")
