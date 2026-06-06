from django.db import models
from django.contrib.auth.models import User

class MileageRecord(models.Model):
    TYPE_CHOICES = [
        ('earn', '获得'),
        ('redeem', '消费'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mileage_records', verbose_name='用户')
    flight = models.ForeignKey('flights.Flight', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='关联航班')
    amount = models.IntegerField(verbose_name='里程数')
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='earn', verbose_name='类型')
    description = models.CharField(max_length=200, verbose_name='说明')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='时间')

    class Meta:
        verbose_name = '里程记录'
        verbose_name_plural = '里程记录'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.get_type_display()} {self.amount} miles"
