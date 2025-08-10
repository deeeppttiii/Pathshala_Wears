from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserProfile
from django.http import Http404
from cart.models import Order

@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        profile.phone = request.POST.get('phone', '')
        profile.shipping_address = {
            'street': request.POST.get('street', ''),
            'city': request.POST.get('city', ''),
            'zip': request.POST.get('zip', '')
        }
        profile.billing_address = {
            'street': request.POST.get('billing_street', ''),
            'city': request.POST.get('billing_city', ''),
            'zip': request.POST.get('billing_zip', '')
        }
        profile.preferences = {
            'preferred_sizes': request.POST.getlist('preferred_sizes', [])
        }
        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('users:profile')
    return render(request, 'users/profile.html', {'profile': profile})

@login_required
def orders_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'users/orders.html', {'orders': orders})


@login_required
def track_order(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        return render(request, 'users/track_orders.html', {'order': order})
    except Order.DoesNotExist:
        raise Http404("The requested order does not exist or is not accessible to you.")
