from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.access.permissions import HasRBACPermissions
from apps.identity.services import success_response
from apps.wanted.models import Wanted
from apps.wanted.serializers import WantedSerializer


class WantedListAPIView(APIView):
    """List wanted persons (optionally filter by status=wanted or most_wanted)."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    permission_codes_by_method = {"GET": ["wanted.view"]}

    def get(self, request):
        queryset = Wanted.objects.select_related("case", "participant").order_by("-marked_at")
        status_filter = request.query_params.get("status")
        if status_filter in ("wanted", "most_wanted"):
            queryset = queryset.filter(status=status_filter)
        serializer = WantedSerializer(queryset, many=True)
        return success_response({"results": serializer.data}, status_code=status.HTTP_200_OK)
