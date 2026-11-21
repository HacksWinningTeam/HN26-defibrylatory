"""API views for core application."""

from django.db import DatabaseError, connection
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.serializers import HealthCheckSerializer


class HealthCheckView(APIView):
    """Report application and database readiness."""

    authentication_classes = []
    permission_classes = []

    @extend_schema(
        tags=["Health"],
        summary="Check API and database health",
        responses={
            200: HealthCheckSerializer,
            503: HealthCheckSerializer,
        },
    )
    def get(self, request: Request) -> Response:
        """Verify database connectivity and return service health status."""
        db_ok = True
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except DatabaseError:
            db_ok = False

        payload = {
            "status": "ok" if db_ok else "degraded",
            "database": "ok" if db_ok else "error",
            "timestamp": timezone.now(),
        }
        serializer = HealthCheckSerializer(payload)
        http_status = status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response(serializer.data, status=http_status)
