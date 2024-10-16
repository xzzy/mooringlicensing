import traceback
from django.http import HttpResponse, HttpResponseRedirect
from django.db import transaction
from wsgiref.util import FileWrapper
from rest_framework import viewsets, serializers, status, views

from rest_framework.decorators import action as detail_route
from rest_framework.response import Response

from mooringlicensing.components.main.decorators import basic_exception_handler
from mooringlicensing.components.main.models import (
        GlobalSettings,
        TemporaryDocumentCollection,
        )
from mooringlicensing.components.main.serializers import (
    OracleSerializer,
    TemporaryDocumentCollectionSerializer,
    BookingSettlementReportSerializer,
)
from mooringlicensing.components.main.process_document import save_document, cancel_document, delete_document

from mooringlicensing.components.proposals.models import Proposal
from mooringlicensing.components.proposals.serializers import ProposalSerializer

import logging
from mooringlicensing.helpers import is_customer, is_internal

from mooringlicensing.settings import LEDGER_SYSTEM_ID

logger = logging.getLogger(__name__)


def oracle_integration(date, override):
    system = LEDGER_SYSTEM_ID

    # TODO: implement oracle_parser_on_invoice
    # oracle_codes = oracle_parser_on_invoice(date, system, SYSTEM_NAME, override=override)

class GetExternalDashboardSectionsList(views.APIView):
    """
    Return the section's name list for the external dashboard
    """

    def get(self, request, format=None):
        # data = ['LicencesAndPermitsTable', 'ApplicationsTable', 'CompliancesTable', 'WaitingListTable', 'AuthorisedUserApplicationsTable',]
        data = GlobalSettings.objects.get(key=GlobalSettings.KEY_EXTERNAL_DASHBOARD_SECTIONS_LIST).value
        data = [item.strip() for item in data.split(",")]
        return Response(data)


class OracleJob(views.APIView):

    @basic_exception_handler
    def get(self, request, format=None):
        data = {
            "date":request.GET.get("date"),
            "override": request.GET.get("override")
        }
        serializer = OracleSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        oracle_integration(serializer.validated_data['date'].strftime('%Y-%m-%d'),serializer.validated_data['override'])
        data = {'successful':True}
        return Response(data)

class TemporaryDocumentCollectionViewSet(viewsets.ModelViewSet):
    queryset = TemporaryDocumentCollection.objects.all()
    serializer_class = TemporaryDocumentCollectionSerializer

    def get_queryset(self):
        user = self.request.user
        qs = TemporaryDocumentCollection.objects.none()
        if is_internal(self.request) or is_customer(self.request):
            qs = TemporaryDocumentCollection.objects.all()
        else:
            logger.warn("User is neither customer nor internal user: {} <{}>".format(user.get_full_name(), user.email))
        return qs
    @basic_exception_handler
    def create(self, request, *args, **kwargs):
        print("create temp doc coll")
        print(request.data)
        with transaction.atomic():
            serializer = TemporaryDocumentCollectionSerializer(
                    data=request.data,
                    )
            serializer.is_valid(raise_exception=True)
            if serializer.is_valid():
                instance = serializer.save()
                save_document(request, instance, comms_instance=None, document_type=None)

                return Response(serializer.data)

    @detail_route(methods=['POST'], detail=True)
    def process_temp_document(self, request, *args, **kwargs):
        print("process_temp_document")
        print(request.data)
        try:
            instance = self.get_object()
            action = request.data.get('action')

            if action == 'list':
                pass

            elif action == 'delete':
                delete_document(request, instance, comms_instance=None, document_type='temp_document')

            elif action == 'cancel':
                cancel_document(request, instance, comms_instance=None, document_type='temp_document')

            elif action == 'save':
                save_document(request, instance, comms_instance=None, document_type='temp_document')

            returned_file_data = [dict(
                        file=d._file.url,
                        id=d.id,
                        name=d.name,
                        ) for d in instance.documents.all() if d._file]
            return Response({'filedata': returned_file_data})

        except Exception as e:
            print(traceback.print_exc())
            raise e

