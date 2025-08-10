from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from .models import Cart, CartItem, Order, OrderItem, Notification
from django.core.mail import send_mail
from products.models import Product
from django.conf import settings
import requests
import json

# Get or create the cart for the user
def _get_cart(request):
    if not request.user.is_authenticated:
        return None
    cart, _ = Cart.objects.get_or_create(user=request.user)
    return cart

# View Cart Page
@login_required
def cart_detail(request):
    cart = _get_cart(request)
    return render(request, 'cart/cart_detail.html', {'cart': cart})

# Add Item to Cart (usually from product detail page)
@login_required
def cart_add(request, pk):
    product = get_object_or_404(Product, pk=pk)
    cart = _get_cart(request)

    if request.method == 'POST':
        if product.stock <= 0:
            messages.error(request, 'Sorry, this item is currently out of stock.')
            return redirect('products:product_detail', slug=product.slug)

        try:
            quantity = int(request.POST.get('quantity', 1))
        except (TypeError, ValueError):
            quantity = 1

        if quantity < 1:
            quantity = 1

        if quantity > product.stock:
            messages.error(request, 'Sorry, we don\'t have enough stock.')
            return redirect('products:product_detail', slug=product.slug)  # Use slug instead of pk

        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        cart_item.quantity = cart_item.quantity + quantity if not created else quantity

        if cart_item.quantity > product.stock:
            messages.error(request, 'Sorry, we don\'t have enough stock.')
            return redirect('products:product_detail', slug=product.slug)  # Use slug instead of pk

        cart_item.save()
        messages.success(request, f'Added {quantity} × {product.name} to your cart.')

    return redirect('cart:cart')

# Increase quantity (from cart page)
@login_required
def cart_increase(request, product_id):
    if request.method != 'POST':
        return redirect('cart:cart')

    cart = _get_cart(request)
    product = get_object_or_404(Product, id=product_id)

    if product.stock <= 0:
        messages.warning(request, "This item is currently out of stock.")
        return redirect('cart:cart')

    cart_item, _ = CartItem.objects.get_or_create(cart=cart, product=product)

    if cart_item.quantity < product.stock:
        cart_item.quantity += 1
        cart_item.save()
    else:
        messages.warning(request, "No more stock available for this item.")

    return redirect('cart:cart')

# Decrease quantity (from cart page)
@login_required
def cart_decrease(request, product_id):
    if request.method != 'POST':
        return redirect('cart:cart')

    cart = _get_cart(request)
    product = get_object_or_404(Product, id=product_id)

    try:
        cart_item = CartItem.objects.get(cart=cart, product=product)
        cart_item.quantity -= 1
        if cart_item.quantity <= 0:
            cart_item.delete()
        else:
            cart_item.save()
    except CartItem.DoesNotExist:
        pass

    return redirect('cart:cart')

# Remove item from cart
@login_required
def cart_remove(request, product_id):
    cart = _get_cart(request)
    product = get_object_or_404(Product, id=product_id)

    try:
        cart_item = CartItem.objects.get(cart=cart, product=product)
        cart_item.delete()
    except CartItem.DoesNotExist:
        pass

    return redirect('cart:cart')

