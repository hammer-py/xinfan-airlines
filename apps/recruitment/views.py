from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import JobPosting, JobApplication
from apps.accounts.decorators import role_required

def job_list_view(request):
    jobs = JobPosting.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'recruitment/job_list.html', {'jobs': jobs})

def job_detail_view(request, pk):
    job = get_object_or_404(JobPosting, pk=pk)
    user_applied = False
    if request.user.is_authenticated:
        user_applied = JobApplication.objects.filter(job=job, user=request.user).exists()
    return render(request, 'recruitment/job_detail.html', {'job': job, 'user_applied': user_applied})

@login_required
def job_apply_view(request, pk):
    job = get_object_or_404(JobPosting, pk=pk)
    if not job.is_active:
        messages.error(request, '该职位已关闭申请')
        return redirect('job_list')
    if JobApplication.objects.filter(job=job, user=request.user).exists():
        messages.warning(request, '你已经申请过这个职位了')
        return redirect('job_detail', job.pk)
    if request.method == 'POST':
        JobApplication.objects.create(
            job=job, user=request.user,
            cover_letter=request.POST.get('cover_letter', ''),
            resume=request.POST.get('resume', ''),
        )
        messages.success(request, '申请已提交，请等待审核')
        return redirect('my_applications')
    return render(request, 'recruitment/job_apply.html', {'job': job})

@login_required
def my_applications_view(request):
    applications = JobApplication.objects.select_related('job').filter(user=request.user).order_by('-created_at')
    return render(request, 'recruitment/my_applications.html', {'applications': applications})

# ─── Admin ──────────────────────────────────────────────

@login_required
@role_required(['admin'])
def admin_recruitment_view(request):
    jobs = JobPosting.objects.all().order_by('-created_at')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            job = JobPosting.objects.create(
                title=request.POST.get('title'),
                department=request.POST.get('department'),
                location=request.POST.get('location', '新帆国际机场'),
                job_type=request.POST.get('job_type', 'volunteer'),
                description=request.POST.get('description'),
                requirements=request.POST.get('requirements'),
                contact_email=request.POST.get('contact_email'),
                posted_by=request.user,
                deadline=request.POST.get('deadline') or None,
            )
            messages.success(request, f'职位 "{job.title}" 已发布')
        elif action == 'toggle':
            job = get_object_or_404(JobPosting, pk=request.POST.get('job_id'))
            job.is_active = not job.is_active
            job.save()
            state = '开放' if job.is_active else '关闭'
            messages.success(request, f'"{job.title}" 已{state}')
        elif action == 'delete':
            job = get_object_or_404(JobPosting, pk=request.POST.get('job_id'))
            title = job.title
            job.delete()
            messages.success(request, f'"{title}" 已删除')
        return redirect('admin_recruitment')
    return render(request, 'recruitment/admin_recruitment.html', {
        'jobs': jobs,
        'departments': JobPosting.DEPARTMENTS,
        'job_types': JobPosting.JOB_TYPES,
    })

@login_required
@role_required(['admin'])
def admin_applications_view(request):
    applications = JobApplication.objects.select_related('job', 'user').all().order_by('-created_at')
    if request.method == 'POST':
        app = get_object_or_404(JobApplication, pk=request.POST.get('application_id'))
        action = request.POST.get('action')
        if action == 'accept':
            app.status = 'accepted'
        elif action == 'reject':
            app.status = 'rejected'
        elif action == 'review':
            app.status = 'reviewed'
        app.reviewed_by = request.user
        app.review_note = request.POST.get('review_note', '').strip() or None
        app.save()
        messages.success(request, f'{app.user.username} 的申请已处理')
        return redirect('admin_applications')
    return render(request, 'recruitment/admin_applications.html', {'applications': applications})
