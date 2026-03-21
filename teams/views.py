from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from datetime import datetime
from mongoengine.queryset.visitor import Q

from .models import Team, TeamInvitation
from .serializers import TeamCreateSerializer, TeamUpdateSerializer, InviteSerializer
from accounts.models import User
from activities.utils import log_activity


class TeamListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        teams = Team.objects.filter(Q(owner=user) | Q(members=user))
        return Response([t.to_dict() for t in teams])

    def post(self, request):
        # Requirement: Only Admins can create new teams
        if request.user.role != 'admin':
            return Response(
                {'detail': 'Only Admin users can create teams.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = TeamCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        team = Team(
            name=serializer.validated_data['name'],
            description=serializer.validated_data.get('description', ''),
            owner=request.user,
            members=[request.user],
        )
        team.save()
        log_activity(
            action='created_team',
            user=request.user,
            team=team,
            details={'team_name': team.name},
        )
        return Response(team.to_dict(), status=status.HTTP_201_CREATED)


class TeamDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_team(self, team_id, user):
        try:
            team = Team.objects.get(id=team_id)
        except (Team.DoesNotExist, Exception):
            return None, Response({'detail': 'Team not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not team.is_member(user):
            return None, Response({'detail': 'Not a member of this team.'}, status=status.HTTP_403_FORBIDDEN)

        return team, None

    def get(self, request, team_id):
        team, err = self._get_team(team_id, request.user)
        if err:
            return err
        return Response(team.to_dict())

    def put(self, request, team_id):
        team, err = self._get_team(team_id, request.user)
        if err:
            return err

        if str(team.owner.id) != str(request.user.id):
            return Response({'detail': 'Only the team owner can update the team.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = TeamUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        for field, value in serializer.validated_data.items():
            setattr(team, field, value)
        team.updated_at = datetime.utcnow()
        team.save()

        log_activity(
            action='updated_team',
            user=request.user,
            team=team,
            details={'team_name': team.name},
        )
        return Response(team.to_dict())

    def delete(self, request, team_id):
        team, err = self._get_team(team_id, request.user)
        if err:
            return err

        if str(team.owner.id) != str(request.user.id):
            return Response({'detail': 'Only the team owner can delete the team.'}, status=status.HTTP_403_FORBIDDEN)

        team.delete()
        return Response({'detail': 'Team deleted.'}, status=status.HTTP_204_NO_CONTENT)


class InviteMemberView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, team_id):
        # Requirement: Only Admins can invite members
        if request.user.role != 'admin':
            return Response(
                {'detail': 'Only Admin users can invite members.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            team = Team.objects.get(id=team_id)
        except (Team.DoesNotExist, Exception):
            return Response({'detail': 'Team not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not team.is_member(request.user):
            return Response({'detail': 'You are not a member of this team.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = InviteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']

        invitee = User.objects(email=email).first()
        if invitee and team.is_member(invitee):
            return Response({'detail': 'User is already a team member.'}, status=status.HTTP_400_BAD_REQUEST)

        for inv in team.invitations:
            if inv.email == email and inv.status == 'pending':
                return Response({'detail': 'Invitation already sent.'}, status=status.HTTP_400_BAD_REQUEST)

        token = TeamInvitation.generate_token()
        invitation = TeamInvitation(email=email, token=token)
        team.invitations.append(invitation)
        team.save()

        # In production, send this token via email instead of returning it.
        return Response({
            'detail': f'Invitation sent to {email}.',
            'invite_token': token,
        }, status=status.HTTP_200_OK)


class AcceptInviteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, token):
        user = request.user
        team = Team.objects(__raw__={
            'invitations': {'$elemMatch': {'token': token, 'status': 'pending'}}
        }).first()

        if not team:
            return Response({'detail': 'Invalid or expired invitation token.'}, status=status.HTTP_404_NOT_FOUND)

        for inv in team.invitations:
            if inv.token == token and inv.status == 'pending':
                if inv.email != user.email:
                    return Response(
                        {'detail': 'This invitation is for a different email address.'},
                        status=status.HTTP_403_FORBIDDEN,
                    )
                inv.status = 'accepted'
                break

        member_ids = [str(m.id) for m in team.members]
        if str(user.id) not in member_ids:
            team.members.append(user)

        team.updated_at = datetime.utcnow()
        team.save()

        log_activity(
            action='joined_team',
            user=user,
            team=team,
            details={'team_name': team.name},
        )
        return Response({'detail': f'You have joined {team.name}.', 'team': team.to_dict()})


class RemoveMemberView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, team_id, user_id):
        try:
            team = Team.objects.get(id=team_id)
        except (Team.DoesNotExist, Exception):
            return Response({'detail': 'Team not found.'}, status=status.HTTP_404_NOT_FOUND)

        if str(team.owner.id) != str(request.user.id):
            return Response({'detail': 'Only the team owner can remove members.'}, status=status.HTTP_403_FORBIDDEN)

        if str(team.owner.id) == user_id:
            return Response({'detail': 'Cannot remove the team owner.'}, status=status.HTTP_400_BAD_REQUEST)

        team.members = [m for m in team.members if str(m.id) != user_id]
        team.updated_at = datetime.utcnow()
        team.save()

        return Response({'detail': 'Member removed.'})


class MyInvitationsView(APIView):
    """
    GET /api/teams/my-invitations/
    Returns all pending team invitations sent to the authenticated user's email.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        teams = Team.objects(__raw__={
            'invitations': {'$elemMatch': {'email': user.email, 'status': 'pending'}}
        })

        result = []
        for team in teams:
            for inv in team.invitations:
                if inv.email == user.email and inv.status == 'pending':
                    result.append({
                        'team_id': str(team.id),
                        'team_name': team.name,
                        'team_description': team.description,
                        'invite_token': inv.token,
                        'invited_at': inv.created_at.isoformat(),
                    })

        return Response(result)