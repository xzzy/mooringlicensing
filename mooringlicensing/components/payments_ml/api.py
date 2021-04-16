import logging
from datetime import datetime

import pytz
from ledger.settings_base import TIME_ZONE
from rest_framework import views, viewsets
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from mooringlicensing import settings
from mooringlicensing.components.approvals.models import DcvPermit, DcvOrganisation, DcvVessel
from mooringlicensing.components.approvals.serializers import DcvOrganisationSerializer, DcvVesselSerializer
from mooringlicensing.components.main.models import ApplicationType
from mooringlicensing.components.payments_ml.models import FeeConstructor
from mooringlicensing.components.payments_ml.serializers import DcvPermitSerializer


logger = logging.getLogger('log')

class GetSeasonsForDcvDict(views.APIView):
    renderer_classes = [JSONRenderer, ]

    def get(self, request, format=None):
        # Return current and future seasons for the DCV permit
        application_type = ApplicationType.objects.get(code=settings.APPLICATION_TYPE_DCV_PERMIT['code'])
        fee_constructors = FeeConstructor.get_current_and_future_fee_constructors_by_application_type_and_date(application_type,)
        data = [{'id': item.fee_season.id, 'name': item.fee_season.__str__()} for item in fee_constructors]
        return Response(data)


class DcvPermitViewSet(viewsets.ModelViewSet):
    queryset = DcvPermit.objects.all().order_by('id')
    serializer_class = DcvPermitSerializer

    @staticmethod
    def _handle_dcv_organisation(request):
        data = request.data
        abn_requested = request.data.get('abn_acn', '')
        name_requested = request.data.get('organisation', '')
        try:
            dcv_organisation = DcvOrganisation.objects.get(abn=abn_requested)
        except DcvOrganisation.DoesNotExist:
            data['name'] = name_requested
            data['abn'] = abn_requested
            serializer = DcvOrganisationSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            dcv_organisation = serializer.save()
        except Exception as e:
            logger.error(e)
            raise

        return dcv_organisation

    @staticmethod
    def _handle_dcv_vessel(request, org_id):
        data = request.data
        rego_no_requested = request.data.get('rego_no', '')
        uiv_requested = request.data.get('uiv_vessel_identifier', '')
        vessel_name_requested = request.data.get('vessel_name', '')
        try:
            dcv_vessel = DcvVessel.objects.get(uiv_vessel_identifier=uiv_requested)
        except DcvVessel.DoesNotExist:
            data['rego_no'] = rego_no_requested
            data['uiv_vessel_identifier'] = uiv_requested
            data['vessel_name'] = vessel_name_requested
            data['dcv_organisation_id'] = org_id
            serializer = DcvVesselSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            dcv_vessel = serializer.save()
        except Exception as e:
            logger.error(e)
            raise

        return dcv_vessel

    def create(self, request, *args, **kwargs):
        data = request.data

        dcv_organisation = self._handle_dcv_organisation(request)
        dcv_vessel = self._handle_dcv_vessel(request, dcv_organisation.id)
        fee_season_requested = data.get('season') if data.get('season') else {'id': 0, 'name': ''}

        data['submitter'] = request.user.id
        data['dcv_vessel_id'] = dcv_vessel.id
        data['dcv_organisation_id'] = dcv_organisation.id
        data['fee_season_id'] = fee_season_requested.get('id')
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        dcv_permit = serializer.save()

        return Response(serializer.data)
