from django.urls import path
from .views import TaskListCreateView, TaskDetailView, TaskStatusView, CommentView

urlpatterns = [
    path('', TaskListCreateView.as_view(), name='task-list-create'),
    path('<str:task_id>/', TaskDetailView.as_view(), name='task-detail'),
    path('<str:task_id>/status/', TaskStatusView.as_view(), name='task-status'),
    path('<str:task_id>/comment/', CommentView.as_view(), name='task-comment'),
]
