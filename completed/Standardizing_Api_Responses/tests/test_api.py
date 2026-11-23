# tests/test_api.py  (one way to satisfy Part 6; see README variations)
#
# One test per row of the Part 6 table. Each test should check the HTTP
# status AND the envelope fields, not just one of them.
#
#   1. retrieve products               -> standard envelope
#   2. products with limit=5           -> at most five records, size agrees
#   3. products with offset=5          -> skips the first five matches
#   4. search for products (q=...)     -> total_size reflects the matches
#   5. request beyond available records-> data == [], size == 0
#   6. retrieve one existing product   -> data is a dict
#   7. retrieve a nonexistent product  -> 404, standardized error
#   8. invalid pagination              -> 422, standardized error
#   9. create a customer               -> 201, standardized envelope
#  10. duplicate customer email        -> 409, standardized error
