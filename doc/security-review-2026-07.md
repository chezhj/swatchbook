# Swatchbook security review — July 2026

**Target:** https://swatchbook.vdwaal.net/ (production) + source at this repo.
**Method:** static code review + local tooling (`manage.py check --deploy`, `pytest`,
`pip-audit`) + **black-box** probes of the live site (passive Phase A + active Phase B).
No credentials used. Phase B ran after a confirmed production DB backup.

## Verdict

The application is **reasonably secure** for its single-user, no-public-registration design,
and noticeably better hardened than most hobby Django deployments. Defense-in-depth is real:
every route is auth-gated at two layers, the transport/header hygiene is complete, and there
is no SQL-injection or XSS surface in the code. The findings below are hardening items, not
open holes — the most material one is an **out-of-date Pillow** with known image-processing
CVEs reachable through the photo-upload path.

## Confirmed strengths (verified at runtime)

| Check | Result |
|---|---|
| HTTP → HTTPS | `301` redirect to `https://` |
| HSTS | `max-age=31536000; includeSubDomains; preload` |
| Frame / MIME / referrer | `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin`, `Cross-Origin-Opener-Policy: same-origin` |
| CSRF cookie | `Secure; SameSite=Lax` |
| Auth enforcement | `/` → 302 `/login/`; `/polish/1/`, `/log/` → 302 `/login/`; `/api/polishes/` → **403**; `/admin/` → its own login |
| DEBUG off | bogus path → generic `404` page, no traceback or settings leak |
| Sensitive files | `/.env` → 403, `/db.sqlite3` → 404, `/.git/config` → 403, `/media/` `/static/` → 404 |
| Source not in docroot | `/manage.py`, `/passenger_wsgi.py`, `/catalog/` → 404 |
| `manage.py check --deploy` | clean under prod settings (only warning was the throwaway audit key) |
| Test suite | `pytest` green (93 tests) — includes auth-gating and `?sort=` injection-fallback tests |

Code-level: whole site behind `LoginRequiredMiddleware` with **zero** `@login_not_required`
opt-outs; DRF defaults to `IsAuthenticated` + `SessionAuthentication`, no `AllowAny`; browsable
API stripped in prod; all queries via the ORM (no raw SQL / `.extra()` / `eval`); `?sort=`
allow-listed; templates autoescape (`mark_safe` only on fixed vite content); uploads
re-encoded to JPEG (strips EXIF, neutralizes polyglots); secrets from env, prod `SECRET_KEY`
has no default (fails loud).

## Findings

### F1 — Out-of-date Pillow with reachable CVEs · Medium
`requirements.txt` pins **Pillow 11.3.0**; `pip-audit` reports **18 known CVEs**, all fixed in
Pillow **12.x**. Every uploaded photo flows through `catalog/imaging.py`
(`Image.open` → `exif_transpose` → `thumbnail` → `save`), so the subset that triggers on
`Image.open`/decode of a crafted file **is reachable via the photo-upload form**:
- PSD out-of-bounds write / memory corruption — `PYSEC-2026-2249`, `-2252`
- FITS unbounded GZIP decompression (memory-exhaustion DoS) — `PYSEC-2026-2250`
- JPEG2000 tile OOB — `PYSEC-2026-3496`
- `raw`-codec OOB when opening from a file — `PYSEC-2026-3493`

The font (PCF/BDF), `WindowsViewer` shell-injection, `ImageCms`, PDF, TGA-encoder, and
coordinate-API CVEs are **not** reachable — the app never loads fonts, does color management,
opens PDFs, saves TGA, or passes user coordinates to Pillow.

*Mitigating factor:* only the authenticated sole owner can upload, so an attacker must already
control the single account. Impact is realistically crash/DoS rather than practical RCE.

**Fix:** bump the constraint `pillow (>=11.0,<12.0)` → `>=12.3,<13.0` in `pyproject.toml`,
`poetry lock`, redeploy. Highest value-to-effort item here.

### F2 — No login rate-limiting / lockout · Low  *(confirmed in Phase B)*
No `django-axes`, `django-ratelimit`, or throttle on the login view — password guessing is
unthrottled at the app layer. **Confirmed live:** 10 consecutive failed logins all returned
`200` with steady ~0.75s timing and no `429` / `Retry-After` / lockout — neither the app nor
the host (Apache/DirectAdmin) throttles login attempts. Single-user +
`AUTH_PASSWORD_VALIDATORS` (min-length, common, numeric, similarity) blunt this, but a
lockout/backoff is cheap insurance.
**Fix:** add `django-axes` (lock after N failures) or a per-IP throttle.

