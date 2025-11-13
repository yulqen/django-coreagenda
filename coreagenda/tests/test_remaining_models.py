"""
Tests for Minute, AttendanceRecord, Presenter, and ExternalRequest models.
"""
import pytest
from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError

from coreagenda.models import Minute, AttendanceRecord, Presenter, ExternalRequest


# ===== Minute Model Tests =====

@pytest.mark.unit
class TestMinuteModel:
    """Test cases for Minute model."""

    def test_create_minute(self, meeting, user):
        """Test creating a basic minute."""
        minute = Minute.objects.create(
            meeting=meeting,
            content='Test minute content',
            minute_type='general',
            recorded_by=user,
        )

        assert minute.pk is not None
        assert minute.content == 'Test minute content'
        assert minute.minute_type == 'general'
        assert minute.recorded_by == user
        assert minute.is_draft is True
        assert minute.approved is False

    def test_minute_str_representation(self, minute):
        """Test minute string representation."""
        str_repr = str(minute)
        assert minute.meeting.title in str_repr

    def test_minute_types(self, meeting, user):
        """Test different minute types."""
        types = ['general', 'decision', 'discussion', 'action', 'procedural', 'attendance']

        for minute_type in types:
            minute = Minute.objects.create(
                meeting=meeting,
                content=f'Content for {minute_type}',
                minute_type=minute_type,
                recorded_by=user,
            )
            assert minute.minute_type == minute_type

    def test_decision_minute_with_votes(self, decision_minute):
        """Test decision minute with vote counts."""
        assert decision_minute.is_decision is True
        assert decision_minute.decision_text == 'Approved budget increase of 10%'
        assert decision_minute.vote_count_for == 8
        assert decision_minute.vote_count_against == 2
        assert decision_minute.vote_count_abstain == 1

    def test_get_vote_summary(self, decision_minute):
        """Test get_vote_summary method."""
        summary = decision_minute.get_vote_summary()
        assert 'For: 8' in summary
        assert 'Against: 2' in summary
        assert 'Abstain: 1' in summary

    def test_get_vote_summary_empty(self, minute):
        """Test get_vote_summary for non-decision minute."""
        assert minute.is_decision is False
        assert minute.get_vote_summary() == ''

    def test_approve_minute(self, minute, reviewer):
        """Test approving a minute."""
        assert minute.approved is False
        assert minute.is_draft is True

        minute.approve(reviewer)

        assert minute.approved is True
        assert minute.approved_by == reviewer
        assert minute.approved_at is not None
        assert minute.is_draft is False

    def test_publish_minute(self, minute):
        """Test publishing a minute."""
        assert minute.is_draft is True

        minute.publish()

        assert minute.is_draft is False

    def test_minute_with_agenda_item(self, meeting, agenda_item, user):
        """Test minute linked to specific agenda item."""
        minute = Minute.objects.create(
            meeting=meeting,
            agenda_item=agenda_item,
            content='Discussion about this agenda item',
            minute_type='discussion',
            recorded_by=user,
        )

        assert minute.agenda_item == agenda_item
        assert minute in agenda_item.minutes.all()


# ===== AttendanceRecord Model Tests =====

