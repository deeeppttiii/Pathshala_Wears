from django.urls import path
from django.contrib.auth import views as auth_views
from .auth_views import register, custom_login

app_name = 'auth'

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', custom_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='products:product_list'), name='logout'),
]
