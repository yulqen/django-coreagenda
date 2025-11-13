"""
Tests for the AgendaItem model and its workflow.
"""
import pytest
from datetime import timedelta
from django.utils import timezone

from coreagenda.models import AgendaItem


@pytest.mark.unit
class TestAgendaItemModel:
    """Test cases for AgendaItem model."""

    def test_create_agenda_item(self, meeting, proposer):
        """Test creating a basic agenda item."""
        item = AgendaItem.objects.create(
            meeting=meeting,
            title='Test Item',
            description='Test Description',
            proposer=proposer,
            item_type='internal',
            estimated_duration_minutes=15,
        )

        assert item.pk is not None
        assert item.title == 'Test Item'
        assert item.status == 'draft'  # Default status
        assert item.meeting == meeting
        assert item.proposer == proposer
        assert item.estimated_duration_minutes == 15

    def test_agenda_item_str_representation(self, agenda_item):
        """Test agenda item string representation."""
        str_repr = str(agenda_item)
        assert agenda_item.title in str_repr
        assert agenda_item.get_status_display() in str_repr

    def test_agenda_item_ordering(self, meeting, proposer):
        """Test agenda items are ordered by meeting and order field."""
        item1 = AgendaItem.objects.create(
            meeting=meeting,
            title='First',
            description='Test',
            proposer=proposer,
            order=2,
        )
        item2 = AgendaItem.objects.create(
            meeting=meeting,
            title='Second',
            description='Test',
            proposer=proposer,
            order=1,
        )
        item3 = AgendaItem.objects.create(
            meeting=meeting,
            title='Third',
            description='Test',
            proposer=proposer,
            order=0,
        )

        items = list(AgendaItem.objects.filter(meeting=meeting).order_by('order'))
        assert items[0] == item3  # order=0
        assert items[1] == item2  # order=1
        assert items[2] == item1  # order=2

    def test_item_types(self, meeting, proposer):
        """Test different item types."""
        types = ['internal', 'external', 'consent', 'information', 'discussion', 'decision']

        for item_type in types:
            item = AgendaItem.objects.create(
                meeting=meeting,
                title=f'{item_type} item',
                description='Test',
                proposer=proposer,
                item_type=item_type,
            )
            assert item.item_type == item_type

    def test_consent_item_flag(self, agenda_item):
        """Test consent item flag."""
        assert agenda_item.is_consent_item is False

        agenda_item.is_consent_item = True
        agenda_item.save()
        assert agenda_item.is_consent_item is True

    def test_default_estimated_duration(self, meeting, proposer):
        """Test default estimated duration."""
        item = AgendaItem.objects.create(
            meeting=meeting,
            title='Test',
            description='Test',
            proposer=proposer,
            # No estimated_duration_minutes specified
        )
        assert item.estimated_duration_minutes == 15  # Default

    def test_background_info_and_attachments(self, meeting, proposer):
        """Test optional background info and attachments."""
        item = AgendaItem.objects.create(
            meeting=meeting,
            title='Test',
            description='Test',
            proposer=proposer,
            background_info='Additional background information',
            attachments_url='https://example.com/docs/item1.pdf',
        )

        assert item.background_info == 'Additional background information'
        assert item.attachments_url == 'https://example.com/docs/item1.pdf'

    def test_timestamps(self, agenda_item):
        """Test automatic timestamp fields."""
        assert agenda_item.created_at is not None
        assert agenda_item.updated_at is not None
        assert agenda_item.submitted_at is None  # Not yet submitted
        assert agenda_item.reviewed_at is None  # Not yet reviewed


