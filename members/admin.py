from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    User, Member, NextOfKin, Guarantor, 
    MemberDocument, MemberActivity
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin with role-based management"""
    
    list_display = [
        'username', 'email', 'first_name', 'last_name', 
        'role', 'employee_id', 'is_active', 'date_joined'
    ]
    list_filter = [
        'role', 'is_active', 'is_staff', 'is_superuser', 
        'date_joined', 'last_login'
    ]
    search_fields = ['username', 'email', 'first_name', 'last_name', 'employee_id']
    ordering = ['-date_joined']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('SACCO Information', {
            'fields': ('role', 'employee_id', 'phone_number', 'is_active_staff')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


class NextOfKinInline(admin.TabularInline):
    """Inline for Next of Kin"""
    model = NextOfKin
    extra = 1
    fields = ['full_name', 'relationship', 'phone_number', 'national_id', 'is_primary']


class GuarantorInline(admin.TabularInline):
    """Inline for Guarantors"""
    model = Guarantor
    extra = 0
    fields = [
        'guarantor_member', 'full_name', 'collateral_type', 
        'collateral_value', 'status'
    ]
    readonly_fields = ['created_at']


class MemberDocumentInline(admin.TabularInline):
    """Inline for Member Documents"""
    model = MemberDocument
    extra = 0
    fields = ['document_type', 'title', 'file', 'uploaded_by']
    readonly_fields = ['uploaded_at', 'uploaded_by']


class MemberActivityInline(admin.TabularInline):
    """Inline for Member Activities"""
    model = MemberActivity
    extra = 0
    fields = ['activity_type', 'title', 'description', 'created_by']
    readonly_fields = ['created_at', 'created_by']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')[:10]


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    """Comprehensive Member admin interface"""
    
    list_display = [
        'member_number', 'get_full_name', 'national_id', 
        'phone_number', 'status', 'assigned_loan_officer', 
        'registration_date', 'get_photo_thumbnail'
    ]
    list_filter = [
        'status', 'gender', 'marital_status', 'county', 
        'assigned_loan_officer', 'registration_date'
    ]
    search_fields = [
        'member_number', 'national_id', 'first_name', 
        'last_name', 'phone_number', 'email'
    ]
    ordering = ['-registration_date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'user', 'member_number', 'national_id', 'photo'
            )
        }),
        ('Personal Details', {
            'fields': (
                ('first_name', 'middle_name', 'last_name'),
                ('date_of_birth', 'gender', 'marital_status')
            )
        }),
        ('Contact Information', {
            'fields': (
                ('phone_number', 'alternative_phone'),
                'email'
            )
        }),
        ('Address', {
            'fields': (
                ('county', 'sub_county'),
                ('ward', 'village'),
                ('postal_address', 'postal_code')
            )
        }),
        ('Employment/Business', {
            'fields': (
                'occupation',
                ('employer_name', 'business_name'),
                'monthly_income'
            )
        }),
        ('SACCO Information', {
            'fields': (
                'status', 'assigned_loan_officer', 'created_by'
            )
        }),
        ('Timestamps', {
            'fields': ('registration_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = [
        'member_number', 'registration_date', 'created_at', 
        'updated_at', 'get_photo_thumbnail'
    ]
    
    inlines = [NextOfKinInline, GuarantorInline, MemberDocumentInline, MemberActivityInline]
    
    actions = ['activate_members', 'deactivate_members', 'assign_loan_officer']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'first_name'
    
    def get_photo_thumbnail(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%;" />',
                obj.photo.url
            )
        return "No Photo"
    get_photo_thumbnail.short_description = 'Photo'
    
    def activate_members(self, request, queryset):
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} members activated successfully.')
    activate_members.short_description = "Activate selected members"
    
    def deactivate_members(self, request, queryset):
        updated = queryset.update(status='inactive')
        self.message_user(request, f'{updated} members deactivated successfully.')
    deactivate_members.short_description = "Deactivate selected members"
    
    def assign_loan_officer(self, request, queryset):
        # This would open a form to select loan officer
        pass
    assign_loan_officer.short_description = "Assign loan officer to selected members"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'assigned_loan_officer', 'created_by'
        )


@admin.register(NextOfKin)
class NextOfKinAdmin(admin.ModelAdmin):
    """Next of Kin admin interface"""
    
    list_display = [
        'full_name', 'member', 'relationship', 
        'phone_number', 'is_primary'
    ]
    list_filter = ['relationship', 'is_primary']
    search_fields = ['full_name', 'member__first_name', 'member__last_name', 'phone_number']
    ordering = ['member', '-is_primary', 'full_name']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('member')


@admin.register(Guarantor)
class GuarantorAdmin(admin.ModelAdmin):
    """Guarantor admin interface"""
    
    list_display = [
        'get_guarantor_name', 'member', 'collateral_type', 
        'collateral_value', 'status', 'created_at'
    ]
    list_filter = ['status', 'collateral_type', 'created_at']
    search_fields = [
        'full_name', 'guarantor_member__first_name', 
        'guarantor_member__last_name', 'member__first_name', 
        'member__last_name', 'collateral_type'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Guarantor Information', {
            'fields': (
                'member', 'guarantor_member', 'full_name', 
                'national_id', 'phone_number'
            )
        }),
        ('Employment Details', {
            'fields': ('occupation', 'employer', 'monthly_income')
        }),
        ('Collateral Information', {
            'fields': (
                'collateral_type', 'collateral_description',
                'collateral_value', 'collateral_location'
            )
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_guarantor_name(self, obj):
        if obj.guarantor_member:
            return obj.guarantor_member.get_full_name()
        return obj.full_name or "Unknown"
    get_guarantor_name.short_description = 'Guarantor Name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'member', 'guarantor_member'
        )


@admin.register(MemberDocument)
class MemberDocumentAdmin(admin.ModelAdmin):
    """Member Document admin interface"""
    
    list_display = [
        'title', 'member', 'document_type', 
        'uploaded_by', 'uploaded_at'
    ]
    list_filter = ['document_type', 'uploaded_at']
    search_fields = [
        'title', 'member__first_name', 'member__last_name',
        'member__member_number'
    ]
    ordering = ['-uploaded_at']
    
    readonly_fields = ['uploaded_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'member', 'uploaded_by'
        )


@admin.register(MemberActivity)
class MemberActivityAdmin(admin.ModelAdmin):
    """Member Activity admin interface"""
    
    list_display = [
        'title', 'member', 'activity_type', 
        'created_by', 'created_at'
    ]
    list_filter = ['activity_type', 'created_at']
    search_fields = [
        'title', 'description', 'member__first_name', 
        'member__last_name', 'member__member_number'
    ]
    ordering = ['-created_at']
    
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'member', 'created_by'
        )


# Customize admin site headers
admin.site.site_header = "SACCO Lending System Administration"
admin.site.site_title = "SACCO Admin"
admin.site.index_title = "Welcome to SACCO Lending System Administration"
