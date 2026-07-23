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
