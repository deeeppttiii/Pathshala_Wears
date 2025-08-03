from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('product/<int:product_id>/review/', views.add_review, name='add_review'),
]

# from django.urls import path
# from . import views

# urlpatterns = [
#     path('', views.product_list, name='product_list'),  # maps /products/
#     path('<slug:slug>/', views.product_detail, name='product_detail'),
#     path('<int:product_id>/review/', views.add_review, name='add_review'),
# ]
