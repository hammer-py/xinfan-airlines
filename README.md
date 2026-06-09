# ✈️ 新帆航空 Xinfan Airlines

Roblox 虚拟航空公司官方网站，基于 Python + Django 全栈开发，支持 14 种角色体系、航班管理、机组报名、招聘系统、里程系统。

## 线上地址

🌐 [http://107.174.152.24](http://107.174.152.24)

## 技术栈

| 层面 | 技术 |
|------|------|
| 后端 | Django 6.0 |
| 数据库 | SQLite（开发）/ MySQL 8.0（生产） |
| 前端 | Django Templates + Bootstrap 5 + Bootstrap Icons |
| 认证 | Django Auth + 自定义角色系统 |
| 部署 | Gunicorn + Nginx（待配置） |

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/hammer-py/xinfan-airlines.git
cd xinfan-airlines
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 数据库迁移

```bash
python manage.py makemigrations accounts flights recruitment mileage
python manage.py migrate
```

### 4. 初始化演示数据

```bash
python manage.py setup_demo
```

### 5. 启动开发服务器

```bash
python manage.py runserver 8080
```

访问 `http://127.0.0.1:8080`

## 角色体系（14 种）

### 用户等级

| 角色 | 说明 |
|------|------|
| 经济舱旅客 | 默认注册角色 |
| 商务舱旅客 | 中级旅客 |
| 头等舱旅客 | 高级旅客 |
| 投资者 | 公司投资者 |
| 顶级投资者 | 最高等级旅客 |

### 员工等级

| 实习 | 正式 | 说明 |
|------|------|------|
| 实习空乘 | 正式空乘 | 客舱服务 |
| 实习副驾驶 | 正式副驾驶 | 飞行操作 |
| 实习机长 | 正式机长 | 航班执飞 |
| 实习地勤 | 正式地勤 | 地面保障 |

### 管理员

| 角色 | 说明 |
|------|------|
| 管理员 | 拥有全部权限 |

## 功能模块

### 核心（core）
- 首页：公司标语 + 最新航班快览
- 公司介绍：机队、运营数据、联系方式

### 账户（accounts）
- 注册 / 登录 / 登出
- 个人中心：个人信息、里程查看
- 管理后台：仪表盘、人员角色管理

### 航班（flights）
- 航班列表：支持状态/类型筛选
- 航班详情：机组人员展示
- 航班 CRUD：管理员创建/编辑/删除航班
- 机组报名：员工报名参加航班（选择角色）
- 报名审批：管理员审批/拒绝报名

### 招聘（recruitment）
- 职位列表 + 详情
- 用户提交申请（申请理由 + 个人经历）
- 管理员：发布/开关/删除职位
- 管理员：审核申请（标记/通过/拒绝 + 审核备注）

### 里程（mileage）
- 里程记录查看
- 里程兑换（优先登机、贵宾室、头衔、免费航班券）
- 管理员里程发放

## 预置演示账户

运行 `python manage.py setup_demo` 后生成：

### 员工账户（密码均为 pilot123）

| 用户名 | 角色 |
|--------|------|
| pilot001 | 正式机长 |
| copilot01 | 正式副驾驶 |
| trainee_pilot | 实习副驾驶 |
| cabin01 | 正式空乘 |
| trainee_cabin | 实习空乘 |
| ground01 | 正式地勤 |
| trainee_ground | 实习地勤 |

### 旅客账户（密码均为 user123）

| 用户名 | 角色 |
|--------|------|
| user001 | 经济舱旅客 |
| biz001 | 商务舱旅客 |
| first001 | 头等舱旅客 |
| investor01 | 投资者 |
| vip001 | 顶级投资者 |

### 管理员

| 用户名 | 密码 |
|--------|------|
| admin | admin123 |

## 项目结构

```
xinfan-airlines/
├── manage.py
├── requirements.txt
├── xinfan/                    # Django 配置
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── core/                  # 首页 + 公司介绍
│   ├── accounts/              # 认证 + 角色 + 个人中心 + 管理后台
│   ├── flights/               # 航班管理 + 机组报名
│   ├── recruitment/           # 招聘 + 申请
│   └── mileage/               # 里程系统
├── templates/
│   └── base.html              # 全局基础模板
└── static/
```

## 生产部署

```bash
# 构建静态文件
python manage.py collectstatic

# 使用 Gunicorn（MySQL 环境变量）
DB_PASSWORD=xxx gunicorn xinfan.wsgi -b 0.0.0.0:8000
```

生产环境推荐搭配 Nginx 反向代理 + MySQL 数据库。

## 许可

MIT
