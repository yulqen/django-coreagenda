"""
Tests for service layer classes.
"""
import pytest
from datetime import timedelta
from django.utils import timezone

from coreagenda.models import Meeting, AgendaItem, ActionItem, Minute, AttendanceRecord
from coreagenda.services import (
    MeetingService,
    AgendaService,
    MinuteService,
    ActionService,
    AttendanceService,
)

pytestmark = pytest.mark.django_db


# ===== MeetingService Tests =====

@pytest.mark.integration
class TestMeetingService:
    """Test cases for MeetingService."""

    def test_schedule_meeting(self, chairperson, note_taker):
        """Test scheduling a new meeting."""
        scheduled_date = timezone.now() + timedelta(days=14)

        meeting = MeetingService.schedule_meeting(
            title='Board Meeting',
            scheduled_date=scheduled_date,
            chairperson=chairperson,
            duration_minutes=90,
            location='Main Hall',
            meeting_type='regular',
            description='Regular board meeting',
            note_taker=note_taker,
        )

        assert meeting.pk is not None
        assert meeting.title == 'Board Meeting'
        assert meeting.chairperson == chairperson
        assert meeting.note_taker == note_taker
        assert meeting.duration_minutes == 90
        assert meeting.status == 'draft'

    def test_publish_meeting(self, meeting, chairperson):
        """Test publishing a meeting."""
        assert not meeting.is_published
        assert meeting.status == 'draft'

        published = MeetingService.publish_meeting(meeting, chairperson)

        assert published.is_published is True
        assert published.status == 'scheduled'

    def test_cancel_meeting(self, meeting, chairperson):
        """Test cancelling a meeting."""
        reason = 'Venue unavailable'

        cancelled = MeetingService.cancel_meeting(meeting, chairperson, reason)

        assert cancelled.status == 'cancelled'

    def test_start_meeting(self, scheduled_meeting, chairperson):
        """Test starting a meeting."""
        assert scheduled_meeting.status == 'scheduled'

        started = MeetingService.start_meeting(scheduled_meeting, chairperson)

        assert started.status == 'in_progress'

    def test_complete_meeting(self, scheduled_meeting, chairperson):
        """Test completing a meeting."""
        # First start it
        MeetingService.start_meeting(scheduled_meeting, chairperson)

        completed = MeetingService.complete_meeting(scheduled_meeting, chairperson)

        assert completed.status == 'completed'

    def test_get_upcoming_meetings(self, chairperson):
        """Test getting upcoming meetings."""
        # Create some meetings
        for i in range(3):
            MeetingService.schedule_meeting(
                title=f'Future Meeting {i}',
                scheduled_date=timezone.now() + timedelta(days=i+1),
                chairperson=chairperson,
            )

        # Create a past meeting
        past = Meeting.objects.create(
            title='Past Meeting',
            scheduled_date=timezone.now() - timedelta(days=1),
            chairperson=chairperson,
            status='completed',
        )

        upcoming = MeetingService.get_upcoming_meetings(limit=10)

        assert upcoming.count() >= 3
        assert past not in upcoming


# ===== AgendaService Tests =====

