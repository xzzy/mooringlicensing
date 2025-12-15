import logging

from decimal import *

from rest_framework import views
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework_datatables.pagination import DatatablesPageNumberPagination

from mooringlicensing import settings
from mooringlicensing.helpers import is_internal
from mooringlicensing.components.main.models import ApplicationType
from mooringlicensing.components.payments_ml.models import FeeConstructor, ApplicationFee, StickerActionFee
from mooringlicensing.components.payments_ml.serializers import FeeConstructorSerializer, InvoiceListSerializer

#TODO replace with dedicated payment permission
from mooringlicensing.components.approvals.permissions import (
    InternalApprovalPermission,
)

from ledger_api_client.ledger_models import Invoice

logger = logging.getLogger(__name__)

from rest_framework.permissions import IsAuthenticated

class GetSeasonsForDcvPermitDict(views.APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request, format=None):
        # Return current and future seasons for the DCV permit
        application_type = ApplicationType.objects.get(code=settings.APPLICATION_TYPE_DCV_PERMIT['code'])
        fee_constructors = FeeConstructor.get_current_and_future_fee_constructors_by_application_type_and_date(application_type,)
        data = [{'id': item.fee_season.id, 'name': item.fee_season.__str__()} for item in fee_constructors]
        return Response(data)


class GetFeeConfigurations(views.APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request, format=None):
        # Return current and future seasons for the DCV admission
        application_type = ApplicationType.objects.get(code=settings.APPLICATION_TYPE_DCV_ADMISSION['code'])
        fee_constructors = FeeConstructor.get_current_and_future_fee_constructors_by_application_type_and_date(application_type,)
        serializer = FeeConstructorSerializer(fee_constructors, many=True)

        return Response(serializer.data)

class InvoicePaginatedViewSet(viewsets.ReadOnlyModelViewSet):

    #filter_backends = (ApprovalFilterBackend,) TODO
    pagination_class = DatatablesPageNumberPagination
    queryset = Invoice.objects.none()
    serializer_class = InvoiceListSerializer
    permission_classes=[InternalApprovalPermission]

    def get_queryset(self):
        all = Invoice.objects.all()

        if is_internal(self.request):
            #We only want invoices relevant to Mooring Licensing
            applicable_references = []
            application_references = list(ApplicationFee.objects.all().values_list('invoice_reference', flat=True))
            sticker_action_references = list(StickerActionFee.objects.all().values_list('invoice_reference', flat=True))
            #TODO include DCV references when required

            applicable_references = application_references + sticker_action_references

            #NOTE: this approach uses an ever growing list of references
            #local tests indicate use of 63kb of space in memory for approx. 6 months worth of records
            #this should be sustainable albeit quite inefficient - an alternative arrangement or caching may be preferable at some stage
            #import sys
            #print("\n\n\n",sys.getsizeof(applicable_references))
            all = Invoice.objects.filter(reference__in=applicable_references)

            return all
        
        return Invoice.objects.none()
