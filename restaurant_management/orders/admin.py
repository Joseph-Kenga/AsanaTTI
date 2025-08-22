from django.contrib import admin
from .models import Order, OrderItem, OrderItemTopping, OrderStatusHistory

class OrderItemToppingInline(admin.TabularInline):
    model = OrderItemTopping
    extra = 1

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    inlines = [OrderItemToppingInline]

class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ['created_at']
    can_delete = False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'table', 'waiter', 'status', 'order_type', 'total_amount', 'created_at']
    list_filter = ['status', 'order_type', 'created_at']
    search_fields = ['table__table_number', 'waiter__username', 'special_instructions']
    list_editable = ['status']
    ordering = ['-created_at']
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('table', 'waiter', 'status', 'order_type')
        }),
        ('Details', {
            'fields': ('special_instructions',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    
    def total_amount(self, obj):
        return f"${obj.total_amount}"
    total_amount.short_description = 'Total'

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'item', 'size', 'quantity', 'unit_price', 'total_price', 'cooking_preference']
    list_filter = ['item__category', 'item__item_type', 'cooking_preference']
    search_fields = ['order__id', 'item__name', 'special_instructions']
    ordering = ['-created_at']
    inlines = [OrderItemToppingInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order', 'item', 'quantity')
        }),
        ('Customization', {
            'fields': ('size', 'cooking_preference', 'special_instructions')
        }),
        ('Pricing', {
            'fields': ('unit_price',)
        }),
    )
    
    def total_price(self, obj):
        return f"${obj.total_price}"
    total_price.short_description = 'Total Price'

@admin.register(OrderItemTopping)
class OrderItemToppingAdmin(admin.ModelAdmin):
    list_display = ['order_item', 'topping', 'topping_price']
    list_filter = ['topping']
    search_fields = ['order_item__item__name', 'topping__name']
    ordering = ['order_item', 'topping']
    
    def topping_price(self, obj):
        return f"${obj.topping.price}"
    topping_price.short_description = 'Topping Price'

@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['order', 'status', 'changed_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order__id', 'changed_by__username', 'notes']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Status Change', {
            'fields': ('order', 'status', 'changed_by')
        }),
        ('Details', {
            'fields': ('notes',)
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
