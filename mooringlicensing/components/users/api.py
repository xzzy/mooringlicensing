import traceback
# import base64
# import geojson
# from six.moves.urllib.parse import urlparse
# from wsgiref.util import FileWrapper
from django.db.models import Q, Min, CharField, Value
from django.db.models.functions import Concat
from django.db import transaction
# from django.http import HttpResponse
# from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.conf import settings
# from django.contrib import messages
# from django.views.decorators.http import require_http_methods
# from django.views.decorators.csrf import csrf_exempt
# from django.utils import timezone
from django_countries import countries
from rest_framework import viewsets, serializers, status, generics, views, mixins
# from rest_framework.decorators import detail_route, list_route,renderer_classes
from rest_framework.decorators import action as detail_route
# from rest_framework.decorators import action as list_route
from rest_framework.decorators import renderer_classes
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import BasePermission, OR
# from rest_framework.pagination import PageNumberPagination
# from datetime import datetime, timedelta
# from collections import OrderedDict
from django.core.cache import cache
# from ledger.accounts.models import EmailUser,Address, Profile, EmailIdentity, EmailUserAction
from ledger_api_client.ledger_models import EmailUserRO as EmailUser, Address
from ledger_api_client.managed_models import SystemUser
from mooringlicensing.components.approvals.models import Approval
from mooringlicensing.components.proposals.models import ProposalApplicant
from django.core.paginator import Paginator, EmptyPage
from mooringlicensing.components.main.decorators import basic_exception_handler
from rest_framework import filters
from django.core.exceptions import ObjectDoesNotExist
from mooringlicensing.components.proposals.models import Proposal, ProposalApplicant
                              
from mooringlicensing.components.proposals.serializers import EmailUserAppViewSerializer
from mooringlicensing.components.users.models import EmailUserLogEntry
from mooringlicensing.components.users.utils import get_user_name
from mooringlicensing.components.users.serializers import (
    UserForEndorserSerializer,
    UserSerializer,
    EmailUserCommsSerializer,
)
import logging

from mooringlicensing.helpers import is_customer, is_internal
from mooringlicensing.ledger_api_utils import retrieve_system_user
# logger = logging.getLogger('mooringlicensing')
logger = logging.getLogger(__name__)


class GetCountries(views.APIView):
    def get(self, request):
        data = cache.get('country_list')
        if not data:
            country_list = []
            for country in list(countries):
                country_list.append({"name": country.name, "code": country.code})
            cache.set('country_list',country_list, settings.LOV_CACHE_TIMEOUT)
            data = cache.get('country_list')
        return Response(data)


class GetProposalApplicantUser(views.APIView):
    def get(self, request, proposal_pk, format=None):
        try: 
            proposal = Proposal.objects.get(id=proposal_pk)

            if (is_customer(self.request) and proposal.submitter == request.user.id) or is_internal(self.request):
                # Holder of this proposal is accessing OR internal user is accessing.
                submitter = retrieve_system_user(proposal.submitter)
                serializer = UserSerializer(submitter)
                return Response(serializer.data)
            elif is_customer(self.request) and proposal.site_licensee_email == request.user.email:
                # ML holder is accessing the proposal as an endorser
                submitter = retrieve_system_user(proposal.submitter)
                serializer = UserForEndorserSerializer(submitter)
                return Response(serializer.data)
            raise serializers.ValidationError("not authorised to view this user")
        except ObjectDoesNotExist:
            raise serializers.ValidationError("proposal does not exist")


class GetProfile(views.APIView):
    def get(self, request):
        if request.user.is_authenticated:
            try:
                system_user = SystemUser.objects.get(ledger_id=request.user)
                serializer = UserSerializer(system_user, context={'request':request})
                response = Response(serializer.data)
                return response
            except ObjectDoesNotExist:
                raise serializers.ValidationError("system user does not exists")
            except Exception as e:
                print(e)
                raise serializers.ValidationError("error")
        raise serializers.ValidationError("user not authenticated")


