"""
Presenter model for agenda item presenters.
"""
from django.db import models
from django.conf import settings
from .agenda_item import AgendaItem


class Presenter(models.Model):
    """
    Represents a presenter for an agenda item.

    An agenda item can have multiple presenters, and a person can present
    multiple agenda items (many-to-many relationship).

    Attributes:
        agenda_item: The agenda item being presented
        user: The user presenting (if internal)
        name: Name of the presenter (if external or custom)
        email: Email of the presenter
        affiliation: Organization or department
        is_primary: Whether this is the primary presenter
        presentation_order: Order in which presenters will present
        notes: Special notes about the presenter or presentation
        created_at: Timestamp when presenter was added
    """

    agenda_item = models.ForeignKey(
        AgendaItem,
        on_delete=models.CASCADE,
        related_name='presenters',
        help_text="The agenda item being presented"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='presentations',
        help_text="The user presenting (if internal)"
    )

    name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Name of the presenter (required if no user)"
    )

    email = models.EmailField(
        blank=True,
        help_text="Email of the presenter"
    )

    affiliation = models.CharField(
        max_length=255,
        blank=True,
        help_text="Organization or department"
    )

    is_primary = models.BooleanField(
        default=False,
        help_text="Whether this is the primary presenter"
    )

    presentation_order = models.PositiveIntegerField(
        default=0,
        help_text="Order in which presenters will present"
    )

    notes = models.TextField(
        blank=True,
        help_text="Special notes about the presenter or presentation"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when presenter was added"
    )

    class Meta:
        ordering = ['agenda_item', 'presentation_order', '-is_primary']
        indexes = [
            models.Index(fields=['agenda_item', 'presentation_order']),
        ]
        verbose_name = 'Presenter'
        verbose_name_plural = 'Presenters'

    def __str__(self):
        name = self.get_presenter_name()
        return f"{name} - {self.agenda_item.title}"

    def get_presenter_name(self):
        """Get the presenter's name from user or name field."""
        if self.user:
            return self.user.get_full_name() or self.user.username
        return self.name

    def get_presenter_email(self):
        """Get the presenter's email from user or email field."""
        if self.user:
            return self.user.email
        return self.email

    def clean(self):
        """Validate that either user or name is provided."""
        from django.core.exceptions import ValidationError
        if not self.user and not self.name:
            raise ValidationError("Either user or name must be provided")

    def save(self, *args, **kwargs):
        """Override save to run validation."""
        self.clean()
        super().save(*args, **kwargs)
