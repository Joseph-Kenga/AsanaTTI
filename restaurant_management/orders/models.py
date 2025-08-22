from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from tables.models import Table
from menu.models import Item, Size, Topping, CookingPreference
from decimal import Decimal

class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('served', 'Served'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    ORDER_TYPE_CHOICES = [
        ('kitchen', 'Kitchen'),
        ('bar', 'Bar'),
        ('both', 'Both'),
    ]
    
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='orders')
    waiter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders_created')
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    order_type = models.CharField(max_length=10, choices=ORDER_TYPE_CHOICES, default='both')
    special_instructions = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"Order #{self.id} - Table {self.table.table_number} - {self.status}"
    
    @property
    def total_amount(self):
        return sum(item.total_price for item in self.order_items.all())
    
    @property
    def has_kitchen_items(self):
        return self.order_items.filter(item__item_type='food').exists()
    
    @property
    def has_bar_items(self):
        return self.order_items.filter(item__item_type='drink').exists()
    
    def update_order_type(self):
        if self.has_kitchen_items and self.has_bar_items:
            self.order_type = 'both'
        elif self.has_kitchen_items:
            self.order_type = 'kitchen'
        elif self.has_bar_items:
            self.order_type = 'bar'
        self.save()
    
    class Meta:
        ordering = ['-created_at']

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    cooking_preference = models.ForeignKey(CookingPreference, on_delete=models.SET_NULL, blank=True, null=True)
    special_instructions = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.quantity}x {self.item.name} - Order #{self.order.id}"
    
    @property
    def total_price(self):
        base_price = self.unit_price * self.quantity
        topping_price = sum(topping.topping.price for topping in self.order_item_toppings.all())
        return base_price + topping_price
    
    @property
    def toppings_list(self):
        return [topping.topping.name for topping in self.order_item_toppings.all()]

class OrderItemTopping(models.Model):
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='order_item_toppings')
    topping = models.ForeignKey(Topping, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.topping.name} - {self.order_item}"
    
    class Meta:
        unique_together = ['order_item', 'topping']

class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20, choices=Order.ORDER_STATUS_CHOICES)
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Order #{self.order.id} - {self.status} by {self.changed_by.username}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Order status histories"
