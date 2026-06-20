from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

ROLE_CHOICES = [
    # 普通用户等级
    ('economy', '经济舱旅客'),
    ('business', '商务舱旅客'),
    ('first_class', '头等舱旅客'),
    ('investor', '投资者'),
    ('uinv', '顶级投资者'),
    # 员工等级（实习）
    ('trainee_cabin_crew', '实习空乘'),
    ('trainee_first_officer', '实习副驾驶'),
    ('trainee_captain', '实习机长'),
    ('trainee_ground', '实习地勤'),
    # 员工等级（正式）
    ('cabin_crew', '正式空乘'),
    ('first_officer', '正式副驾驶'),
    ('captain', '正式机长'),
    ('ground_staff', '正式地勤'),
    # 管理员（全部权限）
    ('admin', '管理员'),
    ('hod', 'HOD-部门主管'),
    ('shr', 'SHR-高级管理'),
    ('vice_chairman', '副董事长'),
    ('chairman', '董事长'),
    ('group_owner', '集团所有者'),
    # 管理员（部分权限）
    ('flight_host', '飞行经理'),
]

USER_ROLES = {'economy', 'business', 'first_class', 'investor', 'uinv'}
EMPLOYEE_ROLES = {
    'trainee_cabin_crew', 'trainee_first_officer', 'trainee_captain', 'trainee_ground',
    'cabin_crew', 'first_officer', 'captain', 'ground_staff',
}
TRAINEE_ROLES = {'trainee_cabin_crew', 'trainee_first_officer', 'trainee_captain', 'trainee_ground'}
STAFF_ROLES = {'cabin_crew', 'first_officer', 'captain', 'ground_staff'}
ADMIN_ROLES = {'admin', 'hod', 'shr', 'vice_chairman', 'chairman', 'group_owner'}
ALL_STAFF_ROLES = ADMIN_ROLES | {'flight_host'}
PREMIUM_ROLES = {'business', 'first_class', 'investor', 'uinv'} | ADMIN_ROLES


def is_employee(role):
    return role in EMPLOYEE_ROLES or role in ALL_STAFF_ROLES


def is_trainee(role):
    return role in TRAINEE_ROLES


def is_staff(role):
    return role in STAFF_ROLES

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='economy', verbose_name='角色')
    miles = models.IntegerField(default=0, verbose_name='累计里程')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='手机号')
    bio = models.TextField(blank=True, null=True, verbose_name='个人简介')

    class Meta:
        verbose_name = '用户资料'
        verbose_name_plural = '用户资料'

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    @property
    def is_employee(self):
        return self.role in EMPLOYEE_ROLES or self.role in ALL_STAFF_ROLES

    @property
    def is_trainee(self):
        return self.role in TRAINEE_ROLES

    @property
    def is_staff(self):
        return self.role in STAFF_ROLES

    @property
    def is_admin(self):
        return self.role in ADMIN_ROLES

    @property
    def has_staff_access(self):
        return self.role in ALL_STAFF_ROLES

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
