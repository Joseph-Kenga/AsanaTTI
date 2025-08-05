from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from decimal import Decimal
from datetime import date, timedelta
import uuid


class LoanType(models.Model):
    """Different types of loans offered by the SACCO"""
    
    INTEREST_CALCULATION_CHOICES = [
        ('flat', 'Flat Rate'),
        ('reducing', 'Reducing Balance'),
        ('compound', 'Compound Interest'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    interest_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    interest_calculation_method = models.CharField(
        max_length=20, 
        choices=INTEREST_CALCULATION_CHOICES, 
        default='reducing'
    )
    minimum_amount = models.DecimalField(max_digits=12, decimal_places=2)
    maximum_amount = models.DecimalField(max_digits=12, decimal_places=2)
    minimum_term_months = models.PositiveIntegerField(default=1)
    maximum_term_months = models.PositiveIntegerField(default=60)
    processing_fee_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    requires_guarantor = models.BooleanField(default=True)
    minimum_guarantors = models.PositiveIntegerField(default=1)
    requires_collateral = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_loan_types'
    )
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Loan Type'
        verbose_name_plural = 'Loan Types'
    
    def __str__(self):
        return f"{self.name} ({self.interest_rate}%)"


class LoanApplication(models.Model):
    """Loan application submitted by members"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('disbursed', 'Disbursed'),
    ]
    
    PURPOSE_CHOICES = [
        ('business', 'Business'),
        ('education', 'Education'),
        ('medical', 'Medical'),
        ('agriculture', 'Agriculture'),
        ('emergency', 'Emergency'),
        ('development', 'Development'),
        ('other', 'Other'),
    ]
    
    application_number = models.CharField(max_length=20, unique=True)
    member = models.ForeignKey('members.Member', on_delete=models.CASCADE, related_name='loan_applications')
    loan_type = models.ForeignKey(LoanType, on_delete=models.CASCADE, related_name='applications')
    
    # Loan Details
    requested_amount = models.DecimalField(max_digits=12, decimal_places=2)
    approved_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    term_months = models.PositiveIntegerField()
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    purpose_description = models.TextField()
    
    # Status and Workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    application_date = models.DateTimeField(auto_now_add=True)
    review_date = models.DateTimeField(null=True, blank=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    disbursement_date = models.DateTimeField(null=True, blank=True)
    
    # Staff Assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_loan_applications'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_loan_applications'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_loan_applications'
    )
    
    # Comments and Notes
    member_comments = models.TextField(blank=True, null=True)
    staff_comments = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Loan Application'
        verbose_name_plural = 'Loan Applications'
    
    def __str__(self):
        return f"{self.application_number} - {self.member.get_full_name()}"
    
    def save(self, *args, **kwargs):
        if not self.application_number:
            # Generate application number
            year = date.today().year
            last_app = LoanApplication.objects.filter(
                application_number__startswith=f"LA{year}"
            ).order_by('-id').first()
            
            if last_app:
                last_number = int(last_app.application_number[-4:])
                self.application_number = f"LA{year}{str(last_number + 1).zfill(4)}"
            else:
                self.application_number = f"LA{year}0001"
        
        super().save(*args, **kwargs)
    
    @property
    def calculated_interest(self):
        """Calculate total interest based on loan type"""
        if not self.approved_amount:
            amount = self.requested_amount
        else:
            amount = self.approved_amount
            
        rate = self.loan_type.interest_rate / 100
        
        if self.loan_type.interest_calculation_method == 'flat':
            return amount * rate * (self.term_months / 12)
        elif self.loan_type.interest_calculation_method == 'reducing':
            # Simplified reducing balance calculation
            monthly_rate = rate / 12
            return amount * monthly_rate * self.term_months
        else:
            # Compound interest
            return amount * ((1 + rate) ** (self.term_months / 12) - 1)
    
    @property
    def processing_fee(self):
        """Calculate processing fee"""
        amount = self.approved_amount or self.requested_amount
        return amount * (self.loan_type.processing_fee_rate / 100)
    
    @property
    def total_repayment(self):
        """Calculate total amount to be repaid"""
        amount = self.approved_amount or self.requested_amount
        return amount + self.calculated_interest
    
    @property
    def monthly_repayment(self):
        """Calculate monthly repayment amount"""
        return self.total_repayment / self.term_months


class Loan(models.Model):
    """Active loan after disbursement"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('defaulted', 'Defaulted'),
        ('written_off', 'Written Off'),
        ('restructured', 'Restructured'),
    ]
    
    loan_number = models.CharField(max_length=20, unique=True)
    application = models.OneToOneField(LoanApplication, on_delete=models.CASCADE, related_name='loan')
    member = models.ForeignKey('members.Member', on_delete=models.CASCADE, related_name='loans')
    loan_type = models.ForeignKey(LoanType, on_delete=models.CASCADE, related_name='active_loans')
    
    # Loan Details
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    term_months = models.PositiveIntegerField()
    monthly_repayment = models.DecimalField(max_digits=12, decimal_places=2)
    total_interest = models.DecimalField(max_digits=12, decimal_places=2)
    processing_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Dates
    disbursement_date = models.DateField()
    first_repayment_date = models.DateField()
    maturity_date = models.DateField()
    
    # Current Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    outstanding_balance = models.DecimalField(max_digits=12, decimal_places=2)
    outstanding_interest = models.DecimalField(max_digits=12, decimal_places=2)
    total_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    penalty_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Staff
    loan_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='managed_loans'
    )
    disbursed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='disbursed_loans'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Loan'
        verbose_name_plural = 'Loans'
    
    def __str__(self):
        return f"{self.loan_number} - {self.member.get_full_name()}"
    
    def save(self, *args, **kwargs):
        if not self.loan_number:
            # Generate loan number
            year = date.today().year
            last_loan = Loan.objects.filter(
                loan_number__startswith=f"LN{year}"
            ).order_by('-id').first()
            
            if last_loan:
                last_number = int(last_loan.loan_number[-4:])
                self.loan_number = f"LN{year}{str(last_number + 1).zfill(4)}"
            else:
                self.loan_number = f"LN{year}0001"
        
        # Calculate maturity date
        if self.disbursement_date and not self.maturity_date:
            self.maturity_date = self.disbursement_date + timedelta(days=self.term_months * 30)
        
        # Calculate first repayment date (usually next month)
        if self.disbursement_date and not self.first_repayment_date:
            self.first_repayment_date = self.disbursement_date + timedelta(days=30)
        
        super().save(*args, **kwargs)
    
    @property
    def days_overdue(self):
        """Calculate number of days overdue"""
        if self.status != 'active':
            return 0
        
        from repayments.models import RepaymentSchedule
        overdue_schedules = RepaymentSchedule.objects.filter(
            loan=self,
            due_date__lt=date.today(),
            status='pending'
        )
        
        if overdue_schedules.exists():
            earliest_overdue = overdue_schedules.earliest('due_date')
            return (date.today() - earliest_overdue.due_date).days
        return 0
    
    @property
    def is_overdue(self):
        """Check if loan has overdue payments"""
        return self.days_overdue > 0
    
    @property
    def completion_percentage(self):
        """Calculate loan completion percentage"""
        if self.principal_amount + self.total_interest == 0:
            return 0
        total_loan = self.principal_amount + self.total_interest
        return (self.total_paid / total_loan) * 100


