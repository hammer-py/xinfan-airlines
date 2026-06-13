from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = '创建演示账户并初始化示例航班和招聘职位'

    def handle(self, *args, **options):
        # Create admin user
        if not User.objects.filter(username='admin').exists():
            user = User.objects.create_superuser(
                username='admin', email='admin@xinfan.com', password='admin123'
            )
            user.profile.role = 'admin'
            user.profile.save()
            self.stdout.write(self.style.SUCCESS('管理员创建成功: admin / admin123'))

        # Demo employee users at various levels
        employees = [
            ('pilot001', 'pilot001@xinfan.com', 'pilot123', 'captain', '正式机长', 5000),
            ('copilot01', 'copilot@xinfan.com', 'pilot123', 'first_officer', '正式副驾驶', 2500),
            ('trainee_pilot', 'tpilot@xinfan.com', 'pilot123', 'trainee_first_officer', '实习副驾驶', 500),
            ('cabin01', 'cabin@xinfan.com', 'pilot123', 'cabin_crew', '正式空乘', 1500),
            ('trainee_cabin', 'tcabin@xinfan.com', 'pilot123', 'trainee_cabin_crew', '实习空乘', 200),
            ('ground01', 'ground@xinfan.com', 'pilot123', 'ground_staff', '正式地勤', 1000),
            ('trainee_ground', 'tground@xinfan.com', 'pilot123', 'trainee_ground', '实习地勤', 100),
        ]
        for uname, email, pw, role, dname, miles in employees:
            if not User.objects.filter(username=uname).exists():
                u = User.objects.create_user(username=uname, email=email, password=pw)
                u.profile.role = role
                u.profile.miles = miles
                u.profile.save()
                self.stdout.write(self.style.SUCCESS(f'{dname}创建成功: {uname} / {pw}'))

        # Demo user/passenger accounts at various levels
        passengers = [
            ('user001', 'user@xinfan.com', 'user123', 'economy', '经济舱旅客', 300),
            ('biz001', 'business@xinfan.com', 'user123', 'business', '商务舱旅客', 1200),
            ('first001', 'first@xinfan.com', 'user123', 'first_class', '头等舱旅客', 3000),
            ('investor01', 'investor@xinfan.com', 'user123', 'investor', '投资者', 10000),
            ('vip001', 'vip@xinfan.com', 'user123', 'uinv', '顶级投资者', 50000),
        ]
        for uname, email, pw, role, dname, miles in passengers:
            if not User.objects.filter(username=uname).exists():
                u = User.objects.create_user(username=uname, email=email, password=pw)
                u.profile.role = role
                u.profile.miles = miles
                u.profile.save()
                self.stdout.write(self.style.SUCCESS(f'{dname}创建成功: {uname} / {pw}'))

        # Create demo flights
        from apps.flights.models import Flight
        if Flight.objects.count() == 0:
            admin = User.objects.get(username='admin')
            flights = [
                ('XF001', '香港国际机场', '东京羽田机场', '2026-06-10 08:00', '2026-06-10 12:00', 'B787-10', 'international'),
                ('XF002', '香港国际机场', '北京首都机场', '2026-06-10 14:00', '2026-06-10 16:30', 'B737-800', 'domestic'),
                ('XF003', '香港国际机场', '新加坡樟宜机场', '2026-06-11 09:00', '2026-06-11 14:00', 'A350-900', 'international'),
                ('XF004', '香港国际机场', '上海浦东机场', '2026-06-11 16:00', '2026-06-11 18:00', 'B737-800', 'domestic'),
                ('XF005', '香港国际机场', '伦敦希思罗机场', '2026-06-12 10:00', '2026-06-12 23:00', 'B787-10', 'international'),
            ]
            for fn, orig, dest, dep, arr, ac, rtype in flights:
                Flight.objects.create(
                    flight_number=fn, origin=orig, destination=dest,
                    departure_time=dep, arrival_time=arr, aircraft=ac,
                    route_type=rtype, created_by=admin, notes='初始化演示航班'
                )
            self.stdout.write(self.style.SUCCESS(f'{len(flights)} 个演示航班已创建'))

        # Create demo job postings
        from apps.recruitment.models import JobPosting
        if JobPosting.objects.count() == 0:
            admin = User.objects.get(username='admin')
            JobPosting.objects.create(
                title='A320 机长（正式）', department='flight_dept', job_type='volunteer',
                location='香港国际机场',
                description='负责 A320neo 机型的执飞任务，带领机组团队确保航班安全准时运行。',
                requirements='1. 需达到实习机长等级后方可申请\n2. 在 Roblox 平台有丰富飞行经验\n3. 熟悉 A320 操作流程\n4. 有团队领导和协作精神',
                contact_email='hr@xinfan.com', posted_by=admin,
            )
            JobPosting.objects.create(
                title='空乘人员招募', department='cabin_dept', job_type='volunteer',
                location='香港国际机场',
                description='负责客舱服务，为旅客提供优质的飞行体验，处理客舱内各项事务。',
                requirements='1. 热情开朗，善于沟通\n2. 有 Roblox 航空社区经验优先\n3. 实习空乘表现优秀可晋升正式空乘',
                contact_email='hr@xinfan.com', posted_by=admin,
            )
            JobPosting.objects.create(
                title='地勤人员招募', department='ground_dept', job_type='volunteer',
                location='香港国际机场',
                description='负责航班的地面保障工作，包括行李装卸、加油、推车等。',
                requirements='1. 责任心强，注重细节\n2. 能够准时到场\n3. 实习地勤表现优秀可晋升正式地勤',
                contact_email='hr@xinfan.com', posted_by=admin,
            )
            self.stdout.write(self.style.SUCCESS('3 个演示招聘职位已创建'))

        self.stdout.write(self.style.SUCCESS('\n=== 初始化完成 ==='))
        self.stdout.write('——— 员工账户 ———')
        self.stdout.write('  captain:  pilot001 / pilot123')
        self.stdout.write('  副驾驶:   copilot01 / pilot123')
        self.stdout.write('  实习副驾: trainee_pilot / pilot123')
        self.stdout.write('  空乘:     cabin01 / pilot123')
        self.stdout.write('  实习空乘: trainee_cabin / pilot123')
        self.stdout.write('  地勤:     ground01 / pilot123')
        self.stdout.write('  实习地勤: trainee_ground / pilot123')
        self.stdout.write('——— 旅客账户 ———')
        self.stdout.write('  经济舱:   user001 / user123')
        self.stdout.write('  商务舱:   biz001 / user123')
        self.stdout.write('  头等舱:   first001 / user123')
        self.stdout.write('  投资者:   investor01 / user123')
        self.stdout.write('  顶级投资: vip001 / user123')
        self.stdout.write('——— 管理员 ———')
        self.stdout.write('  admin:    admin / admin123')
