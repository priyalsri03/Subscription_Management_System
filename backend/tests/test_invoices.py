"""
Tests for Invoice Management - Person 2
"""
import pytest
from datetime import date, timedelta


def test_create_invoice(client, db, sample_data, mock_auth):
    """Test creating an invoice for a subscription."""
    # First create and activate a subscription with lines
    response = client.post(
        "/api/v1/subscriptions",
        json={
            "customer_id": sample_data["customer"].id,
            "plan_id": sample_data["plan1"].id,
            "start_date": str(date.today()),
            "lines": [
                {"product_id": sample_data["product1"].id, "quantity": 1}
            ],
        },
    )
    sub_id = response.json()["id"]

    # Confirm and activate the subscription
    client.post(f"/api/v1/subscriptions/{sub_id}/status", json={"new_status": "confirmed"})
    client.post(f"/api/v1/subscriptions/{sub_id}/status", json={"new_status": "active"})

    # Create invoice
    today = date.today()
    response = client.post(
        "/api/v1/invoices",
        json={
            "subscription_id": sub_id,
            "period_start": str(today),
            "period_end": str(today),
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "draft"
    assert float(data["subtotal"]) >= 0


def test_prevent_duplicate_invoice(client, db, sample_data, mock_auth):
    """Test that duplicate invoices cannot be created (double-billing prevention)."""
    # Create active subscription with lines
    response = client.post(
        "/api/v1/subscriptions",
        json={
            "customer_id": sample_data["customer"].id,
            "plan_id": sample_data["plan1"].id,
            "start_date": str(date.today()),
            "lines": [
                {"product_id": sample_data["product1"].id, "quantity": 1}
            ],
        },
    )
    sub_id = response.json()["id"]
    client.post(f"/api/v1/subscriptions/{sub_id}/status", json={"new_status": "confirmed"})
    client.post(f"/api/v1/subscriptions/{sub_id}/status", json={"new_status": "active"})

    today = date.today()
    period_start = str(today)

    # Create first invoice
    response = client.post(
        "/api/v1/invoices",
        json={
            "subscription_id": sub_id,
            "period_start": period_start,
            "period_end": period_start,
        },
    )
    assert response.status_code == 201

    # Try to create duplicate - should fail
    response = client.post(
        "/api/v1/invoices",
        json={
            "subscription_id": sub_id,
            "period_start": period_start,
            "period_end": period_start,
        },
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


def test_list_invoices(client, db, sample_data, mock_auth):
    """Test listing invoices."""
    response = client.get("/api/v1/invoices")
    assert response.status_code == 200


def test_get_invoice_by_id(client, db, sample_data, mock_auth):
    """Test getting invoice by ID."""
    # Create subscription and invoice first
    response = client.post(
        "/api/v1/subscriptions",
        json={
            "customer_id": sample_data["customer"].id,
            "plan_id": sample_data["plan1"].id,
            "start_date": str(date.today()),
            "lines": [
                {"product_id": sample_data["product1"].id, "quantity": 1}
            ],
        },
    )
    sub_id = response.json()["id"]
    client.post(f"/api/v1/subscriptions/{sub_id}/status", json={"new_status": "confirmed"})
    client.post(f"/api/v1/subscriptions/{sub_id}/status", json={"new_status": "active"})

    response = client.post(
        "/api/v1/invoices",
        json={
            "subscription_id": sub_id,
            "period_start": str(date.today()),
            "period_end": str(date.today()),
        },
    )
    inv_id = response.json()["id"]

    response = client.get(f"/api/v1/invoices/{inv_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == inv_id


def test_confirm_invoice(client, db, sample_data, mock_auth):
    """Test confirming an invoice."""
    # Setup subscription
    response = client.post(
        "/api/v1/subscriptions",
        json={
            "customer_id": sample_data["customer"].id,
            "plan_id": sample_data["plan1"].id,
            "start_date": str(date.today()),
            "lines": [
                {"product_id": sample_data["product1"].id, "quantity": 1}
            ],
        },
    )
    sub_id = response.json()["id"]
    client.post(f"/api/v1/subscriptions/{sub_id}/status", json={"new_status": "confirmed"})
    client.post(f"/api/v1/subscriptions/{sub_id}/status", json={"new_status": "active"})

    # Create invoice
    response = client.post(
        "/api/v1/invoices",
        json={
            "subscription_id": sub_id,
            "period_start": str(date.today()),
            "period_end": str(date.today()),
        },
    )
    inv_id = response.json()["id"]

    # Confirm
    response = client.post(f"/api/v1/invoices/{inv_id}/confirm")
    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"


def test_cancel_invoice(client, db, sample_data, mock_auth):
    """Test cancelling an invoice."""
    # Setup
    response = client.post(
        "/api/v1/subscriptions",
        json={
            "customer_id": sample_data["customer"].id,
            "plan_id": sample_data["plan1"].id,
            "start_date": str(date.today()),
            "lines": [
                {"product_id": sample_data["product1"].id, "quantity": 1}
            ],
        },
    )
    sub_id = response.json()["id"]
    client.post(f"/api/v1/subscriptions/{sub_id}/status", json={"new_status": "confirmed"})
    client.post(f"/api/v1/subscriptions/{sub_id}/status", json={"new_status": "active"})

    response = client.post(
        "/api/v1/invoices",
        json={
            "subscription_id": sub_id,
            "period_start": str(date.today()),
            "period_end": str(date.today()),
        },
    )
    inv_id = response.json()["id"]

    # Cancel
    response = client.post(f"/api/v1/invoices/{inv_id}/cancel")
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_cannot_cancel_paid_invoice(client, db, sample_data, mock_auth):
    """Test that paid invoices cannot be cancelled."""
    # Setup with payment
    response = client.post(
        "/api/v1/subscriptions",
        json={
            "customer_id": sample_data["customer"].id,
            "plan_id": sample_data["plan1"].id,
            "start_date": str(date.today()),
            "lines": [
                {"product_id": sample_data["product1"].id, "quantity": 1}
            ],
        },
    )
    sub_id = response.json()["id"]
    client.post(f"/api/v1/subscriptions/{sub_id}/status", json={"new_status": "confirmed"})
    client.post(f"/api/v1/subscriptions/{sub_id}/status", json={"new_status": "active"})

    response = client.post(
        "/api/v1/invoices",
        json={
            "subscription_id": sub_id,
            "period_start": str(date.today()),
            "period_end": str(date.today()),
        },
    )
    inv_id = response.json()["id"]
    inv_total = response.json()["total"]

    # Add payment
    client.post(
        "/api/v1/payments",
        json={
            "invoice_id": inv_id,
            "amount": inv_total,
            "method": "bank_transfer",
        },
    )

    # Try to cancel paid invoice
    response = client.post(f"/api/v1/invoices/{inv_id}/cancel")
    assert response.status_code == 400


def test_run_billing_cycle(client, db, sample_data, mock_auth):
    """Test running automated billing cycle."""
    # Create multiple active subscriptions
    for i in range(2):
        response = client.post(
            "/api/v1/subscriptions",
            json={
                "customer_id": sample_data["customer"].id,
                "plan_id": sample_data["plan1"].id,
                "start_date": str(date.today() - timedelta(days=i)),
            },
        )
        sub_id = response.json()["id"]
        client.post(f"/api/v1/subscriptions/{sub_id}/status", json={"new_status": "confirmed"})
        client.post(f"/api/v1/subscriptions/{sub_id}/status", json={"new_status": "active"})

    # Run billing cycle
    response = client.post("/api/v1/invoices/billing-cycle")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1  # At least one invoice created