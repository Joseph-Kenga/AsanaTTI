from django.db import models
from django.contrib.auth.models import User
from orders.models import Order
from tables.models import Table
from decimal import Decimal

class Bill(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('mobile_money', 'Mobile Money'),
        ('other', 'Other'),
    ]
    
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='bills')
    orders = models.ManyToManyField(Order, related_name='bills')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)
    cashier = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bills_processed', blank=True, null=True)
    customer_name = models.CharField(max_length=200, blank=True, null=True)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    special_requests = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    receipt_printed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Bill #{self.id} - Table {self.table.table_number} - {self.payment_status}"
    
    def calculate_totals(self):
        # Calculate subtotal from all orders
        self.subtotal = sum(order.total_amount for order in self.orders.all())
        
        # Calculate tax (assuming 10% tax rate)
        self.tax_amount = self.subtotal * Decimal('0.10')
        
        # Calculate total
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount
        self.save()
    
    @property
    def is_paid(self):
        return self.payment_status == 'paid'
    
    @property
    def can_print_receipt(self):
        return self.is_paid and not self.receipt_printed
    
    class Meta:
        ordering = ['-created_at']

class Receipt(models.Model):
    bill = models.OneToOneField(Bill, on_delete=models.CASCADE, related_name='receipt')
    receipt_number = models.CharField(max_length=50, unique=True)
    printed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='receipts_printed')
    printed_at = models.DateTimeField(auto_now_add=True)
    receipt_data = models.JSONField(default=dict)  # Store receipt details as JSON
    
    def __str__(self):
        return f"Receipt #{self.receipt_number} - Bill #{self.bill.id}"
    
    def generate_receipt_number(self):
        import datetime
        now = datetime.datetime.now()
        return f"RCP{now.strftime('%Y%m%d')}{self.bill.id:04d}"
    
    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = self.generate_receipt_number()
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-printed_at']

class Payment(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=Bill.PAYMENT_METHOD_CHOICES)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    processed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments_processed')
    processed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Payment ${self.amount} - Bill #{self.bill.id}"
    
    class Meta:
        ordering = ['-processed_at']

class TableTransfer(models.Model):
    from_table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='transfers_from')
    to_table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='transfers_to')
    orders = models.ManyToManyField(Order, related_name='table_transfers')
    transferred_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='table_transfers_made')
    transferred_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Transfer from Table {self.from_table.table_number} to Table {self.to_table.table_number}"
    
    class Meta:
        ordering = ['-transferred_at']
