from django.db import models
from django.contrib.auth.models import User
from products.models import Product
from django.core.validators import MinValueValidator

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
        
    @property
    def total(self):
        return sum(item.get_cost() for item in self.items.all())

    def __str__(self):
        return f"Cart for {self.user.username}"
        
    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())

    class Meta:
        verbose_name = "Cart"
        verbose_name_plural = "Carts"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
        
    def get_cost(self):
        return self.product.current_price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    class Meta:
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"

class Order(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('esewa', 'eSewa'),
        ('khalti', 'Khalti'), 
        ('cod', 'Cash on Delivery'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'), 
        ('delivered', 'Delivered'), 
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
        ('completed', 'Completed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    items = models.ManyToManyField('CartItem')
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, editable=False)
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='cod',
        help_text="Payment method used for this order"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current status of the order"
    )
    tracking_number = models.CharField(max_length=50, blank=True, null=True)  # New
    courier_name = models.CharField(max_length=100, blank=True, null=True)  # New
    estimated_delivery = models.DateField(blank=True, null=True)  # New
    khalti_pidx = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Khalti Payment ID"
    )
    khalti_transaction_id = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Khalti Transaction ID"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"
    
    def save(self, *args, **kwargs):
        # # Calculate total before saving if items exist
        # if self.items.exists():  # Check if there are related items
        #     self.total = sum(item.get_cost() for item in self.items.all())
        # else:
        #     self.total = 0.00  # Set default if no items
        super().save(*args, **kwargs)

    def update_total(self):
        self.total = sum(item.get_cost() for item in self.items.all())
        self.save(update_fields=['total'])
    
    def get_total_items(self):
        return sum(item.quantity for item in self.items.all())
    

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Order"
        verbose_name_plural = "Orders"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='order_items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2)
        
    def get_cost(self):
        if self.price is None or self.quantity is None:
            return 0  # or Decimal('0.00') if you prefer a Decimal
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=20, choices=(('email', 'Email'), ('sms', 'SMS')))
    
    def __str__(self):
        return f"Notification for {self.user.username} - Order #{self.order.id}"
