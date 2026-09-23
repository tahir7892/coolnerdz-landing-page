#!/usr/bin/env bash
# Update the CoolNerdz server in place: pull the latest code, install
# dependencies, back up the database, migrate, collect static files, restart
# Gunicorn, reload Nginx, and smoke-test the site.
#
# Run on the server as root (or a user with sudo):
#   sudo ./deploy.sh              # pull origin/main and deploy
#   sudo ./deploy.sh --no-pull    # deploy the code already on disk
#   sudo ./deploy.sh --skip-tests # skip the Django test suite
#
# The frontend (templates + static/) and the backend (Django + DRF API) are
# one app, so a single deploy updates both.

set -Eeuo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_USER="coolnerdz"
SERVICE="coolnerdz-django"
BRANCH="main"
SOCKET="/run/coolnerdz/gunicorn.sock"
BACKUP_KEEP=10

PULL=1
RUN_TESTS=1
for arg in "$@"; do
  case "$arg" in
    --no-pull) PULL=0 ;;
    --skip-tests) RUN_TESTS=0 ;;
    -h|--help) sed -n '2,13p' "$0"; exit 0 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done

step() { printf '\n\033[1;32m==> %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m!!  %s\033[0m\n' "$*" >&2; }
fail() { printf '\033[1;31mxx  %s\033[0m\n' "$*" >&2; exit 1; }
trap 'fail "Deploy failed on line $LINENO. The previous Gunicorn process keeps running unless the restart step was reached."' ERR

SUDO=""
[ "$(id -u)" -eq 0 ] || SUDO="sudo"
as_app() { sudo -u "$APP_USER" -- "$@"; }

cd "$APP_DIR"
PY="$APP_DIR/env/bin/python"
# Django loads .env itself; the script only needs a couple of values from it.
env_value() { grep -E "^$1=" .env | tail -n 1 | cut -d= -f2- | tr -d '"'"'"; }

[ -f .env ] || fail ".env is missing in $APP_DIR (copy .env.example and fill it in)."

if [ "$PULL" -eq 1 ]; then
  step "Pulling origin/$BRANCH"
  if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
    warn "Working tree has local changes; the pull only succeeds if they don't conflict:"
    git status --short --untracked-files=no >&2
  fi
  git fetch --prune origin "$BRANCH"
  git merge --ff-only "origin/$BRANCH"
  git log -1 --format='Now at %h  %s (%cr)'
fi

step "Installing Python dependencies"
[ -x "$PY" ] || python3 -m venv env
env/bin/pip install --quiet --upgrade pip
env/bin/pip install --quiet -r requirements.txt

step "Running Django checks"
"$PY" manage.py check --deploy --fail-level ERROR
if [ "$RUN_TESTS" -eq 1 ]; then
  step "Running tests"
  "$PY" manage.py test --noinput
fi

if [ -f db.sqlite3 ]; then
  step "Backing up the database"
  backup="db.sqlite3.backup-$(date +%Y%m%d-%H%M%S)"
  cp -p db.sqlite3 "$backup"
  chmod 600 "$backup"
  echo "Saved $backup"
  # Keep only the newest $BACKUP_KEEP backups.
  ls -1t db.sqlite3.backup-* 2>/dev/null | tail -n +$((BACKUP_KEEP + 1)) | xargs -r rm -f --
fi

step "Applying migrations"
# Run as the app user so SQLite journal files stay owned by it.
as_app "$PY" manage.py migrate --noinput

step "Collecting static files"
"$PY" manage.py collectstatic --noinput

step "Installing systemd unit and restarting $SERVICE"
if ! cmp -s deploy/coolnerdz-django.service "/etc/systemd/system/$SERVICE.service"; then
  $SUDO install -m 644 deploy/coolnerdz-django.service "/etc/systemd/system/$SERVICE.service"
  $SUDO systemctl daemon-reload
  echo "Unit file updated."
fi
$SUDO systemctl restart "$SERVICE"

step "Reloading Nginx"
$SUDO nginx -t
$SUDO systemctl reload nginx

step "Smoke-testing the site"
allowed="$(env_value DJANGO_ALLOWED_HOSTS)"
host="$(printf '%s' "${allowed:-coolnerdz.com}" | cut -d, -f1 | tr -d ' ')"
ok=0
for _ in $(seq 1 15); do
  if code="$(curl -s -o /dev/null -w '%{http_code}' --unix-socket "$SOCKET" \
        -H "Host: $host" -H 'X-Forwarded-Proto: https' "http://$host/")" && [ "$code" = 200 ]; then
    ok=1; break
  fi
  sleep 1
done
if [ "$ok" -ne 1 ]; then
  $SUDO journalctl -u "$SERVICE" -n 30 --no-pager >&2 || true
  fail "Gunicorn did not answer 200 on $SOCKET (last status: ${code:-none})."
fi
echo "Gunicorn: 200"

site="$(env_value SITE_URL)"
site="${site:-https://$host}"
site="${site%/}"
for path in / /static/css/style.css /api/waitlist; do
  code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$site$path" || true)"
  [ "$code" = 200 ] && echo "$site$path: $code" || warn "$site$path returned ${code:-no response}"
done

trap - ERR
step "Deploy complete: $(git log -1 --format='%h %s' 2>/dev/null || echo 'code on disk')"
