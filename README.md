# ✈️ 新帆航空 Xinfan Airlines

Roblox 虚拟航空公司官方网站，基于 Python + Django 全栈开发。

## 线上地址

🌐 [https://xinfan.199265.xyz](https://xinfan.199265.xyz)

## 技术栈

| 层面 | 技术 |
|------|------|
| 后端 | Django 6.0 |
| 数据库 | MySQL 8.0 |
| 前端 | Django Templates + Bootstrap 5 + Bootstrap Icons + Boxicons |
| 认证 | Django Auth + 自定义角色系统 + Cloudflare Turnstile 人机验证 |
| 部署 | Gunicorn + Nginx + Cloudflare CDN |

## 首页

- 5 张全屏轮播图，每张有独特的滑动动画（zoom / slideRight / scaleUp）
- 标题字符逐字 3D 翻转出现
- 关于我们 / 服务介绍 / 理念与目标 / 运营数据 / 社交链接
- 手机端全适配

## 角色体系（21 种）

### 用户等级

| 角色 | 说明 |
|------|------|
| 经济舱旅客 | 默认注册角色 |
| 商务舱旅客 | 中级旅客 |
| 头等舱旅客 | 高级旅客 |
| 投资者 | 公司投资者 |
| 顶级投资者 (uinv) | 最高等级旅客 |

### 员工等级

| 实习 | 正式 | 说明 |
|------|------|------|
| 实习空乘 | 正式空乘 | 客舱服务 |
| 实习副驾驶 | 正式副驾驶 | 飞行操作 |
| 实习机长 | 正式机长 | 航班执飞 |
| 实习地勤 | 正式地勤 | 地面保障 |

### 管理员（全部权限）

| 角色 | 说明 |
|------|------|
| 管理员 (admin) | 拥有全部权限 |
| HOD-部门主管 | 部门管理全权限 |
| SHR-高级管理 | 高级管理全权限 |
| Vice Chairman-副董事长 | 副董事长全权限 |
| Chairman-董事长 | 董事长全权限 |
| Group Owner-集团所有者 | 集团所有者全权限 |

### 管理员（有限权限）

| 角色 | 说明 |
|------|------|
| Flight Host-飞行经理 | 仅管理航班创建/审批报名/私人航班审批/发放里程 |

## 功能模块

### 核心（core）
- 首页：5 图轮播 + 双按钮（各 slide 不同） + 公司介绍 + 服务卡片 + 理念目标 + 统计数据
- 公司介绍：完整机队 13 架 + 私人机队 6 架 + 未来计划 + 维修中 + 三大枢纽
- 高舱俱乐部：商务舱及以上用户可见，敬请期待

### 账户（accounts）
- 注册 / 登录：Cloudflare Turnstile 人机验证
- 个人中心：个人信息、里程查看、签到活动
- 管理后台：仪表盘、人员管理（批量增删改查、搜索过滤）
- 21 种角色，完整的权限分层

### 航班（flights）
- 航班列表：支持状态/类型筛选
- 航班详情：机组人员展示 + 私人航班标识
- 航班 CRUD：管理员创建/编辑/删除航班
- 机型下拉菜单：主航 13 个机型可选
- 机组报名：员工报名参加航班（选择角色）
- 报名审批：管理员审批/拒绝报名
- 私人航班系统：商务舱+ 用户申请 → 管理员审批 → 自动创建航班
- 私人航班可见性：经济舱旅客不可见

### 招聘（recruitment）
- 职位列表 + 详情
- 用户提交申请（申请理由 + 个人经历）
- 管理员：发布/开关/删除职位
- 管理员：审核申请（标记/通过/拒绝 + 审核备注）

### 里程（mileage）
- 里程记录查看
- 里程兑换（5 种权益）
- 管理员里程发放

## 社区链接

- Discord: [discord.gg/xNCBJVPsmR](https://discord.gg/xNCBJVPsmR)
- Roblox Group: [Xinfan Airlines](https://www.roblox.com/communities/16064021/Xinfan-Airlines#!/about)

## 快速开始

```bash
git clone https://github.com/hammer-py/xinfan-airlines.git
cd xinfan-airlines
pip install -r requirements.txt
python manage.py makemigrations accounts flights recruitment mileage
python manage.py migrate
python manage.py setup_demo
python manage.py runserver 8080
```
