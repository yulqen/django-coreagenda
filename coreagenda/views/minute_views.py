"""
Views for meeting minutes management.

This module provides views for:
- Recording minutes during meetings
- Editing and reviewing minutes
- Approving and publishing minutes
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView

from ..models import Meeting, Minute
from ..services import MinuteService


@login_required
def meeting_minutes(request, meeting_pk):
    """
    Display and manage minutes for a meeting.

    TODO: Show minutes organized by agenda item
    TODO: Enable inline editing
    TODO: Add decision recording interface
    """
    meeting = get_object_or_404(Meeting, pk=meeting_pk)
    # minutes = MinuteService.get_minutes_for_meeting(meeting, include_drafts=True)
    minutes = meeting.minutes.all()

    return render(request, 'coreagenda/meeting_minutes.html', {
        'meeting': meeting,
        'minutes': minutes
    })


@login_required
def record_minute(request, meeting_pk):
    """
    Record a new minute entry.

    TODO: Implement rich text editor
    TODO: Support template insertion
    TODO: Auto-save drafts
    """
    meeting = get_object_or_404(Meeting, pk=meeting_pk)

    if request.method == 'POST':
        # content = request.POST.get('content')
        # MinuteService.record_minute(meeting, content, request.user)
        return redirect('coreagenda:meeting_minutes', meeting_pk=meeting_pk)

    return render(request, 'coreagenda/record_minute.html', {
        'meeting': meeting
    })


@login_required
def record_decision(request, meeting_pk, agenda_item_pk):
    """
    Record a decision made for an agenda item.

    TODO: Implement decision form with vote counts
    TODO: Validate voting data
    TODO: Link to related action items
    """
    meeting = get_object_or_404(Meeting, pk=meeting_pk)

    if request.method == 'POST':
        # MinuteService.record_decision(...)
        return redirect('coreagenda:meeting_minutes', meeting_pk=meeting_pk)

    return render(request, 'coreagenda/record_decision.html', {
        'meeting': meeting
    })


@login_required
def approve_minutes(request, meeting_pk):
    """
    Approve and publish minutes for a meeting.

    TODO: Review all minutes
    TODO: Allow final edits
    TODO: Generate final document
    """
    meeting = get_object_or_404(Meeting, pk=meeting_pk)

    if request.method == 'POST':
        # MinuteService.publish_minutes(meeting, request.user)
        return redirect('coreagenda:meeting_minutes', meeting_pk=meeting_pk)

    return render(request, 'coreagenda/approve_minutes.html', {
        'meeting': meeting
    })


@login_required
def export_minutes(request, meeting_pk):
    """
    Export meeting minutes in specified format.

    TODO: Implement PDF generation
    TODO: Support DOCX format
    TODO: Include all approved minutes
    """
    meeting = get_object_or_404(Meeting, pk=meeting_pk)
    format = request.GET.get('format', 'pdf')

    # TODO: Use MinuteService.export_minutes(meeting, format)

    return render(request, 'coreagenda/export_minutes.html', {
        'meeting': meeting
    })
