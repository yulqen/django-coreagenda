from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Meeting,
    AgendaItem,
    Presenter,
    ActionItem,
    Minute,
    AttendanceRecord,
    ExternalRequest,
)


# Inline admin classes

class PresenterInline(admin.TabularInline):
    """Inline admin for Presenters within AgendaItem."""
    model = Presenter
    extra = 1
    fields = ['user', 'name', 'email', 'affiliation', 'is_primary', 'presentation_order']
    autocomplete_fields = ['user']


class AgendaItemInline(admin.TabularInline):
    """Inline admin for AgendaItems within Meeting."""
    model = AgendaItem
    extra = 0
    fields = ['title', 'proposer', 'status', 'order', 'estimated_duration_minutes']
    readonly_fields = ['proposer']
    show_change_link = True


class ActionItemInline(admin.TabularInline):
    """Inline admin for ActionItems within Meeting."""
    model = ActionItem
    extra = 0
    fields = ['title', 'assigned_to', 'status', 'priority', 'due_date']
    show_change_link = True


class AttendanceRecordInline(admin.TabularInline):
    """Inline admin for AttendanceRecords within Meeting."""
    model = AttendanceRecord
    extra = 0
    fields = ['user', 'present', 'attendance_type', 'role', 'arrived_late', 'left_early']


