<details>
<summary>⚙️ Details</summary>

```yaml
is_due: true
id: A03-Standardizing_Api_Responses
name: A03-Standardizing_Api_Responses
title: Standardizing REST API Responses
description: REST APIs, MongoDB, Response Models, and Pagination
category: Assignments
date_due:
  month: '12'
  day: '04'
  year: 2026
  hour: 17
```

</details>

# Assignment: Standardizing REST API Responses

## Overview

A database API does more than retrieve information. It provides a consistent interface through which other applications can access, interpret, and process that information.

The current multiple versions of our `api.py`  provides several REST endpoints that retrieve and modify MongoDB documents incrementally adding more functionality.  Although these endpoints work, their responses vary in structure. Some return lists, others return dictionaries, and error responses use a different format.

Your task is to **design and implement a reusable response mechanism** that standardizes the JSON returned by the API.
>This is a fancy way of saying send every response to a class or function first so it can be fancied up. See [HERE](./response_example.md) for simple examples.

The goal is to improve consistency, maintainability, and usability without rewriting the existing application.

## Learning Objectives

Upon completing this assignment, students should be able to:

1. Design a consistent JSON response structure for a REST API.
2. Implement reusable Python functions or classes.
3. Integrate response formatting with FastAPI.
4. Implement database pagination using `limit` and `offset`.
5. Distinguish between the number of returned records and the total number of matching records.
6. Handle HTTP errors without losing meaningful status codes.
7. Minimize duplicated code through appropriate software design.

---

## Part 1: The Response Format (20 points)

Every API endpoint must return a JSON object following a consistent structure.

### Successful Response

For example, a request to:

`GET /api/products?limit=5&offset=0`

Might produce:

```json
{
  "response_code": 200,
  "error_response": null,
  "data": [
    {"id": 101, "name": "Desk Chair", "price": "24.99"},
    {"id": 102, "name": "Floor Lamp", "price": "59.99"},
    {"id": 103, "name": "Kitchen Lamp", "price": "34.99"},
    {"id": 104, "name": "Microwave", "price": "359.99"},
    {"id": 105, "name": "Fan", "price": "17.99"}
  ],
  "total_size": 1000,
  "size": 5,
  "offset": 0,
  "limit": 5
}
```

### Required Fields

| Field            | Description                                        |
| ---------------- | -------------------------------------------------- |
| `response_code`  | HTTP status code associated with the response      |
| `error_response` | Error information, or `null` when successful       |
| `data`           | Actual result returned by the API                  |
| `total_size`     | Total number of matching records before pagination |
| `size`           | Number of records included in `data`               |
| `offset`         | Number of matching records skipped                 |
| `limit`          | Maximum number of records requested                |

### Response Rules

- `response_code` must agree with the actual HTTP response status.
- `error_response` must be `null` for successful requests.
- `data` may contain a list, dictionary, or `null`, depending on the endpoint.
- `size` must represent the number of records actually returned.
- `total_size` must represent the total number of records matching the query, regardless of pagination.
- `offset` and `limit` must reflect the actual pagination values used.

For endpoints that return a single resource or do not support pagination, use `null` for fields that do not apply. For a successful single-resource response, `size` and `total_size` should both be `1`.

For an empty collection, `data` must be `[]`, with `size` equal to `0`.

**Important:** The example above illustrates the required structure. It does not represent actual data or counts from the supplied database.

---

## Part 2: Reusable Response Design (20 points)

A standardized response format should not require every endpoint to manually construct the same dictionary.

Develop a reusable mechanism that creates the required response structure.

You may choose one of the following approaches:

- A Python function that accepts data and response metadata.
- A Python class responsible for constructing responses.
- A Pydantic response model.
- Another reasonable approach supported by FastAPI.

### Design Requirements

Your implementation must:

1. Be reusable across multiple endpoints.
2. Avoid duplicating response-formatting logic.
3. Accept different types of response data.
4. Support optional pagination information.
5. Support successful and unsuccessful responses.
6. Keep response formatting separate from MongoDB query logic.

You may introduce additional modules if doing so improves organization.

### Design Considerations

Consider the following questions before implementing your solution:

- Should a response object know anything about MongoDB?
- Should it calculate `size`, or should the endpoint supply that value?
- How should a response containing one dictionary differ from one containing a list?
- Should response formatting be handled by a function, class, or Pydantic model?
- How can the design remain useful if MongoDB is replaced with PostgreSQL?

There is no single required implementation. Your design should be straightforward, reusable, and appropriate for a production-style Python application.

---

## Part 3: Pagination (25 points)

The current application supports a `limit` parameter for product searches but does not implement `offset` pagination.

Extend the product endpoint to support both parameters.

### Required Endpoint

`GET /api/products?q=lamp&limit=5&offset=10`

The endpoint must:

1. Apply the existing product search filter.
2. Count all products matching the filter.
3. Skip the first 10 matching records.
4. Return at most 5 records.
5. Include the total matching record count in `total_size`.
6. Include the actual number returned in `size`.

### Parameter Requirements

| Parameter |      Default | Validation                 |
| --------- | -----------: | -------------------------- |
| `limit`   |          100 | Integer from 1 through 100 |
| `offset`  |            0 | Nonnegative integer        |
| `q`       | Empty string | Existing search behavior   |

Invalid parameters should produce an appropriate HTTP error.

