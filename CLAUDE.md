# Swatchbook — notes for Claude

Personal nail polish catalog + wear log. Single user, no public registration.
Source of truth for intent: `doc/swatchbook-spec.md`. Visual reference:
`doc/swatchbook-mockup-v2.html` (static mockup, not production code).

## Commands

```bash
poetry run python manage.py runserver
poetry run python manage.py seed_demo     # sample data from the mockup
poetry run pytest
poetry run ruff check . && poetry run black .
cd frontend && npm run build              # or: npm run watch
```

Verification commands: prefer the PowerShell tool. The Bash tool swallows stdout from
`python -c` in this environment.

## Layout

- `config/` — settings split into `base` / `dev` / `prod` / `test`; `api_urls.py` holds
  the DRF router.
- `catalog/` — Brand, Collection, Formula, Color, Tag, Polish, PolishPhoto. Also
  `imaging.py` (shared Pillow resize) and `filters.py`.
- `wearlog/` — LogEntry, LogEntryPolish, LogPhoto.
- `web/` — template views, templates, the `vite` template tag, `seed_demo`.
- `frontend/` — Vite. SCSS in `src/styles/`, Alpine components in `src/alpine/`.
- `tests/` — pytest, split by layer.

## Conventions

- **URL names**: web routes use underscores (`polish_detail`), because the DRF router
  already owns the hyphenated names (`polish-detail`). Don't collide them.
- **Auth**: `LoginRequiredMiddleware` protects everything. Use `@login_not_required`
  to open a view up rather than adding exemptions to the middleware.
- **Swatch rendering**: `Polish.hex_color` is the base; finish overlays come from
  `Formula.css_class` (`f-holo`, `f-glitter`, …) matching `frontend/src/styles/_swatch.scss`.
  A polish tagged with the `Rainbow` colour renders as a conic gradient via `is_rainbow`.
- **Vocabularies**: `Formula` and `Color` are seeded by `catalog/migrations/0002`. They
  are fixed lists — edit via admin or a new migration, never hardcode them in templates
  or JS.
- **Querysets**: use `Polish.objects.with_related()` before rendering any grid; the
  cell touches brand, formulas, colors and photos and will N+1 without it.
  `.with_last_used()` annotates the `Max("log_entries__date_worn")` the sort needs.
- **Sorting**: `?sort=` maps through an allowlist (`POLISH_SORTS` in `catalog/api.py`).
  Add new sorts there, not by passing the param through to `order_by`.
- **Grid markup exists twice**: server-rendered in `web/_swatch_cell.html` and
  client-rendered in `frontend/src/alpine/grid.js`. Keep the two in step.
- **Images**: any new `ImageField` should call `resize_in_place` in `save()`.

## Scope

MVP + compare are built. The **randomizer is deliberately not implemented** (spec §7,
phase 2) — `/random/` is a placeholder and `/api/polishes/random/` doesn't exist. Don't
"fix" that without being asked.
