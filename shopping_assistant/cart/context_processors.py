from .models import Cart

def cart_context(request):
    cart = None
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(
            user=request.user,
            defaults={'is_active': True}
        )
        # Ensure the cart is active (optional, depending on your logic)
        if not cart.is_active:
            cart.is_active = True
            cart.save()
    return {"cart": cart}