class LoanGuarantor(models.Model):
    """Link guarantors to specific loans"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('released', 'Released'),
        ('defaulted', 'Defaulted'),
    ]
    
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='loan_guarantors')
    guarantor = models.ForeignKey('members.Guarantor', on_delete=models.CASCADE, related_name='guaranteed_loans')
    guaranteed_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Loan Guarantor'
        verbose_name_plural = 'Loan Guarantors'
        unique_together = ['loan', 'guarantor']
    
    def __str__(self):
        return f"{self.guarantor} - {self.loan.loan_number}"


class LoanDocument(models.Model):
    """Documents related to loan applications and active loans"""
    
    DOCUMENT_TYPES = [
        ('application_form', 'Application Form'),
        ('guarantor_form', 'Guarantor Form'),
        ('collateral_document', 'Collateral Document'),
        ('approval_letter', 'Approval Letter'),
        ('disbursement_voucher', 'Disbursement Voucher'),
        ('loan_agreement', 'Loan Agreement'),
        ('other', 'Other'),
    ]
    
    loan_application = models.ForeignKey(
        LoanApplication, 
        on_delete=models.CASCADE, 
        related_name='documents',
        null=True,
        blank=True
    )
    loan = models.ForeignKey(
        Loan, 
        on_delete=models.CASCADE, 
        related_name='documents',
        null=True,
        blank=True
    )
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=100)
    file = models.FileField(upload_to='loan_documents/')
    description = models.TextField(blank=True, null=True)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name = 'Loan Document'
        verbose_name_plural = 'Loan Documents'
    
    def __str__(self):
        if self.loan:
            return f"{self.title} - {self.loan.loan_number}"
        return f"{self.title} - {self.loan_application.application_number}"


class LoanTopUp(models.Model):
    """Track loan top-ups and restructuring"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    
    original_loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='topups')
    new_loan = models.ForeignKey(
        Loan, 
        on_delete=models.CASCADE, 
        related_name='topup_source',
        null=True,
        blank=True
    )
    
    topup_amount = models.DecimalField(max_digits=12, decimal_places=2)
    new_term_months = models.PositiveIntegerField()
    new_monthly_repayment = models.DecimalField(max_digits=12, decimal_places=2)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reason = models.TextField()
    
    requested_date = models.DateTimeField(auto_now_add=True)
    approved_date = models.DateTimeField(null=True, blank=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='requested_topups'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_topups'
    )
    
    class Meta:
        verbose_name = 'Loan Top-up'
        verbose_name_plural = 'Loan Top-ups'
    
    def __str__(self):
        return f"Top-up {self.original_loan.loan_number} - {self.topup_amount}"
