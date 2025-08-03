from django.urls import path
from . import views

app_name = 'payment' 

urlpatterns = [
    path('esewa/', views.esewa_payment, name='esewa'),
    path('khalti/', views.khalti_payment, name='khalti'),
]