from rest_framework import serializers
from .models import User


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=50)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6, write_only=True)
    role = serializers.ChoiceField(choices=['admin', 'member'], default='member')

    def validate_username(self, value):
        if User.objects(username=value).first():
            raise serializers.ValidationError('Username already taken.')
        return value

    def validate_email(self, value):
        if User.objects(email=value).first():
            raise serializers.ValidationError('Email already registered.')
        return value

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            role=validated_data.get('role', 'member'),
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    username = serializers.CharField()
    email = serializers.EmailField()
    role = serializers.CharField()
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField()

    def get_id(self, obj):
        return str(obj.id)


class UpdateProfileSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=50, required=False)
    password = serializers.CharField(min_length=6, write_only=True, required=False)

    def validate_username(self, value):
        user = self.context['request'].user
        if User.objects(username=value).exclude(id=user.id).first():
            raise serializers.ValidationError('Username already taken.')
        return value

    def update(self, instance, validated_data):
        if 'username' in validated_data:
            instance.username = validated_data['username']
        if 'password' in validated_data:
            instance.set_password(validated_data['password'])
        instance.save()
        return instance
