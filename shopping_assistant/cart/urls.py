from django.urls import path, include
from . import views


app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail, name='cart'),
    path('add/<int:product_id>/', views.cart_add, name='add_to_cart'),
    path('remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path("inc/<int:product_id>/", views.cart_increase, name="cart_increase"),
    path("dec/<int:product_id>/", views.cart_decrease, name="cart_decrease"),
    path('payment/', include('payment.urls', namespace='payment')),
    path('esewa/<int:order_id>/', views.esewa_checkout, name='esewa_checkout'),
    path('khalti/<int:order_id>/', views.khalti_checkout, name='khalti_checkout'),
    path('checkout/', views.checkout, name='checkout'),
    path('success/', views.order_success, name='order_success'),
]

