"""
Tests for Quotation Management - Person 2
"""
import pytest


def test_create_quotation_template(client, sample_data, mock_auth):
    """Test creating a quotation template."""
    response = client.post(
        "/api/v1/quotation-templates",
        json={
            "name": "New Template",
            "plan_id": sample_data["plan1"].id,
            "validity_days": 15,
            "lines": [
                {"product_id": sample_data["product1"].id, "quantity": 2}
            ],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Template"
    assert data["validity_days"] == 15
    assert len(data["lines"]) == 1


def test_list_quotation_templates(client, sample_data, mock_auth):
    """Test listing quotation templates."""
    response = client.get("/api/v1/quotation-templates")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["name"] == "Enterprise Template"


def test_get_quotation_template(client, sample_data, mock_auth):
    """Test getting a specific quotation template."""
    template_id = sample_data["template"].id
    response = client.get(f"/api/v1/quotation-templates/{template_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == template_id
    assert len(data["lines"]) == 2


def test_update_quotation_template(client, sample_data, mock_auth):
    """Test updating a quotation template."""
    template_id = sample_data["template"].id
    response = client.patch(
        f"/api/v1/quotation-templates/{template_id}",
        json={"name": "Updated Template", "validity_days": 45},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Template"
    assert data["validity_days"] == 45


def test_delete_quotation_template(client, sample_data, mock_auth):
    """Test deleting a quotation template."""
    template_id = sample_data["template"].id
    response = client.delete(f"/api/v1/quotation-templates/{template_id}")
    assert response.status_code == 204

    # Verify deleted
    response = client.get(f"/api/v1/quotation-templates/{template_id}")
    assert response.status_code == 404