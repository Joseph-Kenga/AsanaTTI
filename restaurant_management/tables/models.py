from django.db import models
from django.contrib.auth.models import User

class Table(models.Model):
    TABLE_STATUS_CHOICES = [
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('reserved', 'Reserved'),
        ('cleaning', 'Cleaning'),
    ]
    
    table_number = models.IntegerField(unique=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    capacity = models.IntegerField(default=4)
    current_occupancy = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=TABLE_STATUS_CHOICES, default='available')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Table {self.table_number} - {self.name or 'Unnamed'}"
    
    @property
    def is_available(self):
        return self.status == 'available' and self.current_occupancy == 0
    
    @property
    def has_active_order(self):
        return self.order_set.filter(status__in=['pending', 'preparing', 'ready']).exists()
    
    class Meta:
        ordering = ['table_number']
