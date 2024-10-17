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

#TODO remove, it is not used
#class TemporaryDocumentCollectionViewSet(viewsets.ModelViewSet):
#    queryset = TemporaryDocumentCollection.objects.all()
#    serializer_class = TemporaryDocumentCollectionSerializer
#
#    def get_queryset(self):
#        user = self.request.user
#        qs = TemporaryDocumentCollection.objects.none()
#        if is_internal(self.request) or is_customer(self.request):
#            qs = TemporaryDocumentCollection.objects.all()
#        else:
#            logger.warn("User is neither customer nor internal user: {} <{}>".format(user.get_full_name(), user.email))
#        return qs
#    @basic_exception_handler
#    def create(self, request, *args, **kwargs):
#        print("create temp doc coll")
#        print(request.data)
#        with transaction.atomic():
#            serializer = TemporaryDocumentCollectionSerializer(
#                    data=request.data,
#                    )
#            serializer.is_valid(raise_exception=True)
#            if serializer.is_valid():
#                instance = serializer.save()
#                save_document(request, instance, comms_instance=None, document_type=None)
#
#                return Response(serializer.data)
#
#    @detail_route(methods=['POST'], detail=True)
#    def process_temp_document(self, request, *args, **kwargs):
#        print("process_temp_document")
#        print(request.data)
#        try:
#            instance = self.get_object()
#            action = request.data.get('action')
#
#            if action == 'list':
#                pass
#
#            elif action == 'delete':
#                delete_document(request, instance, comms_instance=None, document_type='temp_document')
#
#            elif action == 'cancel':
#                cancel_document(request, instance, comms_instance=None, document_type='temp_document')
#
#            elif action == 'save':
#                save_document(request, instance, comms_instance=None, document_type='temp_document')
#
#            returned_file_data = [dict(
#                        file=d._file.url,
#                        id=d.id,
#                        name=d.name,
#                        ) for d in instance.documents.all() if d._file]
#            return Response({'filedata': returned_file_data})
#
#        except Exception as e:
#            print(traceback.print_exc())
#            raise e

