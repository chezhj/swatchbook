# Swatchbook — Nail Polish Catalog App

Working title, rename freely. Personal, single-user catalog of a nail polish collection plus a wear log, with a compare view and a (phase 2) randomizer. Design reference: `swatchbook-mockup.html` (static HTML/CSS/JS mockup, visual reference only — not production code).

## 1. Tech stack

| Layer | Choice | Notes |
|---|---|---|
| Backend | Django + Django REST Framework | |
| Database | SQLite | Fine for a single-user, read-heavy catalog. Revisit only if this ever becomes multi-user or needs concurrent heavy writes. Keep Django migrations clean so a later move to MySQL/Postgres stays low-friction. |
| Auth | Django's built-in `User` model, session-based login | Single account, created via `createsuperuser` (or a fixture). No public registration flow. |
| Frontend | Vite + vanilla JS + SCSS + Tailwind CSS | No JS framework. |
| Interactivity layer | Alpine.js | For stateful UI: filter chips, grid selection/compare mode, forms. |
| Media | Django `MEDIA_ROOT` | Bottle photos + log photos. |
| Hosting | Existing cPanel host | Django as a Python app (Passenger); Vite build output served as static files. If frontend/backend end up on different subdomains, add `django-cors-headers` and reconsider CSRF handling; same-origin is simpler and preferred. |

App language throughout (code, DB, UI copy) is English.

## 2. Data model (Django)

```python
class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    website = models.URLField(blank=True)

class Collection(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="collections")
    name = models.CharField(max_length=150)
    year = models.PositiveSmallIntegerField(null=True, blank=True)

class Formula(models.Model):
    # fixed vocabulary, seeded via migration — see §3
    name = models.CharField(max_length=30, unique=True)

class Color(models.Model):
    # fixed vocabulary, seeded via migration — see §3
    name = models.CharField(max_length=30, unique=True)

class Tag(models.Model):
    # free-form, user-created
    name = models.CharField(max_length=40, unique=True)

class Polish(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="polishes")
    collection = models.ForeignKey(Collection, on_delete=models.SET_NULL, null=True, blank=True, related_name="polishes")
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    webshop_link = models.URLField(blank=True)
    formulas = models.ManyToManyField(Formula, related_name="polishes")
    colors = models.ManyToManyField(Color, related_name="polishes")
    tags = models.ManyToManyField(Tag, blank=True, related_name="polishes")
    catalog_code = models.CharField(max_length=20, unique=True, blank=True)  # e.g. "HT-014", can auto-generate
    in_collection = models.BooleanField(default=True)  # false = "had it, no longer own it"
    created_at = models.DateTimeField(auto_now_add=True)

class PolishPhoto(models.Model):
    polish = models.ForeignKey(Polish, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="polishes/")
    is_primary = models.BooleanField(default=False)

class LogEntry(models.Model):
    date_worn = models.DateField()
    notes = models.TextField(blank=True)
    polishes = models.ManyToManyField(Polish, through="LogEntryPolish", related_name="log_entries")

class LogEntryPolish(models.Model):
    ROLE_CHOICES = [("base", "Base"), ("topper", "Topper"), ("accent", "Accent")]
    log_entry = models.ForeignKey(LogEntry, on_delete=models.CASCADE)
    polish = models.ForeignKey(Polish, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="base")

class LogPhoto(models.Model):
    log_entry = models.ForeignKey(LogEntry, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="log/")
```

Notes:
- `Formula` and `Color` are real lookup tables (not `TextChoices`) so they can be attached via `ManyToManyField` — a polish can have several of each, per the original spec.
- `Polish.in_collection` distinguishes "currently own" from "had it before" (the brief mentions both collection *and* history of owned polish).
- `catalog_code` powers the small index-card labels used throughout the mockup (e.g. `HT-014`); can be auto-generated from brand initials + sequence on save, or left manual.

## 3. Fixed vocabularies (seed data)