@pytest.mark.integration
class TestAgendaService:
    """Test cases for AgendaService."""

    def test_submit_agenda_item(self, meeting, proposer):
        """Test submitting a new agenda item."""
        item = AgendaService.submit_agenda_item(
            meeting=meeting,
            title='Budget Review',
            description='Review Q4 budget',
            proposer=proposer,
            item_type='internal',
            estimated_duration_minutes=30,
        )

        assert item.pk is not None
        assert item.title == 'Budget Review'
        assert item.proposer == proposer
        assert item.meeting == meeting
        assert item.status == 'draft'

    def test_submit_agenda_item_with_presenters(self, meeting, proposer, user):
        """Test submitting agenda item with presenters."""
        presenters = [
            {'user': user, 'is_primary': True, 'presentation_order': 1}
        ]

        item = AgendaService.submit_agenda_item(
            meeting=meeting,
            title='Policy Update',
            description='Review policy',
            proposer=proposer,
            presenters=presenters,
        )

        assert item.presenters.count() == 1
        presenter = item.presenters.first()
        assert presenter.user == user
        assert presenter.is_primary is True

    def test_review_agenda_item_approve(self, submitted_agenda_item, reviewer):
        """Test approving an agenda item through review."""
        item = AgendaService.review_agenda_item(
            agenda_item=submitted_agenda_item,
            reviewer=reviewer,
            decision='approve',
            notes='Looks good',
        )

        assert item.status == 'approved'
        assert item.reviewed_by == reviewer

    def test_review_agenda_item_defer(self, submitted_agenda_item, reviewer):
        """Test deferring an agenda item through review."""
        item = AgendaService.review_agenda_item(
            agenda_item=submitted_agenda_item,
            reviewer=reviewer,
            decision='defer',
            notes='Need more information',
        )

        assert item.status == 'deferred'
        assert item.reviewed_by == reviewer

    def test_organize_agenda(self, meeting, proposer, reviewer):
        """Test organizing agenda item order."""
        # Create multiple items
        items = []
        for i in range(3):
            item = AgendaItem.objects.create(
                meeting=meeting,
                title=f'Item {i}',
                description='Test',
                proposer=proposer,
                status='approved',
                order=i,
            )
            items.append(item)

        # Reverse the order
        new_order = [items[2].pk, items[1].pk, items[0].pk]

        organized = AgendaService.organize_agenda(meeting, new_order, reviewer)

        # Check new order
        assert organized[0].order == 1
        assert organized[1].order == 2
        assert organized[2].order == 3

    def test_bundle_consent_agenda(self, meeting, proposer, reviewer):
        """Test bundling items into consent agenda."""
        # Create items
        item1 = AgendaItem.objects.create(
            meeting=meeting,
            title='Consent 1',
            description='Test',
            proposer=proposer,
            status='approved',
        )
        item2 = AgendaItem.objects.create(
            meeting=meeting,
            title='Consent 2',
            description='Test',
            proposer=proposer,
            status='approved',
        )

        bundled = AgendaService.bundle_consent_agenda(
            meeting=meeting,
            item_ids=[item1.pk, item2.pk],
            user=reviewer,
        )

        assert len(bundled) == 2
        assert all(item.is_consent_item for item in bundled)

    def test_add_presenter(self, agenda_item, user):
        """Test adding a presenter to agenda item."""
        presenter = AgendaService.add_presenter(
            agenda_item=agenda_item,
            user=user,
            is_primary=True,
        )

        assert presenter.agenda_item == agenda_item
        assert presenter.user == user
        assert presenter.is_primary is True

    def test_get_agenda_for_meeting(self, meeting_with_agenda):
        """Test getting agenda items for a meeting."""
        items = AgendaService.get_agenda_for_meeting(meeting_with_agenda)

        assert items.count() == 3
        assert all(item.meeting == meeting_with_agenda for item in items)

    def test_get_agenda_with_status_filter(self, meeting_with_agenda):
        """Test getting agenda items filtered by status."""
        items = AgendaService.get_agenda_for_meeting(
            meeting_with_agenda,
            status_filter='approved'
        )

        assert all(item.status == 'approved' for item in items)


# ===== MinuteService Tests =====

