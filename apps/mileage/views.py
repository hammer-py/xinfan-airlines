from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import MileageRecord
from apps.accounts.decorators import role_required

@login_required
def mileage_list_view(request):
    records = MileageRecord.objects.filter(user=request.user).order_by('-created_at')
    total = request.user.profile.miles
    return render(request, 'mileage/mileage_list.html', {'records': records, 'total': total})

@login_required
def mileage_redeem_view(request):
    if request.method == 'POST':
        item = request.POST.get('item', '')
        costs = {'priority_boarding': 500, 'lounge_access': 1000, 'free_flight': 5000, 'custom_title': 2000}
        cost = costs.get(item, 0)
        if cost == 0:
            messages.error(request, '无效的兑换项目')
        elif request.user.profile.miles < cost:
            messages.error(request, f'里程不足，需要 {cost} 英里')
        else:
            names = {'priority_boarding': '优先登机', 'lounge_access': '贵宾休息室', 'free_flight': '免费航班券', 'custom_title': '自定义头衔'}
            request.user.profile.miles -= cost
            request.user.profile.save()
            MileageRecord.objects.create(user=request.user, amount=-cost, type='redeem', description=f'兑换: {names.get(item, item)}')
            messages.success(request, f'兑换成功！消耗 {cost} 英里')
        return redirect('mileage_list')
    items = [
        {'key': 'priority_boarding', 'name': '优先登机', 'cost': 500, 'icon': 'bi bi-airplane'},
        {'key': 'lounge_access', 'name': '贵宾休息室', 'cost': 1000, 'icon': 'bi bi-cup-hot'},
        {'key': 'custom_title', 'name': '自定义头衔', 'cost': 2000, 'icon': 'bi bi-tag'},
        {'key': 'free_flight', 'name': '免费航班券', 'cost': 5000, 'icon': 'bi bi-ticket-perforated'},
    ]
    return render(request, 'mileage/redeem.html', {'items': items})

@login_required
@role_required(['admin'])
def mileage_grant_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        amount = int(request.POST.get('amount', 0))
        description = request.POST.get('description', '管理员发放').strip()
        try:
            user = User.objects.get(username=username)
            user.profile.miles += amount
            user.profile.save()
            MileageRecord.objects.create(user=user, amount=amount, type='earn', description=description)
            messages.success(request, f'已向 {username} 发放 {amount} 英里')
        except User.DoesNotExist:
            messages.error(request, f'用户 {username} 不存在')
        return redirect('mileage_grant')
    return render(request, 'mileage/grant.html')
