"""一次性数据体检：确认时区修复后没有残留的脏数据。

只读，不修改任何数据。跑完确认没问题后可以删除本文件。

    python manage.py audit_data
"""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from apps.accounts.models import ADMIN_ROLES
from apps.flights.models import Flight, FlightCrewSignup, PrivateFlightRequest


class Command(BaseCommand):
    help = '只读检查航班/私人申请是否有时间脏数据，以及账号权限是否错位'

    def handle(self, *args, **options):
        say = self.stdout.write

        # ── 1. 航班与私人申请 ──────────────────────────
        flights = Flight.objects.count()
        requests = PrivateFlightRequest.objects.count()

        say('== 航班数据 ==')
        say('航班总数      : %d' % flights)
        say('私人航班申请数: %d' % requests)
        say('机组报名数    : %d' % FlightCrewSignup.objects.count())
        say('')

        if flights:
            say('-- 最近 20 个航班（对照你当初录入的时间）--')
            for f in Flight.objects.all()[:20]:
                say('%s | %s -> %s | %s' % (
                    f.flight_number, f.departure_time, f.arrival_time, f.status))
        else:
            say('航班表为空，没有时间脏数据需要修正。')
        say('')

        if requests:
            say('-- 全部私人航班申请 --')
            for r in PrivateFlightRequest.objects.all()[:20]:
                say('%s | %s | %s -> %s | %s' % (
                    r.flight_number, r.user.username,
                    r.departure_time, r.arrival_time, r.status))
        else:
            say('私人航班申请表为空。')
        say('')

        # ── 2. 账号与权限 ──────────────────────────────
        total_users = User.objects.count()
        say('== 账号 ==')
        say('注册用户总数: %d' % total_users)
        say('')

        staff = User.objects.filter(is_staff=True)
        say('-- 可登录 Django 后台 /admin/ 的账号（is_staff=True）--')
        if staff.exists():
            for u in staff:
                role = getattr(getattr(u, 'profile', None), 'role', 'MISSING')
                say('%-20s role=%-18s superuser=%s' % (u.username, role, u.is_superuser))
        else:
            say('（无）')
        say('')

        say('-- 能修改他人角色的账号（role in ADMIN_ROLES）--')
        privileged = User.objects.filter(profile__role__in=sorted(ADMIN_ROLES))
        say('共 %d 个：' % privileged.count())
        for u in privileged:
            say('%-20s role=%s' % (u.username, u.profile.role))
        say('')

        say('== 检查完成，未修改任何数据 ==')
