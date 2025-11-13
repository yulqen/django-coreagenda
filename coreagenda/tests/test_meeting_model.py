"""
Tests for the Meeting model.
"""
import pytest
from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError

from coreagenda.models import Meeting


@pytest.mark.unit
class TestMeetingModel:
    """Test cases for Meeting model."""

    def test_create_meeting(self, chairperson, note_taker):
        """Test creating a basic meeting."""
        scheduled_date = timezone.now() + timedelta(days=7)
        meeting = Meeting.objects.create(
            title='Test Meeting',
            description='Test Description',
            scheduled_date=scheduled_date,
            duration_minutes=60,
            location='Test Location',
            meeting_type='regular',
            chairperson=chairperson,
            note_taker=note_taker,
        )

        assert meeting.pk is not None
        assert meeting.title == 'Test Meeting'
        assert meeting.status == 'draft'  # Default status
        assert meeting.duration_minutes == 60
        assert meeting.chairperson == chairperson
        assert meeting.note_taker == note_taker
        assert not meeting.is_published

    def test_meeting_str_representation(self, meeting):
        """Test meeting string representation."""
        str_repr = str(meeting)
        assert meeting.title in str_repr
        assert meeting.scheduled_date.strftime('%Y-%m-%d') in str_repr

    def test_meeting_ordering(self, chairperson):
        """Test meetings are ordered by scheduled date descending."""
        now = timezone.now()
        meeting1 = Meeting.objects.create(
            title='First',
            scheduled_date=now + timedelta(days=1),
            chairperson=chairperson,
        )
        meeting2 = Meeting.objects.create(
            title='Second',
            scheduled_date=now + timedelta(days=2),
            chairperson=chairperson,
        )
        meeting3 = Meeting.objects.create(
            title='Third',
            scheduled_date=now + timedelta(days=3),
            chairperson=chairperson,
        )

        meetings = list(Meeting.objects.all())
        # Most recent first (descending order)
        assert meetings[0] == meeting3
        assert meetings[1] == meeting2
        assert meetings[2] == meeting1

    def test_get_end_time(self, meeting):
        """Test calculating meeting end time."""
        end_time = meeting.get_end_time()
        expected_end = meeting.scheduled_date + timedelta(minutes=meeting.duration_minutes)
        assert end_time == expected_end

    def test_is_upcoming(self, meeting):
        """Test is_upcoming method."""
        # meeting fixture is scheduled in the future
        assert meeting.is_upcoming() is True

        # Change to past date
        meeting.scheduled_date = timezone.now() - timedelta(days=1)
        meeting.save()
        assert meeting.is_upcoming() is False

        # Completed meeting is not upcoming
        meeting.status = 'completed'
        meeting.scheduled_date = timezone.now() + timedelta(days=1)
        meeting.save()
        assert meeting.is_upcoming() is False

    def test_is_past(self, meeting, past_meeting):
        """Test is_past method."""
        assert meeting.is_past() is False
        assert past_meeting.is_past() is True

    def test_can_add_agenda_items(self, meeting):
        """Test can_add_agenda_items method."""
        # Draft meeting can have items added
        assert meeting.status == 'draft'
        assert meeting.can_add_agenda_items() is True

        # Scheduled meeting can have items added
        meeting.status = 'scheduled'
        meeting.save()
        assert meeting.can_add_agenda_items() is True

        # Completed meeting cannot have items added
        meeting.status = 'completed'
        meeting.save()
        assert meeting.can_add_agenda_items() is False

        # In progress meeting cannot have items added
        meeting.status = 'in_progress'
        meeting.save()
        assert meeting.can_add_agenda_items() is False

    def test_meeting_types(self, chairperson):
        """Test different meeting types."""
        types = ['regular', 'emergency', 'special', 'workshop', 'retreat']

        for meeting_type in types:
            meeting = Meeting.objects.create(
                title=f'{meeting_type} meeting',
                scheduled_date=timezone.now() + timedelta(days=1),
                chairperson=chairperson,
                meeting_type=meeting_type,
            )
            assert meeting.meeting_type == meeting_type
            assert meeting.get_meeting_type_display() in [
                'Regular Meeting', 'Emergency Meeting', 'Special Meeting',
                'Workshop', 'Retreat'
            ]

    def test_meeting_statuses(self, meeting):
        """Test different meeting statuses."""
        statuses = ['draft', 'scheduled', 'in_progress', 'completed', 'cancelled', 'postponed']

        for status in statuses:
            meeting.status = status
            meeting.save()
            assert meeting.status == status

    def test_consent_agenda_enabled(self, meeting):
        """Test consent agenda enabling."""
        assert meeting.consent_agenda_enabled is False

        meeting.consent_agenda_enabled = True
        meeting.save()
        assert meeting.consent_agenda_enabled is True

    def test_meeting_without_note_taker(self, chairperson):
        """Test creating meeting without note taker."""
        meeting = Meeting.objects.create(
            title='Test Meeting',
            scheduled_date=timezone.now() + timedelta(days=7),
            chairperson=chairperson,
        )
        assert meeting.note_taker is None

    def test_meeting_with_agenda_items(self, meeting_with_agenda):
        """Test meeting with related agenda items."""
        meeting = meeting_with_agenda
        agenda_items = meeting.agenda_items.all()

        assert agenda_items.count() == 3
        assert all(item.meeting == meeting for item in agenda_items)

    def test_meeting_with_action_items(self, full_meeting):
        """Test meeting with related action items."""
        action_items = full_meeting.action_items.all()
        assert action_items.count() == 2
        assert all(item.meeting == full_meeting for item in action_items)

    def test_meeting_with_attendance(self, full_meeting):
        """Test meeting with attendance records."""
        attendance = full_meeting.attendance_records.all()
        assert attendance.count() > 0
        assert all(record.meeting == full_meeting for record in attendance)

    def test_meeting_with_minutes(self, full_meeting):
        """Test meeting with minutes."""
        minutes = full_meeting.minutes.all()
        assert minutes.count() > 0
        assert all(minute.meeting == full_meeting for minute in minutes)

    def test_default_duration(self, chairperson):
        """Test default meeting duration."""
        meeting = Meeting.objects.create(
            title='Test Meeting',
            scheduled_date=timezone.now() + timedelta(days=1),
            chairperson=chairperson,
            # No duration_minutes specified
        )
        assert meeting.duration_minutes == 60  # Default value

    def test_publishing_meeting(self, meeting):
        """Test publishing a meeting."""
        assert not meeting.is_published

        meeting.is_published = True
        meeting.status = 'scheduled'
        meeting.save()

        assert meeting.is_published
        assert meeting.status == 'scheduled'

    def test_timestamps(self, meeting):
        """Test automatic timestamp fields."""
        assert meeting.created_at is not None
        assert meeting.updated_at is not None

        original_updated = meeting.updated_at

        # Wait a tiny bit and update
        meeting.title = 'Updated Title'
        meeting.save()

        assert meeting.updated_at > original_updated


