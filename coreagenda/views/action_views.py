"""
Views for action item management.

This module provides views for:
- Listing action items
- Action item detail
- Creating/assigning actions
- Action item workflow (start, complete, reject)
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from ..models import ActionItem
from ..services import ActionService


class ActionItemListView(ListView):
    """
    Display list of action items.

    TODO: Filter by status, assigned user, meeting
    TODO: Show overdue items prominently
    TODO: Add search and sorting
    """
    model = ActionItem
    template_name = 'coreagenda/action_item_list.html'
    context_object_name = 'action_items'
    paginate_by = 20


class ActionItemDetailView(DetailView):
    """
    Display detailed information about an action item.

    TODO: Show related agenda item and meeting
    TODO: Display completion history
    TODO: Add comment/update functionality
    """
    model = ActionItem
    template_name = 'coreagenda/action_item_detail.html'
    context_object_name = 'action_item'


@login_required
def my_actions(request):
    """
    Display action items assigned to current user.

    TODO: Group by status
    TODO: Highlight overdue items
    TODO: Add quick action buttons
    """
    # actions = ActionService.get_actions_for_user(request.user)
    actions = ActionItem.objects.filter(assigned_to=request.user)

    return render(request, 'coreagenda/my_actions.html', {
        'action_items': actions
    })


@login_required
def action_start(request, pk):
    """
    Start work on an action item.

    TODO: Check user is assigned
    TODO: Update status to in_progress
    TODO: Send notification
    """
    action = get_object_or_404(ActionItem, pk=pk)

    if request.method == 'POST':
        # ActionService.start_action(action, request.user)
        return redirect('coreagenda:action_detail', pk=pk)

    return render(request, 'coreagenda/action_start_confirm.html', {
        'action': action
    })


@login_required
def action_complete(request, pk):
    """
    Mark an action as completed.

    TODO: Capture completion notes
    TODO: Verify work is complete
    TODO: Send completion notification
    """
    action = get_object_or_404(ActionItem, pk=pk)

    if request.method == 'POST':
        # notes = request.POST.get('notes', '')
        # ActionService.complete_action(action, request.user, notes)
        return redirect('coreagenda:action_detail', pk=pk)

    return render(request, 'coreagenda/action_complete.html', {
        'action': action
    })


@login_required
def overdue_actions(request):
    """
    Display all overdue action items.

    TODO: Filter by user or show all
    TODO: Add escalation functionality
    TODO: Send reminders
    """
    # actions = ActionService.get_overdue_actions(request.user)
    actions = ActionItem.objects.filter(assigned_to=request.user)

    return render(request, 'coreagenda/overdue_actions.html', {
        'action_items': actions
    })
