#!/usr/bin/env bash
#
# Xinfan Airlines - one-shot deploy.
#
# Pull the latest code, refresh static files, run checks, restart the web
# service and verify it came back up.
#
# Usage:
#   bash deploy/deploy.sh            # deploy
#   bash deploy/deploy.sh --dry-run  # show what would happen
#
# Safe to re-run. Aborts on any failure rather than leaving the site in a
# half-updated state.

set -euo pipefail

# ---- configuration -------------------------------------------------------
PROJECT_DIR="${PROJECT_DIR:-/opt/xinfan-airlines}"
SERVICE="${SERVICE:-xinfan.service}"
NGINX_CONF="${NGINX_CONF:-/etc/nginx/sites-enabled/xinfan.conf}"
HEALTH_HOST="${HEALTH_HOST:-xinfan.199265.xyz}"
BRANCH="${BRANCH:-main}"

DRY_RUN=0
if [ "${1:-}" = "--dry-run" ]; then
    DRY_RUN=1
fi

# ---- helpers -------------------------------------------------------------
step()  { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
info()  { printf '    %s\n' "$*"; }
ok()    { printf '\033[1;32m    OK\033[0m %s\n' "$*"; }
warn()  { printf '\033[1;33m    WARN\033[0m %s\n' "$*"; }
die()   { printf '\033[1;31m    FAIL\033[0m %s\n' "$*" >&2; exit 1; }

run() {
    if [ "$DRY_RUN" = "1" ]; then
        printf '    [dry-run] %s\n' "$*"
    else
        "$@"
    fi
}

# ---- preflight -----------------------------------------------------------
[ -d "$PROJECT_DIR" ] || die "project dir not found: $PROJECT_DIR"
cd "$PROJECT_DIR"

[ -f manage.py ] || die "no manage.py in $PROJECT_DIR (wrong PROJECT_DIR?)"

if [ -x "$PROJECT_DIR/venv/bin/python" ]; then
    PY="$PROJECT_DIR/venv/bin/python"
elif [ -x "$PROJECT_DIR/.venv/bin/python" ]; then
    PY="$PROJECT_DIR/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PY="$(command -v python3)"
else
    die "no python interpreter found (looked for venv/bin/python and python3)"
fi

step "Configuration"
info "project : $PROJECT_DIR"
info "python  : $PY"
info "service : $SERVICE"
info "branch  : $BRANCH"
[ "$DRY_RUN" = "1" ] && warn "DRY RUN - nothing will be changed"

# ---- 1. make sure we are not clobbering local edits ----------------------
step "Checking working tree"
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
    git status --short
    die "working tree has local changes - commit or stash them first"
fi
ok "clean"

# ---- 2. pull -------------------------------------------------------------
step "Pulling latest code"
BEFORE="$(git rev-parse HEAD)"
info "before: $BEFORE"

run git fetch --quiet origin
run git checkout --quiet "$BRANCH"
run git pull --quiet --ff-only origin "$BRANCH"

AFTER="$(git rev-parse HEAD)"
info "after : $AFTER"

if [ "$BEFORE" = "$AFTER" ]; then
    ok "already up to date"
else
    ok "updated $BEFORE -> $AFTER"
    git --no-pager log --oneline "$BEFORE..$AFTER" | sed 's/^/    /'
fi

# ---- 3. dependencies (only if requirements changed) ----------------------
step "Checking dependencies"
if git diff --name-only "$BEFORE" "$AFTER" | grep -qx 'requirements.txt'; then
    warn "requirements.txt changed - installing"
    run "$PY" -m pip install -q -r requirements.txt
    ok "dependencies installed"
else
    ok "requirements.txt unchanged, skipping pip"
fi

# ---- 4. django system check ---------------------------------------------
step "Running Django system check"
if [ "$DRY_RUN" = "1" ]; then
    info "[dry-run] $PY manage.py check"
else
    if ! "$PY" manage.py check 2>&1 | sed 's/^/    /'; then
        die "django check failed - not restarting"
    fi
fi
ok "check passed"

# ---- 5. migrations -------------------------------------------------------
step "Applying migrations"
if [ "$DRY_RUN" = "1" ]; then
    info "[dry-run] $PY manage.py migrate --noinput"
else
    "$PY" manage.py migrate --noinput 2>&1 | tail -5 | sed 's/^/    /'
fi
ok "migrations applied"

# ---- 6. static files -----------------------------------------------------
step "Collecting static files"
if [ "$DRY_RUN" = "1" ]; then
    info "[dry-run] $PY manage.py collectstatic --noinput"
else
    "$PY" manage.py collectstatic --noinput 2>&1 | tail -3 | sed 's/^/    /'
fi
ok "static files collected"

# ---- 7. nginx config (optional, if it exists in the repo) ---------------
if [ -f "$PROJECT_DIR/deploy/nginx-xinfan.conf" ] && [ -f "$NGINX_CONF" ]; then
    step "Syncing nginx config"
    if cmp -s "$PROJECT_DIR/deploy/nginx-xinfan.conf" "$NGINX_CONF"; then
        ok "nginx config already in sync"
    else
        warn "nginx config differs - updating $NGINX_CONF"
        run cp "$PROJECT_DIR/deploy/nginx-xinfan.conf" "$NGINX_CONF"
        if [ "$DRY_RUN" = "1" ]; then
            info "[dry-run] nginx -t && systemctl reload nginx"
        else
            nginx -t 2>&1 | sed 's/^/    /' || die "nginx -t failed"
            systemctl reload nginx
            ok "nginx reloaded"
        fi
    fi
fi

# ---- 8. restart the web service -----------------------------------------
step "Restarting $SERVICE"
run systemctl restart "$SERVICE"
info "waiting for it to come back up"
sleep 3
if [ "$DRY_RUN" = "1" ]; then
    info "[dry-run] systemctl is-active $SERVICE"
else
    STATE="$(systemctl is-active "$SERVICE" || true)"
    [ "$STATE" = "active" ] || die "$SERVICE is $STATE after restart"
    ok "service is active"
fi

# ---- 9. health check -----------------------------------------------------
step "Health check"
if [ "$DRY_RUN" = "1" ]; then
    info "[dry-run] curl / and /about/"
else
    for path in / /about/; do
        CODE="$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 \
                -H "Host: $HEALTH_HOST" "http://127.0.0.1$path" || echo 000)"
        if [ "$CODE" = "200" ]; then
            ok "GET $path -> $CODE"
        else
            die "GET $path -> $CODE"
        fi
    done
fi

# ---- done ----------------------------------------------------------------
step "Done"
if [ "$DRY_RUN" = "1" ]; then
    warn "DRY RUN finished - nothing was changed"
else
    ok "deployed $AFTER"
    info "site: https://$HEALTH_HOST/"
fi