# Main admin classes

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    """Admin interface for Meeting model."""

    list_display = [
        'title',
        'scheduled_date',
        'meeting_type',
        'status_badge',
        'chairperson',
        'duration_minutes',
        'is_published',
    ]

    list_filter = [
        'status',
        'meeting_type',
        'is_published',
        'scheduled_date',
    ]

    search_fields = [
        'title',
        'description',
        'location',
        'chairperson__username',
        'chairperson__email',
    ]

    readonly_fields = [
        'created_at',
        'updated_at',
        'get_end_time',
    ]

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'meeting_type')
        }),
        ('Scheduling', {
            'fields': ('scheduled_date', 'duration_minutes', 'location')
        }),
        ('People', {
            'fields': ('chairperson', 'note_taker')
        }),
        ('Status', {
            'fields': ('status', 'is_published', 'consent_agenda_enabled')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'get_end_time'),
            'classes': ('collapse',)
        }),
    )

    inlines = [AgendaItemInline, ActionItemInline, AttendanceRecordInline]

    date_hierarchy = 'scheduled_date'

    autocomplete_fields = ['chairperson', 'note_taker']

    def status_badge(self, obj):
        """Display status with color coding."""
        colors = {
            'draft': '#6c757d',
            'scheduled': '#007bff',
            'in_progress': '#28a745',
            'completed': '#6c757d',
            'cancelled': '#dc3545',
            'postponed': '#ffc107',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def get_end_time(self, obj):
        """Display calculated end time."""
        return obj.get_end_time()
    get_end_time.short_description = 'End Time'


@admin.register(AgendaItem)
class AgendaItemAdmin(admin.ModelAdmin):
    """Admin interface for AgendaItem model."""

    list_display = [
        'title',
        'meeting',
        'proposer',
        'item_type',
        'status_badge',
        'order',
        'estimated_duration_minutes',
        'is_consent_item',
    ]

    list_filter = [
        'status',
        'item_type',
        'is_consent_item',
        'meeting__scheduled_date',
    ]

    search_fields = [
        'title',
        'description',
        'background_info',
        'proposer__username',
        'meeting__title',
    ]

    readonly_fields = [
        'created_at',
        'updated_at',
        'submitted_at',
        'reviewed_at',
        'reviewed_by',
    ]

    fieldsets = (
        ('Basic Information', {
            'fields': ('meeting', 'title', 'description', 'proposer')
        }),
        ('Classification', {
            'fields': ('item_type', 'estimated_duration_minutes', 'is_consent_item', 'order')
        }),
        ('Content', {
            'fields': ('background_info', 'attachments_url')
        }),
        ('Workflow', {
            'fields': ('status', 'submitted_at', 'reviewed_at', 'reviewed_by')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [PresenterInline]

    autocomplete_fields = ['meeting', 'proposer', 'reviewed_by']

    actions = ['submit_items', 'approve_items', 'defer_items']

    def status_badge(self, obj):
        """Display status with color coding."""
        colors = {
            'draft': '#6c757d',
            'submitted': '#007bff',
            'approved': '#28a745',
            'deferred': '#ffc107',
            'withdrawn': '#dc3545',
            'completed': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def submit_items(self, request, queryset):
        """Submit selected agenda items."""
        count = 0
        for item in queryset:
            if item.can_submit():
                item.submit()
                count += 1
        self.message_user(request, f'{count} item(s) submitted successfully.')
    submit_items.short_description = 'Submit selected items'

    def approve_items(self, request, queryset):
        """Approve selected agenda items."""
        count = 0
        for item in queryset:
            if item.can_approve():
                item.approve(request.user)
                count += 1
        self.message_user(request, f'{count} item(s) approved successfully.')
    approve_items.short_description = 'Approve selected items'

    def defer_items(self, request, queryset):
        """Defer selected agenda items."""
        count = 0
        for item in queryset:
            if item.can_defer():
                item.defer(request.user)
                count += 1
        self.message_user(request, f'{count} item(s) deferred successfully.')
    defer_items.short_description = 'Defer selected items'


@admin.register(Presenter)
class PresenterAdmin(admin.ModelAdmin):
    """Admin interface for Presenter model."""

    list_display = [
        'get_presenter_name',
        'agenda_item',
        'affiliation',
        'is_primary',
        'presentation_order',
    ]

    list_filter = [
        'is_primary',
        'agenda_item__meeting',
    ]

    search_fields = [
        'name',
        'email',
        'affiliation',
        'user__username',
        'agenda_item__title',
    ]

    autocomplete_fields = ['agenda_item', 'user']


@admin.register(ActionItem)
class ActionItemAdmin(admin.ModelAdmin):
    """Admin interface for ActionItem model."""

    list_display = [
        'title',
        'meeting',
        'assigned_to',
        'status_badge',
        'priority_badge',
        'due_date',
        'overdue_indicator',
    ]

    list_filter = [
        'status',
        'priority',
        'is_recurring',
        'due_date',
        'meeting__scheduled_date',
    ]

    search_fields = [
        'title',
        'description',
        'assigned_to__username',
        'meeting__title',
    ]

    readonly_fields = [
        'created_at',
        'updated_at',
        'completed_at',
        'overdue_indicator',
    ]

    fieldsets = (
        ('Basic Information', {
            'fields': ('meeting', 'agenda_item', 'title', 'description')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'assigned_by', 'due_date')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority')
        }),
        ('Completion', {
            'fields': ('completed_at', 'completion_notes')
        }),
        ('Recurrence', {
            'fields': ('is_recurring', 'recurrence_pattern'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'overdue_indicator'),
            'classes': ('collapse',)
        }),
    )

    autocomplete_fields = ['meeting', 'agenda_item', 'assigned_to', 'assigned_by']

    actions = ['mark_in_progress', 'mark_complete']

    date_hierarchy = 'due_date'

    def status_badge(self, obj):
        """Display status with color coding."""
        colors = {
            'proposed': '#6c757d',
            'assigned': '#007bff',
            'in_progress': '#ffc107',
            'done': '#28a745',
            'rejected': '#dc3545',
            'blocked': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def priority_badge(self, obj):
        """Display priority with color coding."""
        colors = {
            'low': '#28a745',
            'medium': '#007bff',
            'high': '#ffc107',
            'urgent': '#dc3545',
        }
        color = colors.get(obj.priority, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'

    def overdue_indicator(self, obj):
        """Show if action is overdue."""
        if obj.is_overdue():
            return format_html('<span style="color: red; font-weight: bold;">⚠ OVERDUE</span>')
        return '✓ On track'
    overdue_indicator.short_description = 'Status'

    def mark_in_progress(self, request, queryset):
        """Mark selected actions as in progress."""
        count = 0
        for action in queryset:
            if action.can_start():
                action.start()
                count += 1
        self.message_user(request, f'{count} action(s) marked as in progress.')
    mark_in_progress.short_description = 'Mark as in progress'

    def mark_complete(self, request, queryset):
        """Mark selected actions as complete."""
        count = 0
        for action in queryset:
            if action.can_complete():
                action.complete()
                count += 1
        self.message_user(request, f'{count} action(s) marked as complete.')
    mark_complete.short_description = 'Mark as complete'


@admin.register(Minute)
class MinuteAdmin(admin.ModelAdmin):
    """Admin interface for Minute model."""

    list_display = [
        'meeting',
        'agenda_item',
        'minute_type',
        'recorded_by',
        'is_draft',
        'approved',
        'is_decision',
    ]

    list_filter = [
        'minute_type',
        'is_draft',
        'approved',
        'is_decision',
        'meeting__scheduled_date',
    ]

    search_fields = [
        'content',
        'decision_text',
        'meeting__title',
        'agenda_item__title',
    ]

    readonly_fields = [
        'created_at',
        'updated_at',
        'approved_at',
        'get_vote_summary',
    ]

    fieldsets = (
        ('Basic Information', {
            'fields': ('meeting', 'agenda_item', 'minute_type', 'section_order')
        }),
        ('Content', {
            'fields': ('content', 'recorded_by')
        }),
        ('Decision Information', {
            'fields': (
                'is_decision',
                'decision_text',
                'vote_count_for',
                'vote_count_against',
                'vote_count_abstain',
                'get_vote_summary',
            ),
            'classes': ('collapse',)
        }),
        ('Approval', {
            'fields': ('is_draft', 'approved', 'approved_by', 'approved_at')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    autocomplete_fields = ['meeting', 'agenda_item', 'recorded_by', 'approved_by']

    actions = ['approve_minutes', 'publish_minutes']

    def approve_minutes(self, request, queryset):
        """Approve selected minutes."""
        count = 0
        for minute in queryset.filter(approved=False):
            minute.approve(request.user)
            count += 1
        self.message_user(request, f'{count} minute(s) approved successfully.')
    approve_minutes.short_description = 'Approve selected minutes'

    def publish_minutes(self, request, queryset):
        """Publish selected minutes."""
        count = 0
        for minute in queryset.filter(is_draft=True):
            minute.publish()
            count += 1
        self.message_user(request, f'{count} minute(s) published successfully.')
    publish_minutes.short_description = 'Publish selected minutes'


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    """Admin interface for AttendanceRecord model."""

    list_display = [
        'user',
        'meeting',
        'present_indicator',
        'attendance_type',
        'role',
        'arrived_late',
        'left_early',
    ]

    list_filter = [
        'present',
        'attendance_type',
        'role',
        'arrived_late',
        'left_early',
        'meeting__scheduled_date',
    ]

    search_fields = [
        'user__username',
        'user__email',
        'meeting__title',
        'notes',
    ]

    readonly_fields = [
        'recorded_at',
        'created_at',
        'updated_at',
    ]

    fieldsets = (
        ('Basic Information', {
            'fields': ('meeting', 'user', 'recorded_by')
        }),
        ('Attendance Details', {
            'fields': ('present', 'attendance_type', 'role')
        }),
        ('Timing', {
            'fields': ('arrived_late', 'arrival_time', 'left_early', 'departure_time')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('recorded_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    autocomplete_fields = ['meeting', 'user', 'recorded_by']

    def present_indicator(self, obj):
        """Visual indicator for presence."""
        if obj.present:
            return format_html('<span style="color: green; font-weight: bold;">✓ Present</span>')
        return format_html('<span style="color: red;">✗ Absent</span>')
    present_indicator.short_description = 'Attendance'


@admin.register(ExternalRequest)
class ExternalRequestAdmin(admin.ModelAdmin):
    """Admin interface for ExternalRequest model."""

    list_display = [
        'proposed_title',
        'requester_name',
        'requester_organization',
        'meeting',
        'status_badge',
        'created_at',
    ]

    list_filter = [
        'status',
        'meeting__scheduled_date',
        'created_at',
    ]

    search_fields = [
        'proposed_title',
        'proposed_description',
        'requester_name',
        'requester_email',
        'requester_organization',
        'justification',
    ]

    readonly_fields = [
        'created_at',
        'updated_at',
        'reviewed_at',
        'agenda_item',
    ]

    fieldsets = (
        ('Requester Information', {
            'fields': ('requester_name', 'requester_email', 'requester_organization')
        }),
        ('Proposed Agenda Item', {
            'fields': ('meeting', 'proposed_title', 'proposed_description', 'justification')
        }),
        ('Supporting Materials', {
            'fields': ('supporting_documents_url',)
        }),
        ('Review', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'review_notes', 'agenda_item')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    autocomplete_fields = ['meeting', 'reviewed_by', 'agenda_item']

    actions = ['approve_requests', 'reject_requests']

    date_hierarchy = 'created_at'

    def status_badge(self, obj):
        """Display status with color coding."""
        colors = {
            'pending': '#ffc107',
            'approved': '#28a745',
            'rejected': '#dc3545',
            'deferred': '#007bff',
            'withdrawn': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def approve_requests(self, request, queryset):
        """Approve selected external requests."""
        count = 0
        for ext_request in queryset:
            if ext_request.can_approve():
                ext_request.approve(request.user, create_agenda_item=True)
                count += 1
        self.message_user(request, f'{count} request(s) approved successfully.')
    approve_requests.short_description = 'Approve selected requests'

    def reject_requests(self, request, queryset):
        """Reject selected external requests."""
        count = 0
        for ext_request in queryset:
            if ext_request.can_reject():
                ext_request.reject(request.user)
                count += 1
        self.message_user(request, f'{count} request(s) rejected.')
    reject_requests.short_description = 'Reject selected requests'
