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

## 部署到 nginx

把整个 `skylink-site/` 目录上传到服务器，例如 `/var/www/skylink`：

```bash
scp -r skylink-site/* root@<服务器IP>:/var/www/skylink/
```

nginx 配置（`/etc/nginx/sites-enabled/skylink.conf`）：

```nginx
server {
    listen 80;
    server_name skylink.example.com;

    root /var/www/skylink;
    index index.html;

    # 静态资源缓存 1 小时（不要用 immutable + 长期，见下方说明）
    location ~* \.(css|js|png|jpg|jpeg|svg|woff2?)$ {
        expires 1h;
        add_header Cache-Control "public";
    }

    location / {
        try_files $uri $uri/ =404;
    }
}
```

```bash
nginx -t && systemctl reload nginx
```

> **为什么缓存只给 1 小时**：`immutable` + 长期缓存会让一次错误的缓存（比如资源还没上传）在用户浏览器里停留很久，
> 而且服务端自测一切正常、极难排查。1 小时足够快，出问题也能自动恢复。

### HTTPS

这个站点没有后端，用 Cloudflare 代理最省事：

1. 域名 DNS 托管到 Cloudflare，添加指向服务器 IP 的 `A` 记录
2. 打开橙色云朵（Proxied）
3. SSL/TLS 模式选 **Flexible**（源站只监听 80）或 **Full**（源站也配证书）

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
