# A03 - Standardizing REST API Responses

## Files
- `api.py` - the API, updated to use the standard response format and pagination
- `responses.py` - the resuable response helper
- `index.html` - browser page, updated to read the new format
- `test.py` - automated tests (pytest + FastAPI TestClient)
- `test_output.txt` - test results (10 passed)

## Response Design
Every endpoint returns its data through `api_response()` in `responses.py`, which builds:

```json
{
    "response_code": 200,
    "error_response": null,
    "data": [ ... ],
    "total_size": 43,
    "size": 10,
    "offset": 20,
    "limit": 10
}
```

Errors use the same shape through `error_response()`. Exception handlers in `api.py` catch `HTTPException` (404, 409, 400), validation errors (422), and unexpected errors (500, with no traceback or database details shown).

## Questions
**Why a function instead of a class or Pydantic model?**
In my opinion, a function was the simplest option. It works with any data type and doesn't need any setup, on the other hand, a class would add unnecessary complexity without adding anything useful.

**How does it avoid repeated code?**
The response dictionary is built in one place. Every endpoint calls `api_response()`, and every error goes through `error_response` using the exception handlersm so no endpoint is building the format from scratch. The existing `raise HTTPException(...)` lines do not need to change.

**What is the difference between `total_size` and `size`?**
`total_size` is how many records match the query in total, BEFORE pagination. `size` is how mnay records are actually in `data` for this page.
Example: a serch matchin 43 product with `limt=10` has `total_size` 43 and `size` 10.

**What happens when the offset is past the last record?**
The API retursn HTTP 200 with `data: []` and `size: 0`. `total_size` still shows the real match count because it is not an error.

**What would change for PostgreSQL?**
Only the query code in `api.py`: `find().skip().limit()` would become `SELECT ... LIMIT ... OFFSET ...`, and `count_documents()` would become `SELECT COUNT(*)`. `responses.py` would not change because it knows nothing about the database.

## Pagination
`GET /api/products` accepts `limit` (1-100, default 100) and `offset` (>= 0, default 0). Paging happens in the database with `.skip(offset).limit(limit)`. The count uses the same filter as the search. `_id` was added as a final sort key so the order is always teh same between pages.

## Client-Side Changes
`index.html` expected a bare array, so it was updated:
- `this.results = data` -> `this.results = data.data`
- Error messages are now read from `data.error_response` instead of `data.detail`

## Other Changes
Testing found that creating a customer with a card number already on file crashed with a 500 (MongoDB unique index on `cards.card_number`). `create_customer` now catches `DuplicateKeyError` and returns a 409 with the standard error format.

## Testing
Run with: `python -m pytest test.py -v`

All 10 required tests pass (see `test_output.txt`):

| Test | Result |
|------|--------|
| Retrieve products | Standard JSON response |
| `limit=5` | No more than 5 records |
| `offset=5` | Skips first 5 records |
| Search | `total_size` matches the database count |
| Offset beyond records | Empty `data` array |
| One existing product | Dictionary in `data` |
| Nonexistent product| 404 with standard error |
| Invalid pagination | 422 |
| Create customer | 201 with standard response |
| Duplicate email | 409 |

## Example: product not found
```json
{
    "response_code": 404,
    "error_response": {"message": "Product 999999 not found"},
    "data": null,
    "total_size": null,
    "size": 0,
    "offset": null,
    "limit": null
}

```