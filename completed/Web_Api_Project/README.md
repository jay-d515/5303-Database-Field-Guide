# Completed structure: Web API Project

Assignment: [assignments/Web_Api_Project](../../assignments/Web_Api_Project/README.md)

This folder is what `Web_Api_Project/` in your course repo should look like
when you're done. Every file here holds only a description of what belongs
in it: no answers and no solution code.

## The structure

```
Web_Api_Project/
├── README.md            (required)  your report: run steps, checklist, UX notes, checkpoint answers
├── api.py               (required)  the server: the page + every route in section 3.2
├── index.html           (required)  the page: activities + all the UI/UX work
├── requirements.txt     (required)  what to pip install
├── .env.example         (recommended) MONGO_URL, MONGO_DB, REDIS_URL, CACHE_SECONDS: placeholders
├── .gitignore           (optional)  or one at the root of your repo
└── screenshots/         (required)  desktop, phone width, an error state, a receipt, Lighthouse
```

## How the files map to the grading

| Category                  | Points | Where it shows up                                                               |
| ------------------------- | -----: | ------------------------------------------------------------------------------- |
| Core app                  |     25 | `api.py` routes + `index.html` flows, run end to end                            |
| Required activities A1–A8 |     20 | A4, A6, A8 mostly in `api.py`; A1, A2, A3, A5, A7, A8 on `index.html`           |
| UI/UX                     |     25 | `index.html` (and any CSS/JS files); proved by `screenshots/` and your UX notes |
| Data and API correctness  |     15 | `api.py`                                                                        |
| README and evidence       |     15 | `README.md`, `screenshots/`                                                     |

## Your `README.md`

The file you're reading explains the structure. **Your** `README.md` in this
spot is your report, with these sections (section 6 of the assignment):

| Section            | What goes in it                                                                                                                                |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| How to run it      | The database copy, environment variables, the start command, the URL to open                                                                   |
| Feature checklist  | The ten features (section 1) and activities A1–A8 (section 4), each marked done or not                                                         |
| UX notes           | Three design decisions (before → after, and why), your walkthrough results, your Lighthouse accessibility score, one thing you'd still improve |
| Checkpoint answers | Lessons 06, 08, 09, 10, 12, 13, and 14, two to four sentences each                                                                             |
| Screenshots        | Embedded or linked from `screenshots/`                                                                                                         |

## Acceptable variations

| Shown                                  | Also fine                                                                                                                                               |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `api.py`                               | `main.py`, or a package: `app/main.py` (+ `app/models.py`, `app/cache.py`, ...), run with `uvicorn app.main:app`                                        |
| `index.html`                           | `static/index.html`, `templates/index.html`, `public/index.html`                                                                                        |
| JavaScript and CSS inside `index.html` | Separate files such as `static/app.js` and `static/styles.css`, served from a `/static` mount. **Never mount the folder that holds `api.py` or `.env`** |
| `requirements.txt`                     | `pyproject.toml`                                                                                                                                        |
| `screenshots/`                         | `images/`, `docs/screenshots/`, `docs/`                                                                                                                 |
| Answers in `README.md`                 | A separate `CHECKPOINTS.md` or `UX_NOTES.md` linked from the README                                                                                     |

## What must NOT be in the folder

- `.venv/`, `venv/`, `__pycache__/`
- A real `.env` (commit `.env.example` instead)
- Database dumps (`mongodump` output) or `dump.rdb` from Redis
- `.DS_Store`

The `.gitignore` here covers the usual ones; copy it if you don't have one.

## Common mistakes the structure helps you catch

- `api.py` or `index.html` unchanged from lesson 14: neither the activities
  nor the UX work is there yet.
- No screenshots, or none at phone width.
- A README with no walkthrough results or Lighthouse score.
- `StaticFiles` pointed at the project folder, which publishes `api.py`.

## Check your folder

The field guide's [check_completed.py](../../check_completed.py) compares
your folder with this one and looks inside each file for work of your own.
Run it from your course repo:

```bash
cd ~/5303/my-repo
python ~/5303/5303-Database-Field-Guide/check_completed.py web
```

✅ means the file is there with content of your own, 🟡 is worth a look,
❌ is missing or still the template, and ⚪ is optional. It checks that your
work is **there**, not that it's **right**.
