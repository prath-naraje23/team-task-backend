from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from datetime import datetime
from mongoengine.queryset.visitor import Q

from .models import Task, Comment
from .serializers import TaskCreateSerializer, TaskUpdateSerializer, TaskStatusSerializer, CommentSerializer
from teams.models import Team
from accounts.models import User
from activities.utils import log_activity


def _get_task_for_user(task_id, user):
    try:
        task = Task.objects.get(id=task_id)
    except (Task.DoesNotExist, Exception):
        return None, Response({'detail': 'Task not found.'}, status=status.HTTP_404_NOT_FOUND)

    if not task.team.is_member(user):
        return None, Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    return task, None


class TaskListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # Accept both ?team=<id> and ?team_id=<id> for convenience
        team_id = request.query_params.get('team') or request.query_params.get('team_id')
        task_status = request.query_params.get('status')
        priority = request.query_params.get('priority')
        assigned_to_me = request.query_params.get('assigned_to_me')

        user_teams = list(Team.objects.filter(Q(owner=user) | Q(members=user)).scalar('id'))
        filters = {'team__in': user_teams}

        if team_id:
            filters['team'] = team_id
        if task_status:
            # Case-insensitive: accept "Done", "done", "In_Progress", etc.
            filters['status'] = task_status.lower()
        if priority:
            filters['priority'] = priority.lower()
        if assigned_to_me == 'true':
            filters['assigned_to'] = user.id

        tasks = Task.objects.filter(**filters)
        return Response([t.to_dict() for t in tasks])

    def post(self, request):
        serializer = TaskCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            team = Team.objects.get(id=data['team_id'])
        except (Team.DoesNotExist, Exception):
            return Response({'detail': 'Team not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not team.is_member(request.user):
            return Response({'detail': 'You are not a member of this team.'}, status=status.HTTP_403_FORBIDDEN)

        assigned_to = None
        if data.get('assigned_to_id'):
            assigned_to = User.objects(id=data['assigned_to_id']).first()
            if not assigned_to:
                return Response({'detail': 'Assigned user not found.'}, status=status.HTTP_404_NOT_FOUND)

        task = Task(
            title=data['title'],
            description=data.get('description', ''),
            priority=data.get('priority', 'medium'),
            team=team,
            created_by=request.user,
            assigned_to=assigned_to,
            due_date=data.get('due_date'),
        )
        task.save()

        log_activity(
            action='created_task',
            user=request.user,
            task=task,
            team=team,
            details={'task_title': task.title},
        )
        return Response(task.to_dict(), status=status.HTTP_201_CREATED)


class TaskDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        task, err = _get_task_for_user(task_id, request.user)
        if err:
            return err
        return Response(task.to_dict())

    def put(self, request, task_id):
        task, err = _get_task_for_user(task_id, request.user)
        if err:
            return err

        serializer = TaskUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        if 'assigned_to_id' in data:
            if data['assigned_to_id']:
                assigned_user = User.objects(id=data['assigned_to_id']).first()
                if not assigned_user:
                    return Response({'detail': 'Assigned user not found.'}, status=status.HTTP_404_NOT_FOUND)
                task.assigned_to = assigned_user
            else:
                task.assigned_to = None

        old_status = task.status
        for field in ('title', 'description', 'priority', 'due_date', 'status'):
            if field in data:
                setattr(task, field, data[field])

        task.updated_at = datetime.utcnow()
        task.save()

        action = 'updated_task'
        details = {'task_title': task.title}
        if 'status' in data and data['status'] != old_status:
            action = 'changed_task_status'
            details.update({'from_status': old_status, 'to_status': task.status})

        log_activity(action=action, user=request.user, task=task, team=task.team, details=details)
        return Response(task.to_dict())

    def patch(self, request, task_id):
        """Shortcut: PATCH /api/tasks/<id>/ with {"status": "done"} to update status."""
        return self.put(request, task_id)

    def delete(self, request, task_id):
        task, err = _get_task_for_user(task_id, request.user)
        if err:
            return err

        task.delete()
        return Response({'detail': 'Task deleted.'}, status=status.HTTP_204_NO_CONTENT)


class TaskStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, task_id):
        task, err = _get_task_for_user(task_id, request.user)
        if err:
            return err

        serializer = TaskStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        old_status = task.status
        task.status = serializer.validated_data['status']
        task.updated_at = datetime.utcnow()
        task.save()

        log_activity(
            action='changed_task_status',
            user=request.user,
            task=task,
            team=task.team,
            details={
                'task_title': task.title,
                'from_status': old_status,
                'to_status': task.status,
            },
        )
        return Response(task.to_dict())


class CommentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        task, err = _get_task_for_user(task_id, request.user)
        if err:
            return err

        serializer = CommentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        comment = Comment(
            text=serializer.validated_data['text'],
            author=request.user,
        )
        task.comments.append(comment)
        task.updated_at = datetime.utcnow()
        task.save()

        log_activity(
            action='added_comment',
            user=request.user,
            task=task,
            team=task.team,
            details={'task_title': task.title},
        )
        return Response(comment.to_dict(), status=status.HTTP_201_CREATED)