### F3 — No upload size cap or decompression-bomb guard · Low
No `DATA_UPLOAD_MAX_MEMORY_SIZE` / `FILE_UPLOAD_MAX_MEMORY_SIZE` override and no
`Image.MAX_IMAGE_PIXELS` guard, so there is no ceiling on upload size or decoded pixel count.
This compounds F1's FITS/decompression angle.
**Fix:** set a sane `DATA_UPLOAD_MAX_MEMORY_SIZE` (e.g. 10–15 MB) and keep Pillow's default
`MAX_IMAGE_PIXELS` bomb check (don't disable it).

### F4 — No Content-Security-Policy header · Low
All other security headers are present, but there is no `Content-Security-Policy`. XSS risk is
already low (autoescaping, no user `mark_safe`), so CSP here is defense-in-depth.
**Fix:** add a CSP (via `django-csp` or a middleware/header). Start report-only, then enforce.

### F9 — Unauthenticated 500 emails admins (error-mail amplification) · Low
**Found in Phase B.** A malformed `multipart/form-data` POST to `/login/` returns a **500**
(generic page, *no* traceback leak — DEBUG is off). But prod logging routes `django.request`
ERROR → `AdminEmailHandler` (`config/settings/prod.py:66-72`), so every such 500 emails the
admin. An unauthenticated attacker can therefore trigger admin emails at will with a tiny
crafted request — a mailbox-flood / annoyance-DoS amplifier (and a way to bury a real error
alert in noise). The parse error should be a `400`, not a `500`.
**Fix:** catch `MultiPartParserError` (e.g. a small middleware returning `HttpResponseBadRequest`,
or upgrade/verify Django's handling) so malformed uploads yield `400` and don't page you; and/or
rate-limit `mail_admins`. Low severity — noise, not compromise.

### F5 — Host/version banners disclosed · Info
Responses expose `Server: Apache/2` and `X-Powered-By: Phusion Passenger(R) 6.0.26`. Minor
fingerprinting aid.
**Fix (optional, host-side):** unset `X-Powered-By` (`passenger_disable_security_update_check`
/ `Header unset X-Powered-By`) and `ServerTokens Prod`.

### F6 — `/config/*` redirects to the DirectAdmin panel on port 2222 (plaintext) · Info
`/config/` and any path under it (e.g. `/config/settings/prod.py`) `302` to
`http://swatchbook.vdwaal.net:2222/` — a **host-level** reserved-path redirect to the
DirectAdmin control panel, **not** an app route, and it leaks no file contents. Worth noting
only because it advertises the control panel and the redirect target is `http://` (not https).
**Fix (optional, host-side):** confirm the panel enforces HTTPS on 2222 and restrict panel
access by IP if the host allows.

### F7 — Admin at the default `/admin/` path · Info
`config/urls.py` mounts admin at `/admin/`. It's login-protected, but the default path invites
automated probing.
**Fix (optional):** move to an obscure path and/or IP-restrict at the web-server level.

### F8 — Insecure `SECRET_KEY` default committed · Info (mitigated)
`config/settings/base.py:15` and `.env.example:5` carry the literal
`"dev-insecure-key-change-me"`. **Mitigated** — `prod.py` reads `DJANGO_SECRET_KEY` with no
default and fails loudly if unset, so production cannot boot on the dev key. No action needed
beyond ensuring the real prod key is long/random (can't be verified black-box).

## Priority

1. **F1** — upgrade Pillow to ≥ 12.3 (do this first; reachable CVEs).
2. **F3** + **F2** + **F9** — upload size cap; login lockout; 400-not-500 on malformed uploads.
3. **F4** — add CSP.
4. **F5–F8** — informational / host-side hardening, at your discretion.

## Phase B results (active, black-box — run after confirmed DB backup)

| Test | Result |
|---|---|
| CSRF — POST `/login/` no token | **403** ✓ enforced |
| CSRF — POST `/login/` mismatched token | **403** ✓ enforced |
| CSRF — unsafe method (PUT) / JSON POST | **403** ✓ |
| Login rate-limiting — 10 failed logins | all `200`, ~0.75s, no throttle → **F2 confirmed** |
| Malformed multipart POST `/login/` | **500**, generic page, no leak → **F9** (emails admin) |
| Long URL / path traversal / bad method | `414` / `404` / `403`, all graceful, no traceback leak |

No authenticated fuzzing was performed (black-box). Failed-login attempts used a **non-existent**
username to avoid locking out the real account.
