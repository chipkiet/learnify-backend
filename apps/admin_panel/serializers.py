from rest_framework import serializers


class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=1)


class AdminUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    full_name = serializers.CharField()
    is_staff = serializers.BooleanField()
    is_superuser = serializers.BooleanField()


class AdminStatsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    total_documents = serializers.IntegerField()
    total_flashcard_sets = serializers.IntegerField()
    total_flashcards = serializers.IntegerField()
    new_users_today = serializers.IntegerField()
    new_users_this_week = serializers.IntegerField()