@pytest.mark.workflow
class TestAgendaItemWorkflow:
    """Test AgendaItem workflow state transitions."""

    def test_can_submit_draft_item(self, agenda_item):
        """Test that draft items can be submitted."""
        assert agenda_item.status == 'draft'
        assert agenda_item.can_submit() is True

    def test_submit_draft_item(self, agenda_item):
        """Test submitting a draft item."""
        assert agenda_item.status == 'draft'
        assert agenda_item.submitted_at is None

        agenda_item.submit()

        assert agenda_item.status == 'submitted'
        assert agenda_item.submitted_at is not None

    def test_cannot_submit_non_draft_item(self, submitted_agenda_item):
        """Test that non-draft items cannot be submitted."""
        assert submitted_agenda_item.status == 'submitted'
        assert submitted_agenda_item.can_submit() is False

        with pytest.raises(ValueError, match="Cannot submit"):
            submitted_agenda_item.submit()

    def test_can_approve_submitted_item(self, submitted_agenda_item):
        """Test that submitted items can be approved."""
        assert submitted_agenda_item.status == 'submitted'
        assert submitted_agenda_item.can_approve() is True

    def test_approve_submitted_item(self, submitted_agenda_item, reviewer):
        """Test approving a submitted item."""
        assert submitted_agenda_item.status == 'submitted'
        assert submitted_agenda_item.reviewed_at is None
        assert submitted_agenda_item.reviewed_by is None

        submitted_agenda_item.approve(reviewer)

        assert submitted_agenda_item.status == 'approved'
        assert submitted_agenda_item.reviewed_at is not None
        assert submitted_agenda_item.reviewed_by == reviewer

    def test_cannot_approve_draft_item(self, agenda_item, reviewer):
        """Test that draft items cannot be approved."""
        assert agenda_item.status == 'draft'
        assert agenda_item.can_approve() is False

        with pytest.raises(ValueError, match="Cannot approve"):
            agenda_item.approve(reviewer)

    def test_can_defer_submitted_item(self, submitted_agenda_item):
        """Test that submitted items can be deferred."""
        assert submitted_agenda_item.can_defer() is True

    def test_defer_submitted_item(self, submitted_agenda_item, reviewer):
        """Test deferring a submitted item."""
        submitted_agenda_item.defer(reviewer)

        assert submitted_agenda_item.status == 'deferred'
        assert submitted_agenda_item.reviewed_at is not None
        assert submitted_agenda_item.reviewed_by == reviewer

    def test_defer_approved_item(self, approved_agenda_item, reviewer):
        """Test deferring an approved item."""
        assert approved_agenda_item.status == 'approved'
        assert approved_agenda_item.can_defer() is True

        approved_agenda_item.defer(reviewer)

        assert approved_agenda_item.status == 'deferred'

    def test_cannot_defer_draft_item(self, agenda_item, reviewer):
        """Test that draft items cannot be deferred."""
        assert agenda_item.status == 'draft'
        assert agenda_item.can_defer() is False

        with pytest.raises(ValueError, match="Cannot defer"):
            agenda_item.defer(reviewer)

    def test_can_withdraw_draft_item(self, agenda_item):
        """Test that draft items can be withdrawn."""
        assert agenda_item.can_withdraw() is True

    def test_can_withdraw_submitted_item(self, submitted_agenda_item):
        """Test that submitted items can be withdrawn."""
        assert submitted_agenda_item.can_withdraw() is True

    def test_withdraw_draft_item(self, agenda_item):
        """Test withdrawing a draft item."""
        agenda_item.withdraw()

        assert agenda_item.status == 'withdrawn'
        assert agenda_item.reviewed_at is not None

    def test_withdraw_submitted_item(self, submitted_agenda_item, reviewer):
        """Test withdrawing a submitted item."""
        submitted_agenda_item.withdraw(reviewer)

        assert submitted_agenda_item.status == 'withdrawn'
        assert submitted_agenda_item.reviewed_by == reviewer

    def test_cannot_withdraw_approved_item(self, approved_agenda_item):
        """Test that approved items cannot be withdrawn."""
        assert approved_agenda_item.status == 'approved'
        assert approved_agenda_item.can_withdraw() is False

        with pytest.raises(ValueError, match="Cannot withdraw"):
            approved_agenda_item.withdraw()

    def test_full_workflow_approve(self, agenda_item, reviewer):
        """Test complete workflow: draft → submitted → approved."""
        # Start in draft
        assert agenda_item.status == 'draft'

        # Submit
        agenda_item.submit()
        assert agenda_item.status == 'submitted'

        # Approve
        agenda_item.approve(reviewer)
        assert agenda_item.status == 'approved'
        assert agenda_item.reviewed_by == reviewer

    def test_full_workflow_defer(self, agenda_item, reviewer):
        """Test complete workflow: draft → submitted → deferred."""
        # Start in draft
        assert agenda_item.status == 'draft'

        # Submit
        agenda_item.submit()
        assert agenda_item.status == 'submitted'

        # Defer
        agenda_item.defer(reviewer)
        assert agenda_item.status == 'deferred'
        assert agenda_item.reviewed_by == reviewer

    def test_full_workflow_withdraw(self, agenda_item):
        """Test complete workflow: draft → submitted → withdrawn."""
        # Start in draft
        assert agenda_item.status == 'draft'

        # Submit
        agenda_item.submit()
        assert agenda_item.status == 'submitted'

        # Withdraw
        agenda_item.withdraw()
        assert agenda_item.status == 'withdrawn'


