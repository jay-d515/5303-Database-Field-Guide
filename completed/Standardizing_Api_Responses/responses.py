# responses.py  (required: the name may differ, see README variations)
#
# Your reusable response mechanism (Part 2). Exactly one of:
#   - a function, e.g. api_response(...)
#   - a class that builds responses
#   - a Pydantic response model (often paired with a small helper function)
#
# It must:
#   - produce the seven fields: response_code, error_response, data,
#     total_size, size, offset, limit
#   - accept a list, a dict, or None as data
#   - support optional pagination values
#   - support both success and error responses
#   - know NOTHING about MongoDB (no pymongo/bson imports here)