### Example

Suppose a product search matches 43 documents.

A request using `limit=10&offset=20` should report:

```json
{
  "response_code": 200,
  "error_response": null,
  "data": [],
  "total_size": 43,
  "size": 10,
  "offset": 20,
  "limit": 10
}
```

The `data` array is abbreviated here. The actual response must contain the 10 matching documents.

### Additional Requirements

- Pagination must occur in the database query, not by retrieving every document and slicing a Python list.
- Results must use a deterministic sort order. Include a unique tie-breaker when sorting on a nonunique field.
- The count must use the same search criteria as the data query.
- A request beyond the final matching record should return an empty list, not an error.

For this assignment, offset-based pagination is sufficient. Cursor-based pagination is not required.

---

## Part 4: Updating Existing Endpoints (15 points)

Apply your standardized response mechanism to the existing endpoints in `api.py`.

| Endpoint                                     | Required behavior                   |
| -------------------------------------------- | ----------------------------------- |
| `GET /api/products`                          | Standard response with pagination   |
| `GET /api/products/{product_id}`             | Standard response for one product   |
| `GET /api/customers`                         | Standard response for customer list |
| `GET /api/customers/{customer_id}`           | Standard response for one customer  |
| `GET /api/customers/{customer_id}/purchases` | Standard response for purchase list |
| `POST /api/customers`                        | Standard response with HTTP 201     |
| `POST /api/purchases`                        | Standard response with HTTP 201     |

Only the product collection endpoint requires new pagination behavior.

Existing limits and query behavior on other endpoints should remain unchanged unless explicitly documented.

The application must continue to perform its original database operations correctly.

Do not change the underlying MongoDB document structure merely to accommodate the new API response format.

### Compatibility Note

Changing an API's response structure can break applications that consume it.

The supplied project also contains browser-facing endpoints. If existing JavaScript expects a bare array, it may need to access the new `data` field instead.

Document any necessary client-side changes.

---

## Part 5: Error Handling (10 points)

Successful responses are only half of an API contract.

An unsuccessful request should also follow the standardized structure.

For example:

`GET /api/products/999999`

If the product does not exist, the API should return HTTP 404 with a response resembling:

```json
{
  "response_code": 404,
  "error_response": {
    "message": "Product 999999 not found"
  },
  "data": null,
  "total_size": null,
  "size": 0,
  "offset": null,
  "limit": null
}
```

### Requirements

- Preserve appropriate HTTP status codes.
- Return useful error messages.
- Do not report an unsuccessful request as HTTP 200.
- Do not expose internal database credentials, connection strings, or Python tracebacks.
- Handle application-generated errors and FastAPI request-validation errors consistently.

Consider how FastAPI's existing exception handling can be extended without rewriting its internal validation mechanisms.

### Errors to Test

- Product not found: `404`
- Duplicate customer email: `409`
- Invalid query parameter: `422`
- Invalid request body: `422`

---

## Part 6: Testing and Documentation (10 points)

Test the updated API using FastAPI's interactive documentation, an HTTP client, or automated Python tests.

At minimum, demonstrate:

| Test                              | Expected result                         |
| --------------------------------- | --------------------------------------- |
| Retrieve products                 | Standard JSON response                  |
| Retrieve products with `limit=5`  | No more than five records               |
| Retrieve products with `offset=5` | Skips the first five matching records   |
| Search for products               | `total_size` reflects matching products |
| Request beyond available records  | Empty `data` array                      |
| Retrieve one existing product     | Dictionary in `data`                    |
| Retrieve nonexistent product      | HTTP 404 with standardized error        |
| Submit invalid pagination         | HTTP 422                                |
| Create a customer successfully    | HTTP 201 with standardized response     |
| Submit duplicate customer email   | HTTP 409                                |

### Submission Requirements

Submit:

1. Your modified `api.py` and any additional Python modules.
2. A short `README.md` explaining your response design.
3. Evidence of successful API testing, such as automated test output or representative HTTP responses.

The README must briefly answer:

- Why did you choose a function, class, or Pydantic model?
- How does your implementation avoid repeated code?
- What is the difference between `total_size` and `size`?
- What happens when an offset exceeds the number of matching records?
- What would need to change if the database were PostgreSQL instead of MongoDB?

---

## Grading Rubric

| Category                               |  Points |
| -------------------------------------- | ------: |
| Correct standardized response format   |      20 |
| Reusable response design               |      20 |
| Correct database pagination and counts |      25 |
| Integration with existing endpoints    |      15 |
| Consistent HTTP error handling         |      10 |
| Testing and documentation              |      10 |
| **Total**                              | **100** |

## Additional Expectations

The following principles should guide your implementation:

**Consistency:** Similar operations should return similarly structured responses.

**Separation of concerns:** Database queries should retrieve data; response formatting should organize it.

**Maintainability:** Adding a new endpoint should not require copying substantial amounts of response-formatting code.

**Correctness:** Metadata must describe the actual result, not an assumed or hardcoded value.

**Simplicity:** Avoid unnecessary abstractions. A small, well-designed function may be preferable to an elaborate class hierarchy.

---

## Final Thought

A working API is not necessarily a well-designed API.

The objective is to create a response structure that another programmer can use confidently without having to inspect the implementation of every endpoint.

Your implementation should make future API development easier, not more complicated.
