from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at', 'total', 'is_active')
    list_filter = ('created_at', 'updated_at', 'is_active')
    search_fields = ('user__username',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity', 'get_cost', 'created_at')
    list_filter = ('cart', 'created_at')
    search_fields = ('product__name', 'cart__user__username')
    readonly_fields = ('created_at',)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('get_cost',)
    fields = ('product', 'quantity', 'price', 'get_cost')
    

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total', 'get_payment_method_display', 'status', 'created_at', 'tracking_number', 'courier_name', 'estimated_delivery')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('user__username', 'user__email', 'id', 'tracking_number')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'khalti_pidx', 'khalti_transaction_id')
    
    def get_total(self, obj):
        return obj.total  # Replace with your calculation logic if needed
    get_total.short_description = 'Total'

    fieldsets = (
        ('Order Information', {
            'fields': ('user', 'status')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'khalti_pidx', 'khalti_transaction_id')
        }),
        ('Shipping Information', {
            'fields': ('tracking_number', 'courier_name', 'estimated_delivery')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    inlines = [OrderItemInline]
    actions = ['mark_completed', 'mark_cancelled', 'mark_processing']    

    def get_payment_method_display(self, obj):
        """Display human-readable payment method"""
        payment_methods = {
            'cod': 'Cash on Delivery',
            'esewa': 'eSewa',
            'khalti': 'Khalti',
        }
        return payment_methods.get(obj.payment_method, obj.payment_method or 'Not specified')
    get_payment_method_display.short_description = 'Payment Method'
    get_payment_method_display.admin_order_field = 'payment_method'

    def mark_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} orders marked as completed.')
    mark_completed.short_description = "Mark selected orders as completed"

    def mark_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} orders marked as cancelled.')
    mark_cancelled.short_description = "Mark selected orders as cancelled"

    def mark_processing(self, request, queryset):
        updated = queryset.update(status='processing')
        self.message_user(request, f'{updated} orders marked as processing.')
    mark_processing.short_description = "Mark selected orders as processing"

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price', 'get_cost')
    list_filter = ('order__status', 'order__created_at')
    search_fields = ('product__name', 'order__user__username')
    readonly_fields = ('get_cost',)
    
