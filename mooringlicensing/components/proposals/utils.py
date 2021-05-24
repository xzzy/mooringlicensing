import re

import pytz
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings
from ledger.settings_base import TIME_ZONE
from preserialize.serialize import serialize
from ledger.accounts.models import EmailUser #, Document
from mooringlicensing.components.proposals.models import (
    ProposalDocument,  # ProposalPark, ProposalParkActivity, ProposalParkAccess, ProposalTrail, ProposalTrailSectionActivity, ProposalTrailSection, ProposalParkZone, ProposalParkZoneActivity, ProposalOtherDetails, ProposalAccreditation,
    ProposalUserAction,
    ProposalAssessment,
    ProposalAssessmentAnswer,
    ChecklistQuestion,
    ProposalStandardRequirement,
    WaitingListApplication,
    AnnualAdmissionApplication,
    AuthorisedUserApplication,
    MooringLicenceApplication,
    Vessel,
    VesselDetails,
    VesselOwnership,
    Owner, 
    Proposal,
    Company,
    CompanyOwnership,
)
from mooringlicensing.components.proposals.serializers import (
        SaveVesselDetailsSerializer,
        SaveVesselOwnershipSerializer,
        SaveCompanyOwnershipSerializer,
        SaveDraftProposalVesselSerializer,
        SaveProposalSerializer,
        SaveWaitingListApplicationSerializer,
        SaveMooringLicenceApplicationSerializer,
        SaveAuthorisedUserApplicationSerializer,
        SaveAnnualAdmissionApplicationSerializer,
        VesselSerializer,
        VesselOwnershipSerializer,
        VesselDetailsSerializer,
        )
from mooringlicensing.components.approvals.models import Approval
from mooringlicensing.components.proposals.email import send_submit_email_notification, send_external_submit_email_notification
#from mooringlicensing.components.main.models import Activity, Park, AccessType, Trail, Section, Zone
import traceback
import os
from copy import deepcopy
from datetime import datetime
import time
from rest_framework import serializers


import logging
logger = logging.getLogger(__name__)

def create_data_from_form(schema, post_data, file_data, post_data_index=None,special_fields=[],assessor_data=False):
    data = {}
    special_fields_list = []
    assessor_data_list = []
    comment_data_list = {}
    special_fields_search = SpecialFieldsSearch(special_fields)
    if assessor_data:
        assessor_fields_search = AssessorDataSearch()
        comment_fields_search = CommentDataSearch()
    try:
        for item in schema:
            data.update(_create_data_from_item(item, post_data, file_data, 0, ''))
            #_create_data_from_item(item, post_data, file_data, 0, '')
            special_fields_search.extract_special_fields(item, post_data, file_data, 0, '')
            if assessor_data:
                assessor_fields_search.extract_special_fields(item, post_data, file_data, 0, '')
                comment_fields_search.extract_special_fields(item, post_data, file_data, 0, '')
        special_fields_list = special_fields_search.special_fields
        if assessor_data:
            assessor_data_list = assessor_fields_search.assessor_data
            comment_data_list = comment_fields_search.comment_data
    except:
        traceback.print_exc()
    if assessor_data:
        return [data],special_fields_list,assessor_data_list,comment_data_list

    return [data],special_fields_list


def _extend_item_name(name, suffix, repetition):
    return '{}{}-{}'.format(name, suffix, repetition)

def _create_data_from_item(item, post_data, file_data, repetition, suffix):
    item_data = {}

    if 'name' in item:
        extended_item_name = item['name']
    else:
        raise Exception('Missing name in item %s' % item['label'])

    if 'children' not in item:
        if item['type'] in ['checkbox' 'declaration']:
            #item_data[item['name']] = post_data[item['name']]
            item_data[item['name']] = extended_item_name in post_data
        elif item['type'] == 'file':
            if extended_item_name in file_data:
                item_data[item['name']] = str(file_data.get(extended_item_name))
                # TODO save the file here
            elif extended_item_name + '-existing' in post_data and len(post_data[extended_item_name + '-existing']) > 0:
                item_data[item['name']] = post_data.get(extended_item_name + '-existing')
            else:
                item_data[item['name']] = ''
        else:
            if extended_item_name in post_data:
                if item['type'] == 'multi-select':
                    item_data[item['name']] = post_data.getlist(extended_item_name)
                else:
                    item_data[item['name']] = post_data.get(extended_item_name)
    else:
        if 'repetition' in item:
            item_data = generate_item_data(extended_item_name,item,item_data,post_data,file_data,len(post_data[item['name']]),suffix)
        else:
            item_data = generate_item_data(extended_item_name, item, item_data, post_data, file_data,1,suffix)


    if 'conditions' in item:
        for condition in item['conditions'].keys():
            for child in item['conditions'][condition]:
                item_data.update(_create_data_from_item(child, post_data, file_data, repetition, suffix))

    return item_data

