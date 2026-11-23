<details>
<summary>⚙️ Details</summary>

```yaml
is_due: true
id: A04-Web_Api_Project
name: A04-Web_Api_Project
title: A Full-Stack Store Page
description: HTML + Alpine.js, FastAPI, MongoDB, and Redis in one app
category: Assignments
date_due:
  month: '12'
  day: '04'
  year: 2026
  hour: 16
```

</details>

# Web API Project: A Full-Stack Store Page

## Overview

You'll build **one web page** where a shop employee picks a customer, finds
a product, and records a purchase. Behind the page is a **FastAPI** server
that reads and writes **MongoDB** and keeps a **Redis** cache in front of
product searches.

The [lessons](../../lessons/README.md) build this app one idea at a time,
from a plain HTML form to the finished app in lesson 14. This assignment is
the summary of all fifteen lessons, in one place:

- **what** your finished app has to do,
- **which lesson** teaches each piece,
- the **lesson activities** that go into your version, and
- what makes the page **good to use**, not just working (UI/UX).

```text
 Browser                          Server                         Data
┌──────────────────────┐  fetch  ┌─────────────────────┐        ┌──────────────┐
│ index.html           │ ──────▶ │ api.py (FastAPI)    │ ─────▶ │ MongoDB      │
│  HTML form           │  JSON   │  routes, validation │        │  noidx_10k   │
│  Alpine.js state     │ ◀────── │  pricing, IDs       │ ◀───── │  (dev copy)  │
│  Tailwind styling    │         │  cache-aside        │ ◀────▶ │ Redis        │
└──────────────────────┘         └─────────────────────┘        └──────────────┘
```

