"""
Tests for Subscription Management - Person 2
"""
import pytest
from datetime import date, timedelta


def test_create_subscription_from_template(client, db, sample_data, mock_auth):
    """Test creating subscription from quotation template."""
    response = client.post(
        "/api/v1/subscriptions",
        json={
            "template_id": sample_data["template"].id,
            "customer_id": sample_data["customer"].id,
            "start_date": str(date.today()),
            "payment_terms": "net_30",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "draft"
    assert data["number"].startswith("SUB-")
    assert len(data["lines"]) == 2


def test_create_subscription_manual(client, db, sample_data, mock_auth):
    """Test creating subscription manually."""
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
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "draft"
    assert data["plan_id"] == sample_data["plan1"].id


def test_list_subscriptions(client, db, sample_data, mock_auth):
    """Test listing subscriptions."""
    # Create a subscription first
    client.post(
        "/api/v1/subscriptions",
        json={
            "customer_id": sample_data["customer"].id,
            "plan_id": sample_data["plan1"].id,
            "start_date": str(date.today()),
        },
    )
    response = client.get("/api/v1/subscriptions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_get_subscription_by_id(client, db, sample_data, mock_auth):
    """Test getting subscription by ID."""
    # First create one
    response = client.post(
        "/api/v1/subscriptions",
        json={
            "customer_id": sample_data["customer"].id,
            "plan_id": sample_data["plan1"].id,
            "start_date": str(date.today()),
        },
    )
    assert response.status_code == 201
    sub_id = response.json()["id"]

    response = client.get(f"/api/v1/subscriptions/{sub_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sub_id


def test_transition_status(client, db, sample_data, mock_auth):
    """Test subscription status transitions."""
    # Create a subscription in draft
    response = client.post(
        "/api/v1/subscriptions",
        json={
            "customer_id": sample_data["customer"].id,
            "plan_id": sample_data["plan1"].id,
            "start_date": str(date.today()),
        },
    )
    assert response.status_code == 201
    sub_id = response.json()["id"]

    # Move to quotation
    response = client.post(
        f"/api/v1/subscriptions/{sub_id}/status",
        json={"new_status": "quotation"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "quotation"

    # Move to confirmed
    response = client.post(
        f"/api/v1/subscriptions/{sub_id}/status",
        json={"new_status": "confirmed"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"


def test_invalid_status_transition(client, db, sample_data, mock_auth):
    """Test that invalid status transitions are rejected."""
    # Create a subscription in draft
    response = client.post(
        "/api/v1/subscriptions",
        json={
            "customer_id": sample_data["customer"].id,
            "plan_id": sample_data["plan1"].id,
            "start_date": str(date.today()),
        },
    )
    sub_id = response.json()["id"]

    # Try invalid: draft -> active (should fail)
    response = client.post(
        f"/api/v1/subscriptions/{sub_id}/status",
        json={"new_status": "active"},
    )
    assert response.status_code == 400


def test_pause_and_resume_subscription(client, db, sample_data, mock_auth):
    """Test pausing and resuming a subscription."""
    # Create subscription
    response = client.post(
        "/api/v1/subscriptions",
        json={
            "customer_id": sample_data["customer"].id,
            "plan_id": sample_data["plan1"].id,
            "start_date": str(date.today()),
        },
    )
    assert response.status_code == 201
    sub_id = response.json()["id"]

    # Move to confirmed then active (required for pause/resume)
    response = client.post(f"/api/v1/subscriptions/{sub_id}/status", json={"new_status": "confirmed"})
    assert response.status_code == 200

    response = client.post(f"/api/v1/subscriptions/{sub_id}/status", json={"new_status": "active"})
    assert response.status_code == 200, f"Activate failed: {response.text[:200]}"

    # Pause
    response = client.post(f"/api/v1/subscriptions/{sub_id}/pause")
    assert response.status_code == 200
    assert response.json()["is_paused"] is True

    # Resume
    response = client.post(f"/api/v1/subscriptions/{sub_id}/resume")
    assert response.status_code == 200
    assert response.json()["is_paused"] is False


def test_subscription_expiry_calculation(client, db, sample_data, mock_auth):
    """Test that expiry date is calculated based on billing period."""
    today = date.today()

    # Monthly plan
    response = client.post(
        "/api/v1/subscriptions",
        json={
            "customer_id": sample_data["customer"].id,
            "plan_id": sample_data["plan1"].id,  # monthly billing
            "start_date": str(today),
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["expiry_date"] is not None