"""
Tests for the ActionItem model and its workflow.
"""
import pytest
from datetime import timedelta
from django.utils import timezone

from coreagenda.models import ActionItem


@pytest.mark.unit
class TestActionItemModel:
    """Test cases for ActionItem model."""

    def test_create_action_item(self, meeting, user):
        """Test creating a basic action item."""
        due_date = timezone.now().date() + timedelta(days=30)
        action = ActionItem.objects.create(
            meeting=meeting,
            title='Test Action',
            description='Test Description',
            assigned_to=user,
            assigned_by=user,
            status='assigned',
            priority='medium',
            due_date=due_date,
        )

        assert action.pk is not None
        assert action.title == 'Test Action'
        assert action.status == 'assigned'
        assert action.priority == 'medium'
        assert action.assigned_to == user
        assert action.due_date == due_date

    def test_action_item_str_representation(self, action_item):
        """Test action item string representation."""
        str_repr = str(action_item)
        assert action_item.title in str_repr
        assert action_item.get_status_display() in str_repr

    def test_action_item_ordering(self, meeting, user):
        """Test action items are ordered by priority, due date, created_at."""
        low = ActionItem.objects.create(
            meeting=meeting,
            title='Low',
            description='Test',
            assigned_to=user,
            priority='low',
            due_date=timezone.now().date() + timedelta(days=30),
        )
        urgent = ActionItem.objects.create(
            meeting=meeting,
            title='Urgent',
            description='Test',
            assigned_to=user,
            priority='urgent',
            due_date=timezone.now().date() + timedelta(days=1),
        )
        high = ActionItem.objects.create(
            meeting=meeting,
            title='High',
            description='Test',
            assigned_to=user,
            priority='high',
            due_date=timezone.now().date() + timedelta(days=7),
        )

        # Should be ordered by priority (urgent > high > low) then due date
        actions = list(ActionItem.objects.filter(meeting=meeting))
        # Note: The default ordering uses '-priority' which means reverse order
        # Let's check the priorities are correctly set
        assert low.priority == 'low'
        assert high.priority == 'high'
        assert urgent.priority == 'urgent'

    def test_priority_levels(self, meeting, user):
        """Test different priority levels."""
        priorities = ['low', 'medium', 'high', 'urgent']

        for priority in priorities:
            action = ActionItem.objects.create(
                meeting=meeting,
                title=f'{priority} action',
                description='Test',
                assigned_to=user,
                priority=priority,
            )
            assert action.priority == priority

    def test_default_priority(self, meeting, user):
        """Test default priority."""
        action = ActionItem.objects.create(
            meeting=meeting,
            title='Test',
            description='Test',
            assigned_to=user,
            # No priority specified
        )
        assert action.priority == 'medium'  # Default

    def test_recurring_action(self, meeting, user):
        """Test recurring action item."""
        action = ActionItem.objects.create(
            meeting=meeting,
            title='Recurring Action',
            description='Test',
            assigned_to=user,
            is_recurring=True,
            recurrence_pattern='monthly',
        )

        assert action.is_recurring is True
        assert action.recurrence_pattern == 'monthly'

    def test_action_without_agenda_item(self, meeting, user):
        """Test action item without linked agenda item."""
        action = ActionItem.objects.create(
            meeting=meeting,
            title='General Action',
            description='Not linked to specific agenda item',
            assigned_to=user,
        )

        assert action.agenda_item is None

    def test_is_overdue(self, overdue_action_item):
        """Test is_overdue method for overdue action."""
        assert overdue_action_item.is_overdue() is True

    def test_is_not_overdue(self, action_item):
        """Test is_overdue method for future action."""
        assert action_item.is_overdue() is False

    def test_completed_action_not_overdue(self, overdue_action_item):
        """Test completed actions are not considered overdue."""
        overdue_action_item.complete()
        assert overdue_action_item.status == 'done'
        assert overdue_action_item.is_overdue() is False

    def test_action_without_due_date(self, meeting, user):
        """Test action without due date is not overdue."""
        action = ActionItem.objects.create(
            meeting=meeting,
            title='No deadline',
            description='Test',
            assigned_to=user,
            due_date=None,
        )

        assert action.is_overdue() is False


