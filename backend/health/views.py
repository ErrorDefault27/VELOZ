from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    """Expose a minimal readiness signal for clients and development tooling."""

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response({"status": "ok", "service": "controle-estoque-api"})

