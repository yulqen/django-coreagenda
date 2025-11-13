"""
Service layer for action item management operations.

This module encapsulates business logic for creating, assigning,
and tracking action items arising from meetings.
"""
from typing import Optional, List
from datetime import date
from django.contrib.auth import get_user_model
from django.db.models import Q

from ..models import Meeting, AgendaItem, ActionItem

User = get_user_model()


class ActionService:
    """
    Service class for action item operations.

    Encapsulates business logic for:
    - Creating action items
    - Assigning actions to users
    - Tracking action completion
    - Managing action workflow
    """

    @staticmethod
    def create_action(
        meeting: Meeting,
        title: str,
        description: str,
        assigned_by: User,
        agenda_item: Optional[AgendaItem] = None,
        assigned_to: Optional[User] = None,
        due_date: Optional[date] = None,
        priority: str = 'medium',
        **kwargs
    ) -> ActionItem:
        """
        Create a new action item from a meeting.

        Args:
            meeting: The meeting where action was identified
            title: Action title
            description: Detailed description
            assigned_by: User creating the action
            agenda_item: Related agenda item (optional)
            assigned_to: User to assign to (optional)
            due_date: Deadline for completion
            priority: Priority level
            **kwargs: Additional action attributes

        Returns:
            ActionItem: The created action item

        Raises:
            ValueError: If validation fails
        """
        # TODO: Implement validation
        # - Check assigned_by has permission
        # - If agenda_item provided, ensure it belongs to meeting
        # - Validate due_date is in the future
        # - Validate priority is valid

        action = ActionItem.objects.create(
            meeting=meeting,
            title=title,
            description=description,
            assigned_by=assigned_by,
            agenda_item=agenda_item,
            assigned_to=assigned_to,
            due_date=due_date,
            priority=priority,
            status='proposed' if not assigned_to else 'assigned',
            **kwargs
        )

        # TODO: Send notification to assigned_to
        # TODO: Create calendar reminder
        # TODO: Link to related documents

        return action

    @staticmethod
    def assign_action(
        action: ActionItem,
        assigned_to: User,
        assigned_by: User,
        due_date: Optional[date] = None
    ) -> ActionItem:
        """
        Assign an action item to a user.

        Args:
            action: The action to assign
            assigned_to: User to assign to
            assigned_by: User performing the assignment
            due_date: Deadline (optional, updates existing)

        Returns:
            ActionItem: The assigned action

        Raises:
            ValueError: If validation fails
        """
        # TODO: Implement validation
        # - Check assigned_by has permission
        # - Validate assigned_to exists
        # - Check action can be assigned

        action.assign(assigned_to, assigned_by)

        if due_date:
            action.due_date = due_date
            action.save()

        # TODO: Send notification to assigned_to
        # TODO: Create calendar entry
        # TODO: Log assignment action

        return action

    @staticmethod
    def start_action(action: ActionItem, user: User) -> ActionItem:
        """
        Mark an action as in progress.

        Args:
            action: The action to start
            user: User starting the action

        Returns:
            ActionItem: The updated action

        Raises:
            ValueError: If validation fails
        """
        # TODO: Implement validation
        # - Check user is assigned to the action
        # - Validate action can be started

        action.start()

        # TODO: Log start time
        # TODO: Send notification to assigned_by

        return action

    @staticmethod
    def complete_action(
        action: ActionItem,
        user: User,
        completion_notes: str = ''
    ) -> ActionItem:
        """
        Mark an action as completed.

        Args:
            action: The action to complete
            user: User completing the action
            completion_notes: Notes about completion

        Returns:
            ActionItem: The completed action

        Raises:
            ValueError: If validation fails
        """
        # TODO: Implement validation
        # - Check user is assigned to the action or has permission
        # - Validate action can be completed

        action.complete(completion_notes)

        # TODO: Send notification to assigned_by and stakeholders
        # TODO: Update related agenda item status if applicable
        # TODO: Archive completed action

        return action

    @staticmethod
    def reject_action(
        action: ActionItem,
        user: User,
        rejection_notes: str = ''
    ) -> ActionItem:
        """
        Reject an action item.

        Args:
            action: The action to reject
            user: User rejecting the action
            rejection_notes: Reason for rejection

        Returns:
            ActionItem: The rejected action

        Raises:
            ValueError: If validation fails
        """
        # TODO: Implement validation
        # - Check user has permission to reject
        # - Validate action can be rejected

        action.reject(rejection_notes)

        # TODO: Send notification to assigned_by
        # TODO: Log rejection

        return action

    @staticmethod
    def update_action_status(
        action: ActionItem,
        user: User,
        new_status: str,
        notes: str = ''
    ) -> ActionItem:
        """
        Update the status of an action item.

        Args:
            action: The action to update
            user: User performing the update
            new_status: New status
            notes: Update notes

        Returns:
            ActionItem: The updated action

        Raises:
            ValueError: If validation fails or transition is invalid
        """
        # TODO: Implement status transition validation
        # - Check user has permission
        # - Validate status transition is valid

        if new_status == 'in_progress':
            return ActionService.start_action(action, user)
        elif new_status == 'done':
            return ActionService.complete_action(action, user, notes)
        elif new_status == 'rejected':
            return ActionService.reject_action(action, user, notes)
        else:
            raise ValueError(f"Invalid status transition: {new_status}")

    @staticmethod
    def get_actions_for_user(
        user: User,
        status_filter: Optional[str] = None,
        include_overdue: bool = False
    ):
        """
        Get action items assigned to a user.

        Args:
            user: The user
            status_filter: Optional status to filter by
            include_overdue: If True, return only overdue items

        Returns:
            QuerySet: Action items
        """
        actions = ActionItem.objects.filter(assigned_to=user)

        if status_filter:
            actions = actions.filter(status=status_filter)

        if include_overdue:
            from django.utils import timezone
            actions = actions.filter(
                due_date__lt=timezone.now().date(),
                status__in=['assigned', 'in_progress']
            )

        return actions

    @staticmethod
    def get_actions_for_meeting(
        meeting: Meeting,
        status_filter: Optional[str] = None,
        agenda_item: Optional[AgendaItem] = None
    ):
        """
        Get action items for a meeting.

        Args:
            meeting: The meeting
            status_filter: Optional status to filter by
            agenda_item: Filter by specific agenda item

        Returns:
            QuerySet: Action items
        """
        actions = meeting.action_items.all()

        if status_filter:
            actions = actions.filter(status=status_filter)

        if agenda_item:
            actions = actions.filter(agenda_item=agenda_item)

        return actions

    @staticmethod
    def get_overdue_actions(user: Optional[User] = None):
        """
        Get all overdue action items.

        Args:
            user: Optional user to filter by

        Returns:
            QuerySet: Overdue action items
        """
        from django.utils import timezone

        actions = ActionItem.objects.filter(
            due_date__lt=timezone.now().date(),
            status__in=['assigned', 'in_progress']
        )

        if user:
            actions = actions.filter(assigned_to=user)

        return actions