class GetPerson(views.APIView):
    def get(self, request):
        #TODO either reform is_internal or replace this check to use auth groups 
        #(permission_classes work too when implemented)
        if is_internal(request): 
            search_term = request.GET.get('search_term', '')
            page_number = request.GET.get('page_number', 1)
            items_per_page = 10

            if search_term:
                my_queryset = SystemUser.objects.annotate(
                    custom_term=Concat(
                        "first_name",
                        Value(" "),
                        "last_name",
                        Value(" "),
                        "email",
                        Value(" "),
                        "legal_first_name",
                        Value(" "),
                        "legal_last_name",
                        output_field=CharField(),
                        )
                    ).distinct("custom_term").order_by("custom_term").filter(custom_term__icontains=search_term)
                paginator = Paginator(my_queryset, items_per_page)

                try:
                    current_page = paginator.page(page_number)
                    my_objects = current_page.object_list
                except EmptyPage:
                    my_objects = []

                data_transform = []
                for user in my_objects:
                    user_name = get_user_name(user)
                    if user.legal_dob:
                        text = '{} {} (DOB: {})'.format(user_name["first_name"], user_name["last_name"], user.legal_dob)
                    else:
                        text = '{} {}'.format(user_name["first_name"], user_name["last_name"])

                    serializer = UserSerializer(user)
                    user_data = serializer.data
                    user_data['text'] = text
                    data_transform.append(user_data)
                return Response({
                    "results": data_transform,
                    "pagination": {
                        "more": current_page.has_next()
                    }
                })
        else:
            raise serializers.ValidationError("unauthorised")

        return Response()


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SystemUser.objects.none()
    serializer_class = UserSerializer
    lookup_field = "ledger_id"
    # permission_classes = [IsOwner | IsInternalUser]

    def get_queryset(self):
        if is_internal(self.request):
            return SystemUser.objects.all()
        elif is_customer(self.request):
            user = self.request.user
            return SystemUser.objects.filter(Q(ledger_id=user.id))
        return SystemUser.objects.none()

    @detail_route(methods=['GET',], detail=True)
    def comms_log(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            qs = EmailUserLogEntry.objects.filter(email_user_id=instance.id)
            serializer = EmailUserCommsSerializer(qs, many=True)
            return Response(serializer.data)
        except Exception as e:
            print(e)
            raise serializers.ValidationError("error")

    @detail_route(methods=['POST',], detail=True)
    @renderer_classes((JSONRenderer,))
    def add_comms_log(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                instance = self.get_object()
                kwargs = {
                    'subject': request.data.get('subject', ''),
                    'text': request.data.get('text', ''),
                    'email_user_id': instance.id,
                    'customer': instance.id,
                    'staff': request.data.get('staff', request.user.id),
                    'to': request.data.get('to', ''),
                    'fromm': request.data.get('fromm', ''),
                    'cc': '',
                }
                eu_entry = EmailUserLogEntry.objects.create(**kwargs)

                # for attachment in attachments:
                for f in request.FILES:
                    document = eu_entry.documents.create(
                    name = str(request.FILES[f]),
                    _file = request.FILES[f]
                    )
                return Response({})
        except Exception as e:
            print(e)
            raise serializers.ValidationError("error")

    #NOTE: to be either removed or moved elsewhere depending on organisation model requirements
    #@detail_route(methods=['GET', ], detail=True)
    #def pending_org_requests(self, request, *args, **kwargs):
    #    try:
    #        instance = self.get_object()
    #        serializer = OrganisationRequestDTSerializer(
    #            instance.organisationrequest_set.filter(
    #                status='with_assessor'),
    #            many=True,
    #            context={'request': request})
    #        return Response(serializer.data)
    #    except serializers.ValidationError:
    #        print(traceback.print_exc())
    #        raise
    #    except ValidationError as e:
    #        print(traceback.print_exc())
    #        raise serializers.ValidationError(repr(e.error_dict))
    #    except Exception as e:
    #        print(traceback.print_exc())
    #        raise serializers.ValidationError(str(e))