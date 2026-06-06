from django.db import models
from django.contrib.auth.models import User

class JobPosting(models.Model):
    JOB_TYPES = [
        ('full_time', '全职'),
        ('part_time', '兼职'),
        ('volunteer', '志愿者'),
    ]
    DEPARTMENTS = [
        ('flight_dept', '飞行部'),
        ('cabin_dept', '客舱部'),
        ('ground_dept', '地勤部'),
        ('ops_dept', '运控部'),
        ('admin_dept', '行政部'),
    ]

    title = models.CharField(max_length=100, verbose_name='职位名称')
    department = models.CharField(max_length=20, choices=DEPARTMENTS, verbose_name='部门')
    location = models.CharField(max_length=100, default='新帆国际机场', verbose_name='工作地点')
    job_type = models.CharField(max_length=20, choices=JOB_TYPES, default='volunteer', verbose_name='工作类型')
    description = models.TextField(verbose_name='职位描述')
    requirements = models.TextField(verbose_name='任职要求')
    contact_email = models.EmailField(verbose_name='联系邮箱')
    is_active = models.BooleanField(default=True, verbose_name='开放申请')
    posted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='发布人')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='发布时间')
    deadline = models.DateTimeField(blank=True, null=True, verbose_name='截止日期')

    class Meta:
        verbose_name = '招聘职位'
        verbose_name_plural = '招聘职位'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_department_display()})"

class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', '待审核'),
        ('reviewed', '已查看'),
        ('accepted', '已通过'),
        ('rejected', '已拒绝'),
    ]

    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications', verbose_name='职位')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_applications', verbose_name='申请人')
    cover_letter = models.TextField(verbose_name='申请理由')
    resume = models.TextField(verbose_name='个人经历')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='审核状态')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_applications', verbose_name='审核人')
    review_note = models.TextField(blank=True, null=True, verbose_name='审核备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='申请时间')

    class Meta:
        verbose_name = '职位申请'
        verbose_name_plural = '职位申请'
        unique_together = ['job', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} → {self.job.title}"
