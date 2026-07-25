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

### F1 — Out-of-date Pillow with reachable CVEs · Medium  ✅ FIXED
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

**Fixed:** bumped the constraint to `pillow (>=12.3,<13.0)`, relocked (Pillow 12.3.0). `pip-audit`
now reports **no known vulnerabilities**; the imaging tests pass unchanged.

### F2 — No login rate-limiting / lockout · Low  ✅ FIXED
No `django-axes`, `django-ratelimit`, or throttle on the login view — password guessing was
unthrottled at the app layer. **Confirmed live:** 10 consecutive failed logins all returned
`200` with steady ~0.75s timing and no `429` / `Retry-After` / lockout — neither the app nor
the host (Apache/DirectAdmin) throttled login attempts.
**Fixed:** added `django-axes` (`AXES_FAILURE_LIMIT=5`, `AXES_COOLOFF_TIME=1h`, lock by IP and
username, reset on success). Verified locally: the 5th failed login onward returns `429`; a
valid login clears the counter. Deploy note: run `manage.py migrate` (axes adds tables); if a
reverse proxy fronts the app, configure `django-ipware` so axes sees the real client IP.

### F3 — No upload size cap or decompression-bomb guard · Low  ✅ PARTLY FIXED
No `DATA_UPLOAD_MAX_MEMORY_SIZE` override, so there was no ceiling on the non-file request body.
**Fixed:** set `DATA_UPLOAD_MAX_MEMORY_SIZE = 5 MB`. Verified locally: a 6 MB form POST → `400`
(`RequestDataTooBig`), normal login unaffected. Pillow's default `MAX_IMAGE_PIXELS` bomb check
is left enabled (F1's upgrade keeps it).
**Still open (host-side):** file-upload *bytes* are exempt from `DATA_UPLOAD_MAX_MEMORY_SIZE`
by Django design, so a hard cap on total photo size should be set at the web server
(Apache `LimitRequestBody`).

### F4 — No Content-Security-Policy header · Low  ✅ FIXED
All other security headers were present but there was no `Content-Security-Policy`.
**Fixed:** added `web.middleware.ContentSecurityPolicyMiddleware`, which attaches a static
policy from `settings.CSP_POLICY` (set in `prod.py`, unset elsewhere so the Vite dev server is
untouched). The policy locks `script`/`frame`/`object`/`connect` to `'self'` (only Google Fonts
is allowed for CSS/fonts); `'unsafe-eval'` is required by Alpine and `'unsafe-inline'` by the
templates' inline `style="…"` attributes, so those remain but everything else is origin-locked.
**Verified** in a browser under the enforced policy: header present, Alpine 3.15 runs, fonts
load, the grid/API-filter/photo-preview paths all work, and zero CSP violations across login,
collection, the photo form, and detail pages.

### F9 — Malformed multipart POST to `/login/` returns 500 · Low  · host-level, needs investigation
**Found in Phase B, re-characterised on follow-up.** A malformed `multipart/form-data` POST to
`/login/` returns a **500**. On closer inspection the 500 body is an **Apache/Passenger error
page** (`Content-Type: text/html; charset=iso-8859-1`, "contact webmaster@vdwaal.net") — *not*
a Django 500 page. The error is generated at the **Apache/Passenger layer, outside Django**:
- Django 5.2.16 does **not** raise on the malformed multipart bodies tested — it parses them to
  empty and the request ends at CSRF (`403`). The 500 could not be reproduced in Django at all.
- Because it isn't a Django-rendered 500, the earlier "emails the admins" conclusion is
  **unconfirmed** — an Apache-level 500 does not reach Django's `django.request` → `mail_admins`
  path. *Action:* check whether any Django error-mail actually arrived during the probes; if
  none did, the mail-flood angle is void.

**Not fixable in Django.** A Django `MalformedUploadMiddleware` was prototyped and **dropped** —
it can't intercept an error Django never sees, and no reachable Django-level 500 exists to guard.
**Fix (host-side):** investigate why Passenger/Apache/mod_security returns 500 on a malformed
multipart body (vs. a `400`), and confirm the admin-mail question above. Low severity — noise at
most, not compromise.

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

### F7 — Admin at the default `/admin/` path · Info  ✅ CONFIGURABLE (set in prod .env)
`config/urls.py` mounted admin at `/admin/` — login-protected, but the default path invites
automated probing.
**Done in code:** the admin path is now `settings.ADMIN_URL`, read from `DJANGO_ADMIN_URL`
(default `admin/`). **Action:** set `DJANGO_ADMIN_URL` to an unguessable path in the production
`.env`; the default `/admin/` then 404s. Optional IP allowlist for that path is in
`doc/host-hardening.md`. The secret path lives only in `.env`, never in git.

### F8 — Insecure `SECRET_KEY` default committed · Info (mitigated)
`config/settings/base.py:15` and `.env.example:5` carry the literal
`"dev-insecure-key-change-me"`. **Mitigated** — `prod.py` reads `DJANGO_SECRET_KEY` with no
default and fails loudly if unset, so production cannot boot on the dev key. No action needed
beyond ensuring the real prod key is long/random (can't be verified black-box).

## Priority

- ✅ **F1** — Pillow upgraded to 12.3 (commit `637cc35`).
- ✅ **F2** + **F3** — django-axes login lockout; `DATA_UPLOAD_MAX_MEMORY_SIZE` cap.
- ✅ **F4** — Content-Security-Policy header (`ContentSecurityPolicyMiddleware`).
- **Open — host-side:** **F9** (investigate the Apache/Passenger 500 on malformed multipart);
  **F3** tail (Apache `LimitRequestBody` for file-body size); **F5–F7** banners / panel / admin
  path. **F8** is mitigated, no action.

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
