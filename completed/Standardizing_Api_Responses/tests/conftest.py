# tests/conftest.py  (optional: only if you write automated tests)
#
# Shared pytest fixtures, typically a FastAPI TestClient built from
# `from api import app`. Point it at a test database (or the classroom one),
# never at data you can't afford to change: the POST tests insert documents.
