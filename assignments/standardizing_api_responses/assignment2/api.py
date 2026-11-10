# Lesson 13: search + price filters + validated sort: GET /api/products?q=lamp&max_price=200&sort=price_asc
#
# Run:   python api.py
# Open:  http://127.0.0.1:8000

import os
import re
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Literal

import uvicorn
from bson import Decimal128
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field
from pymongo import MongoClient, ReturnDocument
from pymongo.errors import DuplicateKeyError

from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from responses import api_response, error_response

HERE = Path(__file__).parent

client = MongoClient(os.getenv("MONGO_URL", "mongodb://localhost:27017"))
db = client[os.getenv("MONGO_DB", "noidx_10k")]

app = FastAPI()

# ---- Error handlers: every failure goes through the same response format ----
@app.exception_handler(StarletteHTTPException)
async def http_error(request, exc):
    return error_response(exc.status_code, str(exc.detail))

@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    details = [{"field": ".".join(map(str, e["loc"])), "message": e["msg"]} for e in exc.errors()]
    return error_response(422, "Invalid request", details)

@app.exception_handler(Exception)
async def server_error(request, exc):
    return error_response(500, "Internal server error")

# ---- Integer ids from the counters collection ----

def ensure_counter(name, current_max):
    """Create a counter starting at current_max, unless it already exists."""
    db.counters.update_one({"_id": name}, {"$setOnInsert": {"seq": current_max}}, upsert=True)


def next_id(name, count=1):
    """Reserve `count` ids in one step and return the first of them."""
    counter = db.counters.find_one_and_update(
        {"_id": name}, {"$inc": {"seq": count}}, return_document=ReturnDocument.AFTER
    )
    return counter["seq"] - count + 1


# noidx_10k only has a purchase_id counter, so start the other two after the existing ids.
last_customer = db.customers.find_one({}, {"_id": 1}, sort=[("_id", -1)])
ensure_counter("customer_id", last_customer["_id"] if last_customer else 0)

top_card = next(db.customers.aggregate([
    {"$unwind": "$cards"},
    {"$group": {"_id": None, "max": {"$max": "$cards.card_id"}}},
]), None)
ensure_counter("card_id", top_card["max"] if top_card else 0)


# ---- Request model: what a POST /api/customers body must look like ----

class NewCustomer(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)  # trim spaces from every string

    first_name: str = Field(min_length=1, max_length=40)
    last_name: str = Field(min_length=1, max_length=40)
    email: str = Field(max_length=100, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    address: str = Field(min_length=1, max_length=100)
    zipcode: str = Field(pattern=r"^\d{5}$")
    state_code: str = Field(pattern=r"^[A-Z]{2}$")
    card_type: Literal["americanexpress", "discover", "mastercard", "visa"]
    card_number: str = Field(pattern=r"^\d{16}$")


# Only the choices the user made. No price, no total, no names.
class NewPurchase(BaseModel):
    customer_id: int
    card_id: int
    product_id: int
    quantity: int = Field(ge=1, le=10)  # ge = greater than or equal, le = less than or equal


def customer_out(doc):
    return {"id": doc["_id"], "name": f"{doc['first_name']} {doc['last_name']}"}


def customer_detail_out(doc):
    # Never send full card numbers to the browser; the last four digits are enough to choose one.
    return {
        **customer_out(doc),
        "email": doc["email"],
        "state_code": doc["state_code"],
        "cards": [
            {"card_id": c["card_id"], "card_type": c["card_type"], "last4": c["card_number"][-4:]}
            for c in doc["cards"]
        ],
    }


def product_out(doc):
    return {"id": doc["_id"], "name": doc["product_name"], "price": str(doc["unit_price"])}


def purchase_out(doc):
    return {
        "id": doc["_id"],
        "product_name": doc["product_name"],
        "amount": str(doc["amount"]),
        "department": doc["department"],
        "purchase_date": doc["purchase_date"].date().isoformat(),  # "2026-04-30"
    }


@app.get("/")
def page():
    return FileResponse(HERE / "index.html")


@app.get("/api/customers")
def get_customers():
    docs = db.customers.find({}, {"first_name": 1, "last_name": 1}).sort([("last_name", 1), ("first_name", 1)])
    customers = [customer_out(doc) for doc in docs]
    return api_response(customers, total_size=len(customers))


# NEW: the only sort orders the API offers, and how each one maps to a MongoDB sort.
# The second key (product_name) breaks ties between equal prices, so the order is stable.
SORTS = {
    "name": [("product_name", 1), ("_id", 1)],
    "price_asc": [("unit_price", 1), ("product_name", 1), ("_id", 1)],
    "price_desc": [("unit_price", -1), ("product_name", 1), ("_id", 1)],
}


@app.get("/api/products")
def get_products(
    q: str = "",
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    sort: Literal["name", "price_asc", "price_desc"] = "name",  # anything else → 422
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    ):
    # Build the filter one condition at a time. Conditions in one dict must ALL match.
    query = {}

    term = q.strip()
    if term:
        query["product_name"] = {"$regex": re.escape(term), "$options": "i"}

    price = {}
    if min_price is not None:
        price["$gte"] = Decimal128(min_price)  # compare like with like: Decimal128 to Decimal128
    if max_price is not None:
        price["$lte"] = Decimal128(max_price)
    if price:
        query["unit_price"] = price

    total = db.products.count_documents(query)
    
    docs = (
        db.products.find(query, {"product_name": 1, "unit_price": 1})
        .sort(SORTS[sort])
        .skip(offset)
        .limit(limit)
    )
    return api_response(
        [product_out(doc) for doc in docs],
        total_size=total, offset=offset, limit=limit)


# {product_id} in the path becomes the function's product_id argument.
# ": int" makes FastAPI convert it, and reject /api/products/abc with a 422 error.
@app.get("/api/products/{product_id}")
def get_product(product_id: int):
    doc = db.products.find_one({"_id": product_id})
    if doc is None:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

    product = product_out(doc)
    product["times_purchased"] = db.purchases.count_documents({"product_id": product_id})
    return api_response(product)


# One customer, with their cards (for the card dropdown).
@app.get("/api/customers/{customer_id}")
def get_customer(customer_id: int):
    doc = db.customers.find_one({"_id": customer_id})
    if doc is None:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
    return api_response(customer_detail_out(doc))


# A customer's most recent purchases.
@app.get("/api/customers/{customer_id}/purchases")
def get_customer_purchases(customer_id: int):
    # "No such customer" (404) is a different answer from "a customer with no purchases" ([]).
    if db.customers.find_one({"_id": customer_id}, {"_id": 1}) is None:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    docs = db.purchases.find({"customer_id": customer_id}).sort([("purchase_date", -1), ("_id", -1)]).limit(10)
    purchases = [purchase_out(doc) for doc in docs]
    total = db.purchases.count_documents({"customer_id": customer_id})
    return api_response(purchases, total_size=total, offset=0, limit=10)


# Create a customer. FastAPI reads the JSON body into a NewCustomer and validates it.
# If validation fails, FastAPI answers 422 itself and this function never runs.
@app.post("/api/customers", status_code=201)
def create_customer(new: NewCustomer):
    email = new.email.lower()
    if db.customers.find_one({"email": email}, {"_id": 1}):
        raise HTTPException(status_code=409, detail=f"A customer with email {email} already exists")

    doc = {
        "_id": next_id("customer_id"),
        "first_name": new.first_name,
        "last_name": new.last_name,
        "email": email,
        "address": new.address,
        "zipcode": new.zipcode,
        "state_code": new.state_code,
        "cards": [
            {"card_id": next_id("card_id"), "card_type": new.card_type, "card_number": new.card_number},
        ],
    }
    try:
        db.customers.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="That card number is already on file")

    return api_response(customer_out(doc), response_code=201)