@pytest.mark.integration
class TestMinuteService:
    """Test cases for MinuteService."""

    def test_record_minute(self, meeting, user):
        """Test recording a minute."""
        minute = MinuteService.record_minute(
            meeting=meeting,
            content='Discussion about budget',
            recorded_by=user,
            minute_type='general',
        )

        assert minute.pk is not None
        assert minute.meeting == meeting
        assert minute.content == 'Discussion about budget'
        assert minute.recorded_by == user
        assert minute.is_draft is True

    def test_record_minute_with_agenda_item(self, meeting, agenda_item, user):
        """Test recording minute for specific agenda item."""
        minute = MinuteService.record_minute(
            meeting=meeting,
            content='Discussion about this item',
            recorded_by=user,
            agenda_item=agenda_item,
        )

        assert minute.agenda_item == agenda_item

    def test_record_decision(self, meeting, agenda_item, user):
        """Test recording a decision."""
        minute = MinuteService.record_decision(
            meeting=meeting,
            agenda_item=agenda_item,
            decision_text='Approved budget increase',
            recorded_by=user,
            vote_for=8,
            vote_against=2,
            vote_abstain=1,
        )

        assert minute.is_decision is True
        assert minute.decision_text == 'Approved budget increase'
        assert minute.vote_count_for == 8
        assert minute.vote_count_against == 2
        assert minute.vote_count_abstain == 1

    def test_update_minute(self, minute, user):
        """Test updating a minute."""
        new_content = 'Updated content'

        updated = MinuteService.update_minute(
            minute=minute,
            user=user,
            content=new_content,
        )

        assert updated.content == new_content

    def test_approve_minute(self, minute, reviewer):
        """Test approving a minute."""
        assert minute.approved is False

        approved = MinuteService.approve_minute(minute, reviewer)

        assert approved.approved is True
        assert approved.approved_by == reviewer

    def test_publish_minutes(self, meeting, user, reviewer):
        """Test publishing all approved minutes."""
        # Create multiple approved minutes
        for i in range(3):
            minute = Minute.objects.create(
                meeting=meeting,
                content=f'Minute {i}',
                recorded_by=user,
                is_draft=True,
            )
            minute.approve(reviewer)

        published = MinuteService.publish_minutes(meeting, reviewer)

        assert len(published) == 3
        assert all(not minute.is_draft for minute in published)

    def test_get_minutes_for_meeting(self, meeting, user):
        """Test getting minutes for a meeting."""
        # Create some minutes
        for i in range(2):
            Minute.objects.create(
                meeting=meeting,
                content=f'Minute {i}',
                recorded_by=user,
            )

        minutes = MinuteService.get_minutes_for_meeting(meeting, include_drafts=True)

        assert minutes.count() == 2


# ===== ActionService Tests =====

@pytest.mark.integration
class TestActionService:
    """Test cases for ActionService."""

    def test_create_action(self, meeting, user, chairperson):
        """Test creating an action item."""
        due_date = timezone.now().date() + timedelta(days=14)

        action = ActionService.create_action(
            meeting=meeting,
            title='Prepare report',
            description='Prepare quarterly report',
            assigned_by=chairperson,
            assigned_to=user,
            due_date=due_date,
            priority='high',
        )

        assert action.pk is not None
        assert action.title == 'Prepare report'
        assert action.assigned_to == user
        assert action.assigned_by == chairperson
        assert action.status == 'assigned'

    def test_assign_action(self, meeting, user, chairperson):
        """Test assigning an action."""
        action = ActionItem.objects.create(
            meeting=meeting,
            title='Test',
            description='Test',
            status='proposed',
        )

        assigned = ActionService.assign_action(
            action=action,
            assigned_to=user,
            assigned_by=chairperson,
        )

        assert assigned.status == 'assigned'
        assert assigned.assigned_to == user
        assert assigned.assigned_by == chairperson

    def test_start_action(self, action_item, user):
        """Test starting an action."""
        started = ActionService.start_action(action_item, user)

        assert started.status == 'in_progress'

    def test_complete_action(self, action_item, user):
        """Test completing an action."""
        notes = 'Task completed successfully'

        completed = ActionService.complete_action(action_item, user, notes)

        assert completed.status == 'done'
        assert completed.completion_notes == notes
        assert completed.completed_at is not None

    def test_reject_action(self, action_item, user):
        """Test rejecting an action."""
        notes = 'Not feasible'

        rejected = ActionService.reject_action(action_item, user, notes)

        assert rejected.status == 'rejected'
        assert rejected.completion_notes == notes

    def test_get_actions_for_user(self, action_item, user):
        """Test getting actions for a user."""
        actions = ActionService.get_actions_for_user(user)

        assert action_item in actions

    def test_get_actions_for_user_by_status(self, action_item, user):
        """Test getting actions filtered by status."""
        actions = ActionService.get_actions_for_user(user, status_filter='assigned')

        assert all(action.status == 'assigned' for action in actions)

    def test_get_overdue_actions(self, overdue_action_item, user):
        """Test getting overdue actions."""
        overdue = ActionService.get_overdue_actions(user)

        assert overdue_action_item in overdue


