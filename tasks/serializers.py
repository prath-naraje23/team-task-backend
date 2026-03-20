from rest_framework import serializers

VALID_STATUSES = ['pending', 'in_progress', 'done']


class TaskCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    priority = serializers.ChoiceField(choices=['low', 'medium', 'high'], default='medium')
    team_id = serializers.CharField()
    assigned_to_id = serializers.CharField(required=False, allow_null=True)
    due_date = serializers.DateTimeField(required=False, allow_null=True)


class TaskUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200, required=False)
    description = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    priority = serializers.ChoiceField(choices=['low', 'medium', 'high'], required=False)
    status = serializers.ChoiceField(choices=VALID_STATUSES, required=False)
    assigned_to_id = serializers.CharField(required=False, allow_null=True)
    due_date = serializers.DateTimeField(required=False, allow_null=True)

    def validate_status(self, value):
        return value.lower()


class TaskStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=VALID_STATUSES)

    def validate_status(self, value):
        return value.lower()


class CommentSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=1000)
