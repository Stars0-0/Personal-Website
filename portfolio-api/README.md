# Portfolio API

The backend for [my portfolio site](https://stars0-0.github.io/Personal-Website/), which lives in the parent folder. The terminal on the site talks to this service, so visitors can type a note into a guestbook, send me a private message, and see a visit counter.

**Stack:** FastAPI, SQLModel, SQLite locally, Postgres in production.

## Endpoints

Interactive docs live at `/docs`.

| Method and path | What it does |
|---|---|
| `GET /api/health` | Liveness check |
| `POST /api/visit` | Adds one to the visit counter (the page calls it once per tab) |
| `GET /api/stats` | Visit count and number of approved guestbook notes |
| `GET /api/guestbook` | Latest 20 approved notes |
| `POST /api/guestbook` | Leaves a note. It stays hidden until I approve it |
| `POST /api/messages` | Sends me a private message. Never returned by any public route |
| `GET /api/admin/inbox` | Private messages and pending notes (token needed) |
| `POST /api/admin/guestbook/{id}/approve` | Publishes a note (token needed) |
| `DELETE /api/admin/guestbook/{id}` | Removes a note (token needed) |

## Design decisions

- **Moderated guestbook.** Anyone can post, nothing is public until I approve it, so spam and abuse never reach the page. Display text is escaped in the terminal, and names are forced onto one line.
- **Admin token.** Admin routes read `ADMIN_TOKEN` from the environment and compare it in constant time. With no token set they return 404, as if they didn't exist.
- **Validation at the edge.** Length limits, an email pattern, whitespace trimming, and rejection of NUL bytes (Postgres would turn those into a 500).
- **CORS allow-list.** Only the origins in `ALLOWED_ORIGINS` can call the API from a browser, and only with GET, POST and `Content-Type`.
- **One global rate limit, not per-IP.** 30 posts per hour across all visitors, kept in memory. Behind a hosting proxy I couldn't verify a trustworthy client IP, and a per-IP limit that can be spoofed is worse than none. Moderation keeps spam off the page either way. Upgrade path: per-IP limits or Redis once the real header layout is confirmed on the deployed service.
- **No migrations.** Tables are created on startup. Add Alembic the first time the schema changes.
- **Visit counter is a vanity number.** It counts every call and does no de-duplication.

## Run it locally

You need Python 3.9 or newer (`python3 --version`). Run these from this folder. On a Mac, plain `python` may not exist, so create the environment with `python3`. On Windows, use `py -m venv .venv` and activate with `.venv\Scripts\activate`.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pytest httpx
ALLOWED_ORIGINS=http://localhost:8765 ADMIN_TOKEN=dev python -m uvicorn main:app --reload
```

Then open http://127.0.0.1:8000/docs. Without `DATABASE_URL` it uses a local SQLite file, `portfolio.db`, which git ignores.

The Postgres driver (`psycopg`) is only installed on Linux, where Render runs the service, so a Mac or Windows install stays small. To try Postgres locally, run `python -m pip install "psycopg[binary]"` and set `DATABASE_URL`.

Python 3.9 reached end of life on 2025-10-31, so prefer a newer Python if you can install one.

## Tests

```bash
python -m pytest -q
```

That runs the suite against SQLite. To run the same checks against Postgres, install the driver as above and run `DATABASE_URL=postgresql://... python -m pytest -q`, using a database you don't mind filling with test rows. The suite covers validation, moderation, admin auth, the rate limit, the counter and the CORS allow-list.

## Deploy (Render + Neon, both free)

This folder sits inside a larger repo, so Render needs to know where the service lives.

1. **Database.** Create a free project on [Neon](https://neon.com). In the console click **Connect**, turn off the connection pooling toggle, and copy the connection string. Neon's free plan is permanent. Render's own free Postgres expires after 30 days, and Render's free web services lose local files whenever they restart, which is why SQLite isn't used in production.
2. **Web service.** On [Render](https://render.com) choose New, then Web Service, and connect this repo.
   - Root directory: `portfolio-api` (Render runs the commands below from inside it, and only redeploys when files in it change)
   - Language: Python 3
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Instance type: Free
3. **Environment variables.**

   | Name | Value |
   |---|---|
   | `DATABASE_URL` | the Neon connection string |
   | `ADMIN_TOKEN` | a long random string. Make one with `python3 -c "import secrets; print(secrets.token_urlsafe(32))"` |
   | `ALLOWED_ORIGINS` | `https://stars0-0.github.io` (no trailing slash and no path) |
   | `PYTHON_VERSION` | `3.13.5` |

   `ALLOWED_ORIGINS` is the site's origin, which is only the scheme and host. The `/Personal-Website/` part of the page address is not included. `PYTHON_VERSION` takes priority over any `.python-version` file, so the service doesn't depend on where Render looks for that file.
4. Open `https://<your-service>.onrender.com/docs` to check it. The free service sleeps after 15 minutes without traffic, and the first request afterwards takes about a minute.
5. In the site's `index.html`, set `const API = 'https://<your-service>.onrender.com';` and push the change.

