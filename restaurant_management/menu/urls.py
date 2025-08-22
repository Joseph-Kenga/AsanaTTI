from django.urls import path
from . import views

app_name = 'menu'

urlpatterns = [
    path('', views.menu_dashboard, name='dashboard'),
    path('categories/', views.category_list, name='category_list'),
    path('items/', views.item_list, name='item_list'),
    path('item/<int:item_id>/', views.item_detail, name='item_detail'),
    path('api/items/', views.menu_api, name='api'),
]