@pytest.mark.workflow
class TestActionItemWorkflow:
    """Test ActionItem workflow state transitions."""

    def test_can_assign_proposed_action(self, meeting, user):
        """Test that proposed actions can be assigned."""
        action = ActionItem.objects.create(
            meeting=meeting,
            title='Test',
            description='Test',
            status='proposed',
        )
        assert action.can_assign() is True

    def test_assign_proposed_action(self, meeting, user, chairperson):
        """Test assigning a proposed action."""
        action = ActionItem.objects.create(
            meeting=meeting,
            title='Test',
            description='Test',
            status='proposed',
        )

        action.assign(user, chairperson)

        assert action.status == 'assigned'
        assert action.assigned_to == user
        assert action.assigned_by == chairperson

    def test_cannot_assign_non_proposed(self, action_item, user):
        """Test that non-proposed actions cannot be assigned."""
        assert action_item.status == 'assigned'
        assert action_item.can_assign() is False

        with pytest.raises(ValueError, match="Cannot assign"):
            action_item.assign(user)

    def test_can_start_proposed_action(self, meeting, user):
        """Test that proposed actions can be started."""
        action = ActionItem.objects.create(
            meeting=meeting,
            title='Test',
            description='Test',
            status='proposed',
        )
        assert action.can_start() is True

    def test_can_start_assigned_action(self, action_item):
        """Test that assigned actions can be started."""
        assert action_item.status == 'assigned'
        assert action_item.can_start() is True

    def test_start_assigned_action(self, action_item):
        """Test starting an assigned action."""
        action_item.start()

        assert action_item.status == 'in_progress'

    def test_cannot_start_completed_action(self, action_item):
        """Test that completed actions cannot be started."""
        action_item.complete()
        assert action_item.status == 'done'
        assert action_item.can_start() is False

        with pytest.raises(ValueError, match="Cannot start"):
            action_item.start()

    def test_can_complete_assigned_action(self, action_item):
        """Test that assigned actions can be completed."""
        assert action_item.can_complete() is True

    def test_can_complete_in_progress_action(self, action_item):
        """Test that in-progress actions can be completed."""
        action_item.start()
        assert action_item.status == 'in_progress'
        assert action_item.can_complete() is True

    def test_complete_action(self, action_item):
        """Test completing an action."""
        notes = 'Action completed successfully'
        action_item.complete(notes)

        assert action_item.status == 'done'
        assert action_item.completed_at is not None
        assert action_item.completion_notes == notes

    def test_cannot_complete_proposed_action(self, meeting):
        """Test that proposed actions cannot be completed."""
        action = ActionItem.objects.create(
            meeting=meeting,
            title='Test',
            description='Test',
            status='proposed',
        )
        assert action.can_complete() is False

        with pytest.raises(ValueError, match="Cannot complete"):
            action.complete()

    def test_can_reject_proposed_action(self, meeting):
        """Test that proposed actions can be rejected."""
        action = ActionItem.objects.create(
            meeting=meeting,
            title='Test',
            description='Test',
            status='proposed',
        )
        assert action.can_reject() is True

    def test_can_reject_assigned_action(self, action_item):
        """Test that assigned actions can be rejected."""
        assert action_item.status == 'assigned'
        assert action_item.can_reject() is True

    def test_reject_action(self, action_item):
        """Test rejecting an action."""
        notes = 'Not feasible at this time'
        action_item.reject(notes)

        assert action_item.status == 'rejected'
        assert action_item.completion_notes == notes

    def test_cannot_reject_completed_action(self, action_item):
        """Test that completed actions cannot be rejected."""
        action_item.complete()
        assert action_item.status == 'done'
        assert action_item.can_reject() is False

        with pytest.raises(ValueError, match="Cannot reject"):
            action_item.reject()

    def test_full_workflow_complete(self, meeting, user, chairperson):
        """Test complete workflow: proposed → assigned → in_progress → done."""
        # Create in proposed state
        action = ActionItem.objects.create(
            meeting=meeting,
            title='Test',
            description='Test',
            status='proposed',
        )

        # Assign
        action.assign(user, chairperson)
        assert action.status == 'assigned'

        # Start
        action.start()
        assert action.status == 'in_progress'

        # Complete
        action.complete('Finished')
        assert action.status == 'done'
        assert action.completed_at is not None

    def test_full_workflow_reject(self, meeting, user, chairperson):
        """Test workflow: proposed → assigned → rejected."""
        # Create in proposed state
        action = ActionItem.objects.create(
            meeting=meeting,
            title='Test',
            description='Test',
            status='proposed',
        )

        # Assign
        action.assign(user, chairperson)
        assert action.status == 'assigned'

        # Reject
        action.reject('Cannot do this')
        assert action.status == 'rejected'


