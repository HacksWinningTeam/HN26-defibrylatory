"""Serializers for core API endpoints."""

from rest_framework import serializers


class HealthCheckSerializer(serializers.Serializer):
    """Schema for the API and database healthcheck payload."""

    status = serializers.ChoiceField(choices=["ok", "degraded"])
    database = serializers.ChoiceField(choices=["ok", "error"])
    timestamp = serializers.DateTimeField()
