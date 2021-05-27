import traceback
import datetime
from rest_framework_datatables.renderers import DatatablesRenderer
from django.db.models import Q, Min
from django.db import transaction
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.conf import settings
from rest_framework import viewsets, serializers, status, generics, views
from rest_framework.decorators import detail_route, list_route, renderer_classes
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from ledger.accounts.models import EmailUser, Address
from datetime import datetime, timedelta, date

from mooringlicensing.components.main.decorators import basic_exception_handler
from mooringlicensing.components.main.utils import add_cache_control
from mooringlicensing.components.payments_ml.api import logger
from mooringlicensing.components.payments_ml.serializers import DcvPermitSerializer, DcvAdmissionSerializer, \
    DcvAdmissionArrivalSerializer, NumberOfPeopleSerializer
from mooringlicensing.components.proposals.models import Proposal#, ApplicationType
from mooringlicensing.components.approvals.models import (
    Approval,
    ApprovalDocument, DcvPermit, DcvOrganisation, DcvVessel, DcvAdmission, AdmissionType, AgeGroup
)
from mooringlicensing.components.approvals.serializers import (
    ApprovalSerializer,
    ApprovalCancellationSerializer,
    ApprovalExtendSerializer,
    ApprovalSuspensionSerializer,
    ApprovalSurrenderSerializer,
    ApprovalUserActionSerializer,
    ApprovalLogEntrySerializer,
    ApprovalPaymentSerializer, 
    ListApprovalSerializer, 
    DcvOrganisationSerializer, 
    DcvVesselSerializer,
    ListDcvPermitSerializer,
)
from mooringlicensing.components.organisations.models import Organisation, OrganisationContact
from mooringlicensing.helpers import is_customer, is_internal
from rest_framework_datatables.pagination import DatatablesPageNumberPagination
#from mooringlicensing.components.proposals.api import ProposalFilterBackend, ProposalRenderer
from rest_framework_datatables.filters import DatatablesFilterBackend
from rest_framework import filters


class GetApprovalTypeDict(views.APIView):
    renderer_classes = [JSONRenderer, ]

    def get(self, request, format=None):
        include_codes = request.GET.get('include_codes', '')
        include_codes = include_codes.split(',')
        types = Approval.approval_types_dict(include_codes)
        return Response(types)


class GetApprovalStatusesDict(views.APIView):
    renderer_classes = [JSONRenderer, ]

    def get(self, request, format=None):
        data = [{'code': i[0], 'description': i[1]} for i in Approval.STATUS_CHOICES]
        return Response(data)


class ApprovalPaymentFilterViewSet(generics.ListAPIView):
    """ https://cop-internal.dbca.wa.gov.au/api/filtered_organisations?search=Org1
    """
    queryset = Approval.objects.none()
    serializer_class = ApprovalPaymentSerializer
    filter_backends = (filters.SearchFilter,)
    #search_fields = ('applicant', 'applicant_id',)
    search_fields = ('id',)

    def get_queryset(self):
        """
        Return All approvals associated with user (proxy_applicant and org_applicant)
        """
        #return Approval.objects.filter(proxy_applicant=self.request.user)
        user = self.request.user

        # get all orgs associated with user
        user_org_ids = OrganisationContact.objects.filter(email=user.email).values_list('organisation_id', flat=True)

        now = datetime.now().date()
        approval_qs =  Approval.objects.filter(Q(proxy_applicant=user) | Q(org_applicant_id__in=user_org_ids) | Q(submitter_id=user))
        approval_qs =  approval_qs.exclude(current_proposal__application_type__name='E Class')
        approval_qs =  approval_qs.exclude(expiry_date__lt=now)
        approval_qs =  approval_qs.exclude(replaced_by__isnull=False) # get lastest licence, ignore the amended
        return approval_qs

    @list_route(methods=['GET',])
    def _list(self, request, *args, **kwargs):
        data =  []
        for approval in self.get_queryset():
            data.append(dict(lodgement_number=approval.lodgement_number, current_proposal=approval.current_proposal_id))
        return Response(data)
        #return Response(self.get_queryset().values_list('lodgement_number','current_proposal_id'))


