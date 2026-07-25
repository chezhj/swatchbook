# Host-side hardening — Swatchbook

Closes the host-level items left open by `doc/security-review-2026-07.md` (F3 tail, F5, F6,
F7, F9). The app-side findings (F1–F4) are already fixed in code.

## Context

- The app runs as a **Passenger** WSGI app (`passenger_wsgi.py`) behind **Apache**. The README
  describes a cPanel host; the live control panel is **DirectAdmin** (port 2222). The Apache +
  Passenger mechanics below are identical either way — only the panel-specific bits (F6) differ.
- The one Apache lever you control on shared hosting is the **`.htaccess`** in the Passenger
  app's document root — the file that already holds the `PassengerAppRoot` / `PassengerPython`
  block. **Add custom directives *outside* the panel-managed `# Passenger …` block and keep a
  backup**, because re-saving the Python app in the panel can rewrite that block.
- `.htaccess` changes take effect on the next request (no restart). A Passenger restart
  (`touch tmp/restart.txt`) is only needed for environment/settings changes.

---

## F3 tail — hard cap on upload size

Django's `DATA_UPLOAD_MAX_MEMORY_SIZE` (now set to 5 MB) covers only form fields, not file
bytes. Cap the whole request body at Apache so oversized uploads are rejected with **413**
before they reach Python:

```apache
# reject request bodies over 15 MB (phone photos are a few MB)
LimitRequestBody 15728640
```

- Bytes; `15728640` = 15 MiB. Raise if a legitimate photo ever exceeds it.
- Verify: `curl -sS -o /dev/null -w "%{http_code}\n" -X POST --data-binary @big25mb.bin \
  https://swatchbook.vdwaal.net/login/` → `413`.
- Ref: [Apache `LimitRequestBody`](https://httpd.apache.org/docs/2.4/mod/core.html#limitrequestbody)
  (allowed in `.htaccess`, override class `All`).

---

## F5 — strip the `X-Powered-By: Phusion Passenger` banner

```apache
<IfModule mod_headers.c>
  Header always unset X-Powered-By
</IfModule>
```

- Passenger-native alternative: `PassengerShowVersionInHeader off` — but that leaves
  `X-Powered-By: Phusion Passenger`, so the `mod_headers` unset is cleaner.
- `Server: Apache/2` is already minimal; trimming further needs `ServerTokens`, which is
  server-config only (not `.htaccess`) — a root/provider change for little gain. Leave it.
- Verify: `curl -sI https://swatchbook.vdwaal.net/login/ | grep -i x-powered-by` → no output.
- Refs: [Apache `mod_headers`](https://httpd.apache.org/docs/2.4/mod/mod_headers.html),
  [Passenger `PassengerShowVersionInHeader`](https://www.phusionpassenger.com/library/config/apache/reference/#passengershowversioninheader).

---

## F7 — restrict `/admin/`

**Preferred (app-side, proxy-proof):** the admin path is now configurable via the
`DJANGO_ADMIN_URL` env var (default `admin/`). Set an unguessable value in the server's `.env`,
e.g. `DJANGO_ADMIN_URL=manage-3f9a2b/`, and the default `/admin/` becomes a 404. The secret
path lives only in `.env`, never in git. See "Reaching the admin after the rename" below.

**Optional host-side add-on (IP allowlist):** Apache 2.4 `<If>` scoped to whatever path you
chose:

```apache
<If "%{REQUEST_URI} =~ m#^/manage-3f9a2b/#">
  Require ip 203.0.113.10        # your fixed IP, or 203.0.113.0/24
</If>
```

- **Caveat — proxies:** `Require ip` matches `REMOTE_ADDR`. The `SECURE_PROXY_SSL_HEADER` in
  settings hints a proxy may front Apache; if so `REMOTE_ADDR` is the proxy, not you. Confirm
  your real IP appears in the domain's Apache access log before relying on this. (Same
  real-client-IP question applies to django-axes' IP lockout from F2.)
- Verify from a disallowed network: `curl -sS -o /dev/null -w "%{http_code}\n" \
  https://swatchbook.vdwaal.net/manage-3f9a2b/` → `403`.
- Refs: [Apache `<If>`](https://httpd.apache.org/docs/2.4/mod/core.html#if),
  [`Require ip`](https://httpd.apache.org/docs/2.4/mod/mod_authz_host.html).

---

## F9 — malformed-multipart 500 (investigate first)

The 500 is generated at the Apache/Passenger layer, **outside Django** (the error page is
Apache's, not Django's). No config one-liner fixes it; work through:

1. **Reproduce and read the logs at that timestamp:**
   ```bash
   curl -sS -o /dev/null -X POST -H "Content-Type: multipart/form-data; boundary=xyz" \
        --data-binary $'--xyz\r\nbroken' https://swatchbook.vdwaal.net/login/
   ```
   Check the domain Apache error log (`~/domains/swatchbook.vdwaal.net/logs/*.error.log` on
   DirectAdmin) and the Passenger app log named in `.htaccess` `PassengerAppLogFile`.
2. **Identify the component.** `ModSecurity` in the log ⇒ a WAF rule is rejecting the malformed
   body (protective, just the wrong status code); rule tuning is provider-controlled on shared
   hosting — raise it with them. A Passenger/Python error ⇒ the request dies in the WSGI bridge.
3. **Settle the mail question.** Check whether any Django error email actually arrived from the
   probes. If none did (likely, since Django never rendered that 500), the "admin-mail flood"
   angle is void and F9 is cosmetic. If some did, re-prioritise.
4. **Optional cosmetic:** `ErrorDocument 500 /500.html` gives a branded page; it does not fix
   the cause.
- Refs: [Passenger `PassengerAppLogFile`](https://www.phusionpassenger.com/library/config/apache/reference/#passengerapplogfile),
  [Apache `ErrorDocument`](https://httpd.apache.org/docs/2.4/mod/core.html#errordocument).

---

## F6 — DirectAdmin panel on `:2222` over http

Mostly provider-side:

- **Force HTTPS on the panel.** On DirectAdmin this is the `SSL=1` / redirect setting in
  `directadmin.conf` — a root/VPS or provider action. If hosting is managed, ask them to force
  SSL on the control panel. Self-managed: see DirectAdmin's security docs.
- **The `/config/*` → `:2222` redirect** happens above your vhost, so an app `.htaccess` rule
  likely can't intercept it. You can test `RewriteRule ^config/ - [R=404,L]`; if the redirect
  still fires it's provider-side and, at Info severity, fine to leave.

---

## After applying

Re-run the per-item `curl` checks above, or re-probe the whole surface:
`manage.py check --deploy` (app) plus the header/exposure probes from the review.