**Formula** (9): Creme, Holographic, Jelly, Glitter, Magnetic, Shimmer, Metallic, Chrome, Flakie

**Color** (12): Pink, Red, Orange, Yellow/Gold, Green, Teal, Blue, Purple, Neutrals, White/Silver, Black, Rainbow

Seed both via a data migration or a `loaddata` fixture — not hardcoded in the frontend, so they stay editable from Django admin if the list ever needs a tweak.

## 4. API endpoints (DRF)

```
/api/auth/login/          POST
/api/auth/logout/         POST

/api/brands/              GET, POST
/api/collections/         GET, POST
/api/formulas/            GET
/api/colors/              GET
/api/tags/                GET, POST

/api/polishes/            GET, POST
/api/polishes/<id>/       GET, PATCH, DELETE
    ?formula=glitter&color=teal&brand=holo-taco&tag=summer
    &in_collection=true
    &sort=-last_used | name | brand | -created_at

/api/log-entries/         GET, POST
/api/log-entries/<id>/    GET, PATCH, DELETE
    ?polish=<id>&sort=-date_worn

/api/polishes/random/     GET   # randomizer — phase 2
    ?mood=beachy&season=summer
```

`django-filter` for the query-param filtering; `?sort=-last_used` needs an annotated field on `Polish` (e.g. `Max("log_entries__date_worn")`) computed in the queryset.

## 5. Screens (frontend)

Matches the mockup 1:1 — see `swatchbook-mockup.html` for the visual reference.

1. **Collection** — swatch grid (rounded-square swatches, per latest design), search + filter entry point, bottom nav.
2. **Filter sheet** — formula chips, color chips, sort options.
3. **Detail** — single polish: hero swatch, name/brand/collection, formula & color pills, tags, description, webshop link, "log this polish" CTA.
4. **Compare picker** — same grid in a multi-select mode; floating bar shows selection + "Compare →".
5. **Compare result** — two-column: bottle swatch ("in collection") vs. logged photo ("from log"), with a small attribute comparison table.
6. **Log** — chronological list of worn entries (photo, date, linked polish/polishes).
7. **Randomizer** *(phase 2)* — mood + season filters, suggests a combo pulled from existing collection data. No AI/generation — just a filtered random pick.

## 6. Design tokens (from mockup)

- Palette: ink `#15131b`, surface `#211e29`, surface-2 `#2a2632`, bone (text) `#f4f0ea`, mauve (secondary text) `#9c93a8`, mauve-dim `#655d72`.
- Signature accent: holographic gradient `linear-gradient(120deg, #6fe7dd, #e893d0, #f5d77a)` — used sparingly, for selection states and primary buttons only.
- Type: display — Fraunces (italic, for polish/screen names); UI/body — Work Sans; index/data/labels — IBM Plex Mono (catalog codes, dates, filter labels).
- Swatches render as **rounded squares**, not circles (`border-radius: ~22%` of the element).

## 7. Phasing

**MVP**
- Collection CRUD (brand, collection, polish, formula/color/tag assignment, photos)
- Filter + sort on Collection view
- Log CRUD (entries, linked polishes, photos)
- Filter + sort on Log view
- Polish detail view
- Login (single user)

**Phase 2** *(explicitly deferred per original brief)*
- Compare picker + compare result view
- Randomizer

Note: the compare flow was sketched out in detail in the original wireframes and has a full mockup screen already, so it may be worth pulling into MVP if it turns out to be low effort on top of the Log/Collection data — worth a quick call once the core models are in place.

## 8. Open items to decide during build

- Auto-generate `catalog_code` or enter manually per polish?
- Image handling: resize/compress on upload (recommended for phone photos — e.g. Pillow-based resize in a model `save()` or signal) to keep the SQLite-backed media folder manageable.
- Same-origin vs. subdomain split for frontend/backend on the cPanel host (affects CORS/CSRF setup).
