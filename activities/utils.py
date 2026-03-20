def _build_message(action, username, details):
    """
    Build a human-readable activity sentence.
    Matches requirement format:
      'Saumyakanta changed status of "Design API endpoints" to In Progress.'
    """
    task_title = details.get('task_title', '')
    team_name = details.get('team_name', '')
    to_status = details.get('to_status', '').replace('_', ' ').title()

    templates = {
        'created_task':        f'{username} created task "{task_title}".',
        'updated_task':        f'{username} updated task "{task_title}".',
        'changed_task_status': f'{username} changed status of "{task_title}" to {to_status}.',
        'added_comment':       f'{username} commented on "{task_title}".',
        'created_team':        f'{username} created team "{team_name}".',
        'updated_team':        f'{username} updated team "{team_name}".',
        'joined_team':         f'{username} joined team "{team_name}".',
    }
    return templates.get(action, f'{username} performed {action.replace("_", " ")}.')


def log_activity(action, user, task=None, team=None, details=None):
    from .models import Activity
    details = details or {}
    message = _build_message(action, user.username, details)
    Activity(
        action=action,
        message=message,
        user=user,
        task=task,
        team=team,
        details=details,
    ).save()