@pytest.mark.unit
class TestAttendanceRecordModel:
    """Test cases for AttendanceRecord model."""

    def test_create_attendance_record(self, meeting, user):
        """Test creating an attendance record."""
        record = AttendanceRecord.objects.create(
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
        assert record.attendance_type == 'in_person'
        assert record.role == 'attendee'

    def test_attendance_record_str(self, attendance_record):
        """Test attendance record string representation."""
        str_repr = str(attendance_record)
        assert 'Present' in str_repr or 'Absent' in str_repr

    def test_attendance_types(self, meeting, user):
        """Test different attendance types."""
        types = ['in_person', 'virtual', 'phone', 'absent', 'excused']

        for attendance_type in types:
            record = AttendanceRecord.objects.create(
                meeting=meeting,
                user=user,
                present=(attendance_type not in ['absent', 'excused']),
                attendance_type=attendance_type,
                role='attendee',
            )
            assert record.attendance_type == attendance_type

    def test_attendance_roles(self, meeting, user):
        """Test different attendance roles."""
        roles = ['attendee', 'observer', 'chairperson', 'note_taker', 'presenter', 'guest']

        for role in roles:
            record = AttendanceRecord.objects.create(
                meeting=meeting,
                user=user,
                present=True,
                attendance_type='in_person',
                role=role,
            )
            assert record.role == role

    def test_mark_present(self, meeting, user):
        """Test mark_present method."""
        record = AttendanceRecord.objects.create(
            meeting=meeting,
            user=user,
            present=False,
        )

        record.mark_present('virtual', 'attendee')

        assert record.present is True
        assert record.attendance_type == 'virtual'
        assert record.role == 'attendee'

    def test_mark_absent(self, meeting, user):
        """Test mark_absent method."""
        record = AttendanceRecord.objects.create(
            meeting=meeting,
            user=user,
            present=True,
        )

        record.mark_absent(is_excused=True)

        assert record.present is False
        assert record.attendance_type == 'excused'

    def test_record_late_arrival(self, meeting, user):
        """Test record_late_arrival method."""
        record = AttendanceRecord.objects.create(
            meeting=meeting,
            user=user,
            present=True,
        )

        arrival_time = timezone.now()
        record.record_late_arrival(arrival_time)

        assert record.arrived_late is True
        assert record.arrival_time == arrival_time

    def test_record_early_departure(self, meeting, user):
        """Test record_early_departure method."""
        record = AttendanceRecord.objects.create(
            meeting=meeting,
            user=user,
            present=True,
        )

        departure_time = timezone.now()
        record.record_early_departure(departure_time)

        assert record.left_early is True
        assert record.departure_time == departure_time

    def test_unique_together_constraint(self, meeting, user):
        """Test that user can only have one attendance record per meeting."""
        AttendanceRecord.objects.create(
            meeting=meeting,
            user=user,
            present=True,
        )

        # Second record for same user and meeting should violate unique_together
        with pytest.raises(Exception):  # Will be IntegrityError in real DB
            AttendanceRecord.objects.create(
                meeting=meeting,
                user=user,
                present=False,
            )


# ===== Presenter Model Tests =====

@pytest.mark.unit
class TestPresenterModel:
    """Test cases for Presenter model."""

    def test_create_internal_presenter(self, agenda_item, user):
        """Test creating an internal presenter with user."""
        presenter = Presenter.objects.create(
            agenda_item=agenda_item,
            user=user,
            is_primary=True,
            presentation_order=1,
        )

        assert presenter.pk is not None
        assert presenter.agenda_item == agenda_item
        assert presenter.user == user
        assert presenter.is_primary is True

    def test_create_external_presenter(self, agenda_item):
        """Test creating an external presenter without user."""
        presenter = Presenter.objects.create(
            agenda_item=agenda_item,
            name='External Speaker',
            email='speaker@external.com',
            affiliation='External Organization',
            is_primary=False,
            presentation_order=2,
        )

        assert presenter.pk is not None
        assert presenter.user is None
        assert presenter.name == 'External Speaker'
        assert presenter.email == 'speaker@external.com'
        assert presenter.affiliation == 'External Organization'

    def test_presenter_str(self, presenter):
        """Test presenter string representation."""
        str_repr = str(presenter)
        assert presenter.agenda_item.title in str_repr

    def test_get_presenter_name_from_user(self, presenter, user):
        """Test get_presenter_name when presenter has user."""
        assert presenter.user == user
        name = presenter.get_presenter_name()
        assert user.get_full_name() in name or user.username in name

    def test_get_presenter_name_from_name_field(self, external_presenter):
        """Test get_presenter_name when presenter has name field."""
        assert external_presenter.user is None
        name = external_presenter.get_presenter_name()
        assert name == external_presenter.name

    def test_get_presenter_email_from_user(self, presenter, user):
        """Test get_presenter_email when presenter has user."""
        assert presenter.user == user
        email = presenter.get_presenter_email()
        assert email == user.email

    def test_get_presenter_email_from_email_field(self, external_presenter):
        """Test get_presenter_email when presenter has email field."""
        assert external_presenter.user is None
        email = external_presenter.get_presenter_email()
        assert email == external_presenter.email

    def test_presenter_validation(self, agenda_item):
        """Test that presenter requires either user or name."""
        presenter = Presenter(
            agenda_item=agenda_item,
            # Neither user nor name provided
        )

        with pytest.raises(ValidationError):
            presenter.clean()

    def test_presentation_order(self, agenda_item, user, multiple_users):
        """Test ordering multiple presenters."""
        presenter1 = Presenter.objects.create(
            agenda_item=agenda_item,
            user=user,
            is_primary=True,
            presentation_order=1,
        )
        presenter2 = Presenter.objects.create(
            agenda_item=agenda_item,
            user=multiple_users[0],
            is_primary=False,
            presentation_order=2,
        )

        presenters = list(agenda_item.presenters.order_by('presentation_order'))
        assert presenters[0] == presenter1
        assert presenters[1] == presenter2


# ===== ExternalRequest Model Tests =====

@pytest.mark.unit
class TestExternalRequestModel:
    """Test cases for ExternalRequest model."""

    def test_create_external_request(self, meeting):
        """Test creating an external request."""
        request = ExternalRequest.objects.create(
            meeting=meeting,
            requester_name='John Doe',
            requester_email='john@example.com',
            requester_organization='Example Org',
            proposed_title='External Proposal',
            proposed_description='We propose this item',
            justification='Important for community',
            status='pending',
        )

        assert request.pk is not None
        assert request.requester_name == 'John Doe'
        assert request.status == 'pending'

    def test_external_request_str(self, external_request):
        """Test external request string representation."""
        str_repr = str(external_request)
        assert external_request.proposed_title in str_repr
        assert external_request.requester_name in str_repr

    def test_can_approve_pending_request(self, external_request):
        """Test that pending requests can be approved."""
        assert external_request.status == 'pending'
        assert external_request.can_approve() is True

    def test_approve_request(self, external_request, reviewer):
        """Test approving an external request."""
        assert external_request.agenda_item is None

        agenda_item = external_request.approve(reviewer, create_agenda_item=True)

        assert external_request.status == 'approved'
        assert external_request.reviewed_by == reviewer
        assert external_request.reviewed_at is not None
        assert agenda_item is not None
        assert external_request.agenda_item == agenda_item
        assert agenda_item.title == external_request.proposed_title
        assert agenda_item.item_type == 'external'

    def test_approve_without_creating_agenda_item(self, external_request, reviewer):
        """Test approving without auto-creating agenda item."""
        result = external_request.approve(reviewer, create_agenda_item=False)

        assert external_request.status == 'approved'
        assert external_request.agenda_item is None
        assert result is None

    def test_cannot_approve_non_pending(self, approved_external_request):
        """Test that non-pending requests cannot be approved."""
        assert approved_external_request.status == 'approved'
        assert approved_external_request.can_approve() is False

        with pytest.raises(ValueError, match="Cannot approve"):
            approved_external_request.approve(None)

    def test_can_reject_pending_request(self, external_request):
        """Test that pending requests can be rejected."""
        assert external_request.can_reject() is True

    def test_reject_request(self, external_request, reviewer):
        """Test rejecting an external request."""
        notes = 'Not appropriate at this time'
        external_request.reject(reviewer, notes)

        assert external_request.status == 'rejected'
        assert external_request.reviewed_by == reviewer
        assert external_request.review_notes == notes

    def test_can_defer_pending_request(self, external_request):
        """Test that pending requests can be deferred."""
        assert external_request.can_defer() is True

    def test_defer_request(self, external_request, reviewer):
        """Test deferring an external request."""
        notes = 'Consider for next meeting'
        external_request.defer(reviewer, notes)

        assert external_request.status == 'deferred'
        assert external_request.reviewed_by == reviewer
        assert external_request.review_notes == notes

    def test_withdraw_request(self, external_request):
        """Test withdrawing an external request."""
        assert external_request.status == 'pending'

        external_request.withdraw()

        assert external_request.status == 'withdrawn'

    def test_cannot_withdraw_approved(self, approved_external_request):
        """Test that approved requests cannot be withdrawn."""
        with pytest.raises(ValueError, match="Cannot withdraw"):
            approved_external_request.withdraw()

    def test_full_workflow_approve(self, meeting, reviewer):
        """Test complete workflow: pending → approved with agenda item."""
        # Create request
        request = ExternalRequest.objects.create(
            meeting=meeting,
            requester_name='Jane Doe',
            requester_email='jane@example.com',
            proposed_title='Important Matter',
            proposed_description='This should be discussed',
            justification='Community interest',
            status='pending',
        )

        # Approve and create agenda item
        agenda_item = request.approve(reviewer, create_agenda_item=True)

        assert request.status == 'approved'
        assert agenda_item.meeting == meeting
        assert agenda_item.proposer == reviewer
        assert agenda_item.title == request.proposed_title
        assert agenda_item.description == request.proposed_description
        assert agenda_item.item_type == 'external'


@pytest.mark.integration
class TestModelRelationships:
    """Test relationships between different models."""

    def test_minute_to_meeting_and_agenda_item(self, meeting, agenda_item, user):
        """Test minute relationships."""
        minute = Minute.objects.create(
            meeting=meeting,
            agenda_item=agenda_item,
            content='Test',
            recorded_by=user,
        )

        assert minute.meeting == meeting
        assert minute.agenda_item == agenda_item
        assert minute in meeting.minutes.all()
        assert minute in agenda_item.minutes.all()

    def test_attendance_cascade_delete(self, meeting, user):
        """Test that deleting meeting deletes attendance records."""
        record = AttendanceRecord.objects.create(
            meeting=meeting,
            user=user,
            present=True,
        )
        record_id = record.pk

        meeting.delete()

        assert not AttendanceRecord.objects.filter(pk=record_id).exists()

    def test_presenter_cascade_delete(self, agenda_item, user):
        """Test that deleting agenda item deletes presenters."""
        presenter = Presenter.objects.create(
            agenda_item=agenda_item,
            user=user,
        )
        presenter_id = presenter.pk

        agenda_item.delete()

        assert not Presenter.objects.filter(pk=presenter_id).exists()

    def test_external_request_with_agenda_item(self, approved_external_request):
        """Test external request linked to created agenda item."""
        assert approved_external_request.agenda_item is not None
        agenda_item = approved_external_request.agenda_item

        assert agenda_item.item_type == 'external'
        assert agenda_item.external_request == approved_external_request
