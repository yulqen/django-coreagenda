"""
Meeting model for executive meeting management.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class Meeting(models.Model):
    """
    Represents an executive meeting with scheduled date, attendees, and agenda.

    Attributes:
        title: Meeting title/name
        description: Detailed description of the meeting
        scheduled_date: Date and time when the meeting is scheduled
        duration_minutes: Expected duration in minutes
        location: Physical or virtual location of the meeting
        meeting_type: Type of meeting (regular, emergency, special, etc.)
        status: Current status of the meeting
        chairperson: User who chairs the meeting
        note_taker: User responsible for taking minutes
        created_at: Timestamp when meeting was created
        updated_at: Timestamp when meeting was last updated
        is_published: Whether the meeting details are published
        consent_agenda_enabled: Whether consent agenda bundling is enabled
    """

    MEETING_TYPE_CHOICES = [
        ('regular', 'Regular Meeting'),
        ('emergency', 'Emergency Meeting'),
        ('special', 'Special Meeting'),
        ('workshop', 'Workshop'),
        ('retreat', 'Retreat'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('postponed', 'Postponed'),
    ]

    title = models.CharField(
        max_length=255,
        help_text="Meeting title"
    )

    description = models.TextField(
        blank=True,
        help_text="Detailed description of the meeting"
    )

    scheduled_date = models.DateTimeField(
        help_text="Date and time when the meeting is scheduled"
    )

    duration_minutes = models.PositiveIntegerField(
        default=60,
        help_text="Expected duration in minutes"
    )

    location = models.CharField(
        max_length=255,
        blank=True,
        help_text="Physical or virtual location"
    )

    meeting_type = models.CharField(
        max_length=20,
        choices=MEETING_TYPE_CHOICES,
        default='regular',
        help_text="Type of meeting"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        help_text="Current status of the meeting"
    )

    chairperson = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='chaired_meetings',
        help_text="User who chairs the meeting"
    )

    note_taker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='note_taken_meetings',
        help_text="User responsible for taking minutes"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when meeting was created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when meeting was last updated"
    )

    is_published = models.BooleanField(
        default=False,
        help_text="Whether the meeting details are published"
    )

    consent_agenda_enabled = models.BooleanField(
        default=False,
        help_text="Whether consent agenda bundling is enabled"
    )

    class Meta:
        ordering = ['-scheduled_date']
        indexes = [
            models.Index(fields=['-scheduled_date']),
            models.Index(fields=['status']),
        ]
        verbose_name = 'Meeting'
        verbose_name_plural = 'Meetings'

    def __str__(self):
        return f"{self.title} - {self.scheduled_date.strftime('%Y-%m-%d')}"

    def get_end_time(self):
        """Calculate and return the meeting end time."""
        from datetime import timedelta
        return self.scheduled_date + timedelta(minutes=self.duration_minutes)

    def is_upcoming(self):
        """Check if the meeting is upcoming."""
        return self.scheduled_date > timezone.now() and self.status in ['draft', 'scheduled']

    def is_past(self):
        """Check if the meeting is in the past."""
        return self.scheduled_date < timezone.now()

    def can_add_agenda_items(self):
        """Check if agenda items can still be added."""
        return self.status in ['draft', 'scheduled']
