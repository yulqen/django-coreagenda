"""
Pytest fixtures for django-coreagenda tests.

This module provides common fixtures for testing models and services.
"""
import pytest
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone

from coreagenda.models import (
    Meeting,
    AgendaItem,
    Presenter,
    ActionItem,
    Minute,
    AttendanceRecord,
    ExternalRequest,
)

User = get_user_model()


# User fixtures

@pytest.fixture
def user(db):
    """Create a regular user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )


@pytest.fixture
def chairperson(db):
    """Create a user who serves as chairperson."""
    return User.objects.create_user(
        username='chair',
        email='chair@example.com',
        password='testpass123',
        first_name='Chair',
        last_name='Person'
    )


@pytest.fixture
def note_taker(db):
    """Create a user who serves as note taker."""
    return User.objects.create_user(
        username='notetaker',
        email='notetaker@example.com',
        password='testpass123',
        first_name='Note',
        last_name='Taker'
    )


@pytest.fixture
def reviewer(db):
    """Create a user who reviews agenda items."""
    return User.objects.create_user(
        username='reviewer',
        email='reviewer@example.com',
        password='testpass123',
        first_name='Review',
        last_name='Er'
    )


@pytest.fixture
def proposer(db):
    """Create a user who proposes agenda items."""
    return User.objects.create_user(
        username='proposer',
        email='proposer@example.com',
        password='testpass123',
        first_name='Prop',
        last_name='Oser'
    )


# Meeting fixtures

@pytest.fixture
def meeting(db, chairperson, note_taker):
    """Create a basic meeting."""
    scheduled_date = timezone.now() + timedelta(days=7)
    return Meeting.objects.create(
        title='Board Meeting',
        description='Regular board meeting',
        scheduled_date=scheduled_date,
        duration_minutes=120,
        location='Conference Room A',
        meeting_type='regular',
        status='draft',
        chairperson=chairperson,
        note_taker=note_taker,
    )


@pytest.fixture
def scheduled_meeting(db, chairperson):
    """Create a scheduled meeting."""
    scheduled_date = timezone.now() + timedelta(days=14)
    return Meeting.objects.create(
        title='Scheduled Board Meeting',
        description='Upcoming scheduled meeting',
        scheduled_date=scheduled_date,
        duration_minutes=90,
        location='Main Hall',
        meeting_type='regular',
        status='scheduled',
        chairperson=chairperson,
        is_published=True,
    )


@pytest.fixture
def past_meeting(db, chairperson):
    """Create a past meeting."""
    scheduled_date = timezone.now() - timedelta(days=7)
    return Meeting.objects.create(
        title='Past Board Meeting',
        description='Already happened',
        scheduled_date=scheduled_date,
        duration_minutes=90,
        location='Virtual',
        meeting_type='regular',
        status='completed',
        chairperson=chairperson,
    )


# AgendaItem fixtures

@pytest.fixture
def agenda_item(db, meeting, proposer):
    """Create a basic agenda item in draft status."""
    return AgendaItem.objects.create(
        meeting=meeting,
        title='Budget Review',
        description='Review Q4 budget',
        proposer=proposer,
        item_type='internal',
        status='draft',
        estimated_duration_minutes=30,
    )


@pytest.fixture
def submitted_agenda_item(db, meeting, proposer):
    """Create a submitted agenda item."""
    item = AgendaItem.objects.create(
        meeting=meeting,
        title='Strategic Planning',
        description='Discuss strategic plan',
        proposer=proposer,
        item_type='internal',
        status='draft',
        estimated_duration_minutes=45,
    )
    item.submit()
    return item


@pytest.fixture
def approved_agenda_item(db, meeting, proposer, reviewer):
    """Create an approved agenda item."""
    item = AgendaItem.objects.create(
        meeting=meeting,
        title='Policy Update',
        description='Review and approve policy changes',
        proposer=proposer,
        item_type='decision',
        status='draft',
        estimated_duration_minutes=20,
    )
    item.submit()
    item.approve(reviewer)
    return item


@pytest.fixture
def consent_agenda_item(db, meeting, proposer):
    """Create a consent agenda item."""
    return AgendaItem.objects.create(
        meeting=meeting,
        title='Meeting Minutes Approval',
        description='Approve minutes from last meeting',
        proposer=proposer,
        item_type='consent',
        status='approved',
        estimated_duration_minutes=5,
        is_consent_item=True,
    )


# Presenter fixtures

@pytest.fixture
def presenter(db, agenda_item, user):
    """Create a presenter for an agenda item."""
    return Presenter.objects.create(
        agenda_item=agenda_item,
        user=user,
        is_primary=True,
        presentation_order=1,
    )


@pytest.fixture
def external_presenter(db, agenda_item):
    """Create an external presenter."""
    return Presenter.objects.create(
        agenda_item=agenda_item,
        name='External Expert',
        email='expert@external.com',
        affiliation='External Organization',
        is_primary=False,
        presentation_order=2,
    )


# ActionItem fixtures

@pytest.fixture
def action_item(db, meeting, user):
    """Create a basic action item."""
    return ActionItem.objects.create(
        meeting=meeting,
        title='Prepare report',
        description='Prepare quarterly report for next meeting',
        assigned_to=user,
        assigned_by=user,
        status='assigned',
        priority='medium',
        due_date=timezone.now().date() + timedelta(days=30),
    )


@pytest.fixture
def urgent_action_item(db, meeting, user):
    """Create an urgent action item."""
    return ActionItem.objects.create(
        meeting=meeting,
        title='Fix critical issue',
        description='Address urgent matter',
        assigned_to=user,
        assigned_by=user,
        status='assigned',
        priority='urgent',
        due_date=timezone.now().date() + timedelta(days=2),
    )


@pytest.fixture
def overdue_action_item(db, meeting, user):
    """Create an overdue action item."""
    return ActionItem.objects.create(
        meeting=meeting,
        title='Overdue task',
        description='This task is overdue',
        assigned_to=user,
        assigned_by=user,
        status='in_progress',
        priority='high',
        due_date=timezone.now().date() - timedelta(days=5),
    )


# Minute fixtures

@pytest.fixture
def minute(db, meeting, user):
    """Create a basic minute entry."""
    return Minute.objects.create(
        meeting=meeting,
        content='Discussion about budget allocation',
        minute_type='general',
        recorded_by=user,
        is_draft=True,
    )


@pytest.fixture
def decision_minute(db, meeting, agenda_item, user):
    """Create a decision minute with votes."""
    return Minute.objects.create(
        meeting=meeting,
        agenda_item=agenda_item,
        content='Motion to approve budget',
        minute_type='decision',
        recorded_by=user,
        is_decision=True,
        decision_text='Approved budget increase of 10%',
        vote_count_for=8,
        vote_count_against=2,
        vote_count_abstain=1,
        is_draft=True,
    )


@pytest.fixture
def approved_minute(db, meeting, user, reviewer):
    """Create an approved minute."""
    minute = Minute.objects.create(
        meeting=meeting,
        content='Approved budget allocation',
        minute_type='decision',
        recorded_by=user,
        is_draft=True,
    )
    minute.approve(reviewer)
    return minute


# AttendanceRecord fixtures

@pytest.fixture
def attendance_record(db, meeting, user):
    """Create a basic attendance record."""
    return AttendanceRecord.objects.create(
        meeting=meeting,
        user=user,
        present=True,
        attendance_type='in_person',
        role='attendee',
    )


@pytest.fixture
def virtual_attendance(db, meeting, user):
    """Create a virtual attendance record."""
    return AttendanceRecord.objects.create(
        meeting=meeting,
        user=user,
        present=True,
        attendance_type='virtual',
        role='attendee',
    )


@pytest.fixture
def absent_record(db, meeting, user):
    """Create an absence record."""
    return AttendanceRecord.objects.create(
        meeting=meeting,
        user=user,
        present=False,
        attendance_type='absent',
        role='attendee',
    )


@pytest.fixture
def late_arrival_record(db, meeting, user):
    """Create an attendance record with late arrival."""
    record = AttendanceRecord.objects.create(
        meeting=meeting,
        user=user,
        present=True,
        attendance_type='in_person',
        role='attendee',
    )
    record.record_late_arrival(timezone.now())
    return record


# ExternalRequest fixtures

@pytest.fixture
def external_request(db, meeting):
    """Create an external request for agenda item."""
    return ExternalRequest.objects.create(
        meeting=meeting,
        requester_name='John External',
        requester_email='john@external.org',
        requester_organization='External Org',
        proposed_title='Community Proposal',
        proposed_description='We propose to add this to the agenda',
        justification='This is important for the community',
        status='pending',
    )


@pytest.fixture
def approved_external_request(db, meeting, reviewer):
    """Create an approved external request."""
    request = ExternalRequest.objects.create(
        meeting=meeting,
        requester_name='Jane External',
        requester_email='jane@external.org',
        requester_organization='External Org',
        proposed_title='Important Matter',
        proposed_description='This should be discussed',
        justification='Community interest',
        status='pending',
    )
    request.approve(reviewer, create_agenda_item=True)
    return request


# Helper fixtures

@pytest.fixture
def multiple_users(db):
    """Create multiple users for testing."""
    return [
        User.objects.create_user(
            username=f'user{i}',
            email=f'user{i}@example.com',
            password='testpass123'
        )
        for i in range(5)
    ]


@pytest.fixture
def meeting_with_agenda(db, meeting, proposer, reviewer):
    """Create a meeting with multiple agenda items."""
    items = []
    for i in range(3):
        item = AgendaItem.objects.create(
            meeting=meeting,
            title=f'Agenda Item {i+1}',
            description=f'Description {i+1}',
            proposer=proposer,
            item_type='internal',
            status='draft',
            order=i,
            estimated_duration_minutes=15,
        )
        item.submit()
        item.approve(reviewer)
        items.append(item)

    meeting.agenda_items_list = items
    return meeting


@pytest.fixture
def full_meeting(db, chairperson, note_taker, proposer, reviewer, multiple_users):
    """Create a complete meeting with all related objects."""
    # Create meeting
    scheduled_date = timezone.now() + timedelta(days=7)
    meeting = Meeting.objects.create(
        title='Full Board Meeting',
        description='Complete meeting with all components',
        scheduled_date=scheduled_date,
        duration_minutes=180,
        location='Main Conference Room',
        meeting_type='regular',
        status='scheduled',
        chairperson=chairperson,
        note_taker=note_taker,
        is_published=True,
    )

    # Create agenda items
    agenda_items = []
    for i in range(3):
        item = AgendaItem.objects.create(
            meeting=meeting,
            title=f'Agenda Item {i+1}',
            description=f'Description for item {i+1}',
            proposer=proposer,
            item_type='discussion' if i % 2 == 0 else 'decision',
            status='approved',
            order=i,
            estimated_duration_minutes=30,
        )
        agenda_items.append(item)

    # Create action items
    for i in range(2):
        ActionItem.objects.create(
            meeting=meeting,
            agenda_item=agenda_items[0] if i == 0 else None,
            title=f'Action Item {i+1}',
            description=f'Action description {i+1}',
            assigned_to=multiple_users[i],
            assigned_by=chairperson,
            status='assigned',
            priority='medium',
            due_date=timezone.now().date() + timedelta(days=14),
        )

    # Create attendance records
    for user in [chairperson, note_taker, proposer] + multiple_users:
        AttendanceRecord.objects.create(
            meeting=meeting,
            user=user,
            present=True,
            attendance_type='in_person',
            role='chairperson' if user == chairperson else 'attendee',
        )

    # Create minutes
    Minute.objects.create(
        meeting=meeting,
        content='Opening remarks by chairperson',
        minute_type='general',
        recorded_by=note_taker,
        is_draft=False,
        approved=True,
        approved_by=chairperson,
    )

    return meeting
