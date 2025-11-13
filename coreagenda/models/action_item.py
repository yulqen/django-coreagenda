"""
ActionItem model for tracking tasks arising from meetings.
"""
from django.db import models
from django.conf import settings
from .agenda_item import AgendaItem
from .meeting import Meeting


class ActionItem(models.Model):
    """
    Represents a task or action arising from a meeting.

    Workflow:
        proposed → assigned → in_progress → done/rejected

    Attributes:
        meeting: The meeting where the action was identified
        agenda_item: The agenda item that generated this action (optional)
        title: Brief title of the action
        description: Detailed description of what needs to be done
        assigned_to: User responsible for completing the action
        assigned_by: User who assigned the action
        status: Current status in the workflow
        priority: Priority level of the action
        due_date: Deadline for completion
        completed_at: When the action was completed
        completion_notes: Notes about the completion
        is_recurring: Whether this action recurs regularly
        recurrence_pattern: Pattern for recurring actions
        created_at: Timestamp when action was created
        updated_at: Timestamp when action was last updated
    """

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    STATUS_CHOICES = [
        ('proposed', 'Proposed'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('rejected', 'Rejected'),
        ('blocked', 'Blocked'),
    ]

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='action_items',
        help_text="The meeting where the action was identified"
    )

    agenda_item = models.ForeignKey(
        AgendaItem,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='action_items',
        help_text="The agenda item that generated this action"
    )

    title = models.CharField(
        max_length=255,
        help_text="Brief title of the action"
    )

    description = models.TextField(
        help_text="Detailed description of what needs to be done"
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='assigned_actions',
        null=True,
        blank=True,
        help_text="User responsible for completing the action"
    )

    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actions_assigned',
        help_text="User who assigned the action"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='proposed',
        help_text="Current status in the workflow"
    )

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        help_text="Priority level of the action"
    )

    due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Deadline for completion"
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the action was completed"
    )

    completion_notes = models.TextField(
        blank=True,
        help_text="Notes about the completion"
    )

    is_recurring = models.BooleanField(
        default=False,
        help_text="Whether this action recurs regularly"
    )

    recurrence_pattern = models.CharField(
        max_length=100,
        blank=True,
        help_text="Pattern for recurring actions (e.g., 'monthly', 'quarterly')"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when action was created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when action was last updated"
    )

    class Meta:
        ordering = ['-priority', 'due_date', '-created_at']
        indexes = [
            models.Index(fields=['status', 'due_date']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['meeting']),
        ]
        verbose_name = 'Action Item'
        verbose_name_plural = 'Action Items'

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def can_assign(self):
        """Check if the action can be assigned."""
        return self.status == 'proposed'

    def assign(self, user, assigned_by=None):
        """
        Assign the action to a user.

        Transitions from 'proposed' to 'assigned'.
        """
        if not self.can_assign():
            raise ValueError(f"Cannot assign action in '{self.status}' status")

        self.status = 'assigned'
        self.assigned_to = user
        if assigned_by:
            self.assigned_by = assigned_by
        self.save()

    def can_start(self):
        """Check if work can start on the action."""
        return self.status in ['proposed', 'assigned']

    def start(self):
        """
        Start work on the action.

        Transitions from 'proposed' or 'assigned' to 'in_progress'.
        """
        if not self.can_start():
            raise ValueError(f"Cannot start action in '{self.status}' status")

        self.status = 'in_progress'
        self.save()

    def can_complete(self):
        """Check if the action can be completed."""
        return self.status in ['assigned', 'in_progress']

    def complete(self, notes=''):
        """
        Mark the action as completed.

        Transitions from 'assigned' or 'in_progress' to 'done'.
        """
        if not self.can_complete():
            raise ValueError(f"Cannot complete action in '{self.status}' status")

        from django.utils import timezone
        self.status = 'done'
        self.completed_at = timezone.now()
        self.completion_notes = notes
        self.save()

    def can_reject(self):
        """Check if the action can be rejected."""
        return self.status in ['proposed', 'assigned']

    def reject(self, notes=''):
        """
        Reject the action.

        Transitions from 'proposed' or 'assigned' to 'rejected'.
        """
        if not self.can_reject():
            raise ValueError(f"Cannot reject action in '{self.status}' status")

        self.status = 'rejected'
        self.completion_notes = notes
        self.save()

    def is_overdue(self):
        """Check if the action is overdue."""
        if not self.due_date or self.status == 'done':
            return False

        from django.utils import timezone
        return timezone.now().date() > self.due_date