class ApprovalFilterBackend(DatatablesFilterBackend):
    def filter_queryset(self, request, queryset, view):
        total_count = queryset.count()

        # Filter by types (wla, aap, aup, ml)
        filter_approval_type = request.GET.get('filter_approval_type')
        if filter_approval_type and not filter_approval_type.lower() == 'all':
            q = None
            for item in Approval.__subclasses__():
                if hasattr(item, 'code') and item.code == filter_approval_type:
                    lookup = "{}__isnull".format(item._meta.model_name)
                    q = Q(**{lookup: False})
                    break
            queryset = queryset.filter(q) if q else queryset

        # Show/Hide expired and/or surrendered
        show_expired_surrendered = request.GET.get('show_expired_surrendered', 'true')
        show_expired_surrendered = True if show_expired_surrendered.lower() in ['true', 'yes', 't', 'y',] else False
        if not show_expired_surrendered:
            queryset = queryset.exclude(status__in=(Approval.APPROVAL_STATUS_EXPIRED, Approval.APPROVAL_STATUS_SURRENDERED))

        # Filter by status
        filter_approval_status = request.GET.get('filter_approval_status')
        if filter_approval_status and not filter_approval_status.lower() == 'all':
            queryset = queryset.filter(status=filter_approval_status)

        getter = request.query_params.get
        fields = self.get_fields(getter)
        ordering = self.get_ordering(getter, fields)
        queryset = queryset.order_by(*ordering)
        if len(ordering):
            queryset = queryset.order_by(*ordering)

        try:
            queryset = super(ApprovalFilterBackend, self).filter_queryset(request, queryset, view)
        except Exception as e:
            print(e)
        setattr(view, '_datatables_total_count', total_count)
        return queryset


