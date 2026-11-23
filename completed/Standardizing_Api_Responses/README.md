# Completed structure: Standardizing REST API Responses

Assignment: [assignments/Standardizing_Api_Responses](../../assignments/standardizing_api_responses/README.md)

This folder is what `Standardizing_Api_Responses/` in your course repo
should look like when you're done. Every file here holds only a description
of what belongs in it: no answers and no solution code.

The assignment asks for three things: your modified `api.py` plus any new
modules, a short `README.md` about your design, and evidence that you tested
it.

## The structure

```
Standardizing_Api_Responses/
├── README.md              (required)  design, the 5 required answers, client changes, how to run
├── api.py                 (required)  your modified api.py: every route returns the envelope
├── responses.py           (required)  the reusable response mechanism (Part 2)
├── index.html             (required*) the browser page, updated to read `data`
├── requirements.txt       (recommended) what to pip install
├── .env.example           (optional)  placeholder MONGO_URL / MONGO_DB
├── .gitignore
├── tests/                 (one evidence option)
│   ├── conftest.py            TestClient fixture
│   └── test_api.py            one test per row of the Part 6 table
└── evidence/              (required: at least one of the two files)
    ├── pytest_output.txt      `pytest -v` output
    └── http_examples.md       request, status, and JSON for each Part 6 test
```

\* Required if your `api.py` serves `index.html` (every lesson version does).
If you changed nothing in it, say so and why under *Client-side changes*.

## How the files map to the assignment

| Part | Points | Where it shows up |
| ---- | -----: | ----------------- |
| 1 · Response format | 20 | The output of every route; visible in `evidence/` |
| 2 · Reusable design | 20 | `responses.py`, and how `api.py` calls it |
| 3 · Pagination | 25 | `GET /api/products` in `api.py`; tests 2–5 |
| 4 · Existing endpoints | 15 | Every route in `api.py`; *Client-side changes* in `README.md`; `index.html` |
| 5 · Error handling | 10 | Exception handlers (in `api.py` or `errors.py`); tests 7, 8, 10 |
| 6 · Testing & docs | 10 | `tests/` and/or `evidence/`; the 5 answers in `README.md` |

## Your `README.md`

The file you're reading explains the structure. **Your** `README.md` in this
spot is your design write-up. Keep it short, with these sections:

| Section | What goes in it |
| ------- | --------------- |
| How to run | Start MongoDB, select the database, start the API, run the tests |
| Response design | What your reusable mechanism is, where it lives, one example call from a route |
| Required questions | Answers to all five, below |
| Error handling | How 404, 409, and 422 all end up in the same envelope |
| Client-side changes | Every change to `index.html` (or other clients) caused by the new response shape |
| Testing evidence | Where the evidence is, and how to reproduce it |

The five required questions:

1. Why did you choose a function, class, or Pydantic model?
2. How does your implementation avoid repeated code?
3. What is the difference between `total_size` and `size`?
4. What happens when an offset exceeds the number of matching records?
5. What would need to change if the database were PostgreSQL instead of
   MongoDB?

## Acceptable variations

The assignment says there is no single required implementation. These are
all fine:

**Where the response code lives**

| Variation | Looks like |
| --------- | ---------- |
| One helper module (shown) | `responses.py` |
| Different module name | `response.py`, `envelope.py`, `api_response.py`, `utils/responses.py` |
| Pydantic model in its own file | `schemas.py` or `models.py` holding `ApiResponse`, maybe with a helper in `responses.py` |
| Separate error handlers | `errors.py` (or `exceptions.py`) with the handlers for `HTTPException` and `RequestValidationError`, registered from `api.py` |
| Package layout | `app/__init__.py`, `app/api.py`, `app/responses.py` (then run with `uvicorn app.api:app`) |

**Keeping it in `api.py`.** A small function at the top of `api.py` meets
Part 2's requirements, because the requirement is no *duplicated* formatting,
not a separate file. A separate module is still the more common choice,
because it makes "keep formatting separate from MongoDB logic" easy to see.

**Evidence**

| Variation | Looks like |
| --------- | ---------- |
| pytest (shown) | `tests/test_api.py` + `evidence/pytest_output.txt` |
| Hand-run HTTP | `evidence/http_examples.md`, or one `.json` file per test (`evidence/07_product_404.json`, ...) |
| REST Client / HTTPie file | `requests.http` (VS Code REST Client) with the responses pasted in, or a shell script of `curl` calls plus its output |
| Screenshots | `evidence/screenshots/*.png` from `/docs`. Fine, but a screenshot must show the status code and the full envelope |
| Postman / Bruno | An exported collection (`.json`) **plus** the results; the collection alone doesn't prove the tests passed |

**Starting point.** You may have started from a different lesson version
of `api.py` (`10-post-purchase`, `13-filter-and-sort`, `14-redis-cache`, ...).
The structure is the same. If yours includes Redis caching, add `redis` to
`requirements.txt`, and make sure cached responses come back in the same
envelope too.

## What must NOT be in the folder

- `.venv/`, `venv/`, `__pycache__/`, `.pytest_cache/`
- A `.env` with real connection strings (commit `.env.example` instead)
- `.DS_Store`

The `.gitignore` here covers them; copy it if you don't have one.

## Common mistakes the structure helps you catch

- No `responses.py` (or equivalent), and every route builds its own dict:
  that loses most of Part 2.
- `size` or `total_size` hardcoded or computed by slicing a Python list.
- Evidence that only shows successful requests. Four of the ten tests are
  errors.
- `index.html` left reading a bare array, so the browser page breaks.

## Check your folder

The field guide's [check_completed.py](../../check_completed.py) compares
your folder with this one and looks inside each file for work of your own.
Run it from your course repo:

```bash
cd ~/5303/my-repo
python ~/5303/5303-Database-Field-Guide/check_completed.py standardizing
```

✅ means the file is there with content of your own, 🟡 is worth a look,
❌ is missing or still the template, and ⚪ is optional. It checks that your
work is **there**, not that it's **right**.