def generate_item_data(item_name,item,item_data,post_data,file_data,repetition,suffix):
    item_data_list = []
    for rep in xrange(0, repetition):
        child_data = {}
        for child_item in item.get('children'):
            child_data.update(_create_data_from_item(child_item, post_data, file_data, 0,
                                                     '{}-{}'.format(suffix, rep)))
        item_data_list.append(child_data)

        item_data[item['name']] = item_data_list
    return item_data

class AssessorDataSearch(object):

    def __init__(self,lookup_field='canBeEditedByAssessor'):
        self.lookup_field = lookup_field
        self.assessor_data = []

    def extract_assessor_data(self,item,post_data):
        values = []
        res = {
            'name': item,
            'assessor': '',
            'referrals':[]
        }
        for k in post_data:
            if re.match(item,k):
                values.append({k:post_data[k]})
        if values:
            for v in values:
                for k,v in v.items():
                    parts = k.split('{}-'.format(item))
                    if len(parts) > 1:
                        # split parts to see if referall
                        ref_parts = parts[1].split('Referral-')
                        if len(ref_parts) > 1:
                            # Referrals
                            res['referrals'].append({
                                'value':v,
                                'email':ref_parts[1],
                                'full_name': EmailUser.objects.get(email=ref_parts[1].lower()).get_full_name()
                            })
                        elif k.split('-')[-1].lower() == 'assessor':
                            # Assessor
                            res['assessor'] = v

        return res

    def extract_special_fields(self,item, post_data, file_data, repetition, suffix):
        item_data = {}
        if 'name' in item:
            extended_item_name = item['name']
        else:
            raise Exception('Missing name in item %s' % item['label'])

        if 'children' not in item:
            if 'conditions' in item:
                for condition in item['conditions'].keys():
                    for child in item['conditions'][condition]:
                        item_data.update(self.extract_special_fields(child, post_data, file_data, repetition, suffix))

            if item.get(self.lookup_field):
                self.assessor_data.append(self.extract_assessor_data(extended_item_name,post_data))

        else:
            if 'repetition' in item:
                item_data = self.generate_item_data_special_field(extended_item_name,item,item_data,post_data,file_data,len(post_data[item['name']]),suffix)
            else:
                item_data = self.generate_item_data_special_field(extended_item_name, item, item_data, post_data, file_data,1,suffix)

            if 'conditions' in item:
                for condition in item['conditions'].keys():
                    for child in item['conditions'][condition]:
                        item_data.update(self.extract_special_fields(child, post_data, file_data, repetition, suffix))

        return item_data

    def generate_item_data_special_field(self,item_name,item,item_data,post_data,file_data,repetition,suffix):
        item_data_list = []
        for rep in xrange(0, repetition):
            child_data = {}
            for child_item in item.get('children'):
                child_data.update(self.extract_special_fields(child_item, post_data, file_data, 0,
                                                         '{}-{}'.format(suffix, rep)))
            item_data_list.append(child_data)

            item_data[item['name']] = item_data_list
        return item_data

class CommentDataSearch(object):

    def __init__(self,lookup_field='canBeEditedByAssessor'):
        self.lookup_field = lookup_field
        self.comment_data = {}

    def extract_comment_data(self,item,post_data):
        res = {}
        values = []
        for k in post_data:
            if re.match(item,k):
                values.append({k:post_data[k]})
        if values:
            for v in values:
                for k,v in v.items():
                    parts = k.split('{}'.format(item))
                    if len(parts) > 1:
                        ref_parts = parts[1].split('-comment-field')
                        if len(ref_parts) > 1:
                            res = {'{}'.format(item):v}
        return res

    def extract_special_fields(self,item, post_data, file_data, repetition, suffix):
        item_data = {}
        if 'name' in item:
            extended_item_name = item['name']
        else:
            raise Exception('Missing name in item %s' % item['label'])

        if 'children' not in item:
            self.comment_data.update(self.extract_comment_data(extended_item_name,post_data))

        else:
            if 'repetition' in item:
                item_data = self.generate_item_data_special_field(extended_item_name,item,item_data,post_data,file_data,len(post_data[item['name']]),suffix)
            else:
                item_data = self.generate_item_data_special_field(extended_item_name, item, item_data, post_data, file_data,1,suffix)


        if 'conditions' in item:
            for condition in item['conditions'].keys():
                for child in item['conditions'][condition]:
                    item_data.update(self.extract_special_fields(child, post_data, file_data, repetition, suffix))

        return item_data

    def generate_item_data_special_field(self,item_name,item,item_data,post_data,file_data,repetition,suffix):
        item_data_list = []
        for rep in xrange(0, repetition):
            child_data = {}
            for child_item in item.get('children'):
                child_data.update(self.extract_special_fields(child_item, post_data, file_data, 0,
                                                         '{}-{}'.format(suffix, rep)))
            item_data_list.append(child_data)

            item_data[item['name']] = item_data_list
        return item_data

