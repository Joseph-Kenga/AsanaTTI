from django.urls import path
from . import views

app_name = 'tables'

urlpatterns = [
    path('', views.table_dashboard, name='dashboard'),
    path('list/', views.table_list, name='list'),
    path('<int:table_id>/', views.table_detail, name='detail'),
    path('<int:table_id>/status/', views.update_table_status, name='update_status'),
    path('<int:table_id>/occupancy/', views.update_table_occupancy, name='update_occupancy'),
    path('<int:table_id>/clear/', views.clear_table, name='clear'),
    path('api/status/', views.table_status_api, name='status_api'),
]