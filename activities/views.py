from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Activity
from teams.models import Team


class ActivityListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # Accept both ?team=<id> and ?team_id=<id>
        team_id = request.query_params.get('team') or request.query_params.get('team_id')
        # Accept both ?task=<id> and ?task_id=<id>
        task_id = request.query_params.get('task') or request.query_params.get('task_id')
        limit = int(request.query_params.get('limit', 50))

        user_teams = Team.objects.filter(
            __raw__={'$or': [{'owner': user.id}, {'members': user.id}]}
        ).values_list('id')

        filters = {'team__in': list(user_teams)}

        if team_id:
            filters['team'] = team_id
        if task_id:
            filters['task'] = task_id

        activities = Activity.objects.filter(**filters).limit(limit)
        return Response([a.to_dict() for a in activities])
