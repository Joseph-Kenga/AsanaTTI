from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.order_dashboard, name='dashboard'),
    path('create/<int:table_id>/', views.create_order, name='create'),
    path('<int:order_id>/', views.order_detail, name='detail'),
    path('<int:order_id>/status/', views.update_order_status, name='update_status'),
    path('<int:order_id>/add-items/', views.add_item_to_order, name='add_items'),
    path('item/<int:order_item_id>/modify/', views.modify_order_item, name='modify_item'),
    path('kitchen/', views.kitchen_orders, name='kitchen'),
    path('bar/', views.bar_orders, name='bar'),
    path('api/status/', views.order_status_api, name='status_api'),
]