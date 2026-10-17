#!/usr/bin/env bash
#
# SKY LINK - one-shot deploy (static site).
#
# Pull the latest code, publish the files to the web root, sync the nginx
# vhost and verify the site responds.
#
# Usage:
#   bash skylink-site/deploy.sh            # deploy
#   bash skylink-site/deploy.sh --dry-run  # show what would happen
#
# Safe to re-run: rsync only touches files that actually changed.

set -euo pipefail

# ---- configuration -------------------------------------------------------
WEB_ROOT="${WEB_ROOT:-/var/www/skylink}"
NGINX_CONF="${NGINX_CONF:-/etc/nginx/sites-enabled/skylink.conf}"
SITE_HOST="${SITE_HOST:-skylink.199265.xyz}"
BRANCH="${BRANCH:-main}"

# 脚本所在目录 = 仓库里的 skylink-site/
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SRC_DIR/.." && pwd)"

DRY_RUN=0
if [ "${1:-}" = "--dry-run" ]; then
    DRY_RUN=1
fi

# ---- helpers -------------------------------------------------------------
step() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
info() { printf '    %s\n' "$*"; }
ok()   { printf '\033[1;32m    OK\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m    WARN\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31m    FAIL\033[0m %s\n' "$*" >&2; exit 1; }

run() {
    if [ "$DRY_RUN" = "1" ]; then
        printf '    [dry-run] %s\n' "$*"
    else
        "$@"
    fi
}

need_root() {
    [ "$(id -u)" = "0" ] || die "please run as root (or with sudo)"
}

# ---- preflight -----------------------------------------------------------
step "Configuration"
info "source   : $SRC_DIR"
info "web root : $WEB_ROOT"
info "nginx    : $NGINX_CONF"
info "host     : $SITE_HOST"
[ "$DRY_RUN" = "1" ] && warn "DRY RUN - nothing will be changed"

[ -f "$SRC_DIR/index.html" ] || die "index.html not found in $SRC_DIR"

# dry-run 不写任何东西，所以不要求 root
if [ "$DRY_RUN" != "1" ]; then
    need_root
fi

command -v rsync >/dev/null 2>&1 || die "rsync not installed (apt install rsync)"
command -v nginx >/dev/null 2>&1 || die "nginx not installed (apt install nginx)"

# ---- 1. pull latest ------------------------------------------------------
step "Pulling latest code"
cd "$REPO_DIR"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
    warn "not a git repository - skipping pull, deploying current files"
else
    BEFORE="$(git rev-parse HEAD)"
    info "before: $BEFORE"
    run git fetch --quiet origin
    run git pull --quiet --ff-only origin "$BRANCH"
    AFTER="$(git rev-parse HEAD)"
    info "after : $AFTER"
    if [ "$BEFORE" = "$AFTER" ]; then
        ok "already up to date"
    else
        ok "updated $BEFORE -> $AFTER"
        git --no-pager log --oneline "$BEFORE..$AFTER" | sed 's/^/    /'
    fi
fi

# ---- 2. publish files ----------------------------------------------------
step "Publishing to $WEB_ROOT"
run mkdir -p "$WEB_ROOT"
if [ "$DRY_RUN" = "1" ]; then
    info "[dry-run] rsync -a --delete $SRC_DIR/ $WEB_ROOT/"
else
    # 排除部署/说明文件，它们不需要对外提供
    rsync -a --delete \
        --exclude 'deploy.sh' \
        --exclude 'nginx-skylink.conf' \
        --exclude 'README.md' \
        "$SRC_DIR/" "$WEB_ROOT/"
fi
ok "files published"

# ---- 3. permissions ------------------------------------------------------
step "Setting permissions"
run chown -R www-data:www-data "$WEB_ROOT"
run find "$WEB_ROOT" -type d -exec chmod 755 {} +
run find "$WEB_ROOT" -type f -exec chmod 644 {} +
ok "permissions set"

# ---- 4. nginx vhost ------------------------------------------------------
step "Syncing nginx vhost"
if [ -f "$SRC_DIR/nginx-skylink.conf" ]; then
    if [ -f "$NGINX_CONF" ] && cmp -s "$SRC_DIR/nginx-skylink.conf" "$NGINX_CONF"; then
        ok "vhost already in sync"
    else
        run cp "$SRC_DIR/nginx-skylink.conf" "$NGINX_CONF"
        if [ "$DRY_RUN" = "1" ]; then
            info "[dry-run] nginx -t && systemctl reload nginx"
        else
            nginx -t 2>&1 | sed 's/^/    /' || die "nginx -t failed"
            systemctl reload nginx
            ok "vhost updated, nginx reloaded"
        fi
    fi
else
    warn "nginx-skylink.conf not found in repo, skipping"
fi

# ---- 5. health check -----------------------------------------------------
step "Health check"
if [ "$DRY_RUN" = "1" ]; then
    info "[dry-run] curl http://127.0.0.1/ -H 'Host: $SITE_HOST'"
else
    CODE="$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 \
            -H "Host: $SITE_HOST" http://127.0.0.1/ || echo 000)"
    [ "$CODE" = "200" ] || die "GET / -> $CODE"
    ok "GET / -> $CODE"

    # 抽两张图片确认静态资源也通
    for asset in assets/css/style.css assets/img/skylink-wordmark.png; do
        CODE="$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 \
                -H "Host: $SITE_HOST" "http://127.0.0.1/$asset" || echo 000)"
        [ "$CODE" = "200" ] || die "GET /$asset -> $CODE"
        ok "GET /$asset -> $CODE"
    done
fi

# ---- done ----------------------------------------------------------------
step "Done"
if [ "$DRY_RUN" = "1" ]; then
    warn "DRY RUN finished - nothing was changed"
else
    ok "deployed to $WEB_ROOT"
    info "site: https://$SITE_HOST/"
fi