@pytest.mark.integration
class TestMeetingRelationships:
    """Test Meeting model relationships."""

    def test_chairperson_relationship(self, meeting, chairperson):
        """Test chairperson foreign key relationship."""
        assert meeting.chairperson == chairperson
        assert meeting in chairperson.chaired_meetings.all()

    def test_note_taker_relationship(self, meeting, note_taker):
        """Test note taker foreign key relationship."""
        assert meeting.note_taker == note_taker
        assert meeting in note_taker.note_taken_meetings.all()

    def test_cascade_agenda_items(self, meeting, agenda_item):
        """Test that deleting meeting deletes agenda items."""
        assert agenda_item.meeting == meeting
        meeting_id = meeting.pk

        meeting.delete()

        from coreagenda.models import AgendaItem
        assert not AgendaItem.objects.filter(pk=agenda_item.pk).exists()

    def test_cascade_action_items(self, full_meeting):
        """Test that deleting meeting deletes action items."""
        action_items = list(full_meeting.action_items.all())
        assert len(action_items) > 0

        meeting_id = full_meeting.pk
        full_meeting.delete()

        from coreagenda.models import ActionItem
        for action in action_items:
            assert not ActionItem.objects.filter(pk=action.pk).exists()

    def test_multiple_meetings_same_chairperson(self, chairperson):
        """Test multiple meetings with same chairperson."""
        meeting1 = Meeting.objects.create(
            title='Meeting 1',
            scheduled_date=timezone.now() + timedelta(days=1),
            chairperson=chairperson,
        )
        meeting2 = Meeting.objects.create(
            title='Meeting 2',
            scheduled_date=timezone.now() + timedelta(days=2),
            chairperson=chairperson,
        )

        chaired = chairperson.chaired_meetings.all()
        assert meeting1 in chaired
        assert meeting2 in chaired
        assert chaired.count() >= 2
