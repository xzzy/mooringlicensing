import logging

from decimal import *

from rest_framework import views
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework_datatables.pagination import DatatablesPageNumberPagination
from rest_framework_datatables.filters import DatatablesFilterBackend
from django.db.models import Q

from mooringlicensing import settings
from mooringlicensing.helpers import is_internal
from mooringlicensing.components.main.models import ApplicationType
from mooringlicensing.components.payments_ml.models import FeeConstructor, ApplicationFee, StickerActionFee
from mooringlicensing.components.payments_ml.serializers import FeeConstructorSerializer, InvoiceListSerializer

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


class InvoiceFilterBackend(DatatablesFilterBackend):

    def filter_queryset(self, request, queryset, view):

        filter_query = Q()

        # status filter
        filter_status = request.GET.get('filter_status')
        if filter_status and not filter_status.lower() == 'all':
            if filter_status.lower() == 'settled':
                filter_query &= (~Q(settlement_date=None) & Q(voided=False))
            elif filter_status.lower() == 'not_settled':
                filter_query &= (Q(settlement_date=None) & Q(voided=False))
            elif filter_status.lower() == 'voided':
                filter_query &= Q(voided=True)

        filter_fee_source_type = request.GET.get('filter_fee_source_type')
        if filter_fee_source_type and not filter_fee_source_type.lower() == 'all':
            if filter_fee_source_type.lower() == 'application':
                application_references = list(ApplicationFee.objects.all().values_list('invoice_reference', flat=True))
                filter_query &= Q(reference__in=application_references)
            elif filter_fee_source_type.lower() == 'sticker_action':
                sticker_action_references = list(StickerActionFee.objects.all().values_list('invoice_reference', flat=True))
                filter_query &= Q(reference__in=sticker_action_references)
        queryset = queryset.filter(filter_query)    

        try:
            super_queryset = super(InvoiceFilterBackend, self).filter_queryset(request, queryset, view)

            # Custom search
            search_text= request.GET.get('search[value]')  # This has a search term.
            if search_text:
                application_references = list(ApplicationFee.objects.filter(proposal__lodgement_number__icontains=search_text.lower()).values_list('invoice_reference', flat=True))
                sticker_action_references = list(StickerActionFee.objects.filter(sticker_action_details__approval__lodgement_number__icontains=search_text.lower()).values_list('invoice_reference', flat=True))
                applicable_references = application_references + sticker_action_references
                queryset = queryset.filter(reference__in=applicable_references)

                queryset = queryset.distinct() | super_queryset 
        except Exception as e:
            logger.error(e)

        fields = self.get_fields(request)
        ordering = self.get_ordering(request, view, fields)
        if len(ordering):
            queryset = queryset.order_by(*ordering)

        total_count = queryset.count()
        setattr(view, '_datatables_filtered_count', total_count)
        return queryset


class InvoicePaginatedViewSet(viewsets.ReadOnlyModelViewSet):

    filter_backends = (InvoiceFilterBackend,) 
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