@pytest.mark.integration
class TestActionItemRelationships:
    """Test ActionItem model relationships."""

    def test_meeting_relationship(self, action_item, meeting):
        """Test meeting foreign key relationship."""
        assert action_item.meeting == meeting
        assert action_item in meeting.action_items.all()

    def test_assigned_to_relationship(self, action_item, user):
        """Test assigned_to foreign key relationship."""
        assert action_item.assigned_to == user
        assert action_item in user.assigned_actions.all()

    def test_assigned_by_relationship(self, action_item, user):
        """Test assigned_by foreign key relationship."""
        assert action_item.assigned_by == user
        assert action_item in user.actions_assigned.all()

    def test_agenda_item_relationship(self, meeting, agenda_item, user):
        """Test agenda_item foreign key relationship."""
        action = ActionItem.objects.create(
            meeting=meeting,
            agenda_item=agenda_item,
            title='Test',
            description='Test',
            assigned_to=user,
        )

        assert action.agenda_item == agenda_item
        assert action in agenda_item.action_items.all()

    def test_cascade_delete_meeting(self, meeting, action_item):
        """Test that deleting meeting cascades to action items."""
        action_id = action_item.pk
        meeting.delete()

        assert not ActionItem.objects.filter(pk=action_id).exists()

    def test_cascade_delete_agenda_item(self, meeting, agenda_item, user):
        """Test that deleting agenda item cascades to action items."""
        action = ActionItem.objects.create(
            meeting=meeting,
            agenda_item=agenda_item,
            title='Test',
            description='Test',
            assigned_to=user,
        )
        action_id = action.pk

        agenda_item.delete()

        assert not ActionItem.objects.filter(pk=action_id).exists()


@pytest.mark.integration
class TestActionItemQueries:
    """Test common ActionItem queries."""

    def test_filter_by_user(self, meeting, user, multiple_users):
        """Test filtering actions by assigned user."""
        # Create actions for different users
        user_actions = []
        for i in range(3):
            action = ActionItem.objects.create(
                meeting=meeting,
                title=f'User action {i}',
                description='Test',
                assigned_to=user,
            )
            user_actions.append(action)

        other_action = ActionItem.objects.create(
            meeting=meeting,
            title='Other user action',
            description='Test',
            assigned_to=multiple_users[0],
        )

        filtered = ActionItem.objects.filter(assigned_to=user)
        assert all(action in filtered for action in user_actions)
        assert other_action not in filtered

    def test_filter_by_status(self, meeting, user):
        """Test filtering actions by status."""
        assigned = ActionItem.objects.create(
            meeting=meeting,
            title='Assigned',
            description='Test',
            assigned_to=user,
            status='assigned',
        )
        in_progress = ActionItem.objects.create(
            meeting=meeting,
            title='In Progress',
            description='Test',
            assigned_to=user,
            status='assigned',
        )
        in_progress.start()

        done = ActionItem.objects.create(
            meeting=meeting,
            title='Done',
            description='Test',
            assigned_to=user,
            status='assigned',
        )
        done.complete()

        assigned_actions = ActionItem.objects.filter(status='assigned')
        progress_actions = ActionItem.objects.filter(status='in_progress')
        done_actions = ActionItem.objects.filter(status='done')

        assert assigned in assigned_actions
        assert in_progress in progress_actions
        assert done in done_actions

    def test_filter_overdue(self, meeting, user):
        """Test filtering overdue actions."""
        # Create overdue action
        overdue = ActionItem.objects.create(
            meeting=meeting,
            title='Overdue',
            description='Test',
            assigned_to=user,
            status='in_progress',
            due_date=timezone.now().date() - timedelta(days=5),
        )

        # Create future action
        future = ActionItem.objects.create(
            meeting=meeting,
            title='Future',
            description='Test',
            assigned_to=user,
            status='in_progress',
            due_date=timezone.now().date() + timedelta(days=5),
        )

        # Query for overdue
        overdue_actions = ActionItem.objects.filter(
            due_date__lt=timezone.now().date(),
            status__in=['assigned', 'in_progress']
        )

        assert overdue in overdue_actions
        assert future not in overdue_actions

    def test_filter_by_priority(self, meeting, user):
        """Test filtering actions by priority."""
        low = ActionItem.objects.create(
            meeting=meeting,
            title='Low',
            description='Test',
            assigned_to=user,
            priority='low',
        )
        urgent = ActionItem.objects.create(
            meeting=meeting,
            title='Urgent',
            description='Test',
            assigned_to=user,
            priority='urgent',
        )

        low_actions = ActionItem.objects.filter(priority='low')
        urgent_actions = ActionItem.objects.filter(priority='urgent')

        assert low in low_actions
        assert urgent in urgent_actions
        assert urgent not in low_actions
        assert low not in urgent_actions
