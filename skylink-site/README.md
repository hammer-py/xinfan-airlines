# SKY LINK 蓝天联盟官网

纯静态站点（HTML + CSS + 原生 JS），无框架、无构建步骤、无后端依赖。
整个目录约 **155 KB**，直接丢到 nginx 上就能跑。

## 目录结构

```
skylink-site/
├── index.html                 单页站点（首屏 / 关于 / 成员 / 权益 / 加入）
└── assets/
    ├── css/style.css          全部样式
    ├── js/main.js             导航、回到顶部、滚动动画
    └── img/
        ├── skylink-wordmark.png   官方字标（透明背景）
        ├── member-lockup.png      "a member of SKY LINK" 标识
        ├── logo-vastlake.png      广湖航空 logo
        └── logo-xinfan.png        新帆航空 logo
```

## 本地预览

```bash
python3 -m http.server 8080
# 打开 http://localhost:8080
```

直接双击 `index.html` 也能看，但用 HTTP 服务更接近线上环境。

## 部署

**线上地址**：https://skylink.199265.xyz

| 项 | 值 |
|---|---|
| 域名 | `skylink.199265.xyz`（Cloudflare 代理） |
| 服务器 | `69.12.65.118` |
| 站点根目录 | `/var/www/skylink` |
| nginx 配置 | `/etc/nginx/sites-enabled/skylink.conf` |

### 一条命令部署

服务器上首次准备好之后，每次更新只需：

```bash
cd /opt/xinfan-airlines && bash skylink-site/deploy.sh
```

它会：拉取最新代码 → `rsync` 发布到 `/var/www/skylink` → 修正属主与权限 →
同步 nginx 配置（有变化时 `nginx -t` 后 reload）→ 验证首页和两个静态资源都返回 200。

```bash
# 只看会做什么，不改任何东西
bash skylink-site/deploy.sh --dry-run

# 自定义路径/域名
WEB_ROOT=/var/www/skylink SITE_HOST=skylink.199265.xyz bash skylink-site/deploy.sh
```

### 首次部署（新服务器）

```bash
# 1. 装依赖
apt update && apt install -y nginx git rsync

# 2. 拉代码
git clone https://github.com/hammer-py/xinfan-airlines.git /opt/xinfan-airlines

# 3. 一条命令部署
cd /opt/xinfan-airlines && bash skylink-site/deploy.sh
```

脚本会自动创建 `/var/www/skylink`、写入 nginx 配置并 reload，不需要手工操作。

### HTTPS

域名已配置 Cloudflare 代理（橙色云朵），源站只监听 80 端口：

1. Cloudflare DNS：`skylink` → `A` → `69.12.65.118`，**Proxied**
2. SSL/TLS 模式选 **Flexible**（源站只监听 80）或 **Full**（源站在 443 配证书）
3. 建议开 **Always Use HTTPS** 和 **Automatic HTTPS Rewrites**

> **为什么缓存只给 1 小时**：`immutable` + 长期缓存会让一次错误的缓存（比如资源还没上传）在用户浏览器里停留很久，
> 而且服务端自测一切正常、极难排查。主站踩过这个坑。1 小时足够快，出问题也能自动恢复。

## 内容维护

需要改的地方都在 `index.html`，按注释分段：

| 区块 | 锚点 | 内容 |
|---|---|---|
| 首屏 | `#top` | 标语、按钮、三个统计数字 |
| 关于联盟 | `#about` | 联盟简介、成立日期等事实表 |
| 成员航空公司 | `#members` | 成员卡片（增删成员改这里） |
| 会员权益 | `#benefits` | 三张权益卡片 |
| 加入我们 | `#join` | 招募文案与联系方式 |
| 页脚 | — | 导航、版权 |

**新增成员**：复制 `#members` 里任意一个 `<article class="member">`，改 logo 路径、名称和描述，
把 logo 图片放进 `assets/img/`。创始成员用 `<span class="tag tag--founding">创始成员</span>`，
普通成员用 `<span class="tag">成员</span>`。

## 设计说明

- **配色**：取自 SKY LINK 标识 —— 深海军蓝 `#0b2a4a`、品牌蓝 `#1288e8`、浅空蓝 `#4fb8f0`
- **首屏**：纯 CSS 渐变 + SVG 飞机图案，比栅格图片更轻、任意宽度都无缝
- **字体**：Inter（数字/拉丁）+ 系统中文字体（PingFang / 微软雅黑），不额外加载中文字体包
- **响应式**：900px / 760px 两个断点，已验证 360 / 390 / 430 / 768 / 1440 宽度
- **无障碍**：装饰性图片 `alt=""`，导航按钮带 `aria-expanded`、`aria-controls`，
  尊重 `prefers-reduced-motion`

## 待补充

- 广湖航空（Vastlake Airline）的详细介绍、官网链接尚未提供，目前只有名称与「创始成员」标记
