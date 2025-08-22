from django.contrib import admin
from .models import Table

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ['table_number', 'name', 'capacity', 'current_occupancy', 'status', 'is_active', 'has_active_order']
    list_filter = ['status', 'is_active', 'capacity']
    search_fields = ['table_number', 'name']
    list_editable = ['status', 'current_occupancy', 'is_active']
    ordering = ['table_number']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('table_number', 'name', 'capacity')
        }),
        ('Status', {
            'fields': ('status', 'current_occupancy', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def has_active_order(self, obj):
        return obj.has_active_order
    has_active_order.boolean = True
    has_active_order.short_description = 'Active Order'
