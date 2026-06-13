#!/bin/bash
# ============================================
# 新帆航空 — VPS 一键部署脚本 (Ubuntu 24.04)
# 通过 VNC 执行: bash deploy_vps.sh
# ============================================
set -e

export DEBIAN_FRONTEND=noninteractive

APP_NAME="xinfan-airlines"
APP_DIR="/opt/$APP_NAME"
DOMAIN="107.174.152.24"

echo "=========================================="
echo "  新帆航空 VPS 部署脚本"
echo "  Domain: $DOMAIN"
echo "=========================================="

# ---------- 1. 系统依赖 ----------
echo "[1/9] 安装系统依赖..."
apt update -y
apt install -y python3 python3-pip python3-venv python3-dev \
    build-essential pkg-config \
    mysql-server libmysqlclient-dev \
    nginx git curl

# ---------- 2. 克隆项目 ----------
echo "[2/9] 克隆项目..."
if [ -d "$APP_DIR" ]; then
    echo "  项目目录已存在，git pull 更新..."
    cd "$APP_DIR"
    git pull origin main
else
    git clone https://github.com/hammer-py/xinfan-airlines.git "$APP_DIR"
    cd "$APP_DIR"
fi

# ---------- 3. Python 虚拟环境 ----------
echo "[3/9] 创建虚拟环境并安装依赖..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# ---------- 4. MySQL 数据库 ----------
echo "[4/9] 配置 MySQL 数据库..."
DB_PASS=$(openssl rand -hex 16)
echo "  生成的数据库密码: $DB_PASS"

mysql -u root <<SQL
CREATE DATABASE IF NOT EXISTS xinfan CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'xinfan'@'localhost' IDENTIFIED BY '$DB_PASS';
GRANT ALL PRIVILEGES ON xinfan.* TO 'xinfan'@'localhost';
FLUSH PRIVILEGES;
SQL
echo "  MySQL 数据库和用户已创建"

# ---------- 5. 环境变量 ----------
echo "[5/9] 生成生产环境配置..."
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')

cat > "$APP_DIR/.env" <<ENV
DEBUG=False
SECRET_KEY=$SECRET_KEY
ALLOWED_HOSTS=$DOMAIN localhost 127.0.0.1
DB_NAME=xinfan
DB_USER=xinfan
DB_PASSWORD=$DB_PASS
DB_HOST=127.0.0.1
DB_PORT=3306
USE_SQLITE=false
ENV
chmod 600 "$APP_DIR/.env"
echo "  .env 文件已生成"

# ---------- 6. Django 初始化 ----------
echo "[6/9] Django 数据库迁移和静态文件..."
source venv/bin/activate
python manage.py makemigrations accounts flights recruitment mileage
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py setup_demo

# ---------- 7. Gunicorn systemd 服务 ----------
echo "[7/9] 配置 Gunicorn 系统服务..."
cat > /etc/systemd/system/xinfan.service <<UNIT
[Unit]
Description=新帆航空 Gunicorn
After=network.target mysql.service

[Service]
User=root
Group=root
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn xinfan.wsgi:application \
    --bind 127.0.0.1:8000 \
    --workers 3 \
    --access-logfile /var/log/xinfan-access.log \
    --error-logfile /var/log/xinfan-error.log

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable xinfan
systemctl restart xinfan
echo "  Gunicorn 服务已启动"

# ---------- 8. Nginx 配置 ----------
echo "[8/9] 配置 Nginx..."
cat > /etc/nginx/sites-available/xinfan.conf <<NGINX
server {
    listen 80;
    server_name $DOMAIN;

    client_max_body_size 10M;

    # 静态文件
    location /static/ {
        alias $APP_DIR/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias $APP_DIR/media/;
    }

    # 代理到 Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/xinfan.conf /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx
echo "  Nginx 已配置并启动"

# ---------- 9. 完成 ----------
echo ""
echo "=========================================="
echo "  部署完成!"
echo "=========================================="
echo "  网站地址: http://$DOMAIN"
echo "  管理后台: http://$DOMAIN/admin"
echo "  Demo 账号: 见 README"
echo ""
echo "  数据库密码: $DB_PASS"
echo "  (已保存在 $APP_DIR/.env)"
echo "=========================================="
