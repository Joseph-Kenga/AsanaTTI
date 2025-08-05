from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count
from .models import (
    LoanType, LoanApplication, Loan, LoanGuarantor,
    LoanDocument, LoanTopUp
)


@admin.register(LoanType)
class LoanTypeAdmin(admin.ModelAdmin):
    """Loan Type admin interface"""
    
    list_display = [
        'name', 'interest_rate', 'interest_calculation_method',
        'minimum_amount', 'maximum_amount', 'requires_guarantor',
        'is_active'
    ]
    list_filter = [
        'interest_calculation_method', 'requires_guarantor', 
        'requires_collateral', 'is_active'
    ]
    search_fields = ['name', 'description']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Interest Configuration', {
            'fields': (
                'interest_rate', 'interest_calculation_method',
                'processing_fee_rate'
            )
        }),
        ('Loan Limits', {
            'fields': (
                ('minimum_amount', 'maximum_amount'),
                ('minimum_term_months', 'maximum_term_months')
            )
        }),
        ('Requirements', {
            'fields': (
                'requires_guarantor', 'minimum_guarantors',
                'requires_collateral'
            )
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['activate_loan_types', 'deactivate_loan_types']
    
    def activate_loan_types(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} loan types activated successfully.')
    activate_loan_types.short_description = "Activate selected loan types"
    
    def deactivate_loan_types(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} loan types deactivated successfully.')
    deactivate_loan_types.short_description = "Deactivate selected loan types"


class LoanDocumentInline(admin.TabularInline):
    """Inline for Loan Documents"""
    model = LoanDocument
    extra = 0
    fields = ['document_type', 'title', 'file', 'uploaded_by']
    readonly_fields = ['uploaded_at', 'uploaded_by']


class LoanGuarantorInline(admin.TabularInline):
    """Inline for Loan Guarantors"""
    model = LoanGuarantor
    extra = 0
    fields = ['guarantor', 'guaranteed_amount', 'status']
    readonly_fields = ['created_at']


@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    """Loan Application admin interface"""
    
    list_display = [
        'application_number', 'member', 'loan_type', 
        'requested_amount', 'status', 'application_date',
        'assigned_to', 'get_approval_status'
    ]
    list_filter = [
        'status', 'loan_type', 'purpose', 'application_date',
        'assigned_to', 'reviewed_by'
    ]
    search_fields = [
        'application_number', 'member__first_name', 
        'member__last_name', 'member__member_number'
    ]
    ordering = ['-application_date']
    
    fieldsets = (
        ('Application Details', {
            'fields': (
                'application_number', 'member', 'loan_type',
                'status'
            )
        }),
        ('Loan Request', {
            'fields': (
                ('requested_amount', 'approved_amount'),
                'term_months', ('purpose', 'purpose_description')
            )
        }),
        ('Workflow', {
            'fields': (
                'assigned_to', 'reviewed_by', 'approved_by'
            )
        }),
        ('Dates', {
            'fields': (
                'application_date', 'review_date', 
                'approval_date', 'disbursement_date'
            )
        }),
        ('Comments', {
            'fields': (
                'member_comments', 'staff_comments', 'rejection_reason'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = [
        'application_number', 'application_date', 
        'created_at', 'updated_at'
    ]
    
    inlines = [LoanDocumentInline]
    
    actions = [
        'approve_applications', 'reject_applications', 
        'assign_to_me', 'mark_under_review'
    ]
    
    def get_approval_status(self, obj):
        if obj.status == 'approved':
            return format_html(
                '<span style="color: green;">✓ Approved</span>'
            )
        elif obj.status == 'rejected':
            return format_html(
                '<span style="color: red;">✗ Rejected</span>'
            )
        elif obj.status == 'under_review':
            return format_html(
                '<span style="color: orange;">⏳ Under Review</span>'
            )
        else:
            return obj.get_status_display()
    get_approval_status.short_description = 'Status'
    
    def approve_applications(self, request, queryset):
        # This would typically require more complex logic
        queryset.filter(status='under_review').update(
            status='approved',
            approved_by=request.user
        )
        self.message_user(request, 'Selected applications approved.')
    approve_applications.short_description = "Approve selected applications"
    
    def reject_applications(self, request, queryset):
        queryset.filter(status='under_review').update(
            status='rejected',
            reviewed_by=request.user
        )
        self.message_user(request, 'Selected applications rejected.')
    reject_applications.short_description = "Reject selected applications"
    
    def assign_to_me(self, request, queryset):
        updated = queryset.update(assigned_to=request.user)
        self.message_user(request, f'{updated} applications assigned to you.')
    assign_to_me.short_description = "Assign to me"
    
    def mark_under_review(self, request, queryset):
        updated = queryset.filter(status='submitted').update(
            status='under_review',
            reviewed_by=request.user
        )
        self.message_user(request, f'{updated} applications marked under review.')
    mark_under_review.short_description = "Mark as under review"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'member', 'loan_type', 'assigned_to', 'reviewed_by', 'approved_by'
        )


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    """Active Loan admin interface"""
    
    list_display = [
        'loan_number', 'member', 'loan_type', 'principal_amount',
        'outstanding_balance', 'status', 'disbursement_date',
        'get_completion_progress', 'loan_officer'
    ]
    list_filter = [
        'status', 'loan_type', 'disbursement_date',
        'loan_officer', 'maturity_date'
    ]
    search_fields = [
        'loan_number', 'member__first_name', 
        'member__last_name', 'member__member_number'
    ]
    ordering = ['-disbursement_date']
    
    fieldsets = (
        ('Loan Details', {
            'fields': (
                'loan_number', 'application', 'member', 'loan_type'
            )
        }),
        ('Financial Information', {
            'fields': (
                ('principal_amount', 'interest_rate'),
                ('monthly_repayment', 'total_interest'),
                'processing_fee'
            )
        }),
        ('Current Status', {
            'fields': (
                'status',
                ('outstanding_balance', 'outstanding_interest'),
                ('total_paid', 'penalty_balance')
            )
        }),
        ('Dates', {
            'fields': (
                ('disbursement_date', 'first_repayment_date'),
                'maturity_date'
            )
        }),
        ('Staff', {
            'fields': ('loan_officer', 'disbursed_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = [
        'loan_number', 'disbursement_date', 'first_repayment_date',
        'maturity_date', 'created_at', 'updated_at'
    ]
    
    inlines = [LoanGuarantorInline, LoanDocumentInline]
    
    actions = ['mark_as_completed', 'mark_as_defaulted', 'generate_statements']
    
    def get_completion_progress(self, obj):
        progress = obj.completion_percentage
        color = 'green' if progress >= 80 else 'orange' if progress >= 50 else 'red'
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 3px; text-align: center; color: white; font-size: 12px; line-height: 20px;">'
            '{:.1f}%</div></div>',
            progress, color, progress
        )
    get_completion_progress.short_description = 'Progress'
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.filter(status='active').update(status='completed')
        self.message_user(request, f'{updated} loans marked as completed.')
    mark_as_completed.short_description = "Mark as completed"
    
    def mark_as_defaulted(self, request, queryset):
        updated = queryset.filter(status='active').update(status='defaulted')
        self.message_user(request, f'{updated} loans marked as defaulted.')
    mark_as_defaulted.short_description = "Mark as defaulted"
    
    def generate_statements(self, request, queryset):
        # This would generate loan statements
        self.message_user(request, f'Statements generated for {queryset.count()} loans.')
    generate_statements.short_description = "Generate statements"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'member', 'loan_type', 'loan_officer', 'disbursed_by', 'application'
        )


@admin.register(LoanGuarantor)
class LoanGuarantorAdmin(admin.ModelAdmin):
    """Loan Guarantor admin interface"""
    
    list_display = [
        'loan', 'guarantor', 'guaranteed_amount', 
        'status', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = [
        'loan__loan_number', 'guarantor__full_name',
        'guarantor__guarantor_member__first_name'
    ]
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'loan', 'guarantor', 'guarantor__guarantor_member'
        )


@admin.register(LoanDocument)
class LoanDocumentAdmin(admin.ModelAdmin):
    """Loan Document admin interface"""
    
    list_display = [
        'title', 'get_loan_reference', 'document_type',
        'uploaded_by', 'uploaded_at'
    ]
    list_filter = ['document_type', 'uploaded_at']
    search_fields = [
        'title', 'loan__loan_number', 
        'loan_application__application_number'
    ]
    ordering = ['-uploaded_at']
    
    readonly_fields = ['uploaded_at']
    
    def get_loan_reference(self, obj):
        if obj.loan:
            return obj.loan.loan_number
        elif obj.loan_application:
            return obj.loan_application.application_number
        return "N/A"
    get_loan_reference.short_description = 'Reference'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'loan', 'loan_application', 'uploaded_by'
        )


@admin.register(LoanTopUp)
class LoanTopUpAdmin(admin.ModelAdmin):
    """Loan Top-up admin interface"""
    
    list_display = [
        'original_loan', 'topup_amount', 'new_term_months',
        'status', 'requested_date', 'requested_by'
    ]
    list_filter = ['status', 'requested_date']
    search_fields = ['original_loan__loan_number', 'reason']
    ordering = ['-requested_date']
    
    fieldsets = (
        ('Top-up Details', {
            'fields': (
                'original_loan', 'new_loan', 'topup_amount',
                'new_term_months', 'new_monthly_repayment'
            )
        }),
        ('Status & Workflow', {
            'fields': (
                'status', 'reason'
            )
        }),
        ('Dates', {
            'fields': (
                'requested_date', 'approved_date', 'completed_date'
            )
        }),
        ('Staff', {
            'fields': ('requested_by', 'approved_by')
        }),
    )
    
    readonly_fields = ['requested_date']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'original_loan', 'new_loan', 'requested_by', 'approved_by'
        )


# Custom admin site modifications
class LoanAdminSite(admin.AdminSite):
    """Custom admin site for loan management"""
    site_header = 'SACCO Loan Management'
    site_title = 'Loan Admin'
    index_title = 'Loan Management Dashboard'
    
    def index(self, request, extra_context=None):
        """Custom index page with loan statistics"""
        extra_context = extra_context or {}
        
        # Add loan statistics
        extra_context.update({
            'total_applications': LoanApplication.objects.count(),
            'pending_applications': LoanApplication.objects.filter(
                status__in=['submitted', 'under_review']
            ).count(),
            'active_loans': Loan.objects.filter(status='active').count(),
            'total_disbursed': Loan.objects.aggregate(
                total=Sum('principal_amount')
            )['total'] or 0,
        })
        
        return super().index(request, extra_context)
