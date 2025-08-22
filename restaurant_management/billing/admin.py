from django.contrib import admin
from .models import Bill, Receipt, Payment, TableTransfer

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 1
    readonly_fields = ['processed_at']

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ['id', 'table', 'payment_status', 'subtotal', 'tax_amount', 'total_amount', 'cashier', 'created_at']
    list_filter = ['payment_status', 'payment_method', 'created_at']
    search_fields = ['table__table_number', 'customer_name', 'customer_phone']
    list_editable = ['payment_status']
    ordering = ['-created_at']
    inlines = [PaymentInline]
    
    fieldsets = (
        ('Bill Information', {
            'fields': ('table', 'orders', 'payment_status', 'payment_method')
        }),
        ('Customer Information', {
            'fields': ('customer_name', 'customer_phone', 'special_requests')
        }),
        ('Financial', {
            'fields': ('subtotal', 'tax_amount', 'discount_amount', 'total_amount')
        }),
        ('Processing', {
            'fields': ('cashier', 'receipt_printed')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'paid_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'paid_at']
    
    def save_model(self, request, obj, form, change):
        if not change:  # New bill
            obj.cashier = request.user
        super().save_model(request, obj, form, change)

@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'bill', 'printed_by', 'printed_at']
    list_filter = ['printed_at']
    search_fields = ['receipt_number', 'bill__id']
    ordering = ['-printed_at']
    readonly_fields = ['receipt_number', 'printed_at']
    
    fieldsets = (
        ('Receipt Information', {
            'fields': ('bill', 'receipt_number', 'printed_by')
        }),
        ('Receipt Data', {
            'fields': ('receipt_data',),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('printed_at',),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # New receipt
            obj.printed_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['bill', 'amount', 'payment_method', 'reference_number', 'processed_by', 'processed_at']
    list_filter = ['payment_method', 'processed_at']
    search_fields = ['bill__id', 'reference_number', 'processed_by__username']
    ordering = ['-processed_at']
    readonly_fields = ['processed_at']
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('bill', 'amount', 'payment_method', 'reference_number')
        }),
        ('Processing', {
            'fields': ('processed_by', 'notes')
        }),
        ('Timestamp', {
            'fields': ('processed_at',),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # New payment
            obj.processed_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(TableTransfer)
class TableTransferAdmin(admin.ModelAdmin):
    list_display = ['from_table', 'to_table', 'transferred_by', 'transferred_at', 'order_count']
    list_filter = ['transferred_at']
    search_fields = ['from_table__table_number', 'to_table__table_number', 'transferred_by__username']
    ordering = ['-transferred_at']
    readonly_fields = ['transferred_at']
    
    fieldsets = (
        ('Transfer Information', {
            'fields': ('from_table', 'to_table', 'orders')
        }),
        ('Details', {
            'fields': ('transferred_by', 'reason')
        }),
        ('Timestamp', {
            'fields': ('transferred_at',),
            'classes': ('collapse',)
        }),
    )
    
    def order_count(self, obj):
        return obj.orders.count()
    order_count.short_description = 'Orders'
    
    def save_model(self, request, obj, form, change):
        if not change:  # New transfer
            obj.transferred_by = request.user
        super().save_model(request, obj, form, change)
