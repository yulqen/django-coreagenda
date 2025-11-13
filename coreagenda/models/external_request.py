"""
ExternalRequest model for requests from external parties to add agenda items.
"""
from django.db import models
from django.conf import settings
from .meeting import Meeting
from .agenda_item import AgendaItem


class ExternalRequest(models.Model):
    """
    Represents a request from an external party to add an agenda item.

    External parties (non-members) can submit requests to have items
    added to meeting agendas. These requests go through an approval process.

    Attributes:
        meeting: The meeting for which the item is requested
        requester_name: Name of the person making the request
        requester_email: Email of the requester
        requester_organization: Organization the requester represents
        proposed_title: Proposed title for the agenda item
        proposed_description: Proposed description
        justification: Why this item should be on the agenda
        supporting_documents_url: URL to supporting documents
        status: Current status of the request
        reviewed_by: User who reviewed the request
        reviewed_at: When the request was reviewed
        review_notes: Notes from the review
        agenda_item: Created agenda item (if approved)
        created_at: Timestamp when request was created
        updated_at: Timestamp when request was last updated
    """

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('deferred', 'Deferred'),
        ('withdrawn', 'Withdrawn'),
    ]

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='external_requests',
        help_text="The meeting for which the item is requested"
    )

    requester_name = models.CharField(
        max_length=255,
        help_text="Name of the person making the request"
    )

    requester_email = models.EmailField(
        help_text="Email of the requester"
    )

    requester_organization = models.CharField(
        max_length=255,
        blank=True,
        help_text="Organization the requester represents"
    )

    proposed_title = models.CharField(
        max_length=255,
        help_text="Proposed title for the agenda item"
    )

    proposed_description = models.TextField(
        help_text="Proposed description for the agenda item"
    )

    justification = models.TextField(
        help_text="Why this item should be on the agenda"
    )

    supporting_documents_url = models.URLField(
        blank=True,
        help_text="URL to supporting documents"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current status of the request"
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='external_requests_reviewed',
        help_text="User who reviewed the request"
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the request was reviewed"
    )

    review_notes = models.TextField(
        blank=True,
        help_text="Notes from the review"
    )

    agenda_item = models.OneToOneField(
        AgendaItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='external_request',
        help_text="Created agenda item (if approved)"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when request was created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when request was last updated"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['meeting']),
        ]
        verbose_name = 'External Request'
        verbose_name_plural = 'External Requests'

    def __str__(self):
        return f"{self.proposed_title} by {self.requester_name} ({self.get_status_display()})"

    def can_approve(self):
        """Check if the request can be approved."""
        return self.status == 'pending'

    def approve(self, reviewer, create_agenda_item=True):
        """
        Approve the external request.

        Args:
            reviewer: User approving the request
            create_agenda_item: Whether to automatically create an agenda item

        Returns:
            AgendaItem: The created agenda item (if create_agenda_item=True)
        """
        if not self.can_approve():
            raise ValueError(f"Cannot approve request in '{self.status}' status")

        from django.utils import timezone
        self.status = 'approved'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()

        if create_agenda_item and not self.agenda_item:
            # Create an agenda item from this request
            agenda_item = AgendaItem.objects.create(
                meeting=self.meeting,
                title=self.proposed_title,
                description=self.proposed_description,
                proposer=reviewer,  # The reviewer becomes the internal proposer
                item_type='external',
                status='submitted',
                background_info=self.justification,
                attachments_url=self.supporting_documents_url,
            )
            self.agenda_item = agenda_item

        self.save()
        return self.agenda_item

    def can_reject(self):
        """Check if the request can be rejected."""
        return self.status == 'pending'

    def reject(self, reviewer, notes=''):
        """
        Reject the external request.

        Args:
            reviewer: User rejecting the request
            notes: Reason for rejection
        """
        if not self.can_reject():
            raise ValueError(f"Cannot reject request in '{self.status}' status")

        from django.utils import timezone
        self.status = 'rejected'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()

    def can_defer(self):
        """Check if the request can be deferred."""
        return self.status == 'pending'

    def defer(self, reviewer, notes=''):
        """
        Defer the external request to a future meeting.

        Args:
            reviewer: User deferring the request
            notes: Reason for deferral
        """
        if not self.can_defer():
            raise ValueError(f"Cannot defer request in '{self.status}' status")

        from django.utils import timezone
        self.status = 'deferred'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()

    def withdraw(self):
        """
        Withdraw the external request (by requester).
        """
        if self.status not in ['pending', 'deferred']:
            raise ValueError(f"Cannot withdraw request in '{self.status}' status")

        self.status = 'withdrawn'
        self.save()
