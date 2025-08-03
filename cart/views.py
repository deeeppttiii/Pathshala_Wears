from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Cart, CartItem
from .models import Order, OrderItem
from products.models import Product 
import requests

# Get or create the cart for the user
@login_required()
def _get_cart(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    return cart


# View Cart Page
@login_required()
def cart_detail(request):
    cart = _get_cart(request)
    return render(request, 'cart/cart_detail.html', {'cart': cart})


#  Add Item to Cart (usually from product detail page)
@login_required
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = _get_cart(request)

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))

        if quantity > product.stock:
            messages.error(request, 'Sorry, we don\'t have enough stock.')
            return redirect('products:product_detail', pk=product_id)

        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        cart_item.quantity = cart_item.quantity + quantity if not created else quantity

        if cart_item.quantity > product.stock:
            messages.error(request, 'Sorry, we don\'t have enough stock.')
            return redirect('products:product_detail', pk=product_id)

        cart_item.save()
        messages.success(request, f'Added {quantity} × {product.name} to your cart.')

    return redirect('cart:cart')


# Increase quantity (from cart page)
def cart_increase(request, product_id):
    if request.method != 'POST':
        return redirect('cart:cart')

    cart = _get_cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart_item, _ = CartItem.objects.get_or_create(cart=cart, product=product)

    if cart_item.quantity < product.stock:
        cart_item.quantity += 1
        cart_item.save()
    else:
        messages.warning(request, "No more stock available for this item.")

    return redirect('cart:cart')


#  Decrease quantity (from cart page)
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
def cart_remove(request, product_id):
    cart = _get_cart(request)
    product = get_object_or_404(Product, id=product_id)

    try:
        cart_item = CartItem.objects.get(cart=cart, product=product)
        cart_item.delete()
    except CartItem.DoesNotExist:
        pass

    return redirect('cart:cart')

def esewa_checkout(request, order_id):
    order = Order.objects.get(id=order_id, user=request.user)

    context = {
        'order': order,
        'amount': order.total,
        'pid': str(order.id),
        'success_url': request.build_absolute_uri('/cart/esewa/verify/'),
        'failure_url': request.build_absolute_uri('/cart/esewa/failure/'),
        'merchant_code': 'YOUR_MERCHANT_CODE'  # Replace this with your real eSewa merchant code
    }

    return render(request, 'cart/esewa_payment.html', context)


def esewa_verify(request):
    oid = request.GET.get('oid')
    amt = request.GET.get('amt')
    refId = request.GET.get('refId')

    data = {
        'amt': amt,
        'scd': 'YOUR_MERCHANT_CODE',
        'pid': oid,
        'rid': refId
    }

    response = requests.post("https://uat.esewa.com.np/epay/transrec", data=data)

    if 'Success' in response.text:
        order = Order.objects.get(id=oid, user=request.user)
        order.is_paid = True
        order.save()
        return redirect('cart:order_success')
    else:
        return redirect('cart:order_failed')


def khalti_checkout(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'cart/khalti_checkout.html', {'order': order})

# Checkout page
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

        # Create the order
        order = Order.objects.create(
            user=request.user,
            total=cart.get_total(),
            payment_method=payment_method  # ensure your Order model has this field
        )

        # Transfer cart items to order
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
            item.product.stock -= item.quantity
            item.product.save()

        # Clear cart
        cart.items.all().delete()

        # Redirect based on payment method
        if payment_method == 'cod':
            messages.success(request, "Order placed successfully with Cash on Delivery.")
            return redirect('cart:order_success')
        elif payment_method == 'esewa':
            # Redirect to eSewa payment gateway
            return redirect('payment:esewa_checkout', order_id=order.id)
        elif payment_method == 'khalti':
            # Redirect to Khalti payment page
            return redirect('payment:khalti_checkout', order_id=order.id)
        else:
            messages.error(request, "Invalid payment method selected.")
            return redirect('cart:checkout')

    return render(request, 'cart/checkout.html', {'cart': cart})

@login_required
def order_success(request):
    return render(request, 'cart/order_success.html')


