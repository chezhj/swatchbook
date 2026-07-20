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
- **Swatch rendering**: a polish's photo *is* its swatch — `Polish.photo_url` (the
  primary photo, else the first) becomes the tile's `background-image`. There is no
  `hex_color`; polishes with no photo yet fall back to an `.is-empty` placeholder,
  and only that placeholder wears the finish overlays from `Formula.css_class`
  (`f-holo`, `f-glitter`, …) in `frontend/src/styles/_swatch.scss`. A photo already
  shows its own finish, so painting a simulated one over it just muddies the picture.
  `Rainbow`-tagged polishes get a conic gradient via `is_rainbow`, placeholder only.
- **Vocabularies**: `Formula` and `Color` are seeded by `catalog/migrations/0002`. They
  are fixed lists — edit via admin or a new migration, never hardcode them in templates
  or JS.
- **Querysets**: use `Polish.objects.with_related()` before rendering any grid; the
  cell touches brand, formulas, colors and photos and will N+1 without it.
  `.with_last_used()` annotates the `Max("log_entries__date_worn")` the sort needs.
- **Sorting**: `?sort=` maps through an allowlist (`POLISH_SORTS` in `catalog/api.py`).
  Add new sorts there, not by passing the param through to `order_by`.
- **Grid markup exists twice**: server-rendered in `web/_swatch_cell.html` (which
  defers the tile itself to the `web/_swatch.html` partial) and client-rendered in
  `frontend/src/alpine/grid.js` (`swatchClasses` / `swatchStyle`). Keep them in step.
- **Images**: any new `ImageField` should call `resize_in_place` in `save()`.
- **Vite integration is hand-rolled**, not `django-vite`: `web/templatetags/vite.py`.
  `VITE_DEV_MODE=True` → `settings.VITE_DEV_SERVER` → the tag loads from
  `localhost:5173` with HMR; otherwise it reads the build manifest.
  **Gotcha**: `base` in `vite.config.js` applies to the dev server too, so it's `/` when
  serving and `/static/dist/` only when building. If you make `base` unconditional
  again, the dev URLs 404 and the page silently renders unstyled.
- **Polish CRUD lives in the web UI**, not just admin (`web/forms.py:PolishForm`).
  Brand and collection can be created inline from that form — a fresh install has no
  brands, so a plain dropdown would make the first polish unaddable. Keep that path
  working if you touch the form. The form **leads with photos** — a lead tile plus
  smaller slots, driven by `frontend/src/alpine/photoTile.js` for pre-save previews —
  because a photo is what the polish looks like. Don't demote them below the metadata.

## Scope

MVP + compare are built. The **randomizer is deliberately not implemented** (spec §7,
phase 2) — `/random/` is a placeholder and `/api/polishes/random/` doesn't exist. Don't
"fix" that without being asked.
