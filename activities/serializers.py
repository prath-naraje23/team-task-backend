from rest_framework import serializers


class ActivitySerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    action = serializers.CharField()
    user = serializers.SerializerMethodField()
    task = serializers.SerializerMethodField()
    team = serializers.SerializerMethodField()
    details = serializers.DictField()
    created_at = serializers.DateTimeField()

    def get_id(self, obj):
        return str(obj.id)

    def get_user(self, obj):
        return obj.user.to_dict() if obj.user else None

    def get_task(self, obj):
        return str(obj.task.id) if obj.task else None

    def get_team(self, obj):
        return str(obj.team.id) if obj.team else None
