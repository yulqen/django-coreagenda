"""
AgendaItem model for meeting agenda management.
"""
from django.db import models
from django.conf import settings
from .meeting import Meeting


class AgendaItem(models.Model):
    """
    Represents an item to be discussed in a meeting.

    Workflow:
        draft → submitted → approved/deferred/withdrawn

    Attributes:
        meeting: The meeting this item belongs to
        title: Brief title of the agenda item
        description: Detailed description
        proposer: User who proposed the item
        item_type: Type of agenda item (internal/external/consent)
        status: Current status in the workflow
        order: Display order in the agenda
        estimated_duration_minutes: Expected discussion time
        is_consent_item: Whether this is part of consent agenda
        background_info: Additional background information
        attachments_url: URL to related documents
        submitted_at: When the item was submitted
        reviewed_at: When the item was reviewed
        reviewed_by: User who reviewed the item
        created_at: Timestamp when item was created
        updated_at: Timestamp when item was last updated
    """

    ITEM_TYPE_CHOICES = [
        ('internal', 'Internal Item'),
        ('external', 'External Item'),
        ('consent', 'Consent Item'),
        ('information', 'Information Item'),
        ('discussion', 'Discussion Item'),
        ('decision', 'Decision Item'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('deferred', 'Deferred'),
        ('withdrawn', 'Withdrawn'),
        ('completed', 'Completed'),
    ]

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='agenda_items',
        help_text="The meeting this item belongs to"
    )

    title = models.CharField(
        max_length=255,
        help_text="Brief title of the agenda item"
    )

    description = models.TextField(
        help_text="Detailed description of the agenda item"
    )

    proposer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='proposed_agenda_items',
        help_text="User who proposed the item"
    )

    item_type = models.CharField(
        max_length=20,
        choices=ITEM_TYPE_CHOICES,
        default='internal',
        help_text="Type of agenda item"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        help_text="Current status in the workflow"
    )

    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order in the agenda"
    )

    estimated_duration_minutes = models.PositiveIntegerField(
        default=15,
        help_text="Expected discussion time in minutes"
    )

    is_consent_item = models.BooleanField(
        default=False,
        help_text="Whether this is part of consent agenda"
    )

    background_info = models.TextField(
        blank=True,
        help_text="Additional background information"
    )

    attachments_url = models.URLField(
        blank=True,
        help_text="URL to related documents"
    )

    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the item was submitted"
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the item was reviewed"
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_agenda_items',
        help_text="User who reviewed the item"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when item was created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when item was last updated"
    )

    # Many-to-many relationship with Presenter (defined in Presenter model)
    # presenters = ManyToManyField (reverse relation from Presenter)

    class Meta:
        ordering = ['meeting', 'order']
        indexes = [
            models.Index(fields=['meeting', 'order']),
            models.Index(fields=['status']),
        ]
        verbose_name = 'Agenda Item'
        verbose_name_plural = 'Agenda Items'

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def can_submit(self):
        """Check if the item can be submitted."""
        return self.status == 'draft'

    def submit(self, user=None):
        """
        Submit the agenda item for review.

        Transitions from 'draft' to 'submitted'.
        """
        if not self.can_submit():
            raise ValueError(f"Cannot submit item in '{self.status}' status")

        from django.utils import timezone
        self.status = 'submitted'
        self.submitted_at = timezone.now()
        self.save()

    def can_approve(self):
        """Check if the item can be approved."""
        return self.status == 'submitted'

    def approve(self, user):
        """
        Approve the agenda item.

        Transitions from 'submitted' to 'approved'.
        """
        if not self.can_approve():
            raise ValueError(f"Cannot approve item in '{self.status}' status")

        from django.utils import timezone
        self.status = 'approved'
        self.reviewed_at = timezone.now()
        self.reviewed_by = user
        self.save()

    def can_defer(self):
        """Check if the item can be deferred."""
        return self.status in ['submitted', 'approved']

    def defer(self, user):
        """
        Defer the agenda item to a future meeting.

        Transitions from 'submitted' or 'approved' to 'deferred'.
        """
        if not self.can_defer():
            raise ValueError(f"Cannot defer item in '{self.status}' status")

        from django.utils import timezone
        self.status = 'deferred'
        self.reviewed_at = timezone.now()
        self.reviewed_by = user
        self.save()

    def can_withdraw(self):
        """Check if the item can be withdrawn."""
        return self.status in ['draft', 'submitted']

    def withdraw(self, user=None):
        """
        Withdraw the agenda item.

        Transitions from 'draft' or 'submitted' to 'withdrawn'.
        """
        if not self.can_withdraw():
            raise ValueError(f"Cannot withdraw item in '{self.status}' status")

        from django.utils import timezone
        self.status = 'withdrawn'
        self.reviewed_at = timezone.now()
        if user:
            self.reviewed_by = user
        self.save()
