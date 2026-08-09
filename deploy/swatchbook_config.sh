#!/bin/bash
# swatchbook_config.sh - per-app deploy configuration, owned by this repo.
#
# Secret-free by design, so it is safe to commit here. The release workflow
# (.github/workflows/release-deploy.yaml) rsyncs it to ~/domains/swatchbook_config.sh
# on every deploy, where activate.sh / rollback.sh source it. Real secrets live in
# shared/swatchbook/.env on the server (see www_installer's docs/BOOTSTRAP.md).
#
# There is no GITHUB_URL / FILES_TO_COPY here anymore: CI rsyncs the whole
# built tree straight into releases/<app>_<tag>/, so nothing needs to be
# fetched or itemized on the server side.

DOMAIN="swatchbook.vdwaal.net"
DOMAIN_BASE_DIR="/home/vdwanet/domains/"      # must have trailing slash
VERSION_FILE="config/__init__.py"          # file containing __version__ = "x.y.z"
PYTHON_ENV="/home/vdwanet/virtualenv/domains/swatchbook.vdwaal.net/3.11/bin/activate"
DJANGO_SETTINGS_MODULE="config.settings.prod"   # matches activate.sh's default; only needed if it ever differs

DATABASE_ENGINE="sqlite"                   # sqlite | mysql
DATABASE_SOURCE="production"               # production | repository

# Extra paths (besides db.sqlite3 and .env, handled automatically) to
# symlink from shared/<app>/ into every release. "release_path:shared_name"
# maps a nested release path to a flat name under shared/ - here,
# public_html/media (where Apache serves uploads from) maps to shared/swatchbook/media.
SHARED_PATHS=("public_html/media:media")

# Optional extra "manage.py <args>" commands run once, after migrate. Each
# is skipped (with a message, not an error) if the app version being
# activated doesn't have that command yet - matters on rollback or when
# re-activating an older tag.
# POST_MIGRATE_COMMANDS=("checklist_content import --replace --noinput")

# Used by the GitHub Actions smoke test after activation.
SMOKE_URL="https://swatchbook.vdwaal.net/"
