"""
Minute model for meeting minutes and notes.
"""
from django.db import models
from django.conf import settings
from .meeting import Meeting
from .agenda_item import AgendaItem


class Minute(models.Model):
    """
    Represents meeting minutes and notes.

    Minutes can be associated with the overall meeting or specific agenda items.

    Attributes:
        meeting: The meeting these minutes belong to
        agenda_item: Specific agenda item (if applicable)
        content: The minute content/notes
        minute_type: Type of minute entry
        recorded_by: User who recorded the minutes
        is_draft: Whether the minutes are still in draft
        approved: Whether the minutes have been approved
        approved_by: User who approved the minutes
        approved_at: When the minutes were approved
        section_order: Order of this minute section
        is_decision: Whether this records a decision
        decision_text: Text of the decision made
        vote_count_for: Number of votes for (if applicable)
        vote_count_against: Number of votes against (if applicable)
        vote_count_abstain: Number of abstentions (if applicable)
        created_at: Timestamp when minute was created
        updated_at: Timestamp when minute was last updated
    """

    MINUTE_TYPE_CHOICES = [
        ('general', 'General Note'),
        ('decision', 'Decision'),
        ('discussion', 'Discussion Summary'),
        ('action', 'Action Point'),
        ('procedural', 'Procedural Note'),
        ('attendance', 'Attendance Note'),
    ]

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='minutes',
        help_text="The meeting these minutes belong to"
    )

    agenda_item = models.ForeignKey(
        AgendaItem,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='minutes',
        help_text="Specific agenda item (if applicable)"
    )

    content = models.TextField(
        help_text="The minute content/notes"
    )

    minute_type = models.CharField(
        max_length=20,
        choices=MINUTE_TYPE_CHOICES,
        default='general',
        help_text="Type of minute entry"
    )

    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='minutes_recorded',
        help_text="User who recorded the minutes"
    )

    is_draft = models.BooleanField(
        default=True,
        help_text="Whether the minutes are still in draft"
    )

    approved = models.BooleanField(
        default=False,
        help_text="Whether the minutes have been approved"
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='minutes_approved',
        help_text="User who approved the minutes"
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the minutes were approved"
    )

    section_order = models.PositiveIntegerField(
        default=0,
        help_text="Order of this minute section"
    )

    # Decision-specific fields
    is_decision = models.BooleanField(
        default=False,
        help_text="Whether this records a decision"
    )

    decision_text = models.TextField(
        blank=True,
        help_text="Text of the decision made"
    )

    vote_count_for = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of votes for (if applicable)"
    )

    vote_count_against = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of votes against (if applicable)"
    )

    vote_count_abstain = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of abstentions (if applicable)"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when minute was created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when minute was last updated"
    )

    class Meta:
        ordering = ['meeting', 'section_order', 'created_at']
        indexes = [
            models.Index(fields=['meeting', 'section_order']),
            models.Index(fields=['agenda_item']),
        ]
        verbose_name = 'Minute'
        verbose_name_plural = 'Minutes'

    def __str__(self):
        if self.agenda_item:
            return f"Minutes for {self.agenda_item.title}"
        return f"Minutes for {self.meeting.title}"

    def approve(self, user):
        """
        Approve the minutes.

        Args:
            user: The user approving the minutes
        """
        from django.utils import timezone
        self.approved = True
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save()

    def publish(self):
        """
        Publish the minutes (mark as not draft).
        """
        self.is_draft = False
        self.save()

    def get_vote_summary(self):
        """
        Get a summary of voting results if this is a decision.

        Returns:
            str: Formatted vote summary or empty string
        """
        if not self.is_decision:
            return ""

        parts = []
        if self.vote_count_for is not None:
            parts.append(f"For: {self.vote_count_for}")
        if self.vote_count_against is not None:
            parts.append(f"Against: {self.vote_count_against}")
        if self.vote_count_abstain is not None:
            parts.append(f"Abstain: {self.vote_count_abstain}")

        return ", ".join(parts) if parts else ""
