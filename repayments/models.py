from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
from datetime import date, timedelta


class RepaymentSchedule(models.Model):
    """Scheduled repayment installments for loans"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('waived', 'Waived'),
    ]
    
    loan = models.ForeignKey('loans.Loan', on_delete=models.CASCADE, related_name='repayment_schedule')
    installment_number = models.PositiveIntegerField()
    due_date = models.DateField()
    
    # Amounts
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_amount = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Payments
    principal_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    interest_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    penalty_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Outstanding
    principal_outstanding = models.DecimalField(max_digits=12, decimal_places=2)
    interest_outstanding = models.DecimalField(max_digits=12, decimal_places=2)
    penalty_outstanding = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_outstanding = models.DecimalField(max_digits=12, decimal_places=2)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_date = models.DateField(null=True, blank=True)
    days_overdue = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['loan', 'installment_number']
        unique_together = ['loan', 'installment_number']
        verbose_name = 'Repayment Schedule'
        verbose_name_plural = 'Repayment Schedules'
    
    def __str__(self):
        return f"{self.loan.loan_number} - Installment {self.installment_number}"
    
    def save(self, *args, **kwargs):
        # Calculate outstanding amounts
        self.principal_outstanding = self.principal_amount - self.principal_paid
        self.interest_outstanding = self.interest_amount - self.interest_paid
        self.total_outstanding = (self.principal_outstanding + 
                                self.interest_outstanding + 
                                self.penalty_outstanding - self.penalty_paid)
        
        # Update status based on payments
        if self.total_paid >= self.total_amount + self.penalty_outstanding:
            self.status = 'paid'
            if not self.payment_date:
                self.payment_date = date.today()
        elif self.total_paid > 0:
            self.status = 'partial'
        elif self.due_date < date.today():
            self.status = 'overdue'
            self.days_overdue = (date.today() - self.due_date).days
        else:
            self.status = 'pending'
        
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        """Check if installment is overdue"""
        return self.due_date < date.today() and self.status in ['pending', 'partial']
    
    @property
    def penalty_amount(self):
        """Calculate penalty for overdue installment"""
        if not self.is_overdue:
            return Decimal('0.00')
        
        # Get penalty rate from settings
        from django.conf import settings
        penalty_rate = Decimal(str(settings.SACCO_SETTINGS.get('PENALTY_RATE', 5.0))) / 100
        
        # Calculate penalty based on outstanding amount and days overdue
        penalty = self.total_outstanding * penalty_rate * (self.days_overdue / 30)
        return penalty.quantize(Decimal('0.01'))


class RepaymentTransaction(models.Model):
    """Individual repayment transactions"""
    
    TRANSACTION_TYPES = [
        ('cash', 'Cash Payment'),
        ('bank_transfer', 'Bank Transfer'),
        ('mobile_money', 'Mobile Money'),
        ('cheque', 'Cheque'),
        ('mpesa', 'M-Pesa'),
        ('bank_deposit', 'Bank Deposit'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('reversed', 'Reversed'),
    ]
    
    transaction_number = models.CharField(max_length=30, unique=True)
    loan = models.ForeignKey('loans.Loan', on_delete=models.CASCADE, related_name='repayment_transactions')
    member = models.ForeignKey('members.Member', on_delete=models.CASCADE, related_name='repayments')
    
    # Transaction Details
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    reference_number = models.CharField(max_length=50, blank=True, null=True)
    
    # Allocation
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    interest_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    penalty_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    processing_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Status and Dates
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_date = models.DateTimeField(auto_now_add=True)
    value_date = models.DateField(default=date.today)
    confirmed_date = models.DateTimeField(null=True, blank=True)
    
    # Staff and Processing
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='received_repayments'
    )
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_repayments'
    )
    
    # Additional Information
    notes = models.TextField(blank=True, null=True)
    receipt_number = models.CharField(max_length=30, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-transaction_date']
        verbose_name = 'Repayment Transaction'
        verbose_name_plural = 'Repayment Transactions'
    
    def __str__(self):
        return f"{self.transaction_number} - {self.loan.loan_number} - {self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.transaction_number:
            # Generate transaction number
            from datetime import datetime
            today = datetime.now()
            prefix = f"TXN{today.strftime('%Y%m%d')}"
            
            last_txn = RepaymentTransaction.objects.filter(
                transaction_number__startswith=prefix
            ).order_by('-id').first()
            
            if last_txn:
                last_number = int(last_txn.transaction_number[-4:])
                self.transaction_number = f"{prefix}{str(last_number + 1).zfill(4)}"
            else:
                self.transaction_number = f"{prefix}0001"
        
        super().save(*args, **kwargs)
        
        # Update loan balances if transaction is completed
        if self.status == 'completed':
            self.update_loan_balances()
    
    def update_loan_balances(self):
        """Update loan outstanding balances after successful payment"""
        loan = self.loan
        
        # Update loan totals
        loan.total_paid += self.amount
        loan.outstanding_balance -= self.principal_amount
        loan.outstanding_interest -= self.interest_amount
        loan.penalty_balance -= self.penalty_amount
        
        # Ensure balances don't go negative
        loan.outstanding_balance = max(loan.outstanding_balance, Decimal('0.00'))
        loan.outstanding_interest = max(loan.outstanding_interest, Decimal('0.00'))
        loan.penalty_balance = max(loan.penalty_balance, Decimal('0.00'))
        
        # Check if loan is fully paid
        total_outstanding = (loan.outstanding_balance + 
                           loan.outstanding_interest + 
                           loan.penalty_balance)
        
        if total_outstanding <= Decimal('1.00'):  # Allow for small rounding differences
            loan.status = 'completed'
        
        loan.save()
        
        # Update repayment schedules
        self.allocate_to_schedules()
    
    def allocate_to_schedules(self):
        """Allocate payment to repayment schedules"""
        remaining_amount = self.amount
        
        # Get pending/partial schedules in order
        schedules = RepaymentSchedule.objects.filter(
            loan=self.loan,
            status__in=['pending', 'partial', 'overdue']
        ).order_by('due_date')
        
        for schedule in schedules:
            if remaining_amount <= 0:
                break
            
            # Calculate how much to pay for this schedule
            schedule_outstanding = schedule.total_outstanding + schedule.penalty_outstanding
            payment_for_schedule = min(remaining_amount, schedule_outstanding)
            
            if payment_for_schedule > 0:
                # Allocate payment (penalties first, then interest, then principal)
                penalty_payment = min(payment_for_schedule, schedule.penalty_outstanding)
                schedule.penalty_paid += penalty_payment
                payment_for_schedule -= penalty_payment
                
                interest_payment = min(payment_for_schedule, schedule.interest_outstanding)
                schedule.interest_paid += interest_payment
                payment_for_schedule -= interest_payment
                
                principal_payment = min(payment_for_schedule, schedule.principal_outstanding)
                schedule.principal_paid += principal_payment
                
                schedule.total_paid += (penalty_payment + interest_payment + principal_payment)
                schedule.save()
                
                remaining_amount -= (penalty_payment + interest_payment + principal_payment)


class PenaltyTransaction(models.Model):
    """Track penalty charges applied to overdue loans"""
    
    STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('waived', 'Waived'),
        ('reversed', 'Reversed'),
    ]
    
    loan = models.ForeignKey('loans.Loan', on_delete=models.CASCADE, related_name='penalty_transactions')
    repayment_schedule = models.ForeignKey(
        RepaymentSchedule, 
        on_delete=models.CASCADE, 
        related_name='penalties'
    )
    
    penalty_amount = models.DecimalField(max_digits=12, decimal_places=2)
    penalty_rate = models.DecimalField(max_digits=5, decimal_places=2)
    days_overdue = models.PositiveIntegerField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='applied')
    applied_date = models.DateField(default=date.today)
    
    applied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='applied_penalties'
    )
    waived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='waived_penalties'
    )
    
    reason = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Penalty Transaction'
        verbose_name_plural = 'Penalty Transactions'
    
    def __str__(self):
        return f"Penalty {self.loan.loan_number} - {self.penalty_amount}"


class RepaymentReminder(models.Model):
    """Track repayment reminders sent to members"""
    
    REMINDER_TYPES = [
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('call', 'Phone Call'),
        ('visit', 'Physical Visit'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    loan = models.ForeignKey('loans.Loan', on_delete=models.CASCADE, related_name='reminders')
    repayment_schedule = models.ForeignKey(
        RepaymentSchedule, 
        on_delete=models.CASCADE, 
        related_name='reminders'
    )
    
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPES)
    message = models.TextField()
    scheduled_date = models.DateTimeField()
    sent_date = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Contact details used
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email_address = models.EmailField(blank=True, null=True)
    
    # Response tracking
    response_received = models.BooleanField(default=False)
    response_message = models.TextField(blank=True, null=True)
    
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_reminders'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scheduled_date']
        verbose_name = 'Repayment Reminder'
        verbose_name_plural = 'Repayment Reminders'
    
    def __str__(self):
        return f"{self.reminder_type} reminder - {self.loan.loan_number}"


class EarlyRepayment(models.Model):
    """Track early repayment requests and calculations"""
    
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('calculated', 'Calculated'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    loan = models.ForeignKey('loans.Loan', on_delete=models.CASCADE, related_name='early_repayments')
    
    # Request Details
    request_date = models.DateField(default=date.today)
    proposed_payment_date = models.DateField()
    
    # Calculations
    outstanding_principal = models.DecimalField(max_digits=12, decimal_places=2)
    outstanding_interest = models.DecimalField(max_digits=12, decimal_places=2)
    penalty_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    early_settlement_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_settlement_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    
    # Processing
    calculated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='calculated_early_repayments'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_early_repayments'
    )
    
    # Final transaction
    settlement_transaction = models.ForeignKey(
        RepaymentTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='early_settlement'
    )
    
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Early Repayment'
        verbose_name_plural = 'Early Repayments'
    
    def __str__(self):
        return f"Early repayment - {self.loan.loan_number}"
    
    def calculate_settlement_amount(self):
        """Calculate the early settlement amount"""
        # This is a simplified calculation - you may want to implement more complex logic
        self.outstanding_principal = self.loan.outstanding_balance
        self.outstanding_interest = self.loan.outstanding_interest
        self.penalty_amount = self.loan.penalty_balance
        
        # Apply early settlement discount (e.g., 10% of remaining interest)
        self.early_settlement_discount = self.outstanding_interest * Decimal('0.10')
        
        self.total_settlement_amount = (
            self.outstanding_principal + 
            self.outstanding_interest - 
            self.early_settlement_discount + 
            self.penalty_amount
        )
        
        self.status = 'calculated'
        self.save()


class RepaymentReport(models.Model):
    """Generated repayment reports and statements"""
    
    REPORT_TYPES = [
        ('member_statement', 'Member Statement'),
        ('loan_statement', 'Loan Statement'),
        ('collection_report', 'Collection Report'),
        ('overdue_report', 'Overdue Report'),
        ('penalty_report', 'Penalty Report'),
    ]
    
    report_type = models.CharField(max_length=30, choices=REPORT_TYPES)
    title = models.CharField(max_length=100)
    
    # Filters
    member = models.ForeignKey(
        'members.Member', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='repayment_reports'
    )
    loan = models.ForeignKey(
        'loans.Loan', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='repayment_reports'
    )
    date_from = models.DateField()
    date_to = models.DateField()
    
    # Generated Report
    report_file = models.FileField(upload_to='repayment_reports/', blank=True, null=True)
    report_data = models.JSONField(blank=True, null=True)
    
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_repayment_reports'
    )
    
    class Meta:
        ordering = ['-generated_at']
        verbose_name = 'Repayment Report'
        verbose_name_plural = 'Repayment Reports'
    
    def __str__(self):
        return f"{self.title} - {self.generated_at.strftime('%Y-%m-%d')}"