@pytest.mark.integration
class TestAgendaItemRelationships:
    """Test AgendaItem model relationships."""

    def test_meeting_relationship(self, agenda_item, meeting):
        """Test meeting foreign key relationship."""
        assert agenda_item.meeting == meeting
        assert agenda_item in meeting.agenda_items.all()

    def test_proposer_relationship(self, agenda_item, proposer):
        """Test proposer foreign key relationship."""
        assert agenda_item.proposer == proposer
        assert agenda_item in proposer.proposed_agenda_items.all()

    def test_reviewed_by_relationship(self, approved_agenda_item, reviewer):
        """Test reviewed_by foreign key relationship."""
        assert approved_agenda_item.reviewed_by == reviewer
        assert approved_agenda_item in reviewer.reviewed_agenda_items.all()

    def test_presenters_relationship(self, agenda_item, presenter):
        """Test presenters one-to-many relationship."""
        assert presenter.agenda_item == agenda_item
        assert presenter in agenda_item.presenters.all()

    def test_action_items_relationship(self, full_meeting):
        """Test action items can be linked to agenda items."""
        agenda_item = full_meeting.agenda_items.first()
        action_items = agenda_item.action_items.all()
        assert action_items.count() > 0

    def test_minutes_relationship(self, approved_agenda_item, note_taker):
        """Test minutes can be linked to agenda items."""
        from coreagenda.models import Minute

        minute = Minute.objects.create(
            meeting=approved_agenda_item.meeting,
            agenda_item=approved_agenda_item,
            content='Discussion about this item',
            recorded_by=note_taker,
        )

        assert minute in approved_agenda_item.minutes.all()

    def test_cascade_delete_meeting(self, meeting, agenda_item):
        """Test that deleting meeting cascades to agenda items."""
        item_id = agenda_item.pk
        meeting.delete()

        assert not AgendaItem.objects.filter(pk=item_id).exists()

    def test_multiple_items_same_meeting(self, meeting, proposer):
        """Test multiple agenda items for same meeting."""
        item1 = AgendaItem.objects.create(
            meeting=meeting,
            title='Item 1',
            description='Test',
            proposer=proposer,
        )
        item2 = AgendaItem.objects.create(
            meeting=meeting,
            title='Item 2',
            description='Test',
            proposer=proposer,
        )

        items = meeting.agenda_items.all()
        assert item1 in items
        assert item2 in items
        assert items.count() >= 2


@pytest.mark.integration
class TestAgendaItemBehaviors:
    """Test AgendaItem complex behaviors."""

    def test_ordering_multiple_items(self, meeting, proposer):
        """Test ordering multiple agenda items."""
        items = []
        for i in range(5):
            item = AgendaItem.objects.create(
                meeting=meeting,
                title=f'Item {i}',
                description='Test',
                proposer=proposer,
                order=i,
            )
            items.append(item)

        retrieved_items = list(meeting.agenda_items.order_by('order'))
        for i, item in enumerate(retrieved_items):
            assert item.order == i

    def test_consent_agenda_items(self, meeting, proposer):
        """Test filtering consent agenda items."""
        regular_item = AgendaItem.objects.create(
            meeting=meeting,
            title='Regular',
            description='Test',
            proposer=proposer,
            is_consent_item=False,
        )
        consent_item = AgendaItem.objects.create(
            meeting=meeting,
            title='Consent',
            description='Test',
            proposer=proposer,
            is_consent_item=True,
        )

        consent_items = meeting.agenda_items.filter(is_consent_item=True)
        assert consent_item in consent_items
        assert regular_item not in consent_items

    def test_filter_by_status(self, meeting, proposer, reviewer):
        """Test filtering agenda items by status."""
        draft = AgendaItem.objects.create(
            meeting=meeting,
            title='Draft',
            description='Test',
            proposer=proposer,
            status='draft',
        )
        submitted = AgendaItem.objects.create(
            meeting=meeting,
            title='Submitted',
            description='Test',
            proposer=proposer,
            status='draft',
        )
        submitted.submit()

        approved = AgendaItem.objects.create(
            meeting=meeting,
            title='Approved',
            description='Test',
            proposer=proposer,
            status='draft',
        )
        approved.submit()
        approved.approve(reviewer)

        draft_items = meeting.agenda_items.filter(status='draft')
        submitted_items = meeting.agenda_items.filter(status='submitted')
        approved_items = meeting.agenda_items.filter(status='approved')

        assert draft in draft_items
        assert submitted in submitted_items
        assert approved in approved_items
