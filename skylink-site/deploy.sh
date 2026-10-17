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

# ---- 2b. asset versioning ------------------------------------------------
# 给 HTML 里引用的静态资源加上 "?v=<内容哈希>"。
# 原因：Cloudflare 会把 /assets/* 缓存到它自己的 TTL（这里 4 小时），
# 而改 CSS 时 URL 没变，CDN 无从知道内容变了 —— 结果就是新 HTML 配旧 CSS，
# 页面样式直接错乱，且服务端自测一切正常、极难排查。
# 内容变了哈希才变，因此只在真正改动时让缓存失效。
step "Stamping asset versions"
if [ "$DRY_RUN" = "1" ]; then
    info "[dry-run] 为 index.html 中的 assets/* 追加内容哈希"
else
    cd "$WEB_ROOT"
    stamped=0
    # 先清掉旧的 ?v=，避免叠加
    sed -i -E 's#(assets/[A-Za-z0-9._/-]+\.(css|js|png|jpe?g|svg|webp))(\?v=[A-Za-z0-9]+)?#\1#g' index.html
    for f in $(grep -oE 'assets/[A-Za-z0-9._/-]+\.(css|js|png|jpe?g|svg|webp)' index.html 2>/dev/null | sort -u || true); do
        [ -f "$f" ] || continue
        hash=$(md5sum "$f" | cut -c1-8)
        sed -i "s#${f}\([\"']\)#${f}?v=${hash}\1#g" index.html
        stamped=$((stamped + 1))
    done
    cd - >/dev/null
    ok "stamped $stamped asset URLs"
fi

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
