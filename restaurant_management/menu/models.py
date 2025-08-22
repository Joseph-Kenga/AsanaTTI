from django.db import models
from django.core.validators import MinValueValidator

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['display_order', 'name']

class Item(models.Model):
    ITEM_TYPE_CHOICES = [
        ('food', 'Food'),
        ('drink', 'Drink'),
        ('dessert', 'Dessert'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES, default='food')
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    preparation_time = models.IntegerField(default=15, help_text="Preparation time in minutes")
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.category.name}"
    
    class Meta:
        ordering = ['category', 'name']

class Size(models.Model):
    name = models.CharField(max_length=50)  # e.g., Small, Medium, Large
    price_modifier = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} (+${self.price_modifier})"
    
    class Meta:
        ordering = ['price_modifier']

class Topping(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} (${self.price})"
    
    class Meta:
        ordering = ['name']

class CookingPreference(models.Model):
    name = models.CharField(max_length=100)  # e.g., Rare, Medium, Well Done
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class ItemSize(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='available_sizes')
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.item.name} - {self.size.name} (${self.price})"
    
    class Meta:
        unique_together = ['item', 'size']

class ItemTopping(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='available_toppings')
    topping = models.ForeignKey(Topping, on_delete=models.CASCADE)
    is_available = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.item.name} - {self.topping.name}"
    
    class Meta:
        unique_together = ['item', 'topping']

class ItemCookingPreference(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='available_cooking_preferences')
    cooking_preference = models.ForeignKey(CookingPreference, on_delete=models.CASCADE)
    is_available = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.item.name} - {self.cooking_preference.name}"
    
    class Meta:
        unique_together = ['item', 'cooking_preference']
