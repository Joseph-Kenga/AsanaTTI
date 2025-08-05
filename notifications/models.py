from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
import uuid


class NotificationTemplate(models.Model):
    """Templates for different types of notifications"""
    
    TEMPLATE_TYPES = [
        ('loan_application_received', 'Loan Application Received'),
        ('loan_approved', 'Loan Approved'),
        ('loan_rejected', 'Loan Rejected'),
        ('loan_disbursed', 'Loan Disbursed'),
        ('repayment_reminder', 'Repayment Reminder'),
        ('payment_received', 'Payment Received'),
        ('overdue_notice', 'Overdue Notice'),
        ('penalty_applied', 'Penalty Applied'),
        ('loan_completed', 'Loan Completed'),
        ('member_birthday', 'Member Birthday'),
        ('welcome_message', 'Welcome Message'),
        ('password_reset', 'Password Reset'),
        ('account_suspended', 'Account Suspended'),
        ('general_announcement', 'General Announcement'),
    ]
    
    NOTIFICATION_CHANNELS = [
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('both', 'SMS and Email'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    template_type = models.CharField(max_length=30, choices=TEMPLATE_TYPES)
    channel = models.CharField(max_length=10, choices=NOTIFICATION_CHANNELS)
    
    # SMS Template
    sms_subject = models.CharField(max_length=50, blank=True, null=True)
    sms_message = models.TextField(help_text="SMS message template. Use {{variable}} for dynamic content.")
    
    # Email Template
    email_subject = models.CharField(max_length=200, blank=True, null=True)
    email_message = models.TextField(blank=True, null=True, help_text="Email message template. Use {{variable}} for dynamic content.")
    email_html = models.TextField(blank=True, null=True, help_text="HTML version of email template.")
    
    # Settings
    is_active = models.BooleanField(default=True)
    is_system_template = models.BooleanField(default=False)  # System templates cannot be deleted
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_notification_templates'
    )
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Notification Template'
        verbose_name_plural = 'Notification Templates'
    
    def __str__(self):
        return f"{self.name} ({self.get_channel_display()})"


class Notification(models.Model):
    """Individual notifications sent to members or staff"""
    
    NOTIFICATION_TYPES = [
        ('system', 'System Notification'),
        ('reminder', 'Reminder'),
        ('alert', 'Alert'),
        ('announcement', 'Announcement'),
        ('transaction', 'Transaction Notification'),
        ('marketing', 'Marketing Message'),
    ]
    
    CHANNELS = [
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('in_app', 'In-App Notification'),
        ('push', 'Push Notification'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    notification_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Recipients
    recipient_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='received_notifications'
    )
    recipient_member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    
    # Content
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    channel = models.CharField(max_length=20, choices=CHANNELS)
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    
    subject = models.CharField(max_length=200)
    message = models.TextField()
    html_message = models.TextField(blank=True, null=True)
    
    # Delivery Details
    phone_number = PhoneNumberField(blank=True, null=True)
    email_address = models.EmailField(blank=True, null=True)
    
    # Status and Scheduling
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Tracking
    read_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    response_received = models.BooleanField(default=False)
    response_message = models.TextField(blank=True, null=True)
    
    # External Service Details
    external_id = models.CharField(max_length=100, blank=True, null=True)  # ID from SMS/Email provider
    delivery_report = models.JSONField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    
    # Context Data
    context_data = models.JSONField(blank=True, null=True)  # Data used to render template
    
    # Related Objects
    related_loan = models.ForeignKey(
        'loans.Loan',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    related_application = models.ForeignKey(
        'loans.LoanApplication',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    related_transaction = models.ForeignKey(
        'repayments.RepaymentTransaction',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_notifications'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
    
    def __str__(self):
        recipient = self.recipient_member or self.recipient_user
        return f"{self.subject} - {recipient}"
    
    @property
    def is_read(self):
        """Check if notification has been read"""
        return self.read_at is not None
    
    @property
    def is_delivered(self):
        """Check if notification was delivered"""
        return self.status == 'delivered'
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.read_at:
            self.read_at = timezone.now()
            self.save(update_fields=['read_at'])
    
    def mark_as_clicked(self):
        """Mark notification as clicked"""
        if not self.clicked_at:
            self.clicked_at = timezone.now()
            self.save(update_fields=['clicked_at'])


class BulkNotification(models.Model):
    """Bulk notifications sent to multiple recipients"""
    
    TARGET_TYPES = [
        ('all_members', 'All Members'),
        ('active_members', 'Active Members'),
        ('overdue_members', 'Members with Overdue Loans'),
        ('loan_officers', 'Loan Officers'),
        ('staff', 'All Staff'),
        ('custom', 'Custom Recipients'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    campaign_name = models.CharField(max_length=100)
    target_type = models.CharField(max_length=20, choices=TARGET_TYPES)
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.CASCADE,
        related_name='bulk_notifications'
    )
    
    # Content
    subject = models.CharField(max_length=200)
    message = models.TextField()
    html_message = models.TextField(blank=True, null=True)
    
    # Targeting
    target_members = models.ManyToManyField(
        'members.Member',
        blank=True,
        related_name='bulk_notifications'
    )
    target_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='bulk_notifications'
    )
    
    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Statistics
    total_recipients = models.PositiveIntegerField(default=0)
    sent_count = models.PositiveIntegerField(default=0)
    delivered_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_bulk_notifications'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Bulk Notification'
        verbose_name_plural = 'Bulk Notifications'
    
    def __str__(self):
        return f"{self.campaign_name} - {self.total_recipients} recipients"


class SMSProvider(models.Model):
    """SMS service provider configuration"""
    
    PROVIDER_TYPES = [
        ('africastalking', 'Africa\'s Talking'),
        ('twilio', 'Twilio'),
        ('infobip', 'Infobip'),
        ('clickatell', 'Clickatell'),
        ('custom', 'Custom API'),
    ]
    
    name = models.CharField(max_length=50)
    provider_type = models.CharField(max_length=20, choices=PROVIDER_TYPES)
    
    # API Configuration
    api_key = models.CharField(max_length=200)
    api_secret = models.CharField(max_length=200, blank=True, null=True)
    sender_id = models.CharField(max_length=20)
    api_url = models.URLField(blank=True, null=True)
    
    # Settings
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    cost_per_sms = models.DecimalField(
        max_digits=6, 
        decimal_places=4, 
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Limits
    daily_limit = models.PositiveIntegerField(default=1000)
    monthly_limit = models.PositiveIntegerField(default=10000)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'SMS Provider'
        verbose_name_plural = 'SMS Providers'
    
    def __str__(self):
        return f"{self.name} ({self.get_provider_type_display()})"


class NotificationLog(models.Model):
    """Log of all notification activities"""
    
    ACTION_TYPES = [
        ('created', 'Created'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('read', 'Read'),
        ('clicked', 'Clicked'),
        ('replied', 'Replied'),
        ('bounced', 'Bounced'),
        ('unsubscribed', 'Unsubscribed'),
    ]
    
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    details = models.JSONField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Notification Log'
        verbose_name_plural = 'Notification Logs'
    
    def __str__(self):
        return f"{self.notification.subject} - {self.get_action_display()}"


class NotificationPreference(models.Model):
    """User preferences for notifications"""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # Channel Preferences
    sms_enabled = models.BooleanField(default=True)
    email_enabled = models.BooleanField(default=True)
    in_app_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)
    
    # Notification Type Preferences
    loan_notifications = models.BooleanField(default=True)
    payment_notifications = models.BooleanField(default=True)
    reminder_notifications = models.BooleanField(default=True)
    marketing_notifications = models.BooleanField(default=False)
    system_notifications = models.BooleanField(default=True)
    
    # Timing Preferences
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    timezone = models.CharField(max_length=50, default='Africa/Nairobi')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'
    
    def __str__(self):
        return f"Preferences for {self.user.username}"


class NotificationQueue(models.Model):
    """Queue for processing notifications"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('retrying', 'Retrying'),
    ]
    
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='queue_entries'
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.PositiveIntegerField(default=5)  # Lower number = higher priority
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    
    scheduled_for = models.DateTimeField()
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    error_message = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['priority', 'scheduled_for']
        verbose_name = 'Notification Queue'
        verbose_name_plural = 'Notification Queue'
    
    def __str__(self):
        return f"Queue: {self.notification.subject} - {self.status}"


class AutomatedNotificationRule(models.Model):
    """Rules for automatically sending notifications based on events"""
    
    TRIGGER_EVENTS = [
        ('loan_application_submitted', 'Loan Application Submitted'),
        ('loan_approved', 'Loan Approved'),
        ('loan_disbursed', 'Loan Disbursed'),
        ('payment_received', 'Payment Received'),
        ('payment_overdue', 'Payment Overdue'),
        ('loan_completed', 'Loan Completed'),
        ('member_registered', 'Member Registered'),
        ('member_birthday', 'Member Birthday'),
    ]
    
    name = models.CharField(max_length=100)
    trigger_event = models.CharField(max_length=30, choices=TRIGGER_EVENTS)
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.CASCADE,
        related_name='automation_rules'
    )
    
    # Conditions
    conditions = models.JSONField(blank=True, null=True)  # JSON conditions for when to trigger
    
    # Timing
    delay_minutes = models.PositiveIntegerField(default=0)  # Delay before sending
    
    # Status
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_notification_rules'
    )
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Automated Notification Rule'
        verbose_name_plural = 'Automated Notification Rules'
    
    def __str__(self):
        return f"{self.name} - {self.get_trigger_event_display()}"