class ApprovalRenderer(DatatablesRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        if 'view' in renderer_context and hasattr(renderer_context['view'], '_datatables_total_count'):
            data['recordsTotal'] = renderer_context['view']._datatables_total_count
        return super(ApprovalRenderer, self).render(data, accepted_media_type, renderer_context)


class ApprovalPaginatedViewSet(viewsets.ModelViewSet):
    filter_backends = (ApprovalFilterBackend,)
    pagination_class = DatatablesPageNumberPagination
    renderer_classes = (ApprovalRenderer,)
    queryset = Approval.objects.none()
    serializer_class = ListApprovalSerializer
    search_fields = ['lodgement_number', ]
    page_size = 10

    def get_queryset(self):
        request_user = self.request.user
        all = Approval.objects.all()  # We may need to exclude the approvals created from the Waiting List Application

        if is_internal(self.request):
            return all
        elif is_customer(self.request):
            qs = all.filter(Q(submitter=request_user))
            return qs
        return Approval.objects.none()

    def list(self, request, *args, **kwargs):
        """
        User is accessing /external/ page
        """
        qs = self.get_queryset()
        qs = self.filter_queryset(qs)
        # on the internal organisations dashboard, filter the Proposal/Approval/Compliance datatables by applicant/organisation
        # applicant_id = request.GET.get('org_id')
        # if applicant_id:
        #     qs = qs.filter(applicant_id=applicant_id)

        self.paginator.page_size = qs.count()
        result_page = self.paginator.paginate_queryset(qs.order_by('-id'), request)
        serializer = ListApprovalSerializer(result_page, context={'request': request}, many=True)
        return add_cache_control(self.paginator.get_paginated_response(serializer.data))

    # def get_queryset(self):
    #     request_user = self.request.user
    #
    #     # Filter by Type(s) according to the tables
    #     filter_approval_types = self.request.GET.get('filter_approval_types', '')
    #     filter_approval_types = filter_approval_types.split(',')
    #     q = Q()
    #     for filter_approval_type in filter_approval_types:
    #         if filter_approval_type:
    #             for item in Approval.__subclasses__():
    #                 if hasattr(item, 'code') and item.code == filter_approval_type:
    #                     lookup = "{}__isnull".format(item._meta.model_name)
    #                     q |= Q(**{lookup: False})
    #     qs = Approval.objects.all()
    #     qs = qs.filter(q).order_by('-id') if q else Approval.objects.none()
    #
    #     if is_internal(self.request):
    #         return qs.all()
    #     elif is_customer(self.request):
    #         # Filter by to_be_endorsed
    #         filter_by_endorsement = self.request.GET.get('filter_by_endorsement', 'false')
    #         filter_by_endorsement = True if filter_by_endorsement.lower() in ['true', 'yes', 't', 'y',] else False
    #         if filter_by_endorsement:
    #             #
    #             qs = qs.filter(authoriseduserpermit__endorsed_by=request_user)
    #         else:
    #             qs = qs.filter(Q(submitter=request_user))  # Not sure if the submitter is the licence holder
    #         return qs
    #     return qs
    #
    # # @list_route(methods=['GET',])
    # def list(self, request, *args, **kwargs):
    #     """
    #     User is accessing /external/ page
    #     """
    #     qs = self.get_queryset()
    #     qs = self.filter_queryset(qs)
    #     # on the internal organisations dashboard, filter the Proposal/Approval/Compliance datatables by applicant/organisation
    #     # applicant_id = request.GET.get('org_id')
    #     # if applicant_id:
    #     #     qs = qs.filter(applicant_id=applicant_id)
    #
    #     self.paginator.page_size = qs.count()
    #     result_page = self.paginator.paginate_queryset(qs, request)
    #     serializer = ListApprovalSerializer(result_page, context={'request': request}, many=True)
    #     return self.paginator.get_paginated_response(serializer.data)


class ApprovalViewSet(viewsets.ModelViewSet):
    #queryset = Approval.objects.all()
    queryset = Approval.objects.none()
    serializer_class = ApprovalSerializer

    def get_queryset(self):
        if is_internal(self.request):
            return Approval.objects.all()
        elif is_customer(self.request):
            user_orgs = [org.id for org in self.request.user.mooringlicensing_organisations.all()]
            queryset =  Approval.objects.filter(Q(org_applicant_id__in = user_orgs) | Q(submitter = self.request.user))
            return queryset
        return Approval.objects.none()

    def list(self, request, *args, **kwargs):
        #queryset = self.get_queryset()
        queryset = self.get_queryset().order_by('lodgement_number', '-issue_date').distinct('lodgement_number')
        # Filter by org
        org_id = request.GET.get('org_id',None)
        if org_id:
            queryset = queryset.filter(org_applicant_id=org_id)
        submitter_id = request.GET.get('submitter_id', None)
        if submitter_id:
            qs = qs.filter(submitter_id=submitter_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # @list_route(methods=['GET',])
    # def filter_list(self, request, *args, **kwargs):
    #     """ Used by the external dashboard filters """
    #     region_qs =  self.get_queryset().filter(current_proposal__region__isnull=False).values_list('current_proposal__region__name', flat=True).distinct()
    #     activity_qs =  self.get_queryset().filter(current_proposal__activity__isnull=False).values_list('current_proposal__activity', flat=True).distinct()
    #     application_types=ApplicationType.objects.all().values_list('name', flat=True)
    #     data = dict(
    #         regions=region_qs,
    #         activities=activity_qs,
    #         approval_status_choices = [i[1] for i in Approval.STATUS_CHOICES],
    #         application_types=application_types,
    #     )
    #     return Response(data)

    @detail_route(methods=['POST'])
    @renderer_classes((JSONRenderer,))
    def process_document(self, request, *args, **kwargs):
            instance = self.get_object()
            action = request.POST.get('action')
            section = request.POST.get('input_name')
            if action == 'list' and 'input_name' in request.POST:
                pass

            elif action == 'delete' and 'document_id' in request.POST:
                document_id = request.POST.get('document_id')
                document = instance.qaofficer_documents.get(id=document_id)

                document.visible = False
                document.save()
                instance.save(version_comment='Licence ({}): {}'.format(section, document.name)) # to allow revision to be added to reversion history

            elif action == 'save' and 'input_name' in request.POST and 'filename' in request.POST:
                proposal_id = request.POST.get('proposal_id')
                filename = request.POST.get('filename')
                _file = request.POST.get('_file')
                if not _file:
                    _file = request.FILES.get('_file')

                document = instance.qaofficer_documents.get_or_create(input_name=section, name=filename)[0]
                path = default_storage.save('{}/proposals/{}/approvals/{}'.format(settings.MEDIA_APP_DIR, proposal_id, filename), ContentFile(_file.read()))

                document._file = path
                document.save()
                instance.save(version_comment='Licence ({}): {}'.format(section, filename)) # to allow revision to be added to reversion history
                #instance.current_proposal.save(version_comment='File Added: {}'.format(filename)) # to allow revision to be added to reversion history

            return  Response( [dict(input_name=d.input_name, name=d.name,file=d._file.url, id=d.id, can_delete=d.can_delete) for d in instance.qaofficer_documents.filter(input_name=section, visible=True) if d._file] )

    @detail_route(methods=['POST',])
    @renderer_classes((JSONRenderer,))
    def add_eclass_licence(self, request, *args, **kwargs):

        def raiser(exception): raise serializers.ValidationError(exception)

        try:
            with transaction.atomic():
                #keys = request.data.keys()
                #file_keys = [key for key in keys if 'file-upload' in i]
                org_applicant = None
                proxy_applicant = None

                _file = request.data.get('file-upload-0') if request.data.get('file-upload-0') else raiser('Licence File is required')
                try:
                    if request.data.get('applicant_type') == 'org':
                        org_applicant = Organisation.objects.get(organisation_id=request.data.get('holder-selected'))
                        #org_applicant = ledger_org.objects.get(id=request.data.get('holder-selected'))
                    else:
                        proxy_applicant = EmailUser.objects.get(id=request.data.get('holder-selected'))
                except:
                    raise serializers.ValidationError('Licence holder is required')

                start_date = datetime.strptime(request.data.get('start_date'), '%d/%m/%Y') if request.data.get('start_date') else raiser('Start Date is required')
                issue_date = datetime.strptime(request.data.get('issue_date'), '%d/%m/%Y') if request.data.get('issue_date') else raiser('Issue Date is required')
                expiry_date = datetime.strptime(request.data.get('expiry_date'), '%d/%m/%Y') if request.data.get('expiry_date') else raiser('Expiry Date is required')

                application_type, app_type_created = ApplicationType.objects.get_or_create(
                    name='E Class',
                    defaults={'visible':False, 'max_renewals':1, 'max_renewal_period':5}
                )

                proposal, proposal_created = Proposal.objects.get_or_create( # Dummy 'E Class' proposal
                    id=0,
                    defaults={'application_type':application_type, 'submitter':request.user, 'schema':[]}
                )

                approval = Approval.objects.create(
                    issue_date=issue_date,
                    expiry_date=expiry_date,
                    start_date=start_date,
                    org_applicant=org_applicant,
                    proxy_applicant=proxy_applicant,
                    current_proposal=proposal
                )

                doc = ApprovalDocument.objects.create(approval=approval, _file=_file)
                approval.licence_document=doc
                approval.save()

                return Response({'approval': approval.lodgement_number})

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e,'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                if hasattr(e,'message'):
                    raise serializers.ValidationError(e.message)
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))



    @detail_route(methods=['POST',])
    def approval_extend(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = ApprovalExtendSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance.approval_extend(request,serializer.validated_data)
            serializer = ApprovalSerializer(instance,context={'request':request})
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e,'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                if hasattr(e,'message'):
                    raise serializers.ValidationError(e.message)
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST',])
    def approval_cancellation(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = ApprovalCancellationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance.approval_cancellation(request,serializer.validated_data)
            serializer = ApprovalSerializer(instance,context={'request':request})
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e,'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                if hasattr(e,'message'):
                    raise serializers.ValidationError(e.message)
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST',])
    def approval_suspension(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = ApprovalSuspensionSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance.approval_suspension(request,serializer.validated_data)
            serializer = ApprovalSerializer(instance,context={'request':request})
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e,'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                if hasattr(e,'message'):
                    raise serializers.ValidationError(e.message)
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))


    @detail_route(methods=['POST',])
    def approval_reinstate(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.reinstate_approval(request)
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e,'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                if hasattr(e,'message'):
                    raise serializers.ValidationError(e.message)
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST',])
    def approval_surrender(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = ApprovalSurrenderSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance.approval_surrender(request,serializer.validated_data)
            serializer = ApprovalSerializer(instance,context={'request':request})
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e,'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                if hasattr(e,'message'):
                    raise serializers.ValidationError(e.message)
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['GET',])
    def action_log(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            qs = instance.action_logs.all()
            serializer = ApprovalUserActionSerializer(qs,many=True)
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['GET',])
    def comms_log(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            qs = instance.comms_logs.all()
            serializer = ApprovalLogEntrySerializer(qs,many=True)
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST',])
    @renderer_classes((JSONRenderer,))
    def add_comms_log(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                instance = self.get_object()
                mutable=request.data._mutable
                request.data._mutable=True
                request.data['approval'] = u'{}'.format(instance.id)
                request.data['staff'] = u'{}'.format(request.user.id)
                request.data._mutable=mutable
                serializer = ApprovalLogEntrySerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                comms = serializer.save()
                # Save the files
                for f in request.FILES:
                    document = comms.documents.create()
                    document.name = str(request.FILES[f])
                    document._file = request.FILES[f]
                    document.save()
                # End Save Documents

                return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))


class DcvAdmissionViewSet(viewsets.ModelViewSet):
    queryset = DcvAdmission.objects.all().order_by('id')
    serializer_class = DcvAdmissionSerializer

    @staticmethod
    def _handle_dcv_vessel(dcv_vessel, org_id=None):
        data = dcv_vessel
        rego_no_requested = data.get('rego_no', '')
        uvi_requested = data.get('uvi_vessel_identifier', '')
        vessel_name_requested = data.get('vessel_name', '')
        try:
            dcv_vessel = DcvVessel.objects.get(uvi_vessel_identifier=uvi_requested)
        except DcvVessel.DoesNotExist:
            data['rego_no'] = rego_no_requested
            data['uvi_vessel_identifier'] = uvi_requested
            data['vessel_name'] = vessel_name_requested
            # data['dcv_organisation_id'] = org_id
            serializer = DcvVesselSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            dcv_vessel = serializer.save()
        except Exception as e:
            logger.error(e)
            raise

        return dcv_vessel

    def create(self, request, *args, **kwargs):
        data = request.data

        dcv_vessel = self._handle_dcv_vessel(request.data.get('dcv_vessel'), None)

        data['submitter'] = request.user.id
        # data['fee_sid'] = fee_season_requested.get('id')
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        dcv_admission = serializer.save()

        for arrival in data.get('arrivals', None):
            arrival['dcv_admission'] = dcv_admission.id
            serializer_arrival = DcvAdmissionArrivalSerializer(data=arrival)
            serializer_arrival.is_valid(raise_exception=True)
            dcv_admission_arrival = serializer_arrival.save()

            # Adults
            age_group_obj = AgeGroup.objects.get(code=AgeGroup.AGE_GROUP_ADULT)
            for admission_type, number in arrival.get('adults').items():
                number = 0 if dcv_admission_arrival.private_visit else number  # When private visit, we don't care the number of people
                admission_type_obj = AdmissionType.objects.get(code=admission_type)
                serializer_num = NumberOfPeopleSerializer(data={
                    'number': number if number else 0,  # when number is blank, set to 0
                    'dcv_admission_arrival': dcv_admission_arrival.id,
                    'age_group': age_group_obj.id,
                    'admission_type': admission_type_obj.id
                })
                serializer_num.is_valid(raise_exception=True)
                number_of_people = serializer_num.save()

            # Children
            age_group_obj = AgeGroup.objects.get(code=AgeGroup.AGE_GROUP_CHILD)
            for admission_type, number in arrival.get('children').items():
                number = 0 if dcv_admission_arrival.private_visit else number  # When private visit, we don't care the number of people
                admission_type_obj = AdmissionType.objects.get(code=admission_type)
                serializer_num = NumberOfPeopleSerializer(data={
                    'number': number if number else 0,  # when number is blank, set to 0
                    'dcv_admission_arrival': dcv_admission_arrival.id,
                    'age_group': age_group_obj.id,
                    'admission_type': admission_type_obj.id
                })
                serializer_num.is_valid(raise_exception=True)
                number_of_people = serializer_num.save()

        return Response(serializer.data)


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
    def _handle_dcv_vessel(request, org_id=None):
        data = request.data
        rego_no_requested = request.data.get('dcv_vessel').get('rego_no', '')
        uvi_requested = request.data.get('dcv_vessel').get('uvi_vessel_identifier', '')
        vessel_name_requested = request.data.get('dcv_vessel').get('vessel_name', '')
        try:
            dcv_vessel = DcvVessel.objects.get(uvi_vessel_identifier=uvi_requested)
        except DcvVessel.DoesNotExist:
            data['rego_no'] = rego_no_requested
            data['uvi_vessel_identifier'] = uvi_requested
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


class DcvPermitFilterBackend(DatatablesFilterBackend):
    def filter_queryset(self, request, queryset, view):
        total_count = queryset.count()

        #filter_compliance_status = request.GET.get('filter_compliance_status')
        #if filter_compliance_status and not filter_compliance_status.lower() == 'all':
         #   queryset = queryset.filter(customer_status=filter_compliance_status)

        getter = request.query_params.get
        fields = self.get_fields(getter)
        ordering = self.get_ordering(getter, fields)
        queryset = queryset.order_by(*ordering)
        if len(ordering):
            queryset = queryset.order_by(*ordering)

        try:
            queryset = super(DcvPermitFilterBackend, self).filter_queryset(request, queryset, view)
        except Exception as e:
            print(e)
        setattr(view, '_datatables_total_count', total_count)
        return queryset


class DcvPermitRenderer(DatatablesRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        if 'view' in renderer_context and hasattr(renderer_context['view'], '_datatables_total_count'):
            data['recordsTotal'] = renderer_context['view']._datatables_total_count
        return super(DcvPermitRenderer, self).render(data, accepted_media_type, renderer_context)


class DcvPermitPaginatedViewSet(viewsets.ModelViewSet):
    filter_backends = (DcvPermitFilterBackend,)
    pagination_class = DatatablesPageNumberPagination
    renderer_classes = (DcvPermitRenderer,)
    queryset = DcvPermit.objects.none()
    serializer_class = ListDcvPermitSerializer
    search_fields = ['lodgement_number', ]
    page_size = 10

    def get_queryset(self):
        request_user = self.request.user
        qs = DcvPermit.objects.none()

        if is_internal(self.request):
            qs = DcvPermit.objects.all()
        #elif is_customer(self.request):
         #   qs = e.objects.filter(Q(approval__submitter=request_user))

        return qs

    @list_route(methods=['GET',])
    def list_external(self, request, *args, **kwargs):
        """
        User is accessing /external/ page
        """
        qs = self.get_queryset()
        qs = self.filter_queryset(qs)

        self.paginator.page_size = qs.count()
        result_page = self.paginator.paginate_queryset(qs, request)
        serializer = ListDcvPermitSerializer(result_page, context={'request': request}, many=True)
        return self.paginator.get_paginated_response(serializer.data)


class DcvVesselViewSet(viewsets.ModelViewSet):
    queryset = DcvVessel.objects.all().order_by('id')
    serializer_class = DcvVesselSerializer

    @detail_route(methods=['GET',])
    @basic_exception_handler
    def lookup_dcv_vessel(self, request, *args, **kwargs):
        dcv_vessel = self.get_object()
        serializer = DcvVesselSerializer(dcv_vessel)

        dcv_vessel_data = serializer.data
        dcv_vessel_data['annual_admission_permits'] = []  # TODO: retrieve the permits
        dcv_vessel_data['authorised_user_permits'] = []  # TODO: retrieve the permits
        dcv_vessel_data['mooring_licence'] = []  # TODO: retrieve the licences

        return add_cache_control(Response(dcv_vessel_data))
