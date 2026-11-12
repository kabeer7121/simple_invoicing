"""An invoice edit must not move it between the Sales and Purchase series.

The number is taken from the voucher type's series at creation and is not
regenerated on edit, so a type change is refused with a 400.
"""

import pytest


def _create_ledger(client):
    response = client.post(
        "/api/ledgers/",
        json={
            "name": "Voucher Type Party",
            "address": "Mumbai",
            "gst": "27ABCDE1234F1Z0",
            "phone_number": "9999999999",
            "email": "party@example.com",
            "website": "",
            "bank_name": "",
            "branch_name": "",
            "account_name": "",
            "account_number": "",
            "ifsc_code": "",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["id"]


def _create_product(client):
    response = client.post(
        "/api/products/",
        json={
            "sku": "VT-001",
            "name": "Voucher Type Product",
            "description": "",
            "hsn_sac": "9988",
            "price": 100,
            "gst_rate": 18,
            "unit": "Pieces",
            "allow_decimal": False,
            "maintain_inventory": False,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["id"]


def _payload(ledger_id, product_id, voucher_type, quantity=1):
    return {
        "ledger_id": ledger_id,
        "voucher_type": voucher_type,
        "tax_inclusive": False,
        "apply_round_off": False,
        "items": [{"product_id": product_id, "quantity": quantity, "unit_price": 100}],
    }


@pytest.mark.parametrize("created_as,changed_to", [("purchase", "sales"), ("sales", "purchase")])
def test_voucher_type_change_on_edit_is_refused(client, created_as, changed_to):
    ledger_id = _create_ledger(client)
    product_id = _create_product(client)
    created = client.post("/api/invoices/", json=_payload(ledger_id, product_id, created_as))
    assert created.status_code == 200, created.text
    invoice = created.json()

    response = client.put(
        f"/api/invoices/{invoice['id']}",
        json=_payload(ledger_id, product_id, changed_to),
    )

    assert response.status_code == 400, response.text
    assert "Sales and Purchase" in response.json()["detail"]

    after = client.get(f"/api/invoices/{invoice['id']}")
    assert after.status_code == 200, after.text
    assert after.json()["voucher_type"] == created_as
    assert after.json()["invoice_number"] == invoice["invoice_number"]


def test_edit_that_keeps_the_voucher_type_still_works(client):
    ledger_id = _create_ledger(client)
    product_id = _create_product(client)
    created = client.post("/api/invoices/", json=_payload(ledger_id, product_id, "purchase"))
    assert created.status_code == 200, created.text
    invoice = created.json()

    response = client.put(
        f"/api/invoices/{invoice['id']}",
        json=_payload(ledger_id, product_id, "purchase", quantity=2),
    )

    assert response.status_code == 200, response.text
    assert response.json()["invoice_number"] == invoice["invoice_number"]
    assert response.json()["items"][0]["quantity"] == 2
