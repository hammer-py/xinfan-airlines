from django.db import models
from django.contrib.auth.models import User

class Flight(models.Model):
    STATUS_CHOICES = [
        ('scheduled', '已排班'),
        ('boarding', '登机中'),
        ('departed', '已起飞'),
        ('arrived', '已到达'),
        ('cancelled', '已取消'),
    ]
    ROUTE_CHOICES = [
        ('domestic', '国内'),
        ('international', '国际'),
    ]

    flight_number = models.CharField(max_length=20, unique=True, verbose_name='航班号')
    origin = models.CharField(max_length=100, verbose_name='出发地')
    destination = models.CharField(max_length=100, verbose_name='目的地')
    departure_time = models.DateTimeField(verbose_name='计划起飞')
    arrival_time = models.DateTimeField(verbose_name='计划到达')
    aircraft = models.CharField(max_length=50, default='A320neo', verbose_name='机型')
    gate = models.CharField(max_length=10, blank=True, null=True, verbose_name='登机口')
    route_type = models.CharField(max_length=20, choices=ROUTE_CHOICES, default='domestic', verbose_name='航线类型')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', verbose_name='状态')
    notes = models.TextField(blank=True, null=True, verbose_name='备注')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='创建人')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '航班'
        verbose_name_plural = '航班'
        ordering = ['-departure_time']

    def __str__(self):
        return f"{self.flight_number}: {self.origin} → {self.destination}"

class FlightCrewSignup(models.Model):
    CREW_ROLES = [
        ('captain', '机长'),
        ('first_officer', '副驾驶'),
        ('purser', '乘务长'),
        ('cabin_crew', '空乘'),
        ('ground_staff', '地勤'),
    ]
    STATUS_CHOICES = [
        ('pending', '待审批'),
        ('approved', '已通过'),
        ('rejected', '已拒绝'),
    ]

    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name='crew_signups', verbose_name='航班')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='crew_signups', verbose_name='报名用户')
    role = models.CharField(max_length=20, choices=CREW_ROLES, verbose_name='报名角色')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='审批状态')
    signed_up_at = models.DateTimeField(auto_now_add=True, verbose_name='报名时间')

    class Meta:
        verbose_name = '航班报名'
        verbose_name_plural = '航班报名'
        unique_together = ['flight', 'user']
        ordering = ['-signed_up_at']

    def __str__(self):
        return f"{self.user.username} → {self.flight.flight_number} ({self.get_role_display()})"
