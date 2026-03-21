from django.urls import path
from .views import (
    TeamListCreateView,
    TeamDetailView,
    InviteMemberView,
    AcceptInviteView,
    RemoveMemberView,
    MyInvitationsView
)

urlpatterns = [
    path('', TeamListCreateView.as_view(), name='team-list-create'),
    path('my-invitations/', MyInvitationsView.as_view(), name='my-invitations'),
    path('<str:team_id>/', TeamDetailView.as_view(), name='team-detail'),
    path('<str:team_id>/invite/', InviteMemberView.as_view(), name='team-invite'),
    path('<str:team_id>/members/<str:user_id>/', RemoveMemberView.as_view(), name='team-remove-member'),
    path('accept-invite/<str:token>/', AcceptInviteView.as_view(), name='accept-invite'),
]
