from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('', views.billing_dashboard, name='dashboard'),
    path('create/<int:table_id>/', views.create_bill, name='create_bill'),
    path('bill/<int:bill_id>/', views.bill_detail, name='bill_detail'),
    path('bill/<int:bill_id>/payment/', views.process_payment, name='process_payment'),
    path('bill/<int:bill_id>/receipt/', views.print_receipt, name='print_receipt'),
    path('bill/<int:bill_id>/payments/', views.payment_history, name='payment_history'),
    path('receipt/<int:receipt_id>/', views.receipt_detail, name='receipt_detail'),
    path('transfer/<int:table_id>/', views.transfer_table, name='transfer_table'),
    path('bills/', views.bill_list, name='bill_list'),
    path('api/', views.billing_api, name='api'),
]