## v0.10.0 (2026-08-09)

### Feat

- **web**: enlarge compare bottles to fill their column

## v0.9.1 (2026-08-05)

### Fix

- **web**: stop the photo carousel skipping past photos on a flick
- **ci**: follow redirects in deploy smoke test

## v0.9.0 (2026-08-05)

### Feat

- **web**: drive About's Retired count by tag and add Limited edition

## v0.8.0 (2026-08-05)

### Feat

- **web**: add an About page with collection stats

## v0.7.1 (2026-08-04)

### Fix

- **compare**: always show the selected polish, not its log photo

## v0.7.0 (2026-07-28)

### Feat

- **web**: add a dev-only passwordless login shortcut

### Fix

- **collection**: order groups by the active sort, not by name

## v0.6.0 (2026-07-26)

### Feat

- **catalog**: add cosmetic slugs to polish detail URLs
- **catalog**: search polishes by tag in the collection search box

## v0.5.0 (2026-07-25)

### Feat

- **catalog**: add a release date to polishes with date sorting
- **collection**: swap grid tiles to each polish's 2nd or 3rd photo
- **security**: make the admin URL configurable via DJANGO_ADMIN_URL
- **security**: send a Content-Security-Policy header in production
- **security**: throttle logins and cap request body size
- **web**: add a quick-save button to the polish and log forms
- **web**: share the photo-tile grid between polish and log forms

### Fix

- **deps**: upgrade Pillow to 12.3 to clear known image CVEs
- **config**: correct SMTP TLS setting for error mail

## v0.4.0 (2026-07-23)

### Feat

- **web**: group the collection grid and persist filters per session
- **config**: email admins on unhandled 500 errors in production

## v0.3.0 (2026-07-23)

### Feat

- **web**: tap a detail photo to view it full-size
- **web**: make the log's polish picker a type-to-search combobox
- **catalog,wearlog**: allow longer image filenames (250 chars)
- **web**: replace collection fields with a brand-scoped combobox
- **catalog**: add Thermal formula with a thermochromic swatch finish

### Fix

- **web**: keep the collection combo working for quoted names
- **config**: stop collectstatic double-collecting web/static

## v0.2.0 (2026-07-21)

### Feat

- show polishes by photo and give the log search, filters & titles
- **web**: serve the Vite dev server over the LAN, not just localhost
- add polish create/edit/delete to the web UI
- scaffold Swatchbook catalog and wear log

### Fix

- **web**: show one polish photo per view with button-sized corners
- make Vite dev mode actually serve assets