# eSewa Checkout
@login_required
def esewa_checkout(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    context = {
        'order': order,
        'amount': str(order.total),  # eSewa expects amount as string
        'pid': str(order.id),
        'success_url': request.build_absolute_uri('/cart/esewa/verify/'),
        'failure_url': request.build_absolute_uri('/cart/esewa/failure/'),
        'merchant_code': 'YOUR_MERCHANT_CODE'  # Replace with your real eSewa merchant code
    }

    return render(request, 'cart/esewa_checkout.html', context)

# eSewa Verify
@login_required
def esewa_verify(request):
    oid = request.GET.get('oid')
    amt = request.GET.get('amt')
    refId = request.GET.get('refId')

    if not all([oid, amt, refId]):
        messages.error(request, "Invalid payment verification data.")
        return redirect('cart:order_failed')

    data = {
        'amt': amt,
        'scd': 'YOUR_MERCHANT_CODE',  # Replace with your real eSewa merchant code
        'pid': oid,
        'rid': refId
    }

    try:
        response = requests.post("https://uat.esewa.com.np/epay/transrec", data=data)
        response.raise_for_status()  # Raise an error for bad responses
        if 'Success' in response.text:
            order = get_object_or_404(Order, id=oid, user=request.user)
            order.status = 'completed'
            order.save()
            return redirect('cart:order_success')
        else:
            messages.error(request, "Payment verification failed.")
            return redirect('cart:order_failed')
    except requests.RequestException as e:
        messages.error(request, f"Error verifying payment: {str(e)}")
        return redirect('cart:order_failed')

# Khalti Checkout
@login_required
def khalti_checkout(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    url = "https://a.khalti.com/api/v2/epayment/initiate/"

    secret_key = settings.KHALTI_SECRET_KEY

    payload = {
        # Modified return URL to include order_id as parameter
        "return_url": request.build_absolute_uri(f'/cart/khalti/verify/?order_id={order.id}'),
        "website_url": request.build_absolute_uri('/'),
        "amount": int(order.total * 100),  # Amount in paisa
        "purchase_order_id": str(order.id),
        "purchase_order_name": "Purchase from Pathshala Wears",
        "customer_info": {
            "name": request.user.get_full_name() or request.user.username,
            "email": request.user.email or "user@example.com",
        },
    }

    headers = {
        "Authorization": f"Key {secret_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response_data = response.json()

        if response.status_code == 200 and response_data.get('pidx'):
            order.khalti_pidx = response_data['pidx']
            order.save()
            context = {
                'order': order,
                'payment_url': response_data['payment_url'],
                'pidx': response_data['pidx'],
            }
            return render(request, 'cart/khalti_checkout.html', context)
        else:
            messages.error(request, "Failed to initiate Khalti payment.")
            return redirect('cart:checkout')
    except requests.RequestException as e:
        messages.error(request, f"Error initiating Khalti payment: {str(e)}")
        return redirect('cart:checkout')

# Modified khalti_verify to handle both GET (return from Khalti) and POST (AJAX verification)
@csrf_exempt
@login_required
def khalti_verify(request):
    if request.method == "GET":
        # Handle return from Khalti payment
        pidx = request.GET.get("pidx")
        order_id = request.GET.get("order_id")
        status = request.GET.get("status")
        transaction_id = request.GET.get("transaction_id")

        if not all([pidx, order_id]):
            messages.error(request, "Invalid payment parameters.")
            return redirect('cart:order_failed')

        try:
            order = get_object_or_404(Order, id=order_id, user=request.user)
            
            # Verify payment with Khalti
            url = "https://a.khalti.com/api/v2/epayment/lookup/"
            headers = {"Authorization": f"Key {settings.KHALTI_SECRET_KEY}"}
            payload = {"pidx": pidx}

            response = requests.post(url, headers=headers, json=payload)
            response_data = response.json()

            if response_data.get("status") == "Completed":
                order.status = "completed"
                order.khalti_transaction_id = transaction_id  # Store transaction ID if needed
                order.save()
                messages.success(request, "Payment completed successfully!")
                return redirect('cart:order_success')
            else:
                order.status = "cancelled"
                order.save()
                messages.error(request, "Payment was not completed.")
                return redirect('cart:order_failed')
                
        except requests.RequestException as e:
            messages.error(request, f"Error verifying payment: {str(e)}")
            return redirect('cart:order_failed')
        except Order.DoesNotExist:
            messages.error(request, "Order not found.")
            return redirect('cart:order_failed')

    elif request.method == "POST":
        # Handle AJAX verification requests (if you want to keep this functionality)
        try:
            data = json.loads(request.body)
            pidx = data.get("pidx")
            order_id = data.get("order_id")

            if not all([pidx, order_id]):
                return JsonResponse({'status': 'error', 'message': 'Missing parameters'}, status=400)

            order = get_object_or_404(Order, id=order_id, user=request.user)

            url = "https://a.khalti.com/api/v2/epayment/lookup/"
            headers = {"Authorization": f"Key {settings.KHALTI_SECRET_KEY}"}
            payload = {"pidx": pidx}

            response = requests.post(url, headers=headers, json=payload)
            response_data = response.json()

            if response_data.get("status") == "Completed":
                order.status = "completed"
                order.save()
                return JsonResponse({"success": True})
            else:
                order.status = "cancelled"
                order.save()
                return JsonResponse({"success": False})
                
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except requests.RequestException as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        except Order.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Order not found'}, status=404)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

# Checkout Page
@login_required
def checkout(request):
    cart = _get_cart(request)

    if cart.items.count() == 0:
        messages.warning(request, "Your cart is empty.")
        return redirect('cart:cart')

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')

        if not payment_method:
            messages.error(request, "Please select a payment method.")
            return redirect('cart:checkout')

        cart_items = list(cart.items.select_related('product'))
        for item in cart_items:
            if item.quantity > item.product.stock:
                if item.product.stock > 0:
                    item.quantity = item.product.stock
                    item.save(update_fields=['quantity'])
                    messages.error(
                        request,
                        f"{item.product.name} only has {item.product.stock} left. Your cart was updated."
                    )
                else:
                    item.delete()
                    messages.error(request, f"{item.product.name} is out of stock and was removed from your cart.")
                return redirect('cart:cart')

        with transaction.atomic():
            locked_products = Product.objects.select_for_update().in_bulk(
                [item.product_id for item in cart_items]
            )

            for item in cart_items:
                product = locked_products[item.product_id]
                if item.quantity > product.stock:
                    messages.error(request, f"{product.name} does not have enough stock right now.")
                    return redirect('cart:cart')

            order = Order.objects.create(
                user=request.user,
                payment_method=payment_method,
                total=0
            )

            total = 0
            for item in cart_items:
                product = locked_products[item.product_id]
                order_item = OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item.quantity,
                    price=product.current_price
                )
                total += order_item.get_cost()
                product.stock -= item.quantity
                product.save(update_fields=['stock'])

            order.total = total
            order.save(update_fields=['total'])

            cart.items.all().delete()
            cart.is_active = False
            cart.save(update_fields=['is_active'])

        # Redirect based on payment method
        if payment_method == 'cod':
            order.status = 'completed'
            order.save()
            messages.success(request, "Order placed successfully with Cash on Delivery.")
            return redirect('cart:order_success')
        elif payment_method == 'esewa':
            return redirect('cart:esewa_checkout', order_id=order.id)
        elif payment_method == 'khalti':
            return redirect('cart:khalti_checkout', order_id=order.id)
        else:
            messages.error(request, "Invalid payment method selected.")
            order.delete()  # Clean up if payment method is invalid
            return redirect('cart:checkout')

    return render(request, 'cart/checkout.html', {
        'cart': cart,
        'payment_methods': [('cod', 'Cash on Delivery'), ('esewa', 'eSewa'), ('khalti', 'Khalti')]
    })
    
@login_required
def admin_update_order_status(request, order_id):
    if not request.user.is_staff:
        messages.error(request, 'Unauthorized access.')
        return redirect('products:product_list')
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        order.status = request.POST.get('status')
        # order.tracking_number = request.POST.get('tracking_number', '')
        # order.courier_name = request.POST.get('courier_name', '')
        # order.estimated_delivery = request.POST.get('estimated_delivery')
        order.save()
        
        # Save notification
        Notification.objects.create(
            user=order.user,
            order=order,
            message=f'Your order #{order.id} is now {order.get_status_display()}.',
            type='email'
        )
        
        # Send email notification
        try:
            send_mail(
                subject=f'Pathshala Wears: Order #{order.id} Update',
                message=f'Your order is now {order.get_status_display()}. Track it here: {request.build_absolute_uri("/users/track/" + str(order.id))}',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[order.user.email],
                fail_silently=False,
            )
        except Exception as e:
            messages.warning(request, f'Order updated, but email failed: {str(e)}')
        
        messages.success(request, 'Order status updated.')
        return redirect('admin:cart_order_changelist')  # Redirect to Django admin order list
    return render(request, 'cart/admin_update_order.html', {'order': order})

# Order Success Page
@login_required
def order_success(request):
    return render(request, 'cart/order_success.html')

# Order Failed Page
def order_failed(request):
    return render(request, 'cart/order_failed.html')