> **Start from the lessons, finish with your own app.** You may begin from the
> lesson 14 code. Lesson 14 alone doesn't earn many points, though: the
> [required activities](#4-required-activities) and the
> [UI/UX](#5-uiux-make-it-good-to-use) work are 45 of the 100 points, and
> neither is in the lesson code.

---

## 1. What the finished app does

A user can do all of this **on one page, without reloading it**:

| #   | The user can…                                                                     | Built in lessons                                                                                                            |
| --- | --------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| 1   | Choose a **customer** from all 500 in the database                                | [05](../../lessons/05-local-arrays/), [07](../../lessons/07-mongo-reads/)                                                   |
| 2   | Choose one of **that customer's cards** (last four digits only)                   | [10](../../lessons/10-post-purchase/)                                                                                       |
| 3   | See that customer's **10 most recent purchases**                                  | [08](../../lessons/08-dependent-requests/)                                                                                  |
| 4   | **Search** products as they type, **filter** by price, and **sort**               | [11](../../lessons/11-keyword-search/), [12](../../lessons/12-search-as-you-type/), [13](../../lessons/13-filter-and-sort/) |
| 5   | Select a product and see its **price and how often it's been bought**             | [08](../../lessons/08-dependent-requests/)                                                                                  |
| 6   | Pick a **quantity** (1–10), see an estimated total, and **place the purchase**    | [03](../../lessons/03-alpine-state/), [10](../../lessons/10-post-purchase/)                                                 |
| 7   | Get a **receipt** with the total the *server* charged; history refreshes          | [10](../../lessons/10-post-purchase/)                                                                                       |
| 8   | **Register a new customer**, who is then selected automatically                   | [09](../../lessons/09-post-customer/)                                                                                       |
| 9   | See whether a search came from the **cache** (HIT / MISS / OFF)                   | [14](../../lessons/14-redis-cache/)                                                                                         |
| 10  | (Developer panel) **Change a product's price**, which invalidates cached searches | [14](../../lessons/14-redis-cache/)                                                                                         |

---

## 2. The lessons at a glance

Work through the lessons in order. Each one has an **Activity** and a
**Checkpoint** at the end; the activities in [section 4](#4-required-activities)
become part of your app, and the checkpoints feed your README
([section 6](#6-what-to-submit)).

| Stage           | Lessons                                                                                                                                                  | You learn                                                                                                 | Your app gains                                                         |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| **0. Setup**    | [00](../../lessons/00-minimal-api/) · [01](../../lessons/01-the-data/)                                                                                   | The smallest FastAPI app; the `noidx_10k` collections; how money is stored                                | A working environment, and a feel for the data                         |
| **1. The page** | [02](../../lessons/02-html-forms/) · [03](../../lessons/03-alpine-state/) · [04](../../lessons/04-alpine-events/) · [05](../../lessons/05-local-arrays/) | Forms and labels, Tailwind, Alpine `x-data` / `x-model` / `x-show` / `@submit.prevent` / `x-for`          | The purchase form, filled from JavaScript arrays (no server yet)       |
| **2. Reading**  | [06](../../lessons/06-first-fastapi/) · [07](../../lessons/07-mongo-reads/) · [08](../../lessons/08-dependent-requests/)                                 | `fetch()`, same-origin and CORS, `find()` and projections, converting BSON, path parameters, 404 vs empty | Dropdowns from MongoDB; product details and purchase history on demand |
| **3. Writing**  | [09](../../lessons/09-post-customer/) · [10](../../lessons/10-post-purchase/)                                                                            | POST with JSON, Pydantic validation, 201/409/422, atomic counters, server-side pricing                    | Customer registration and recorded purchases                           |
| **4. Finding**  | [11](../../lessons/11-keyword-search/) · [12](../../lessons/12-search-as-you-type/) · [13](../../lessons/13-filter-and-sort/)                            | Query parameters, safe regex, debounce, out-of-order responses, combined filters, validated sorts         | Search as you type, with price filters and sorting                     |
| **5. Caching**  | [14](../../lessons/14-redis-cache/)                                                                                                                      | Cache-aside, cache keys, expiration, version-based invalidation, failing soft                             | A Redis cache that makes searches faster and never breaks the app      |

---

## 3. Requirements

### 3.1 Setup

Follow the [lessons README](../../lessons/README.md#one-time-setup): a virtual
environment, `pip install -r lessons/requirements.txt`, MongoDB running with
`noidx_10k` loaded, and Redis (only needed for stage 5).

Your app **writes** to the database, so point it at a copy:

```bash
mongosh noidx_10k --eval 'db.getCollectionNames().forEach(c => db[c].aggregate([{ $out: { db: "noidx_10k_dev", coll: c } }]))'
export MONGO_DB=noidx_10k_dev
```

### 3.2 The API

One `api.py` (or a small package) serves the page **and** these routes.
The status codes matter as much as the data.

| Route                               | Returns                                               | Must also                                                                                                                       |
| ----------------------------------- | ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `GET /`                             | The page                                              | Be the only way the page is opened (same origin, no CORS)                                                                       |
| `GET /api/customers`                | `[{id, name}]`, sorted by name                        | Send only the fields the page needs                                                                                             |
| `GET /api/customers/{id}`           | Name, email, state, cards (**last four digits only**) | 404 for an unknown id, 422 for a non-integer                                                                                    |
| `GET /api/customers/{id}/purchases` | The 10 most recent purchases                          | 404 for an unknown customer, `[]` for one with no purchases; newest first with a tie-breaker                                    |
| `GET /api/products`                 | `[{id, name, price}]`                                 | Accept `q`, `min_price`, `max_price`, `sort`, `limit` (and `whole`; see section 4); 422 on bad values; send an `X-Cache` header |
| `GET /api/products/{id}`            | Name, price, purchase count                           | 404 / 422 as above; never cached                                                                                                |
| `POST /api/customers`               | `{id, name}` with **201**                             | Validate with a Pydantic model; 409 on a duplicate email; new ids from `counters`                                               |
| `POST /api/purchases`               | A receipt with **201**                                | Accept only ids and quantity (1–10); look up the price itself; 404 for unknown ids, 400 for someone else's card                 |
| `PATCH /api/products/{id}/price`    | The updated product                                   | Invalidate cached searches                                                                                                      |

### 3.3 Rules the lessons keep repeating

These don't earn points by themselves, but breaking one costs points
(section 7, "Data and API correctness").

| Rule                                                                                                                   | Why                                        | Lesson                                                                                      |
| ---------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ | ------------------------------------------------------------------------------------------- |
| **Money is never a float.** `Decimal128` in Mongo, `Decimal` in Python, a string in JSON, integer cents in the browser | `0.1 + 0.2` isn't `0.3`                    | [01](../../lessons/01-the-data/#how-money-is-handled-in-these-lessons)                      |
| **The server sets the price.** The browser's total is a preview                                                        | Anyone can send any JSON to your API       | [10](../../lessons/10-post-purchase/)                                                       |
| **Store and send ids, display names**                                                                                  | Three customers are named "Dennis Allen"   | [05](../../lessons/05-local-arrays/), [07](../../lessons/07-mongo-reads/)                   |
| **Validate on the server**, even with browser validation                                                               | `/docs` and `curl` skip the browser        | [09](../../lessons/09-post-customer/)                                                       |
| **Connect to MongoDB once**, at startup                                                                                | Not once per request                       | [07](../../lessons/07-mongo-reads/)                                                         |
| **Convert BSON types** (`Decimal128`, `ObjectId`) before returning                                                     | FastAPI can't serialize them: 500          | [07](../../lessons/07-mongo-reads/)                                                         |
| **New ids come from an atomic `$inc`** on `counters`                                                                   | "Highest id + 1" breaks under two requests | [09](../../lessons/09-post-customer/)                                                       |
| **Escape user text in regexes**; **map sort names** to fields yourself                                                 | `q=.*` and `sort=cards.card_number`        | [11](../../lessons/11-keyword-search/), [13](../../lessons/13-filter-and-sort/)             |
| **Never serve the code folder** with `StaticFiles`                                                                     | It publishes `api.py` and `.env`           | [06](../../lessons/06-first-fastapi/#fix-3-have-fastapi-serve-the-whole-folder-staticfiles) |
| **The cache is optional.** Redis down = slower, never broken                                                           | It's an optimization                       | [14](../../lessons/14-redis-cache/)                                                         |

---

## 4. Required activities

These come from the lessons' **Activity** sections. None of them is in the
lesson code, and each one changes the finished app. Build all of them into
your version.

| #   | Activity                                                                                                           | From                                                   | Done when…                                                                 |
| --- | ------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------ | -------------------------------------------------------------------------- |
| A1  | Duplicate customer names are **distinguishable** in the dropdown                                                   | [07](../../lessons/07-mongo-reads/#activity) #2        | The three Dennis Allens can be told apart                                  |
| A2  | The history shows the **total of the listed purchases**                                                            | [08](../../lessons/08-dependent-requests/#activity) #2 | A total appears under the table and updates after a purchase               |
| A3  | **Friendlier validation messages**: field labels instead of field names, "has the wrong format" instead of a regex | [09](../../lessons/09-post-customer/#activity) #3      | A bad ZIP code says something like "ZIP code has the wrong format"         |
| A4  | A **whole-word search** checkbox sends `whole=true`, handled on the server with `\b`                               | [11](../../lessons/11-keyword-search/#activity) #3     | `key` finds Keyboard with it off, and doesn't with it on                   |
| A5  | An **Under $100** quick filter                                                                                     | [13](../../lessons/13-filter-and-sort/#activity) #1    | One click sets the max price and searches                                  |
| A6  | A **Z–A** sort (`name_desc`)                                                                                       | [13](../../lessons/13-filter-and-sort/#activity) #2    | Accepted by the server and offered by the page; anything else is still 422 |
| A7  | **min > max** shows a message **without** sending a request                                                        | [13](../../lessons/13-filter-and-sort/#activity) #3    | The Network tab shows no request                                           |
| A8  | An **`X-Cache-Key`** header, shown on the page                                                                     | [14](../../lessons/14-redis-cache/#activity) #3        | The page shows the key a search used                                       |

---

## 5. UI/UX: make it good to use

A page can call every route correctly and still be frustrating to use. This
section is worth **25 points**. The lesson pages are deliberately plain, so
this part is yours. The lessons already use most of the tools you need:
`x-show`, `:disabled`, `:class`, Tailwind, and the `loading` and `error`
patterns.

### 5.1 What we look for

**Feedback: the user always knows what's happening** (6 pts)

- Every request has a visible **loading** state, and the control that started
  it is disabled until it finishes. No double purchases. ([06](../../lessons/06-first-fastapi/), [10](../../lessons/10-post-purchase/))
- **"Not loaded yet", "loaded, but empty", and "failed" look different.** For
  example: "Choose a customer to see their history", "No purchases yet", and
  "Couldn't load purchases: …". ([08](../../lessons/08-dependent-requests/#empty-is-not-the-same-as-missing))
- **Success is confirmed** with the server's numbers: the receipt shows the
  charged total and the new purchase appears in the history.
- **Errors are written for people.** No raw JSON, status codes on their own,
  or Python tracebacks on the page. Each message says what went wrong and what
  to do.

**Forms: easy to fill in, hard to get wrong** (6 pts)

- Every input has a visible `<label>`. Placeholder text doesn't count as a
  label. ([02](../../lessons/02-html-forms/))
- Input types fit the data: `type="email"`, `inputmode="numeric"` for ZIP and
  card numbers, number inputs with `min` and `max`. Browser validation
  mirrors the server's rules.
- A validation error appears **next to the field it's about**, and the
  user's input is **kept**, so they fix one field instead of retyping the
  form.
- Dependent controls make sense: the card dropdown is disabled until a
  customer is chosen, and switching customers clears the old card.
- Placing a purchase has a **clear summary first**: who, which card, what,
  how many, and the estimated total, right next to the button.

**Layout and visual design** (5 pts)

- The page reads **in the order the task happens**: customer → product →
  purchase → history. Headings and spacing make the sections obvious.
- **Consistent styling**: one button style per role (primary, secondary,
  danger), one error style, one success style.
- **Money and dates are formatted for people**: `$202.11`, not `202.11` or
  `20211`; numbers right-aligned in tables.
- **Works on a phone.** At 375 px wide nothing overflows sideways, and buttons
  are big enough to tap. ([13](../../lessons/13-filter-and-sort/#responsive-layout))
- The developer price tool is visibly separate from the shop flow, for
  example collapsed in a `<details>` section and labeled as a developer tool.

**Accessibility** (5 pts)

- The whole purchase can be done **with the keyboard alone**: Tab reaches
  everything in a sensible order, focus is always visible, Enter submits,
  and Esc clears the search. ([12](../../lessons/12-search-as-you-type/))
- Status messages are announced: wrap loading, error, and success messages
  in a region with `aria-live="polite"` (or `role="alert"` for errors).
- **Color is never the only signal.** HIT/MISS and error states also have
  text or an icon.
- Text contrast meets WCAG AA (4.5:1). Chrome's **Lighthouse → Accessibility**
  report checks it; aim for a score of 90+.
- `<html lang="en">`, a meaningful `<title>`, and `alt` text on any images.

**Search that behaves** (3 pts)

- Debounced, with a minimum length and a hint below it, and a "no matches"
  message that differs from "type to search". ([12](../../lessons/12-search-as-you-type/))
- **Never shows stale results.** An old, slow answer can't replace a newer
  search (test it with the lesson's slow-network switch).
- Active filters are visible, and one click resets them.

### 5.2 The UX walkthrough (do this before you submit)

Do each run yourself and note the result in your README. Each one catches a
different kind of problem.

| Run           | How                                                                                 | Passes when                                                        |
| ------------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| Keyboard only | Unplug the mouse (or don't touch it). Choose a customer, search, buy 2 of something | You never needed the mouse and always knew where focus was         |
| Phone width   | DevTools → device toolbar → 375 × 667                                               | Nothing scrolls sideways; everything is readable and tappable      |
| Slow network  | Turn on the slow switch (or DevTools → Network → Slow 3G) and type quickly          | Loading states show; results always match the search box           |
| API stopped   | Stop `api.py` with the page open, then try each action                              | Every action shows a readable error; nothing silently does nothing |
| Redis stopped | Stop Redis and search                                                               | The app works and says the cache is off                            |
| Bad input     | Register with an empty form (skip browser checks), a duplicate email, and a bad ZIP | Clear, field-level messages for 422 and 409                        |
| Lighthouse    | DevTools → Lighthouse → Accessibility                                               | Score recorded in your README; aim for 90+                         |

### 5.3 Ideas if you want to go further

None of these are required. Small, careful touches beat big, unfinished ones.

- Highlight the matched text in search results.
- Remember the last selected customer with `localStorage`.
- Show a "recently viewed" list of products.
- Ask "Are you sure?" before a large order (quantity 10) or a price change.
- Add a skeleton or placeholder while the history loads.

---

## 6. What to submit

Put the project in a `Web_Api_Project/` folder in your course repo:

```text
Web_Api_Project/
├── README.md            your report (see below)
├── api.py               the server: page + every route (or app/ as a package)
├── index.html           the page (or static/index.html, plus any .js/.css files)
├── requirements.txt     what to pip install
├── .env.example         MONGO_URL, MONGO_DB, REDIS_URL, CACHE_SECONDS: placeholders only
└── screenshots/         desktop, phone width, an error state, a receipt, Lighthouse
```

Don't commit `.venv/`, `__pycache__/`, a real `.env`, or database dumps.

### Your README must include

1. **How to run it**: database copy, environment variables, the start
   command, and the URL to open.
2. **Feature checklist**: the ten items from [section 1](#1-what-the-finished-app-does)
   and the eight activities from [section 4](#4-required-activities), each
   marked done or not.
3. **UX notes**:
   - Three design decisions you made, and why. For each, say what it looked
     like before and after.
   - Your results from the [walkthrough](#52-the-ux-walkthrough-do-this-before-you-submit) table.
   - Your Lighthouse accessibility score.
   - One thing you'd still improve.
4. **Checkpoint answers**, two to four sentences each, for these lessons:
   - [06](../../lessons/06-first-fastapi/#checkpoint): what runs in the
     browser and what runs on the server
   - [08](../../lessons/08-dependent-requests/#checkpoint): why clear stale data first
   - [09](../../lessons/09-post-customer/#checkpoint): why browser validation isn't enough
   - [10](../../lessons/10-post-purchase/#checkpoint): two buyers, one last item
   - [12](../../lessons/12-search-as-you-type/#checkpoint): how an old response can win
   - [13](../../lessons/13-filter-and-sort/#checkpoint): why sorts are validated
   - [14](../../lessons/14-redis-cache/#checkpoint): expiration vs. invalidation
5. **Screenshots** embedded or linked from `screenshots/`.

---

## 7. Grading

| Category                     |  Points | What earns them                                                                                                                      |
| ---------------------------- | ------: | ------------------------------------------------------------------------------------------------------------------------------------ |
| **Core app**                 |      25 | All ten features from section 1 work end to end on one page, against MongoDB, with the routes and status codes in 3.2                |
| **Required activities**      |      20 | A1–A8 from section 4, 2.5 points each                                                                                                |
| **UI/UX**                    |      25 | Section 5.1: feedback 6, forms 6, layout 5, accessibility 5, search 3                                                                |
| **Data and API correctness** |      15 | The rules in 3.3 hold: money, server-side pricing, validation, atomic ids, BSON conversion, safe regex and sorts, soft-failing cache |
| **README and evidence**      |      15 | Run instructions that work, the checklist, UX notes and walkthrough, checkpoint answers, screenshots                                 |
| **Total**                    | **100** |                                                                                                                                      |

### Bonus (up to +10)

| Extra                                                                                                                                                            | Points | From                                                           |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | -----: | -------------------------------------------------------------- |
| **Stock**: a conditional `update_one` that can't oversell, and a 409 the page explains                                                                           |     +4 | [10](../../lessons/10-post-purchase/#stock-optional-extension) |
| **`monthly_sales` kept up to date** by each purchase (`$inc` with `upsert`)                                                                                      |     +3 | [10](../../lessons/10-post-purchase/#activity) #3              |
| **Product photos**, using the `store` database and image folder, if your instructor provides them                                                                |     +3 | [11 (images)](../../lessons/11-keyword-search_Img/)            |
| **Standardized responses**: your [Standardizing API Responses](../Standardizing_Api_Responses/README.md) envelope on every route, with the page updated to match |     +3 | —                                                              |

---

## 8. Common problems

| Symptom                                      | Usual cause                                                          | See                                                                                                      |
| -------------------------------------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Every request fails, but `api.py` is running | The page was opened from disk (`file://`)                            | [06](../../lessons/06-first-fastapi/#why-opening-the-file-directly-doesnt-work)                          |
| `blocked by CORS policy`                     | The page and the API are on different origins                        | [06](../../lessons/06-first-fastapi/#problem-2-with-the-full-address-the-browser-blocks-the-answer-cors) |
| `address already in use`                     | Another lesson's server still holds port 8000                        | [lessons README](../../lessons/README.md#opening-the-lessons)                                            |
| 500 with `Decimal128 … not iterable`         | A BSON value returned without converting                             | [07](../../lessons/07-mongo-reads/#why-theyre-necessary)                                                 |
| `.find()` never matches the selected id      | `"2"` vs `2`: missing `x-model.number`                               | [05](../../lessons/05-local-arrays/#05b--a-dropdown-from-an-array)                                       |
| 422 on a POST that looks right               | Missing `Content-Type: application/json`, or a field fails the model | [09](../../lessons/09-post-customer/#sending-json)                                                       |
| Results don't match the search box           | An out-of-order response                                             | [12](../../lessons/12-search-as-you-type/#out-of-order-responses)                                        |
| A price change doesn't show up in search     | The cache wasn't invalidated                                         | [14](../../lessons/14-redis-cache/#invalidation)                                                         |

Keep the browser's **Network** tab (F12 → Network) open while you work. It
shows every request, its status, and its response, and it's the fastest way
to find out whether a problem is in the page or the server.