class SpecialFieldsSearch(object):

    def __init__(self,lookable_fields):
        self.lookable_fields = lookable_fields
        self.special_fields = {}

    def extract_special_fields(self,item, post_data, file_data, repetition, suffix):
        item_data = {}
        if 'name' in item:
            extended_item_name = item['name']
        else:
            raise Exception('Missing name in item %s' % item['label'])

        if 'children' not in item:
            for f in self.lookable_fields:
                if item['type'] in ['checkbox' 'declaration']:
                    val = None
                    val = item.get(f,None)
                    if val:
                        item_data[f] = extended_item_name in post_data
                        self.special_fields.update(item_data)
                else:
                    if extended_item_name in post_data:
                        val = None
                        val = item.get(f,None)
                        if val:
                            if item['type'] == 'multi-select':
                                item_data[f] = ','.join(post_data.getlist(extended_item_name))
                            else:
                                item_data[f] = post_data.get(extended_item_name)
                            self.special_fields.update(item_data)
        else:
            if 'repetition' in item:
                item_data = self.generate_item_data_special_field(extended_item_name,item,item_data,post_data,file_data,len(post_data[item['name']]),suffix)
            else:
                item_data = self.generate_item_data_special_field(extended_item_name, item, item_data, post_data, file_data,1,suffix)


        if 'conditions' in item:
            for condition in item['conditions'].keys():
                for child in item['conditions'][condition]:
                    item_data.update(self.extract_special_fields(child, post_data, file_data, repetition, suffix))

        return item_data

    def generate_item_data_special_field(self,item_name,item,item_data,post_data,file_data,repetition,suffix):
        item_data_list = []
        for rep in xrange(0, repetition):
            child_data = {}
            for child_item in item.get('children'):
                child_data.update(self.extract_special_fields(child_item, post_data, file_data, 0,
                                                         '{}-{}'.format(suffix, rep)))
            item_data_list.append(child_data)

            item_data[item['name']] = item_data_list
        return item_data


def save_proponent_data(instance, request, viewset):
    if type(instance.child_obj) == WaitingListApplication:
        save_proponent_data_wla(instance, request, viewset)
    elif type(instance.child_obj) == AnnualAdmissionApplication:
        save_proponent_data_aaa(instance, request, viewset)
    elif type(instance.child_obj) == AuthorisedUserApplication:
        save_proponent_data_aua(instance, request, viewset)
    elif type(instance.child_obj) == MooringLicenceApplication:
        save_proponent_data_mla(instance, request, viewset)

