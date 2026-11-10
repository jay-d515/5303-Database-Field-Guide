import uuid
import random
from fastapi.testclient import TestClient
from api import app
from api import db
c = TestClient(app)

def test_limit():
    assert c.get("/api/products?limit=5").json()["size"] <= 5

def test_offset():
    a = c.get("/api/products?limit=10").json()["data"]
    b = c.get("/api/products?limit=5&offset=5").json()["data"]
    assert a[5:] == b

def test_beyond():
    assert c.get("/api/products?offset=999999").json()["data"] == []

def test_404():
    r = c.get("/api/products/999999");
    assert r.status_code == 404 and r.json()["response_code"] == 404

def test_bad_page():
    assert c.get("/api/products?limit=0").status_code == 422

def test_products_standard_format():
    body = c.get("/api/products").json()
    assert set(body) == {"response_code", "error_response", "data",
                         "total_size", "size", "offset", "limit"}
    assert body["response_code"] == 200 and body["error_response"] is None
    assert body["offset"] == 0 and body["limit"] == 100
    

def test_search_total_size():
    body = c.get("/api/products?q=lamp&limit=1").json()
    expected = db.products.count_documents({"product_name": {"$regex": "lamp", "$options": "i"}})
    assert body["total_size"] == expected      # full match count, not just the 1 returned
    assert body["size"] <= 1
    
def test_one_product_is_dict():
    first_id = c.get("/api/products?limit=1").json()["data"][0]["id"]
    body = c.get(f"/api/products/{first_id}").json()
    assert isinstance(body["data"], dict)
    assert body["size"] == 1 and body["total_size"] == 1
     
def new_customer(email, card_number):
    return {"first_name": "Test", "last_name": "User", "email": email,
            "address": "123 Main St", "zipcode": "76308", "state_code": "TX",
            "card_type": "visa", "card_number": card_number}
    
def test_create_then_duplicate_customer():
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"   # unique every run
    card = "".join(random.choices("0123456789", k=16))
    
    r1 = c.post("/api/customers", json=new_customer(email, card))
    assert r1.status_code == 201 and r1.json()["response_code"] == 201

    r2 = c.post("/api/customers", json=new_customer(email, card))
    assert r2.status_code == 409 and r2.json()["error_response"]["message"]

def test_invalid_body():
    r = c.post("/api/customers", json={"first_name": ""})
    assert r.status_code == 422 and r.json()["error_response"]["details"]