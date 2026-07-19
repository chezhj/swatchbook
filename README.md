# Swatchbook

A personal, single-user catalog of a nail polish collection plus a wear log, with a
compare view. Built from [`doc/swatchbook-spec.md`](doc/swatchbook-spec.md) and styled
after [`doc/swatchbook-mockup-v2.html`](doc/swatchbook-mockup-v2.html).

## Stack

| Layer | Choice |
|---|---|
| Backend | Django 5.2 + Django REST Framework |
| Database | SQLite |
| Auth | Django `User`, session-based, single account |
| Frontend | Django templates + Alpine.js, built with Vite (SCSS + Tailwind) |
| Media | `MEDIA_ROOT`, photos downscaled on upload |
| Deploy | cPanel / Passenger (`passenger_wsgi.py`) |

## Setup

Requires Python 3.11+, Poetry, and Node 20+.

```bash
cp .env.example .env          # then edit DJANGO_SECRET_KEY
poetry install
poetry run python manage.py migrate
poetry run python manage.py createsuperuser

cd frontend && npm install && npm run build && cd ..
```

Optionally load the sample collection from the mockup:

```bash
poetry run python manage.py seed_demo
```

## Running

```bash
poetry run python manage.py runserver
```

Then open http://127.0.0.1:8000/ and sign in.

For live-reloading frontend work, run Vite alongside Django and set
`VITE_DEV_SERVER=True` in `config/settings/dev.py`:

```bash
cd frontend && npm run dev
```

Otherwise `npm run watch` rebuilds into `web/static/dist/` on save.

## Screens

| Route | Purpose |
|---|---|
| `/` | Collection grid + filter/sort sheet |
| `/polish/new/` | Add a polish (brand/collection can be created inline) |
| `/polish/<id>/` | Polish detail |
| `/polish/<id>/edit/` | Edit or delete a polish |
| `/compare/` → `/compare/result/` | Pick two polishes, compare side by side |
| `/log/` | Wear log, newest first |
| `/log/new/` | New log entry (photos + linked polishes) |
| `/random/` | Randomizer — placeholder, phase 2 |
| `/admin/` | Bulk edits, and managing the Formula/Color vocabularies |

## API

Session-authenticated, mounted at `/api/`. See spec §4.

```
/api/polishes/?formula=glitter&color=teal&brand=holo-taco&tag=summer
              &in_collection=true&sort=-last_used
/api/log-entries/?polish=<id>&sort=-date_worn
/api/brands/  /api/collections/  /api/tags/
/api/formulas/  /api/colors/     (read-only, fixed vocabularies)
```

Sort accepts `name`, `brand`, `-created_at`, `±last_used`; anything else falls back to
`name`. Never-worn polishes sort last under `last_used`.

## Development

```bash
poetry run pytest              # 86 tests
poetry run ruff check .
poetry run black .
poetry run pre-commit install  # once, to run both on commit
```

Tests use `config.settings.test` (in-memory DB, no debug toolbar).

## Notes on the data model

Follows spec §2, with two additions the mockup requires:

- **`Polish.hex_color`** — the swatch colour. The spec's model omitted it, but every
  grid cell renders from a hex plus finish overlays.
- **`Color.hex_color`** — the filter chip dot colour.

Finish CSS classes (`f-holo`, `f-glitter`, …) are derived from the linked `Formula`
rows via `Formula.css_class`, so the fixed vocabulary stays the single source of truth
and the frontend hardcodes nothing.

`catalog_code` auto-generates as `<brand initials>-<NNN>` (e.g. `HT-014`) when left
blank, and is preserved when set manually. Generation scans existing codes rather than
counting rows, so deleting a polish can't cause a later collision.

## Deploying to cPanel

1. Set the Passenger startup file to `passenger_wsgi.py`.
2. Set `DJANGO_SETTINGS_MODULE=config.settings.prod` plus `DJANGO_SECRET_KEY` and
   `DJANGO_ALLOWED_HOSTS` in the app environment (or `.env`).
3. `poetry install --only main`, `manage.py migrate`, `manage.py collectstatic`.
4. Build the frontend (`npm run build`) and ship `web/static/dist/`.
5. Point the web server at `MEDIA_ROOT` for `/media/`.

Frontend and backend are same-origin by design, so no CORS setup is needed. If they are
ever split across subdomains, add `django-cors-headers` and revisit CSRF.

## Not built

- **Randomizer** (spec §7, SCR-07) — deferred to phase 2. The route and nav slot exist
  as a placeholder; `/api/polishes/random/` is not implemented.
