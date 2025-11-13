"""
Service layer for django-coreagenda.

This module provides business logic services for:
- Meeting management
- Agenda item workflow
- Minute recording
- Action item tracking
- Attendance management
"""

from .meeting_service import MeetingService
from .agenda_service import AgendaService
from .minute_service import MinuteService
from .action_service import ActionService
from .attendance_service import AttendanceService

__all__ = [
    'MeetingService',
    'AgendaService',
    'MinuteService',
    'ActionService',
    'AttendanceService',
]
