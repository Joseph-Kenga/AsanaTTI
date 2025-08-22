from django.contrib import admin
from .models import (
    Category, Item, Size, Topping, CookingPreference,
    ItemSize, ItemTopping, ItemCookingPreference
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_order', 'is_active', 'item_count']
    list_filter = ['is_active']
    search_fields = ['name']
    list_editable = ['display_order', 'is_active']
    ordering = ['display_order', 'name']
    
    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Items'

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'item_type', 'base_price', 'is_available', 'preparation_time']
    list_filter = ['category', 'item_type', 'is_available']
    search_fields = ['name', 'description']
    list_editable = ['base_price', 'is_available', 'preparation_time']
    ordering = ['category', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'item_type')
        }),
        ('Pricing & Availability', {
            'fields': ('base_price', 'is_available', 'preparation_time')
        }),
        ('Media', {
            'fields': ('image',),
            'classes': ('collapse',)
        }),
    )

@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ['name', 'price_modifier', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    list_editable = ['price_modifier', 'is_active']
    ordering = ['price_modifier']

@admin.register(Topping)
class ToppingAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    list_editable = ['price', 'is_active']
    ordering = ['name']

@admin.register(CookingPreference)
class CookingPreferenceAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    ordering = ['name']

@admin.register(ItemSize)
class ItemSizeAdmin(admin.ModelAdmin):
    list_display = ['item', 'size', 'price', 'is_available']
    list_filter = ['is_available', 'size']
    search_fields = ['item__name', 'size__name']
    list_editable = ['price', 'is_available']
    ordering = ['item', 'size']

@admin.register(ItemTopping)
class ItemToppingAdmin(admin.ModelAdmin):
    list_display = ['item', 'topping', 'is_available']
    list_filter = ['is_available', 'topping']
    search_fields = ['item__name', 'topping__name']
    list_editable = ['is_available']
    ordering = ['item', 'topping']

@admin.register(ItemCookingPreference)
class ItemCookingPreferenceAdmin(admin.ModelAdmin):
    list_display = ['item', 'cooking_preference', 'is_available']
    list_filter = ['is_available', 'cooking_preference']
    search_fields = ['item__name', 'cooking_preference__name']
    list_editable = ['is_available']
    ordering = ['item', 'cooking_preference']
