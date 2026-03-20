from django.urls import path, include

urlpatterns = [
    path('api/auth/', include('accounts.urls')),
    path('api/teams/', include('teams.urls')),
    path('api/tasks/', include('tasks.urls')),
    path('api/activities/', include('activities.urls')),
]
