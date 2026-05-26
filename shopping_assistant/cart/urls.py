# cart/urls.py
from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail, name='cart'),
    path('add/<int:pk>/', views.cart_add, name='cart_add'),
    # path('add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('increase/<int:product_id>/', views.cart_increase, name='cart_increase'),
    path('decrease/<int:product_id>/', views.cart_decrease, name='cart_decrease'),
    path('remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),
    path('esewa/checkout/<int:order_id>/', views.esewa_checkout, name='esewa_checkout'),
    path('esewa/verify/', views.esewa_verify, name='esewa_verify'),
    path('khalti/checkout/<int:order_id>/', views.khalti_checkout, name='khalti_checkout'),
    path('khalti/verify/', views.khalti_verify, name='khalti_verify'),
    # path('khalti-callback/', views.khalti_callback, name='khalti_callback'),
    path('order_success/', views.order_success, name='order_success'),
    path('order_failed/', views.order_failed, name='order_failed'),
    path('admin/orders/<int:order_id>/update/', views.admin_update_order_status, name='admin_update_order_status'),
]