# ===== AttendanceService Tests =====

@pytest.mark.integration
class TestAttendanceService:
    """Test cases for AttendanceService."""

    def test_mark_attendance(self, meeting, user):
        """Test marking attendance."""
        record = AttendanceService.mark_attendance(
            meeting=meeting,
            user=user,
            present=True,
            attendance_type='in_person',
            role='attendee',
        )

        assert record.pk is not None
        assert record.meeting == meeting
        assert record.user == user
        assert record.present is True

    def test_mark_present(self, meeting, user):
        """Test marking user as present."""
        record = AttendanceService.mark_present(
            meeting=meeting,
            user=user,
            attendance_type='virtual',
        )

        assert record.present is True
        assert record.attendance_type == 'virtual'

    def test_mark_absent(self, meeting, user):
        """Test marking user as absent."""
        record = AttendanceService.mark_absent(
            meeting=meeting,
            user=user,
            is_excused=True,
        )

        assert record.present is False
        assert record.attendance_type == 'excused'

    def test_record_late_arrival(self, meeting, user):
        """Test recording late arrival."""
        # First mark present
        AttendanceService.mark_present(meeting, user)

        # Then record late arrival
        record = AttendanceService.record_late_arrival(meeting, user)

        assert record.arrived_late is True
        assert record.arrival_time is not None

    def test_record_early_departure(self, meeting, user):
        """Test recording early departure."""
        # First mark present
        AttendanceService.mark_present(meeting, user)

        # Then record early departure
        record = AttendanceService.record_early_departure(meeting, user)

        assert record.left_early is True
        assert record.departure_time is not None

    def test_bulk_mark_attendance(self, meeting, multiple_users):
        """Test bulk marking attendance."""
        attendance_data = [
            {'user': user, 'present': True, 'attendance_type': 'in_person'}
            for user in multiple_users
        ]

        records = AttendanceService.bulk_mark_attendance(
            meeting=meeting,
            attendance_data=attendance_data,
        )

        assert len(records) == len(multiple_users)
        assert all(record.present for record in records)

    def test_get_attendance_for_meeting(self, meeting, user):
        """Test getting attendance records for a meeting."""
        AttendanceService.mark_present(meeting, user)

        records = AttendanceService.get_attendance_for_meeting(meeting)

        assert records.count() >= 1

    def test_get_attendance_for_meeting_present_only(self, meeting, user, multiple_users):
        """Test getting only present attendees."""
        AttendanceService.mark_present(meeting, user)
        AttendanceService.mark_absent(meeting, multiple_users[0])

        records = AttendanceService.get_attendance_for_meeting(meeting, present_only=True)

        assert all(record.present for record in records)

    def test_get_attendance_summary(self, meeting, multiple_users):
        """Test getting attendance summary."""
        # Mark some present, some absent
        AttendanceService.mark_present(meeting, multiple_users[0])
        AttendanceService.mark_present(meeting, multiple_users[1])
        AttendanceService.mark_absent(meeting, multiple_users[2])

        summary = AttendanceService.get_attendance_summary(meeting)

        assert 'total_invited' in summary
        assert 'present' in summary
        assert 'absent' in summary
        assert 'attendance_rate' in summary
        assert summary['present'] == 2
        assert summary['absent'] == 1

    def test_get_user_attendance_history(self, user, multiple_users, chairperson):
        """Test getting user's attendance history."""
        # Create multiple meetings with attendance
        for i in range(3):
            meeting = Meeting.objects.create(
                title=f'Meeting {i}',
                scheduled_date=timezone.now() + timedelta(days=i),
                chairperson=chairperson,
            )
            AttendanceService.mark_present(meeting, user)

        history = AttendanceService.get_user_attendance_history(user)

        assert history.count() == 3
