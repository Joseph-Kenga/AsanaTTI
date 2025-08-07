from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from phonenumber_field.modelfields import PhoneNumberField
from PIL import Image
import os


class User(AbstractUser):
    """Extended User model with role-based permissions"""
    
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('accountant', 'Accountant'),
        ('loan_officer', 'Loan Officer'),
        ('member', 'Member'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    phone_number = PhoneNumberField(blank=True, null=True)
    employee_id = models.CharField(max_length=20, blank=True, null=True, unique=True)
    is_active_staff = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_accountant(self):
        return self.role == 'accountant'
    
    @property
    def is_loan_officer(self):
        return self.role == 'loan_officer'
    
    @property
    def is_member(self):
        return self.role == 'member'


class Member(models.Model):
    """Member profile with comprehensive information"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('blacklisted', 'Blacklisted'),
    ]
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    MARITAL_STATUS_CHOICES = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='member_profile')
    member_number = models.CharField(max_length=20, unique=True)
    national_id = models.CharField(max_length=20, unique=True)
    
    # Personal Information
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES)
    
    # Contact Information
    phone_number = PhoneNumberField()
    alternative_phone = PhoneNumberField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    
    # Address Information
    county = models.CharField(max_length=50)
    sub_county = models.CharField(max_length=50)
    ward = models.CharField(max_length=50)
    village = models.CharField(max_length=50)
    postal_address = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=10, blank=True, null=True)
    
    # Employment/Business Information
    occupation = models.CharField(max_length=100)
    employer_name = models.CharField(max_length=100, blank=True, null=True)
    business_name = models.CharField(max_length=100, blank=True, null=True)
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    
    # SACCO Information
    registration_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    assigned_loan_officer = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_members',
        limit_choices_to={'role': 'loan_officer'}
    )
    
    # Photo
    photo = models.ImageField(upload_to='member_photos/', blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_members'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Member'
        verbose_name_plural = 'Members'
    
    def __str__(self):
        return f"{self.member_number} - {self.get_full_name()}"
    
    def get_full_name(self):
        names = [self.first_name]
        if self.middle_name:
            names.append(self.middle_name)
        names.append(self.last_name)
        return ' '.join(names)
    
    def save(self, *args, **kwargs):
        # Generate member number if not provided
        if not self.member_number:
            last_member = Member.objects.order_by('-id').first()
            if last_member:
                last_number = int(last_member.member_number.split('-')[-1])
                self.member_number = f"MEM-{str(last_number + 1).zfill(6)}"
            else:
                self.member_number = "MEM-000001"
        
        super().save(*args, **kwargs)
        
        # Resize image if uploaded
        if self.photo:
            img = Image.open(self.photo.path)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.photo.path)


class NextOfKin(models.Model):
    """Next of kin information for members"""
    
    RELATIONSHIP_CHOICES = [
        ('spouse', 'Spouse'),
        ('parent', 'Parent'),
        ('child', 'Child'),
        ('sibling', 'Sibling'),
        ('friend', 'Friend'),
        ('other', 'Other'),
    ]
    
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='next_of_kin')
    full_name = models.CharField(max_length=100)
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    phone_number = PhoneNumberField()
    national_id = models.CharField(max_length=20)
    address = models.TextField()
    is_primary = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Next of Kin'
        verbose_name_plural = 'Next of Kin'
    
    def __str__(self):
        return f"{self.full_name} - {self.member.get_full_name()}"


class Guarantor(models.Model):
    """Guarantor information for loan applications"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('blacklisted', 'Blacklisted'),
    ]
    
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='guarantors')
    guarantor_member = models.ForeignKey(
        Member, 
        on_delete=models.CASCADE, 
        related_name='guaranteed_members',
        null=True,
        blank=True
    )
    
    # If guarantor is not a member
    full_name = models.CharField(max_length=100, blank=True, null=True)
    national_id = models.CharField(max_length=20, blank=True, null=True)
    phone_number = PhoneNumberField(blank=True, null=True)
    occupation = models.CharField(max_length=100, blank=True, null=True)
    employer = models.CharField(max_length=100, blank=True, null=True)
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    
    # Collateral Information
    collateral_type = models.CharField(max_length=100)
    collateral_description = models.TextField()
    collateral_value = models.DecimalField(max_digits=12, decimal_places=2)
    collateral_location = models.CharField(max_length=200)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Guarantor'
        verbose_name_plural = 'Guarantors'
    
    def __str__(self):
        if self.guarantor_member:
            return f"{self.guarantor_member.get_full_name()} guarantees {self.member.get_full_name()}"
        return f"{self.full_name} guarantees {self.member.get_full_name()}"


class MemberDocument(models.Model):
    """Documents uploaded by or for members"""
    
    DOCUMENT_TYPES = [
        ('id_copy', 'National ID Copy'),
        ('passport_photo', 'Passport Photo'),
        ('payslip', 'Payslip'),
        ('bank_statement', 'Bank Statement'),
        ('business_permit', 'Business Permit'),
        ('land_title', 'Land Title Deed'),
        ('other', 'Other'),
    ]
    
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=100)
    file = models.FileField(upload_to='member_documents/')
    description = models.TextField(blank=True, null=True)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name = 'Member Document'
        verbose_name_plural = 'Member Documents'
    
    def __str__(self):
        return f"{self.title} - {self.member.get_full_name()}"


class MemberActivity(models.Model):
    """Track member activities and interactions"""
    
    ACTIVITY_TYPES = [
        ('registration', 'Member Registration'),
        ('profile_update', 'Profile Update'),
        ('loan_application', 'Loan Application'),
        ('loan_approval', 'Loan Approval'),
        ('loan_disbursement', 'Loan Disbursement'),
        ('repayment', 'Loan Repayment'),
        ('contact', 'Contact/Communication'),
        ('status_change', 'Status Change'),
        ('other', 'Other'),
    ]
    
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    title = models.CharField(max_length=100)
    description = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Member Activity'
        verbose_name_plural = 'Member Activities'
    
    def __str__(self):
        return f"{self.title} - {self.member.get_full_name()}"