# Record a purchase.
@app.post("/api/purchases", status_code=201)
def create_purchase(new: NewPurchase):
    # 1. The IDs are valid integers and 1 <= quantity <= 10 (Pydantic checked that already).

    # 2. Confirm the customer, the card and the product exist, and that the card is the customer's.
    customer = db.customers.find_one({"_id": new.customer_id})
    if customer is None:
        raise HTTPException(status_code=404, detail=f"Customer {new.customer_id} not found")

    card = next((c for c in customer["cards"] if c["card_id"] == new.card_id), None)
    if card is None:
        raise HTTPException(status_code=400, detail=f"Card {new.card_id} does not belong to this customer")

    product = db.products.find_one({"_id": new.product_id})
    if product is None:
        raise HTTPException(status_code=404, detail=f"Product {new.product_id} not found")

    # 3. The authoritative price comes from the database, never from the request.
    unit_price = product["unit_price"].to_decimal()  # Decimal128 -> Python Decimal, for exact math
    total = unit_price * new.quantity

    # In noidx_10k, department is recorded on each purchase, not on the product.
    # Reuse the department this product was most recently sold under.
    last_sale = db.purchases.find_one({"product_id": new.product_id}, {"department": 1}, sort=[("purchase_date", -1)])
    department = last_sale["department"] if last_sale else "General"

    # 4. One purchase document per unit, matching the existing data. Reserve all the ids at once.
    first_id = next_id("purchase_id", new.quantity)
    now = datetime.now(timezone.utc)
    docs = [
        {
            "_id": first_id + i,
            "customer_id": customer["_id"],
            "card_id": card["card_id"],
            "product_id": product["_id"],
            "department": department,
            "amount": Decimal128(unit_price),       # the price AT PURCHASE TIME
            "purchase_date": now,
            "product_name": product["product_name"],  # copied, so history survives a rename
            "state_code": customer["state_code"],
            "card_type": card["card_type"],
        }
        for i in range(new.quantity)
    ]
    db.purchases.insert_many(docs)

    # 5. Confirm what was recorded.
    return api_response(
        {
            "purchase_ids": [doc["_id"] for doc in docs],
            "customer_name": f"{customer['first_name']} {customer['last_name']}",
            "product_name": product["product_name"],
            "quantity": new.quantity,
            "unit_price": str(unit_price),
            "total": str(total),
            "purchase_date": now.isoformat(),
        },
        response_code=201,
    )


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
