from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import date, datetime
import uuid


class ReportTemplate(models.Model):
    """Templates for different types of reports"""
    
    REPORT_CATEGORIES = [
        ('loan', 'Loan Reports'),
        ('member', 'Member Reports'),
        ('financial', 'Financial Reports'),
        ('performance', 'Performance Reports'),
        ('compliance', 'Compliance Reports'),
        ('operational', 'Operational Reports'),
    ]
    
    REPORT_FORMATS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('html', 'HTML'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=REPORT_CATEGORIES)
    
    # Template Configuration
    query_template = models.TextField(help_text="SQL query template with parameters")
    column_definitions = models.JSONField(help_text="Column definitions and formatting")
    chart_config = models.JSONField(blank=True, null=True, help_text="Chart configuration if applicable")
    
    # Default Settings
    default_format = models.CharField(max_length=10, choices=REPORT_FORMATS, default='pdf')
    is_scheduled_report = models.BooleanField(default=False)
    requires_approval = models.BooleanField(default=False)
    
    # Access Control
    allowed_roles = models.JSONField(default=list, help_text="List of roles that can generate this report")
    is_public = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_report_templates'
    )
    
    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Report Template'
        verbose_name_plural = 'Report Templates'
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class Report(models.Model):
    """Generated reports"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    FORMATS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('html', 'HTML'),
    ]
    
    report_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.CASCADE,
        related_name='generated_reports'
    )
    
    # Report Details
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    format = models.CharField(max_length=10, choices=FORMATS)
    
    # Parameters and Filters
    parameters = models.JSONField(default=dict, help_text="Parameters used to generate the report")
    date_from = models.DateField(null=True, blank=True)
    date_to = models.DateField(null=True, blank=True)
    
    # Filter by entities
    filtered_members = models.ManyToManyField(
        'members.Member',
        blank=True,
        related_name='reports'
    )
    filtered_loan_officers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='officer_reports'
    )
    
    # Generation Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress_percentage = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(100)])
    
    # Timing
    requested_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Files
    report_file = models.FileField(upload_to='reports/', blank=True, null=True)
    file_size = models.PositiveIntegerField(default=0)  # Size in bytes
    
    # Data and Statistics
    total_records = models.PositiveIntegerField(default=0)
    summary_data = models.JSONField(blank=True, null=True)
    chart_data = models.JSONField(blank=True, null=True)
    
    # Access and Sharing
    is_confidential = models.BooleanField(default=False)
    shared_with = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='shared_reports'
    )
    download_count = models.PositiveIntegerField(default=0)
    
    # Error Handling
    error_message = models.TextField(blank=True, null=True)
    
    # User Tracking
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='requested_reports'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_reports'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Report'
        verbose_name_plural = 'Reports'
    
    def __str__(self):
        return f"{self.title} - {self.requested_at.strftime('%Y-%m-%d')}"
    
    @property
    def is_completed(self):
        """Check if report generation is completed"""
        return self.status == 'completed'
    
    @property
    def file_size_mb(self):
        """Get file size in MB"""
        return round(self.file_size / (1024 * 1024), 2) if self.file_size else 0
    
    def mark_as_downloaded(self):
        """Increment download count"""
        self.download_count += 1
        self.save(update_fields=['download_count'])


class ScheduledReport(models.Model):
    """Scheduled reports that run automatically"""
    
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('inactive', 'Inactive'),
    ]
    
    name = models.CharField(max_length=100)
    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.CASCADE,
        related_name='scheduled_reports'
    )
    
    # Scheduling
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    run_time = models.TimeField(default='08:00')
    day_of_week = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        validators=[MinValueValidator(0), MaxValueValidator(6)],
        help_text="0=Monday, 6=Sunday (for weekly reports)"
    )
    day_of_month = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text="Day of month (for monthly reports)"
    )
    
    # Parameters
    default_parameters = models.JSONField(default=dict)
    format = models.CharField(max_length=10, choices=Report.FORMATS, default='pdf')
    
    # Recipients
    recipients = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='scheduled_reports'
    )
    email_recipients = models.TextField(
        blank=True, 
        null=True,
        help_text="Additional email addresses (comma-separated)"
    )
    
    # Status and Control
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    run_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_scheduled_reports'
    )
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Scheduled Report'
        verbose_name_plural = 'Scheduled Reports'
    
    def __str__(self):
        return f"{self.name} ({self.get_frequency_display()})"


class Dashboard(models.Model):
    """Custom dashboards with widgets"""
    
    DASHBOARD_TYPES = [
        ('executive', 'Executive Dashboard'),
        ('operational', 'Operational Dashboard'),
        ('loan_officer', 'Loan Officer Dashboard'),
        ('member', 'Member Dashboard'),
        ('custom', 'Custom Dashboard'),
    ]
    
    name = models.CharField(max_length=100)
    dashboard_type = models.CharField(max_length=20, choices=DASHBOARD_TYPES)
    description = models.TextField(blank=True, null=True)
    
    # Configuration
    layout_config = models.JSONField(default=dict, help_text="Dashboard layout configuration")
    refresh_interval = models.PositiveIntegerField(default=300, help_text="Refresh interval in seconds")
    
    # Access Control
    is_default = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    allowed_roles = models.JSONField(default=list)
    
    # Sharing
    shared_with = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='shared_dashboards'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_dashboards'
    )
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Dashboard'
        verbose_name_plural = 'Dashboards'
    
    def __str__(self):
        return f"{self.name} ({self.get_dashboard_type_display()})"


class DashboardWidget(models.Model):
    """Individual widgets on dashboards"""
    
    WIDGET_TYPES = [
        ('metric', 'Metric/KPI'),
        ('chart', 'Chart'),
        ('table', 'Data Table'),
        ('gauge', 'Gauge'),
        ('progress', 'Progress Bar'),
        ('list', 'List'),
        ('calendar', 'Calendar'),
        ('map', 'Map'),
    ]
    
    CHART_TYPES = [
        ('line', 'Line Chart'),
        ('bar', 'Bar Chart'),
        ('pie', 'Pie Chart'),
        ('doughnut', 'Doughnut Chart'),
        ('area', 'Area Chart'),
        ('scatter', 'Scatter Plot'),
    ]
    
    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        related_name='widgets'
    )
    
    # Widget Configuration
    title = models.CharField(max_length=100)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    chart_type = models.CharField(max_length=20, choices=CHART_TYPES, blank=True, null=True)
    
    # Layout
    position_x = models.PositiveIntegerField(default=0)
    position_y = models.PositiveIntegerField(default=0)
    width = models.PositiveIntegerField(default=4)
    height = models.PositiveIntegerField(default=3)
    
    # Data Configuration
    data_source = models.TextField(help_text="SQL query or data source configuration")
    parameters = models.JSONField(default=dict)
    chart_config = models.JSONField(default=dict, help_text="Chart styling and configuration")
    
    # Refresh Settings
    auto_refresh = models.BooleanField(default=True)
    refresh_interval = models.PositiveIntegerField(default=300, help_text="Refresh interval in seconds")
    
    # Cache
    cached_data = models.JSONField(blank=True, null=True)
    cache_expires = models.DateTimeField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['dashboard', 'position_y', 'position_x']
        verbose_name = 'Dashboard Widget'
        verbose_name_plural = 'Dashboard Widgets'
    
    def __str__(self):
        return f"{self.dashboard.name} - {self.title}"


class KPIMetric(models.Model):
    """Key Performance Indicators and metrics"""
    
    METRIC_TYPES = [
        ('count', 'Count'),
        ('sum', 'Sum'),
        ('average', 'Average'),
        ('percentage', 'Percentage'),
        ('ratio', 'Ratio'),
        ('rate', 'Rate'),
    ]
    
    CALCULATION_PERIODS = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('all_time', 'All Time'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPES)
    
    # Calculation
    calculation_query = models.TextField(help_text="SQL query to calculate the metric")
    calculation_period = models.CharField(max_length=20, choices=CALCULATION_PERIODS)
    
    # Display
    display_format = models.CharField(max_length=50, default='{value}')
    unit = models.CharField(max_length=20, blank=True, null=True)
    
    # Targets and Thresholds
    target_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    warning_threshold = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    critical_threshold = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Current Values
    current_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    previous_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    last_calculated = models.DateTimeField(null=True, blank=True)
    
    # Settings
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=True)
    auto_calculate = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'KPI Metric'
        verbose_name_plural = 'KPI Metrics'
    
    def __str__(self):
        return self.name
    
    @property
    def trend(self):
        """Calculate trend compared to previous value"""
        if not self.current_value or not self.previous_value:
            return 'neutral'
        
        if self.current_value > self.previous_value:
            return 'up'
        elif self.current_value < self.previous_value:
            return 'down'
        else:
            return 'neutral'
    
    @property
    def status(self):
        """Get status based on thresholds"""
        if not self.current_value:
            return 'unknown'
        
        if self.critical_threshold and self.current_value <= self.critical_threshold:
            return 'critical'
        elif self.warning_threshold and self.current_value <= self.warning_threshold:
            return 'warning'
        else:
            return 'good'


class ReportAccess(models.Model):
    """Track report access and downloads"""
    
    ACTION_TYPES = [
        ('view', 'Viewed'),
        ('download', 'Downloaded'),
        ('share', 'Shared'),
        ('print', 'Printed'),
    ]
    
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='access_logs'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='report_access_logs'
    )
    
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    
    accessed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-accessed_at']
        verbose_name = 'Report Access'
        verbose_name_plural = 'Report Access Logs'
    
    def __str__(self):
        return f"{self.user.username} {self.action} {self.report.title}"


class ReportBookmark(models.Model):
    """User bookmarks for frequently accessed reports"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='report_bookmarks'
    )
    report_template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.CASCADE,
        related_name='bookmarks'
    )
    
    # Saved Parameters
    saved_parameters = models.JSONField(default=dict)
    bookmark_name = models.CharField(max_length=100)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'report_template', 'bookmark_name']
        ordering = ['bookmark_name']
        verbose_name = 'Report Bookmark'
        verbose_name_plural = 'Report Bookmarks'
    
    def __str__(self):
        return f"{self.user.username} - {self.bookmark_name}"


class AnalyticsEvent(models.Model):
    """Track analytics events for business intelligence"""
    
    EVENT_TYPES = [
        ('member_registration', 'Member Registration'),
        ('loan_application', 'Loan Application'),
        ('loan_approval', 'Loan Approval'),
        ('loan_disbursement', 'Loan Disbursement'),
        ('payment_received', 'Payment Received'),
        ('payment_overdue', 'Payment Overdue'),
        ('loan_completion', 'Loan Completion'),
        ('system_login', 'System Login'),
        ('report_generated', 'Report Generated'),
        ('custom_event', 'Custom Event'),
    ]
    
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    event_name = models.CharField(max_length=100)
    
    # Event Data
    properties = models.JSONField(default=dict)
    
    # Context
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='analytics_events'
    )
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='analytics_events'
    )
    
    # Technical Details
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    session_id = models.CharField(max_length=100, blank=True, null=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Analytics Event'
        verbose_name_plural = 'Analytics Events'
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['member', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.event_name} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
