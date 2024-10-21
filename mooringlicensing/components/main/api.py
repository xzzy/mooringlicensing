from rest_framework import  views
from rest_framework.response import Response

from mooringlicensing.components.main.models import (
        GlobalSettings,
        )

import logging

logger = logging.getLogger(__name__)


class GetExternalDashboardSectionsList(views.APIView):
    """
    Return the section's name list for the external dashboard
    """
    def get(self, request, format=None):
        data = GlobalSettings.objects.get(key=GlobalSettings.KEY_EXTERNAL_DASHBOARD_SECTIONS_LIST).value
        data = [item.strip() for item in data.split(",")]
        return Response(data)