def save_proponent_data_aaa(instance, request, viewset):
    print(request.data)
    # vessel
    vessel_data = deepcopy(request.data.get("vessel"))
    if vessel_data:
        if viewset.action == 'submit':
            submit_vessel_data(instance, request, vessel_data)
        elif instance.processing_status == 'draft':
            save_vessel_data(instance, request, vessel_data)
    # proposal
    proposal_data = request.data.get('proposal') if request.data.get('proposal') else {}
    serializer = SaveAnnualAdmissionApplicationSerializer(
            instance, 
            data=proposal_data, 
            context={
                "action": viewset.action
                }
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

def save_proponent_data_wla(instance, request, viewset):
    print(request.data)
    # vessel
    vessel_data = deepcopy(request.data.get("vessel"))
    if vessel_data:
        if viewset.action == 'submit':
            submit_vessel_data(instance, request, vessel_data)
        elif instance.processing_status == 'draft':
            save_vessel_data(instance, request, vessel_data)
    # proposal
    proposal_data = request.data.get('proposal') if request.data.get('proposal') else {}
    serializer = SaveWaitingListApplicationSerializer(
            instance, 
            data=proposal_data, 
            context={
                "action": viewset.action
                }
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    # if instance.pending_amendment_request:
    #     proposal_submit(instance, request)


def save_proponent_data_mla(instance, request, viewset):
    print(request.data)
    # vessel
    vessel_data = deepcopy(request.data.get("vessel"))
    if vessel_data:
        if viewset.action == 'submit':
            submit_vessel_data(instance, request, vessel_data)
        elif instance.processing_status == 'draft':
            save_vessel_data(instance, request, vessel_data)
    # proposal
    proposal_data = request.data.get('proposal') if request.data.get('proposal') else {}
    serializer = SaveMooringLicenceApplicationSerializer(
            instance, 
            data=proposal_data, 
            context={
                "action": viewset.action
                }
    )
    serializer.is_valid(raise_exception=True)
    proposal = serializer.save()

    if viewset.action == 'submit':
        proposal_submit(proposal, request)


def save_proponent_data_aua(instance, request, viewset):
    print(request.data)
    # vessel
    vessel_data = deepcopy(request.data.get("vessel"))
    if vessel_data:
        if viewset.action == 'submit':
            submit_vessel_data(instance, request, vessel_data)
        elif instance.processing_status == 'draft':
            save_vessel_data(instance, request, vessel_data)
    # proposal
    proposal_data = request.data.get('proposal') if request.data.get('proposal') else {}
    serializer = SaveAuthorisedUserApplicationSerializer(
            instance, 
            data=proposal_data, 
            context={
                "action": viewset.action
                }
    )
    serializer.is_valid(raise_exception=True)
    proposal = serializer.save()

    if viewset.action == 'submit':
        proposal_submit(proposal, request)



#def save_proponent_data_aaa(instance, request, viewset):
#    print("save aaa")
#    print(request.data)
#    #save_proposal_data(instance, request)
#    submit_vessel_data(instance, request)

# draft and submit
def save_vessel_data(instance, request, vessel_data):
    print("save vessel data")
    #vessel_data = request.data.get("vessel")
    vessel_details_data = {}
    #if not vessel_data.get("read_only"):
    ## no read_only!!
    #print('if not vessel_data.get("read_only")')
    vessel_details_data = vessel_data.get("vessel_details")
    # add vessel details to vessel_data
    for key in vessel_details_data.keys():
        vessel_data.update({key: vessel_details_data.get(key)})
    if vessel_data.get('id'):
        vessel_data.update({"vessel_id": vessel_data.get('id')})
    # clear stored instance.vessel_details
    #instance.vessel_details = None
    #instance.save()
    ## do not write or link to VesselDetails tables until submit
    #else:
    #vessel_details_id = vessel_data.get("vessel_details", {}).get("id")
    #if vessel_details_id:
    #    instance.vessel_details = VesselDetails.objects.get(id=vessel_details_id)
    #    instance.save()
        #vessel_ownership_id = vessel_data.get("vessel_ownership", {}).get("id")
        #if vessel_ownership_id:
        #    instance.vessel_ownership = VesselOwnership.objects.get(id=vessel_ownership_id)
        #    instance.save()
    # we need this to save vessel ownership to proposal in draft status
    vessel_ownership_data = vessel_data.get("vessel_ownership")
    #company_ownership_id = vessel_ownership_data.get('company_ownership', {}).get('id')
    company_ownership_percentage = vessel_ownership_data.get('company_ownership', {}).get('percentage')
    company_ownership_name = vessel_ownership_data.get('company_ownership', {}).get('company', {}).get('name')
    # need id also?
    #if not company_ownership_id:
    vessel_data.update({"company_ownership_percentage": company_ownership_percentage})
    vessel_data.update({"company_ownership_name": company_ownership_name})
    #else:
        #vessel_data.update({"company_ownership_id": company_ownership_id})
    # remove company_ownership from vessel_ownership_date
    vessel_ownership_data.pop('company_ownership', None)
    # copy VesselOwnership fields to vessel_data
    for key in vessel_ownership_data.keys():
        vessel_data.update({key: vessel_ownership_data.get(key)})
    #import ipdb; ipdb.set_trace()
    serializer = SaveDraftProposalVesselSerializer(instance, vessel_data)
    serializer.is_valid(raise_exception=True)
    print(serializer.validated_data)
    serializer.save()

def submit_vessel_data(instance, request, vessel_data):
    print("submit vessel data")
    ## save vessel data into proposal first
    save_vessel_data(instance, request, vessel_data)
    vessel, vessel_details = store_vessel_data(request, vessel_data)
    # associate vessel_details with proposal
    instance.vessel_details = vessel_details
    instance.save()
    # record ownership data
    #submit_vessel_ownership(instance, request)
    vessel_ownership = store_vessel_ownership(request, vessel, instance)
    # associate vessel_ownership with proposal
    instance.vessel_ownership = vessel_ownership
    instance.save()
    ownership_percentage_validation(vessel_ownership)

def store_vessel_data(request, vessel_data):
    if not vessel_data.get('rego_no'):
        raise serializers.ValidationError({"Missing information": "You must supply a Vessel Registration Number"})
    rego_no = vessel_data.get('rego_no').replace(" ", "").strip().lower() # successfully avoiding dupes?
    vessel, created = Vessel.objects.get_or_create(rego_no=rego_no)
    
    vessel_details_data = vessel_data.get("vessel_details")
    # add vessel to vessel_details_data
    vessel_details_data["vessel"] = vessel.id

    ## Vessel Details
    existing_vessel_details = vessel.latest_vessel_details
    ## we no longer use a read_only flag, so must compare incoming data to existing
    existing_vessel_details_data = VesselDetailsSerializer(existing_vessel_details).data
    #print(existing_vessel_details_data.keys())
    create_vessel_details = False
    for key in existing_vessel_details_data.keys():
        if key in vessel_details_data and existing_vessel_details_data[key] != vessel_details_data[key]:
            create_vessel_details = True
            print(existing_vessel_details_data[key])
            print(vessel_details_data[key])

    vessel_details = None
    if create_vessel_details:
        serializer = SaveVesselDetailsSerializer(data=vessel_details_data)
        serializer.is_valid(raise_exception=True)
        vessel_details = serializer.save()
    else:
        serializer = SaveVesselDetailsSerializer(existing_vessel_details, vessel_details_data)
        serializer.is_valid(raise_exception=True)
        vessel_details = serializer.save()
    return vessel, vessel_details

def store_vessel_ownership(request, vessel, instance=None):
    ## Get Vessel
    #vessel = instance.vessel_details.vessel
    ## Vessel Ownership
    ## we cannot use vessel_data, because this dict has been modified in store_vessel_data()
    vessel_ownership_data = deepcopy(request.data.get('vessel').get("vessel_ownership"))
    if vessel_ownership_data.get('individual_owner') is None:
        raise serializers.ValidationError({"Missing information": "You must select a Vessel Owner"})
    elif (not vessel_ownership_data.get('individual_owner') and not 
            vessel_ownership_data.get("company_ownership").get("company").get("name")
            ):
        raise serializers.ValidationError({"Missing information": "You must supply the company name"})
    company_ownership = None
    company = None
    if not vessel_ownership_data.get('individual_owner'):
        ## Company
        company_name = vessel_ownership_data.get("company_ownership").get("company").get("name")
        company, created = Company.objects.get_or_create(name=company_name)
        ## CompanyOwnership
        company_ownership_data = vessel_ownership_data.get("company_ownership")
        #if not company_ownership_data.get('id'):
        company_ownership_set = CompanyOwnership.objects.filter(
                company=company,
                vessel=vessel,
                )
        ## Do we need to create a new CO record?
        create_company_ownership = False
        edit_company_ownership = True
        if company_ownership_set.filter(status="draft"):
            company_ownership = company_ownership_set.filter(status="draft")[0]
            ## cannot edit draft record with blocking_proposal
            if company_ownership.blocking_proposal:
                edit_company_ownership = False
        elif company_ownership_set.filter(status="approved"):
            company_ownership = company_ownership_set.filter(status="approved")[0]
            existing_company_ownership_data = CompanyOwnershipSerializer(company_ownership).data
            for key in existing_company_ownership_data.keys():
                if key in company_ownership_data and existing_company_ownership_data[key] != company_ownership_data[key]:
                    create_company_ownership = True
                    print(existing_company_ownership_data[key])
                    print(company_ownership_data[key])
        else:
            create_company_ownership = True
        # update company key from dict to pk
        company_ownership_data.update({"company": company.id})
        # add vessel to company_ownership_data
        company_ownership_data.update({"vessel": vessel.id})
        if create_company_ownership:
            serializer = SaveCompanyOwnershipSerializer(data=company_ownership_data)
            serializer.is_valid(raise_exception=True)
            company_ownership = serializer.save()
        elif edit_company_ownership:
            serializer = SaveCompanyOwnershipSerializer(company_ownership, company_ownership_data)
            serializer.is_valid(raise_exception=True)
            company_ownership = serializer.save()
    ## add to vessel_ownership_data
    if company_ownership and company_ownership.id:
        vessel_ownership_data['company_ownership'] = company_ownership.id
        if instance:
            ## set blocking_proposal
            company_ownership.blocking_proposal = instance
            company_ownership.save()
    else:
        vessel_ownership_data['company_ownership'] = None
    vessel_ownership_data['vessel'] = vessel.id
    owner, created = Owner.objects.get_or_create(emailuser=request.user)

    vessel_ownership_data['owner'] = owner.id
    #vessel_ownership = instance.vessel_ownership
    #if not vessel_ownership:
    vessel_ownership, created = VesselOwnership.objects.get_or_create(
            owner=owner, 
            vessel=vessel, 
            company_ownership=company_ownership
            )
    serializer = SaveVesselOwnershipSerializer(vessel_ownership, vessel_ownership_data)
    serializer.is_valid(raise_exception=True)
    vessel_ownership = serializer.save()
    #raise serializers.ValidationError({"Missing information": "blah"})
    return vessel_ownership

def ownership_percentage_validation(vessel_ownership):
    individual_ownership_id = None
    company_ownership_id = None
    min_percent_fail = False
    vessel_ownership_percentage = 0
    ## First ensure applicable % >= 25
    if hasattr(vessel_ownership.company_ownership, 'id'):
        company_ownership_id = vessel_ownership.company_ownership.id
        if not vessel_ownership.company_ownership.percentage:
            raise serializers.ValidationError({
                "Ownership Percentage": "You must specify a percentage"
                })
        else:
            if vessel_ownership.company_ownership.percentage < 25:
                min_percent_fail = True
            else:
                vessel_ownership_percentage = vessel_ownership.company_ownership.percentage
    elif not vessel_ownership.percentage:
        raise serializers.ValidationError({
            "Ownership Percentage": "You must specify a percentage"
            })
        individual_ownership_id = vessel_ownership.id
    else:
        if vessel_ownership.percentage < 25:
            min_percent_fail = True
        else:
            vessel_ownership_percentage = vessel_ownership.percentage
    if min_percent_fail:
        raise serializers.ValidationError({
            "Ownership Percentage": "Minimum of 25 percent"
            })
    ## Calc total existing
    total_percent = vessel_ownership_percentage
    vessel = vessel_ownership.vessel
    for vo in vessel.filtered_vesselownership_set.all():
        if hasattr(vo.company_ownership, 'id'):
            if (vo.company_ownership.id != company_ownership_id and 
                    vo.company_ownership.percentage and
                    vo.company_ownership.blocking_proposal
                    ):
                total_percent += vo.company_ownership.percentage
        elif vo.percentage and vo.id != individual_ownership_id:
            total_percent += vo.percentage
    print("total_percent")
    print(total_percent)
    if total_percent > 100:
        raise serializers.ValidationError({
            "Ownership Percentage": "Total of 100 percent exceeded"
            })

def save_bare_vessel_data(request, vessel_obj=None):
    print("save bare vessel data")
    vessel_data = request.data.get("vessel")
    vessel, vessel_details = store_vessel_data(request, vessel_data)
    # record ownership data
    #submit_vessel_ownership(instance, request)
    vessel_ownership = store_vessel_ownership(request, vessel)
    return VesselOwnershipSerializer(vessel_ownership).data

# no proposal - manage vessels
def bak_save_bare_vessel_data(request, vessel_obj=None):
    #import ipdb; ipdb.set_trace()
    print("save bare vessel data")
    #if not vessel_data.get("read_only"):
    vessel_data = request.data.get("vessel")
    if not vessel_data.get('rego_no'):
        raise serializers.ValidationError({"Missing information": "You must supply a Vessel Registration Number"})
    rego_no = vessel_data.get('rego_no').replace(" ", "").strip().lower() # successfully avoiding dupes?
    if vessel_obj:
        vessel = vessel_obj
    else:
        vessel, created = Vessel.objects.get_or_create(rego_no=rego_no)
    
    vessel_details_data = vessel_data.get("vessel_details")
    # add vessel to vessel_details_data
    vessel_details_data["vessel"] = vessel.id

    ## Vessel Details
    vessel_details = vessel.latest_vessel_details
    if not vessel_details:
        serializer = SaveVesselDetailsSerializer(data=vessel_details_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        #vessel_details = serializer.save()
        # set proposal now has sole right to edit vessel_details
        #vessel_details.blocking_proposal = instance
        #vessel_details.save()
    else:
        serializer = SaveVesselDetailsSerializer(vessel_details, vessel_details_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
    # record ownership data
    vessel_ownership = save_bare_vessel_ownership(request, vessel_data, vessel)
    #return VesselSerializer(vessel).data
    return VesselOwnershipSerializer(vessel_ownership).data

# no proposal - manage vessels
def bak_save_bare_vessel_ownership(request, vessel_data, vessel):
    print("save bare vessel ownership data")
    vessel_ownership_data = vessel_data.get("vessel_ownership")
    if vessel_ownership_data.get('individual_owner') is None:
        raise serializers.ValidationError({"Missing information": "You must select a Vessel Owner"})
    elif not vessel_ownership_data.get('individual_owner') and not vessel_ownership_data.get("org_name"):
        raise serializers.ValidationError({"Missing information": "You must supply the company name"})
    vessel_ownership_data['vessel'] = vessel.id
    org_name = vessel_ownership_data.get("org_name")
    owner, created = Owner.objects.get_or_create(emailuser=request.user)

    vessel_ownership_data['owner'] = owner.id
    #vessel_ownership = instance.vessel_ownership
    #if not vessel_ownership:
    vessel_ownership, created = VesselOwnership.objects.get_or_create(
            owner=owner, 
            vessel=vessel, 
            #org_name=registered_owner_company_name_strip
            org_name=org_name
            )
    if request.data.get('create_vessel') and not created:
        raise serializers.ValidationError("You are already listed as an owner of this vessel.\
                Please select Options > Manage Vessels to edit this vessel.")
    serializer = SaveVesselOwnershipSerializer(vessel_ownership, vessel_ownership_data)
    serializer.is_valid(raise_exception=True)
    vessel_ownership = serializer.save()
    return vessel_ownership

#from mooringlicensing.components.main.models import ApplicationType

def save_assessor_data(instance,request,viewset):
    with transaction.atomic():
        try:
            pass
            #if instance.application_type.name==ApplicationType.FILMING:
            #    save_assessor_data_filming(instance,request,viewset)
            #if instance.application_type.name==ApplicationType.TCLASS:
            #    save_assessor_data_tclass(instance,request,viewset)
            #if instance.application_type.name==ApplicationType.EVENT:
            #    save_assessor_data_event(instance,request,viewset)            
        except:
            raise


def proposal_submit(proposal, request):
    # if proposal.can_user_edit:
    proposal.lodgement_date = datetime.now(pytz.timezone(TIME_ZONE))
    #proposal.training_completed = True
    #if (proposal.amendment_requests):
    #    qs = proposal.amendment_requests.filter(status = "requested")
    #    if (qs):
    #        for q in qs:
    #            q.status = 'amended'
    #            q.save()

    # Create a log entry for the proposal
    proposal.log_user_action(ProposalUserAction.ACTION_LODGE_APPLICATION.format(proposal.id),request)

    ret1 = send_submit_email_notification(request, proposal)
    #ret2 = send_external_submit_email_notification(request, proposal)
    ret2 = True

    if ret1 and ret2:
        # Set new status
        proposal.processing_status = Proposal.PROCESSING_STATUS_WITH_ASSESSOR
        proposal.customer_status = Proposal.CUSTOMER_STATUS_WITH_ASSESSOR
        if proposal.application_type.code == AuthorisedUserApplication.code and proposal.mooring_authorisation_preference.lower() != 'ria':
            # When this application is AUA, and the mooring authorisation preference is RIA
            proposal.processing_status = Proposal.PROCESSING_STATUS_AWAITING_ENDORSEMENT
            proposal.customer_status = Proposal.CUSTOMER_STATUS_AWAITING_ENDORSEMENT
        if proposal.application_type.code == MooringLicenceApplication.code:
            # When this application is MLA,
            proposal.processing_status = Proposal.PROCESSING_STATUS_AWAITING_DOCUMENTS
            proposal.customer_status = Proposal.CUSTOMER_STATUS_AWAITING_DOCUMENTS

        #    #proposal.documents.all().update(can_delete=False)
    #    #proposal.required_documents.all().update(can_delete=False)
        proposal.save()
    else:
       raise ValidationError('An error occurred while submitting proposal (Submit email notifications failed)')
    proposal.save()

    #Create assessor checklist with the current assessor_list type questions
    #Assessment instance already exits then skip.
    #try:
    #    assessor_assessment=ProposalAssessment.objects.get(proposal=proposal,referral_group=None, referral_assessment=False)
    #except ProposalAssessment.DoesNotExist:
    #    assessor_assessment=ProposalAssessment.objects.create(proposal=proposal,referral_group=None, referral_assessment=False)
    #    checklist=ChecklistQuestion.objects.filter(list_type='assessor_list', application_type=proposal.application_type, obsolete=False)
    #    for chk in checklist:
    #        try:
    #            chk_instance=ProposalAssessmentAnswer.objects.get(question=chk, assessment=assessor_assessment)
    #        except ProposalAssessmentAnswer.DoesNotExist:
    #            chk_instance=ProposalAssessmentAnswer.objects.create(question=chk, assessment=assessor_assessment)

    #return proposal

    # else:
    #     raise ValidationError('You can\'t edit this proposal at this moment')


def is_payment_officer(user):
    from mooringlicensing.components.proposals.models import PaymentOfficerGroup
    try:
        group= PaymentOfficerGroup.objects.get(default=True)
    except PaymentOfficerGroup.DoesNotExist:
        group= None
    if group:
        if user in group.members.all():
            return True
    return False


#from mooringlicensing.components.proposals.models import (
#        Proposal, #Referral, 
#        AmendmentRequest, 
#        ProposalDeclinedDetails
#        )
#from mooringlicensing.components.approvals.models import Approval
#from mooringlicensing.components.compliances.models import Compliance
##from mooringlicensing.components.bookings.models import ApplicationFee, Booking
#from ledger.payments.models import Invoice
#from mooringlicensing.components.proposals import email as proposal_email
#from mooringlicensing.components.approvals import email as approval_email
#from mooringlicensing.components.compliances import email as compliance_email
#from mooringlicensing.components.bookings import email as booking_email
#def test_proposal_emails(request):
#    """ Script to test all emails (listed below) from the models """
#    # setup
#    if not (settings.PRODUCTION_EMAIL):
#        recipients = [request.user.email]
#        #proposal = Proposal.objects.last()
#        approval = Approval.objects.filter(migrated=False).last()
#        proposal = approval.current_proposal
#        referral = Referral.objects.last()
#        amendment_request = AmendmentRequest.objects.last()
#        reason = 'Not enough information'
#        proposal_decline = ProposalDeclinedDetails.objects.last()
#        compliance = Compliance.objects.last()
#
#        application_fee = ApplicationFee.objects.last()
#        api = Invoice.objects.get(reference=application_fee.application_fee_invoices.last().invoice_reference)
#
#        booking = Booking.objects.last()
#        bi = Invoice.objects.get(reference=booking.invoices.last().invoice_reference)
#
#        proposal_email.send_qaofficer_email_notification(proposal, recipients, request, reminder=False)
#        proposal_email.send_qaofficer_complete_email_notification(proposal, recipients, request, reminder=False)
#        proposal_email.send_referral_email_notification(referral,recipients,request,reminder=False)
#        proposal_email.send_referral_complete_email_notification(referral,request)
#        proposal_email.send_amendment_email_notification(amendment_request, request, proposal)
#        proposal_email.send_submit_email_notification(request, proposal)
#        proposal_email.send_external_submit_email_notification(request, proposal)
#        proposal_email.send_approver_decline_email_notification(reason, request, proposal)
#        proposal_email.send_approver_approve_email_notification(request, proposal)
#        proposal_email.send_proposal_decline_email_notification(proposal,request,proposal_decline)
#        proposal_email.send_proposal_approver_sendback_email_notification(request, proposal)
#        proposal_email.send_proposal_approval_email_notification(proposal,request)
#
#        approval_email.send_approval_expire_email_notification(approval)
#        approval_email.send_approval_cancel_email_notification(approval)
#        approval_email.send_approval_suspend_email_notification(approval, request)
#        approval_email.send_approval_surrender_email_notification(approval, request)
#        approval_email.send_approval_renewal_email_notification(approval)
#        approval_email.send_approval_reinstate_email_notification(approval, request)
#
#        compliance_email.send_amendment_email_notification(amendment_request, request, compliance, is_test=True)
#        compliance_email.send_reminder_email_notification(compliance, is_test=True)
#        compliance_email.send_internal_reminder_email_notification(compliance, is_test=True)
#        compliance_email.send_due_email_notification(compliance, is_test=True)
#        compliance_email.send_internal_due_email_notification(compliance, is_test=True)
#        compliance_email.send_compliance_accept_email_notification(compliance,request, is_test=True)
#        compliance_email.send_external_submit_email_notification(request, compliance, is_test=True)
#        compliance_email.send_submit_email_notification(request, compliance, is_test=True)
#
#
#        booking_email.send_application_fee_invoice_tclass_email_notification(request, proposal, api, recipients, is_test=True)
#        booking_email.send_application_fee_confirmation_tclass_email_notification(request, application_fee, api, recipients, is_test=True)
#        booking_email.send_invoice_tclass_email_notification(request.user, booking, bi, recipients, is_test=True)
#        booking_email.send_confirmation_tclass_email_notification(request.user, booking, bi, recipients, is_test=True)

