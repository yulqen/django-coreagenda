"""
Service layer for attendance tracking operations.

This module encapsulates business logic for recording and managing
meeting attendance.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from django.contrib.auth import get_user_model

from ..models import Meeting, AttendanceRecord

User = get_user_model()


class AttendanceService:
    """
    Service class for attendance-related operations.

    Encapsulates business logic for:
    - Recording attendance
    - Marking present/absent
    - Tracking late arrivals and early departures
    - Generating attendance reports
    """

    @staticmethod
    def mark_attendance(
        meeting: Meeting,
        user: User,
        present: bool = True,
        attendance_type: str = 'in_person',
        role: str = 'attendee',
        recorded_by: Optional[User] = None,
        notes: str = ''
    ) -> AttendanceRecord:
        """
        Mark attendance for a user at a meeting.

        Args:
            meeting: The meeting
            user: User whose attendance is being marked
            present: Whether user is present
            attendance_type: How they attended
            role: Their role in the meeting
            recorded_by: User recording the attendance
            notes: Additional notes

        Returns:
            AttendanceRecord: The attendance record

        Raises:
            ValueError: If validation fails
        """
        # TODO: Implement validation
        # - Check meeting exists and is active
        # - Validate attendance_type and role choices
        # - Check for duplicate records

        record, created = AttendanceRecord.objects.update_or_create(
            meeting=meeting,
            user=user,
            defaults={
                'present': present,
                'attendance_type': attendance_type,
                'role': role,
                'recorded_by': recorded_by,
                'notes': notes,
            }
        )

        # TODO: Send confirmation to user
        # TODO: Update meeting quorum status
        # TODO: Log attendance change

        return record

    @staticmethod
    def mark_present(
        meeting: Meeting,
        user: User,
        attendance_type: str = 'in_person',
        role: str = 'attendee',
        recorded_by: Optional[User] = None
    ) -> AttendanceRecord:
        """
        Mark a user as present at a meeting.

        Args:
            meeting: The meeting
            user: User to mark as present
            attendance_type: How they attended
            role: Their role
            recorded_by: User recording attendance

        Returns:
            AttendanceRecord: The attendance record
        """
        record = AttendanceService.mark_attendance(
            meeting=meeting,
            user=user,
            present=True,
            attendance_type=attendance_type,
            role=role,
            recorded_by=recorded_by
        )

        # TODO: Send check-in confirmation
        # TODO: Provide meeting materials

        return record

    @staticmethod
    def mark_absent(
        meeting: Meeting,
        user: User,
        is_excused: bool = False,
        recorded_by: Optional[User] = None,
        notes: str = ''
    ) -> AttendanceRecord:
        """
        Mark a user as absent from a meeting.

        Args:
            meeting: The meeting
            user: User to mark as absent
            is_excused: Whether the absence is excused
            recorded_by: User recording attendance
            notes: Reason for absence

        Returns:
            AttendanceRecord: The attendance record
        """
        attendance_type = 'excused' if is_excused else 'absent'

        record = AttendanceService.mark_attendance(
            meeting=meeting,
            user=user,
            present=False,
            attendance_type=attendance_type,
            recorded_by=recorded_by,
            notes=notes
        )

        # TODO: Send absence notification
        # TODO: Share meeting summary later

        return record

    @staticmethod
    def record_late_arrival(
        meeting: Meeting,
        user: User,
        arrival_time: Optional[datetime] = None,
        recorded_by: Optional[User] = None
    ) -> AttendanceRecord:
        """
        Record that a user arrived late to a meeting.

        Args:
            meeting: The meeting
            user: User who arrived late
            arrival_time: Time of arrival (defaults to now)
            recorded_by: User recording this information

        Returns:
            AttendanceRecord: The updated attendance record

        Raises:
            ValueError: If attendance record doesn't exist
        """
        # TODO: Implement validation
        # - Ensure attendance record exists
        # - Validate arrival time is reasonable

        try:
            record = AttendanceRecord.objects.get(meeting=meeting, user=user)
            record.record_late_arrival(arrival_time)

            # TODO: Update meeting minutes with late arrival
            # TODO: Log the late arrival

            return record
        except AttendanceRecord.DoesNotExist:
            # Create a new record if it doesn't exist
            record = AttendanceService.mark_present(
                meeting=meeting,
                user=user,
                recorded_by=recorded_by
            )
            record.record_late_arrival(arrival_time)
            return record

    @staticmethod
    def record_early_departure(
        meeting: Meeting,
        user: User,
        departure_time: Optional[datetime] = None,
        recorded_by: Optional[User] = None
    ) -> AttendanceRecord:
        """
        Record that a user left a meeting early.

        Args:
            meeting: The meeting
            user: User who left early
            departure_time: Time of departure (defaults to now)
            recorded_by: User recording this information

        Returns:
            AttendanceRecord: The updated attendance record

        Raises:
            ValueError: If attendance record doesn't exist
        """
        # TODO: Implement validation
        # - Ensure attendance record exists
        # - Validate departure time is reasonable

        try:
            record = AttendanceRecord.objects.get(meeting=meeting, user=user)
            record.record_early_departure(departure_time)

            # TODO: Update meeting minutes with early departure
            # TODO: Log the early departure

            return record
        except AttendanceRecord.DoesNotExist:
            raise ValueError(f"No attendance record found for {user} at {meeting}")

    @staticmethod
    def bulk_mark_attendance(
        meeting: Meeting,
        attendance_data: List[Dict[str, Any]],
        recorded_by: Optional[User] = None
    ) -> List[AttendanceRecord]:
        """
        Mark attendance for multiple users at once.

        Args:
            meeting: The meeting
            attendance_data: List of dicts with user and attendance info
            recorded_by: User recording attendance

        Returns:
            List[AttendanceRecord]: Created/updated attendance records

        Example attendance_data:
            [
                {'user': user1, 'present': True, 'attendance_type': 'in_person'},
                {'user': user2, 'present': False, 'attendance_type': 'absent'},
            ]
        """
        # TODO: Implement validation
        # - Validate all users exist
        # - Check for duplicate entries

        records = []
        for data in attendance_data:
            record = AttendanceService.mark_attendance(
                meeting=meeting,
                recorded_by=recorded_by,
                **data
            )
            records.append(record)

        # TODO: Generate attendance report
        # TODO: Send summary notifications

        return records

    @staticmethod
    def get_attendance_for_meeting(meeting: Meeting, present_only: bool = False):
        """
        Get attendance records for a meeting.

        Args:
            meeting: The meeting
            present_only: If True, return only present attendees

        Returns:
            QuerySet: Attendance records
        """
        records = meeting.attendance_records.all()

        if present_only:
            records = records.filter(present=True)

        return records

    @staticmethod
    def get_attendance_summary(meeting: Meeting) -> Dict[str, Any]:
        """
        Get a summary of attendance for a meeting.

        Args:
            meeting: The meeting

        Returns:
            Dict with attendance statistics
        """
        records = meeting.attendance_records.all()

        total = records.count()
        present = records.filter(present=True).count()
        absent = total - present
        late = records.filter(arrived_late=True).count()
        left_early = records.filter(left_early=True).count()

        by_type = {}
        for record in records.filter(present=True):
            by_type[record.attendance_type] = by_type.get(record.attendance_type, 0) + 1

        return {
            'total_invited': total,
            'present': present,
            'absent': absent,
            'late_arrivals': late,
            'early_departures': left_early,
            'by_attendance_type': by_type,
            'attendance_rate': (present / total * 100) if total > 0 else 0,
        }

    @staticmethod
    def get_user_attendance_history(user: User, limit: Optional[int] = None):
        """
        Get attendance history for a user across all meetings.

        Args:
            user: The user
            limit: Maximum number of records to return

        Returns:
            QuerySet: Attendance records
        """
        records = AttendanceRecord.objects.filter(user=user).order_by('-meeting__scheduled_date')

        if limit:
            records = records[:limit]

        return records
