# 服务器部署说明（xinfan.199265.xyz）

目标提交：`3c6fb18`（GitHub `main` 已是这个版本，服务器 pull 即得到）

---

## ⚠️ 顺序很重要，别反过来

新代码的 `settings.py` 是「缺配置就拒绝启动」的。而服务器上现在**没有**任何
Turnstile 环境变量（密钥原本硬编码在 `apps/accounts/views.py` 里）。

**所以：必须先补 `.env`，再 `git pull`。** 顺序反了站点会直接起不来。

---

## 步骤

```bash
cd <项目目录>              # 存放 manage.py 的目录

# 1. 备份环境配置
cp -a .env .env.bak.$(date +%Y%m%d%H%M%S)

# 2. 检查这几个键是否已存在，缺的补上
cat .env
```

`.env` 必须包含（缺哪个补哪个，已有的不要动）：

```ini
DEBUG=False
SECRET_KEY=<随机长串>
ALLOWED_HOSTS=xinfan.199265.xyz www.xinfan.199265.xyz 127.0.0.1 localhost
TURNSTILE_SITE_KEY=0x4AAAAAADnKla0lQkl2FCZM
TURNSTILE_SECRET_KEY=0x4AAAAAADnKlcEsR3ju3SUhf65od20RxUU
```

生成 `SECRET_KEY`：

```bash
python3 -c "import secrets;print(secrets.token_urlsafe(64))"
```

> `TURNSTILE_SITE_KEY` 是前端站点密钥，`TURNSTILE_SECRET_KEY` 是服务端私钥，
> 两者**必须成对**。只配一个会导致登录/注册的人机验证失败，用户无法登录。

```bash
# 3. 拉代码
git pull

# 4. 先自检，这一步有任何 error 就先别往下走
source venv/bin/activate        # 或 .venv/bin/activate，按实际情况
python manage.py check

# 5. 数据库迁移 + 静态文件
python manage.py migrate
python manage.py collectstatic --noinput

# 6. 清掉上次泄漏的订阅地址（该文件在仓库里已清，服务器上可能还有残留）
sed -i '/subscribe?token/d' 5245070195fc163a6d7e3927ecac8193.txt
cat 5245070195fc163a6d7e3927ecac8193.txt   # 应该只剩一行校验串

# 7. 重启服务
systemctl restart <你的服务名>

# 8. 验证
curl -s -o /dev/null -w "%{http_code}\n" -H "Host: xinfan.199265.xyz" http://127.0.0.1/
curl -s -H "Host: xinfan.199265.xyz" http://127.0.0.1/5245070195fc163a6d7e3927ecac8193.txt
journalctl -u <你的服务名> -n 30 --no-pager
```

---

## 部署后怎么确认真的生效了

用**未登录**的浏览器（或无痕窗口）打开：

- `https://xinfan.199265.xyz/hkhos-demo/` → 应该**跳回首页**并提示「页面不存在」
  - 如果仍是 200 能打开，说明代码没更新成功
- `https://xinfan.199265.xyz/login/` → 验证码应正常显示
  - 验证码空白/报错 → `TURNSTILE_SITE_KEY` 没配对
  - 提交时提示「人机验证失败」→ `TURNSTILE_SECRET_KEY` 没配对

---

## 部署后请务必做的一件事

**改掉 `admin` 的密码。** `apps/accounts/management/commands/setup_demo.py` 会创建
超级用户 `admin / admin123`。如果这个命令在生产库上跑过，那个弱口令现在仍然有效，
可以直接登录 `/admin/`。

```bash
python manage.py changepassword admin
```

顺便检查一下有没有多余的演示账号（`pilot001`、`biz001`、`vip001` 等）：

```bash
python manage.py shell -c "from django.contrib.auth.models import User; print([u.username for u in User.objects.all()])"
```

---

## 另一个建议：作废泄漏的 token

`5245070195fc163a6d7e3927ecac8193.txt` 里那行订阅地址的 token
（`f6c40a97...b9d0`）已经进过公开的 git 历史，**删文件不能让它变回安全**。
建议在服务商后台重新生成订阅链接。

---

## 顺带一提（不影响本次部署）

如果以后要动这些地方，注意：

- `settings.py` 现在会在生产环境强制要求 `SECRET_KEY` / `ALLOWED_HOSTS`，
  且 `CSRF_TRUSTED_ORIGINS` 会自动从 `ALLOWED_HOSTS` 推导并补上 `https://`。
  以前那版是直接拿裸域名当 origin，Django 会抛 `4_0.E001` 让所有 POST 失败。
- 本次修复了一个真实 bug：`datetime-local` 提交的时间原本按 naive datetime 存库，
  导致所有航班时间在页面上**偏移 8 小时**（时区为 Asia/Shanghai）。
  修复后新建/编辑的航班时间是对的，但**数据库里已有的旧航班仍是错误时间**，
  需要修正。表现是：管理员当初录入 10:00，现在页面上显示成 18:00，编辑框里也是 18:00。

  修正办法（运行前先备份数据库）：

  ```bash
  # 先只看，确认确实是 +8 小时
  python manage.py shell -c "
  from apps.flights.models import Flight
  for f in Flight.objects.all():
      print(f.flight_number, f.departure_time, '->', f.arrival_time)
  "
  ```

  确认后统一减 8 小时（**只跑一次**，重复跑会多减）：

  ```bash
  python manage.py shell -c "
  from datetime import timedelta
  from apps.flights.models import Flight, PrivateFlightRequest
  n = 0
  for f in Flight.objects.all():
      f.departure_time -= timedelta(hours=8)
      f.arrival_time -= timedelta(hours=8)
      f.save()
      n += 1
  print('flights fixed:', n)
  n = 0
  for r in PrivateFlightRequest.objects.all():
      r.departure_time -= timedelta(hours=8)
      r.arrival_time -= timedelta(hours=8)
      r.save()
      n += 1
  print('requests fixed:', n)
  "
  ```

  > 注意：`Flight.save()` 会在状态变化时更新 `status_changed_at`，但这里状态没变，
  > 所以不受影响。跑完记得再核对一遍时间。
