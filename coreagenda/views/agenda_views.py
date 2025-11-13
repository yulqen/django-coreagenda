"""
Views for agenda item management.

This module provides views for:
- Listing agenda items
- Agenda item detail
- Creating/editing agenda items
- Agenda item workflow (submit, approve, defer, withdraw)
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from ..models import Meeting, AgendaItem
from ..services import AgendaService


class AgendaItemListView(ListView):
    """
    Display list of agenda items.

    TODO: Implement filtering by meeting, status, proposer
    TODO: Add search functionality
    TODO: Group by meeting or status
    """
    model = AgendaItem
    template_name = 'coreagenda/agenda_item_list.html'
    context_object_name = 'agenda_items'
    paginate_by = 20

    def get_queryset(self):
        """
        TODO: Filter based on user permissions and query parameters.
        """
        queryset = AgendaItem.objects.all()

        # Filter by meeting if provided
        meeting_id = self.request.GET.get('meeting')
        if meeting_id:
            queryset = queryset.filter(meeting_id=meeting_id)

        # Filter by status if provided
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset


class AgendaItemDetailView(DetailView):
    """
    Display detailed information about an agenda item.

    TODO: Include presenters, action items, minutes
    TODO: Show workflow history
    TODO: Add discussion thread
    """
    model = AgendaItem
    template_name = 'coreagenda/agenda_item_detail.html'
    context_object_name = 'agenda_item'

    def get_context_data(self, **kwargs):
        """
        TODO: Add presenters, action items, minutes to context.
        """
        context = super().get_context_data(**kwargs)
        # context['presenters'] = self.object.presenters.all()
        # context['action_items'] = self.object.action_items.all()
        return context


class AgendaItemCreateView(CreateView):
    """
    Create a new agenda item.

    TODO: Implement form with presenter selection
    TODO: Add file attachments
    TODO: Validate against meeting constraints
    """
    model = AgendaItem
    template_name = 'coreagenda/agenda_item_form.html'
    fields = ['meeting', 'title', 'description', 'item_type',
              'estimated_duration_minutes', 'background_info', 'attachments_url']

    def form_valid(self, form):
        """
        TODO: Use AgendaService to create item.
        TODO: Auto-set proposer to current user.
        """
        form.instance.proposer = self.request.user
        return super().form_valid(form)


class AgendaItemUpdateView(UpdateView):
    """
    Update an existing agenda item.

    TODO: Implement permission checks
    TODO: Restrict editing based on status
    TODO: Track changes
    """
    model = AgendaItem
    template_name = 'coreagenda/agenda_item_form.html'
    fields = ['title', 'description', 'item_type',
              'estimated_duration_minutes', 'background_info', 'attachments_url']

    def form_valid(self, form):
        """
        TODO: Validate user can edit this item.
        TODO: Check item status allows editing.
        """
        return super().form_valid(form)


# Workflow actions

@login_required
def agenda_item_submit(request, pk):
    """
    Submit an agenda item for review.

    TODO: Validate item is in draft status
    TODO: Check all required fields are complete
    TODO: Send notification to reviewers
    """
    agenda_item = get_object_or_404(AgendaItem, pk=pk)

    if request.method == 'POST':
        # agenda_item.submit(request.user)
        # messages.success(request, 'Agenda item submitted for review')
        return redirect('coreagenda:agenda_item_detail', pk=pk)

    return render(request, 'coreagenda/agenda_item_submit_confirm.html', {
        'agenda_item': agenda_item
    })


@login_required
def agenda_item_review(request, pk):
    """
    Review and approve/defer/reject an agenda item.

    TODO: Implement permission checks (only reviewers)
    TODO: Add review form with notes
    TODO: Send notification to proposer
    """
    agenda_item = get_object_or_404(AgendaItem, pk=pk)

    if request.method == 'POST':
        decision = request.POST.get('decision')  # 'approve', 'defer', 'reject'
        notes = request.POST.get('notes', '')

        # AgendaService.review_agenda_item(agenda_item, request.user, decision, notes)
        # messages.success(request, f'Agenda item {decision}d')
        return redirect('coreagenda:agenda_item_detail', pk=pk)

    return render(request, 'coreagenda/agenda_item_review.html', {
        'agenda_item': agenda_item
    })


@login_required
def agenda_item_approve(request, pk):
    """
    Approve an agenda item.

    TODO: Check user has permission
    TODO: Validate item is in correct status
    TODO: Send notification
    """
    agenda_item = get_object_or_404(AgendaItem, pk=pk)

    if request.method == 'POST':
        # agenda_item.approve(request.user)
        # messages.success(request, 'Agenda item approved')
        return redirect('coreagenda:agenda_item_detail', pk=pk)

    return render(request, 'coreagenda/agenda_item_approve_confirm.html', {
        'agenda_item': agenda_item
    })


@login_required
def agenda_item_defer(request, pk):
    """
    Defer an agenda item to a future meeting.

    TODO: Allow selection of future meeting
    TODO: Capture reason for deferral
    TODO: Send notification
    """
    agenda_item = get_object_or_404(AgendaItem, pk=pk)

    if request.method == 'POST':
        # agenda_item.defer(request.user)
        # messages.success(request, 'Agenda item deferred')
        return redirect('coreagenda:agenda_item_detail', pk=pk)

    return render(request, 'coreagenda/agenda_item_defer.html', {
        'agenda_item': agenda_item
    })


@login_required
def agenda_item_withdraw(request, pk):
    """
    Withdraw an agenda item.

    TODO: Check user is proposer or has permission
    TODO: Capture reason for withdrawal
    TODO: Send notification
    """
    agenda_item = get_object_or_404(AgendaItem, pk=pk)

    if request.method == 'POST':
        # agenda_item.withdraw(request.user)
        # messages.success(request, 'Agenda item withdrawn')
        return redirect('coreagenda:agenda_item_detail', pk=pk)

    return render(request, 'coreagenda/agenda_item_withdraw_confirm.html', {
        'agenda_item': agenda_item
    })


@login_required
def organize_agenda(request, meeting_pk):
    """
    Organize the order of agenda items for a meeting.

    TODO: Implement drag-and-drop interface
    TODO: Save order via AJAX
    TODO: Update order field
    """
    meeting = get_object_or_404(Meeting, pk=meeting_pk)

    if request.method == 'POST':
        # item_order = request.POST.getlist('item_order')
        # AgendaService.organize_agenda(meeting, item_order, request.user)
        # messages.success(request, 'Agenda organized')
        return redirect('coreagenda:meeting_detail', pk=meeting_pk)

    agenda_items = meeting.agenda_items.filter(status='approved').order_by('order')

    return render(request, 'coreagenda/organize_agenda.html', {
        'meeting': meeting,
        'agenda_items': agenda_items
    })


@login_required
def bundle_consent_agenda(request, meeting_pk):
    """
    Bundle multiple items into consent agenda.

    TODO: Display list of eligible items
    TODO: Allow multi-select
    TODO: Update is_consent_item flag
    """
    meeting = get_object_or_404(Meeting, pk=meeting_pk)

    if request.method == 'POST':
        # item_ids = request.POST.getlist('item_ids')
        # AgendaService.bundle_consent_agenda(meeting, item_ids, request.user)
        # messages.success(request, 'Consent agenda bundled')
        return redirect('coreagenda:meeting_detail', pk=meeting_pk)

    agenda_items = meeting.agenda_items.filter(status='approved', is_consent_item=False)

    return render(request, 'coreagenda/bundle_consent_agenda.html', {
        'meeting': meeting,
        'agenda_items': agenda_items
    })


@login_required
def add_presenter(request, agenda_item_pk):
    """
    Add a presenter to an agenda item.

    TODO: Implement form for presenter selection
    TODO: Support both internal users and external presenters
    TODO: Send notification to presenter
    """
    agenda_item = get_object_or_404(AgendaItem, pk=agenda_item_pk)

    if request.method == 'POST':
        # TODO: Process form and create presenter
        # AgendaService.add_presenter(...)
        return redirect('coreagenda:agenda_item_detail', pk=agenda_item_pk)

    return render(request, 'coreagenda/add_presenter.html', {
        'agenda_item': agenda_item
    })
