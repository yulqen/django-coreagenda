"""
AttendanceRecord model for tracking meeting attendance.
"""
from django.db import models
from django.conf import settings
from .meeting import Meeting


class AttendanceRecord(models.Model):
    """
    Tracks attendance for meetings.

    Records who attended, their role, and participation details.

    Attributes:
        meeting: The meeting this attendance record is for
        user: The user whose attendance is being tracked
        attendance_type: How the person attended
        role: The person's role in the meeting
        present: Whether the person was present
        arrived_late: Whether the person arrived late
        left_early: Whether the person left early
        arrival_time: Time of arrival (if late)
        departure_time: Time of departure (if early)
        notes: Additional notes about attendance
        recorded_by: User who recorded the attendance
        recorded_at: When the attendance was recorded
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    ATTENDANCE_TYPE_CHOICES = [
        ('in_person', 'In Person'),
        ('virtual', 'Virtual'),
        ('phone', 'By Phone'),
        ('absent', 'Absent'),
        ('excused', 'Excused Absence'),
    ]

    ROLE_CHOICES = [
        ('attendee', 'Attendee'),
        ('observer', 'Observer'),
        ('chairperson', 'Chairperson'),
        ('note_taker', 'Note Taker'),
        ('presenter', 'Presenter'),
        ('guest', 'Guest'),
    ]

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='attendance_records',
        help_text="The meeting this attendance record is for"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='attendance_records',
        help_text="The user whose attendance is being tracked"
    )

    attendance_type = models.CharField(
        max_length=20,
        choices=ATTENDANCE_TYPE_CHOICES,
        default='in_person',
        help_text="How the person attended"
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='attendee',
        help_text="The person's role in the meeting"
    )

    present = models.BooleanField(
        default=True,
        help_text="Whether the person was present"
    )

    arrived_late = models.BooleanField(
        default=False,
        help_text="Whether the person arrived late"
    )

    left_early = models.BooleanField(
        default=False,
        help_text="Whether the person left early"
    )

    arrival_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Time of arrival (if late)"
    )

    departure_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Time of departure (if early)"
    )

    notes = models.TextField(
        blank=True,
        help_text="Additional notes about attendance"
    )

    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendance_records_made',
        help_text="User who recorded the attendance"
    )

    recorded_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the attendance was recorded"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when record was created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when record was last updated"
    )

    class Meta:
        ordering = ['meeting', 'user']
        indexes = [
            models.Index(fields=['meeting', 'present']),
            models.Index(fields=['user']),
        ]
        unique_together = [['meeting', 'user']]
        verbose_name = 'Attendance Record'
        verbose_name_plural = 'Attendance Records'

    def __str__(self):
        status = "Present" if self.present else "Absent"
        return f"{self.user} - {self.meeting.title} ({status})"

    def mark_present(self, attendance_type='in_person', role='attendee'):
        """
        Mark the person as present.

        Args:
            attendance_type: How they attended
            role: Their role in the meeting
        """
        self.present = True
        self.attendance_type = attendance_type
        self.role = role
        self.save()

    def mark_absent(self, is_excused=False):
        """
        Mark the person as absent.

        Args:
            is_excused: Whether the absence is excused
        """
        self.present = False
        self.attendance_type = 'excused' if is_excused else 'absent'
        self.save()

    def record_late_arrival(self, arrival_time=None):
        """
        Record that the person arrived late.

        Args:
            arrival_time: Time of arrival (defaults to now)
        """
        from django.utils import timezone
        self.arrived_late = True
        self.arrival_time = arrival_time or timezone.now()
        self.save()

    def record_early_departure(self, departure_time=None):
        """
        Record that the person left early.

        Args:
            departure_time: Time of departure (defaults to now)
        """
        from django.utils import timezone
        self.left_early = True
        self.departure_time = departure_time or timezone.now()
        self.save()
