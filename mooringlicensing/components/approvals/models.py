from __future__ import unicode_literals

import json
import datetime
import logging

import pytz
from django.db import models,transaction
from django.dispatch import receiver
from django.db.models.signals import pre_delete
from django.utils.encoding import python_2_unicode_compatible
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.contrib.postgres.fields.jsonb import JSONField
from django.utils import timezone
from django.contrib.sites.models import Site
from django.conf import settings
from django.db.models import Q
from ledger.settings_base import TIME_ZONE
from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase
from ledger.accounts.models import Organisation as ledger_organisation
from ledger.accounts.models import EmailUser, RevisionedMixin
from ledger.licence.models import  Licence
from mooringlicensing import exceptions
from mooringlicensing.components.approvals.pdf import create_dcv_permit_document, create_dcv_admission_document, \
    create_approval_doc
from mooringlicensing.components.organisations.models import Organisation
from mooringlicensing.components.payments_ml.models import FeeSeason
from mooringlicensing.components.proposals.models import Proposal, ProposalUserAction, MooringBay, Mooring
from mooringlicensing.components.main.models import CommunicationsLogEntry, UserAction, Document#, ApplicationType
from mooringlicensing.components.approvals.email import (
    send_approval_expire_email_notification,
    send_approval_cancel_email_notification,
    send_approval_suspend_email_notification,
    send_approval_reinstate_email_notification,
    send_approval_surrender_email_notification
)
#from mooringlicensing.utils import search_keys, search_multiple_keys
from mooringlicensing.helpers import is_customer
#from mooringlicensing.components.approvals.email import send_referral_email_notification
from mooringlicensing.settings import PROPOSAL_TYPE_RENEWAL, PROPOSAL_TYPE_AMENDMENT


logger = logging.getLogger('log')


def update_waiting_list_offer_doc_filename(instance, filename):
    return '{}/proposals/{}/approvals/{}/waiting_list_offer/{}'.format(settings.MEDIA_APP_DIR, instance.approval.current_proposal.id, instance.id, filename)

def update_approval_doc_filename(instance, filename):
    return '{}/proposals/{}/approvals/{}'.format(settings.MEDIA_APP_DIR, instance.approval.current_proposal.id,filename)

def update_approval_comms_log_filename(instance, filename):
    return '{}/proposals/{}/approvals/communications/{}'.format(settings.MEDIA_APP_DIR, instance.log_entry.approval.current_proposal.id,filename)


class WaitingListOfferDocument(Document):
    approval = models.ForeignKey('Approval',related_name='waiting_list_offer_documents')
    _file = models.FileField(max_length=512)
    input_name = models.CharField(max_length=255,null=True,blank=True)
    can_delete = models.BooleanField(default=True) # after initial submit prevent document from being deleted
    can_hide= models.BooleanField(default=False) # after initial submit, document cannot be deleted but can be hidden
    hidden=models.BooleanField(default=False) # after initial submit prevent document from being deleted

    class Meta:
        app_label = 'mooringlicensing'
        verbose_name = "Waiting List Offer Documents"


class ApprovalDocument(Document):
    approval = models.ForeignKey('Approval',related_name='documents')
    _file = models.FileField(upload_to=update_approval_doc_filename, max_length=512)
    can_delete = models.BooleanField(default=True) # after initial submit prevent document from being deleted

    def delete(self):
        if self.can_delete:
            return super(ApprovalDocument, self).delete()
        logger.info('Cannot delete existing document object after Application has been submitted (including document submitted before Application pushback to status Draft): {}'.format(self.name))

    class Meta:
        app_label = 'mooringlicensing'


class Approval(RevisionedMixin):
    APPROVAL_STATUS_CURRENT = 'current'
    APPROVAL_STATUS_EXPIRED = 'expired'
    APPROVAL_STATUS_CANCELLED = 'cancelled'
    APPROVAL_STATUS_SURRENDERED = 'surrendered'
    APPROVAL_STATUS_SUSPENDED = 'suspended'
    APPROVAL_STATUS_EXTENDED = 'extended'
    APPROVAL_STATUS_AWAITING_PAYMENT = 'awaiting_payment'

    STATUS_CHOICES = (
        (APPROVAL_STATUS_CURRENT, 'Current'),
        (APPROVAL_STATUS_EXPIRED, 'Expired'),
        (APPROVAL_STATUS_CANCELLED, 'Cancelled'),
        (APPROVAL_STATUS_SURRENDERED, 'Surrendered'),
        (APPROVAL_STATUS_SUSPENDED, 'Suspended'),
        (APPROVAL_STATUS_EXTENDED, 'Extended'),
        (APPROVAL_STATUS_AWAITING_PAYMENT, 'Awaiting Payment'),
    )
    lodgement_number = models.CharField(max_length=9, blank=True, default='')
    status = models.CharField(max_length=40, choices=STATUS_CHOICES,
                                       default=STATUS_CHOICES[0][0])
    licence_document = models.ForeignKey(ApprovalDocument, blank=True, null=True, related_name='licence_document')
    cover_letter_document = models.ForeignKey(ApprovalDocument, blank=True, null=True, related_name='cover_letter_document')
    replaced_by = models.OneToOneField('self', blank=True, null=True, related_name='replace')
    #current_proposal = models.ForeignKey(Proposal,related_name = '+')
    current_proposal = models.ForeignKey(Proposal,related_name='approvals', null=True)
#    activity = models.CharField(max_length=255)
#    region = models.CharField(max_length=255)
#    tenure = models.CharField(max_length=255,null=True)
#    title = models.CharField(max_length=255)
    renewal_document = models.ForeignKey(ApprovalDocument, blank=True, null=True, related_name='renewal_document')
    renewal_sent = models.BooleanField(default=False)
    issue_date = models.DateTimeField()
    wla_queue_date = models.DateTimeField(blank=True, null=True)
    original_issue_date = models.DateField(auto_now_add=True)
    start_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    surrender_details = JSONField(blank=True,null=True)
    suspension_details = JSONField(blank=True,null=True)
    submitter = models.ForeignKey(EmailUser, on_delete=models.PROTECT, blank=True, null=True, related_name='mooringlicensing_approvals')
    org_applicant = models.ForeignKey(Organisation,on_delete=models.PROTECT, blank=True, null=True, related_name='org_approvals')
    proxy_applicant = models.ForeignKey(EmailUser,on_delete=models.PROTECT, blank=True, null=True, related_name='proxy_approvals')
    extracted_fields = JSONField(blank=True, null=True)
    cancellation_details = models.TextField(blank=True)
    extend_details = models.TextField(blank=True)
    cancellation_date = models.DateField(blank=True, null=True)
    set_to_cancel = models.BooleanField(default=False)
    set_to_suspend = models.BooleanField(default=False)
    set_to_surrender = models.BooleanField(default=False)

    #application_type = models.ForeignKey(ApplicationType, null=True, blank=True)
    renewal_count = models.PositiveSmallIntegerField('Number of times an Approval has been renewed', default=0)
    migrated=models.BooleanField(default=False)
    #for eclass licence as it can be extended/ renewed once
    extended = models.BooleanField(default=False)
    expiry_notice_sent = models.BooleanField(default=False)
    # for cron job
    exported = models.BooleanField(default=False) # must be False after every add/edit
    ria_selected_mooring = models.ForeignKey(Mooring, null=True, blank=True, on_delete=models.SET_NULL)
    ria_selected_mooring_bay = models.ForeignKey(MooringBay, null=True, blank=True, on_delete=models.SET_NULL)
    wla_order = models.PositiveIntegerField(help_text='wla order per mooring bay', null=True)

    class Meta:
        app_label = 'mooringlicensing'
        unique_together = ('lodgement_number', 'issue_date')
        ordering = ['-id',]

    def set_wla_order(self):
        # set wla order per bay
        place = 1
        if type(self.child_obj) == WaitingListAllocation and self.wla_queue_date:
        #if self.child_obj.code == 'wla' and self.approval.wla_queue_date:
            for w in WaitingListAllocation.objects.filter(
                    wla_queue_date__isnull=False, current_proposal__preferred_bay=self.current_proposal.preferred_bay).order_by(
                            '-wla_queue_date'):
                w.wla_order = place
                w.save()
                place += 1
                #if w == obj.child_obj:
                    #break
        self.refresh_from_db()
        return self

    @property
    def bpay_allowed(self):
        if self.org_applicant:
            return self.org_applicant.bpay_allowed
        return False

    @property
    def monthly_invoicing_allowed(self):
        if self.org_applicant:
            return self.org_applicant.monthly_invoicing_allowed
        return False

    @property
    def monthly_invoicing_period(self):
        if self.org_applicant:
            return self.org_applicant.monthly_invoicing_period
        return None

    @property
    def monthly_payment_due_period(self):
        if self.org_applicant:
            return self.org_applicant.monthly_payment_due_period
        return None

    @property
    def applicant(self):
        if self.org_applicant:
            return self.org_applicant.organisation.name
        elif self.proxy_applicant:
            return "{} {}".format(
                self.proxy_applicant.first_name,
                self.proxy_applicant.last_name)
        else:
            #return None
            try:
                return "{} {}".format(
                    self.submitter.first_name,
                    self.submitter.last_name)
            except:
                return "Applicant Not Set"

    @property
    def linked_applications(self):
        ids = Proposal.objects.filter(approval__lodgement_number=self.lodgement_number).values_list('id', flat=True)
        all_linked_ids = Proposal.objects.filter(Q(previous_application__in=ids) | Q(id__in=ids)).values_list('lodgement_number', flat=True)
        return all_linked_ids

    @property
    def applicant_type(self):
        if self.org_applicant:
            return "org_applicant"
        elif self.proxy_applicant:
            return "proxy_applicant"
        else:
            #return None
            return "submitter"

    @property
    def is_org_applicant(self):
        return True if self.org_applicant else False

    @property
    def applicant_id(self):
        if self.org_applicant:
            #return self.org_applicant.organisation.id
            return self.org_applicant.id
        elif self.proxy_applicant:
            return self.proxy_applicant.id
        else:
            #return None
            return self.submitter.id

    @property
    def title(self):
        return self.current_proposal.title

    @property
    def next_id(self):
        #ids = map(int,[(i.lodgement_number.split('A')[1]) for i in Approval.objects.all()])
        ids = map(int, [i.split('L')[1] for i in Approval.objects.all().values_list('lodgement_number', flat=True) if i])
        ids = list(ids)
        return max(ids) + 1 if len(ids) else 1

    def save(self, *args, **kwargs):
        if self.lodgement_number in ['', None]:
            self.lodgement_number = 'L{0:06d}'.format(self.next_id)
            #self.save()
        super(Approval, self).save(*args,**kwargs)
        self.child_obj.refresh_from_db()

    def __str__(self):
        return self.lodgement_number

    @property
    def reference(self):
        return 'L{}'.format(self.id)

    @property
    def can_reissue(self):
        return self.status == 'current' or self.status == 'suspended'

    @property
    def can_reinstate(self):
        return (self.status == 'cancelled' or self.status == 'suspended' or self.status == 'surrendered') and self.can_action

    @property
    def allowed_assessors(self):
        return self.current_proposal.allowed_assessors


    def is_assessor(self,user):
        return self.current_proposal.is_assessor(user)


    def is_approver(self,user):
        return self.current_proposal.is_approver(user)


    @property
    def is_issued(self):
        return self.licence_number is not None and len(self.licence_number) > 0

    @property
    def can_action(self):
        if not (self.set_to_cancel or self.set_to_suspend or self.set_to_surrender):
                return True
        else:
            return False



    @property
    def can_renew(self):
        try:
#            if self.current_proposal.application_type.name == 'E Class':
#                #return (self.current_proposal.application_type.max_renewals is not None and self.current_proposal.application_type.max_renewals > self.renewal_count)
#                return self.current_proposal.application_type.max_renewals > self.renewal_count
#                #pass
#            else:
            renew_conditions = {
                'previous_application': self.current_proposal,
                'proposal_type': PROPOSAL_TYPE_RENEWAL,
            }
            proposal=Proposal.objects.get(**renew_conditions)
            if proposal:
                return False
        except Proposal.DoesNotExist:
            return True

    @property
    def can_amend(self):
        try:
            amend_conditions = {
                    'previous_application': self.current_proposal,
                    'proposal_type': PROPOSAL_TYPE_AMENDMENT,
                    }
            proposal=Proposal.objects.get(**amend_conditions)
            if proposal:
                return False
        except Proposal.DoesNotExist:
            if self.current_proposal.is_lawful_authority:
                if self.current_proposal.is_lawful_authority_finalised and self.can_renew:
                        return True
                else:
                        return False
            else:
                if self.can_renew:
                    return True
                else:
                    return False
        return False

    def generate_doc(self, user, preview=False):
        # copied_to_permit = self.copiedToPermit_fields(self.current_proposal)  #Get data related to isCopiedToPermit tag

        if preview:
            from mooringlicensing.doctopdf import create_approval_doc_bytes
            # return create_approval_doc_bytes(self, self.current_proposal, copied_to_permit, user)
            # return create_approval_doc_bytes(self, self.current_proposal, None, user)
            return create_approval_doc_bytes(self)

        # self.licence_document = create_approval_doc(self, self.current_proposal, copied_to_permit, user)
        self.licence_document = create_approval_doc(self, self.current_proposal, None, user)
        self.save(version_comment='Created Approval PDF: {}'.format(self.licence_document.name))
        self.current_proposal.save(version_comment='Created Approval PDF: {}'.format(self.licence_document.name))

#    def generate_preview_doc(self, user):
#        from mooringlicensing.components.approvals.pdf import create_approval_pdf_bytes
#        copied_to_permit = self.copiedToPermit_fields(self.current_proposal) #Get data related to isCopiedToPermit tag

    def generate_renewal_doc(self):
        from mooringlicensing.components.approvals.pdf import create_renewal_doc
        self.renewal_document = create_renewal_doc(self,self.current_proposal)
        self.save(version_comment='Created Approval PDF: {}'.format(self.renewal_document.name))
        self.current_proposal.save(version_comment='Created Approval PDF: {}'.format(self.renewal_document.name))

    #def copiedToPermit_fields(self, proposal):
    #    p=proposal
    #    copied_data = []
    #    search_assessor_data = []
    #    search_schema = search_multiple_keys(p.schema, primary_search='isCopiedToPermit', search_list=['label', 'name'])
    #    if p.assessor_data:
    #        search_assessor_data=search_keys(p.assessor_data, search_list=['assessor', 'name'])
    #    if search_schema:
    #        for c in search_schema:
    #            try:
    #                if search_assessor_data:
    #                    for d in search_assessor_data:
    #                        if c['name'] == d['name']:
    #                            if d['assessor']:
    #                                #copied_data.append({c['label'], d['assessor']})
    #                                copied_data.append({c['label']:d['assessor']})
    #            except:
    #                raise
    #    return copied_data

    def log_user_action(self, action, request):
       return ApprovalUserAction.log_action(self, action, request.user)

    def expire_approval(self,user):
        with transaction.atomic():
            try:
                today = timezone.localtime(timezone.now()).date()
                if self.status == 'current' and self.expiry_date < today:
                    self.status = 'expired'
                    self.save()
                    send_approval_expire_email_notification(self)
                    proposal = self.current_proposal
                    ApprovalUserAction.log_action(self,ApprovalUserAction.ACTION_EXPIRE_APPROVAL.format(self.id),user)
                    ProposalUserAction.log_action(proposal,ProposalUserAction.ACTION_EXPIRED_APPROVAL_.format(proposal.id),user)
            except:
                raise

    def approval_extend(self,request,details):
        with transaction.atomic():
            try:
                if not request.user in self.allowed_assessors:
                    raise ValidationError('You do not have access to extend this approval')
                if not self.can_extend and self.can_action:
                    raise ValidationError('You cannot extend approval any further')
                self.renewal_count += 1
                self.extend_details = details.get('extend_details')
                self.expiry_date = datetime.date(self.expiry_date.year + self.current_proposal.application_type.max_renewal_period, self.expiry_date.month, self.expiry_date.day)
                today = timezone.now().date()
                if self.expiry_date <= today:
                    if not self.status == 'extended':
                        self.status = 'extended'
                        #send_approval_extend_email_notification(self)
                self.extended=True
                self.save()
                # Log proposal action
                self.log_user_action(ApprovalUserAction.ACTION_EXTEND_APPROVAL.format(self.id),request)
                # Log entry for organisation
                self.current_proposal.log_user_action(ProposalUserAction.ACTION_EXTEND_APPROVAL.format(self.current_proposal.id),request)
            except:
                raise


    def approval_cancellation(self,request,details):
        with transaction.atomic():
            try:
                if not request.user in self.allowed_assessors:
                    raise ValidationError('You do not have access to cancel this approval')
                if not self.can_reissue and self.can_action:
                    raise ValidationError('You cannot cancel approval if it is not current or suspended')
                self.cancellation_date = details.get('cancellation_date').strftime('%Y-%m-%d')
                self.cancellation_details = details.get('cancellation_details')
                cancellation_date = datetime.datetime.strptime(self.cancellation_date,'%Y-%m-%d')
                cancellation_date = cancellation_date.date()
                self.cancellation_date = cancellation_date # test hack
                today = timezone.now().date()
                if cancellation_date <= today:
                    if not self.status == 'cancelled':
                        self.status = 'cancelled'
                        self.set_to_cancel = False
                        send_approval_cancel_email_notification(self)
                else:
                    self.set_to_cancel = True
                self.save()
                # Log proposal action
                self.log_user_action(ApprovalUserAction.ACTION_CANCEL_APPROVAL.format(self.id),request)
                # Log entry for organisation
                self.current_proposal.log_user_action(ProposalUserAction.ACTION_CANCEL_APPROVAL.format(self.current_proposal.id),request)
            except:
                raise

    def approval_suspension(self,request,details):
        with transaction.atomic():
            try:
                if not request.user in self.allowed_assessors:
                    raise ValidationError('You do not have access to suspend this approval')
                if not self.can_reissue and self.can_action:
                    raise ValidationError('You cannot suspend approval if it is not current or suspended')
                if details.get('to_date'):
                    to_date= details.get('to_date').strftime('%d/%m/%Y')
                else:
                    to_date=''
                self.suspension_details = {
                    'from_date' : details.get('from_date').strftime('%d/%m/%Y'),
                    'to_date' : to_date,
                    'details': details.get('suspension_details'),
                }
                today = timezone.now().date()
                from_date = datetime.datetime.strptime(self.suspension_details['from_date'],'%d/%m/%Y')
                from_date = from_date.date()
                if from_date <= today:
                    if not self.status == 'suspended':
                        self.status = 'suspended'
                        self.set_to_suspend = False
                        self.save()
                        send_approval_suspend_email_notification(self)
                else:
                    self.set_to_suspend = True
                self.save()
                # Log approval action
                self.log_user_action(ApprovalUserAction.ACTION_SUSPEND_APPROVAL.format(self.id),request)
                # Log entry for proposal
                self.current_proposal.log_user_action(ProposalUserAction.ACTION_SUSPEND_APPROVAL.format(self.current_proposal.id),request)
            except:
                raise

    def reinstate_approval(self,request):
        with transaction.atomic():
            try:
                if not request.user in self.allowed_assessors:
                    raise ValidationError('You do not have access to reinstate this approval')
                if not self.can_reinstate:
                #if not self.status == 'suspended':
                    raise ValidationError('You cannot reinstate approval at this stage')
                today = timezone.now().date()
                if not self.can_reinstate and self.expiry_date>= today:
                #if not self.status == 'suspended' and self.expiry_date >= today:
                    raise ValidationError('You cannot reinstate approval at this stage')
                if self.status == 'cancelled':
                    self.cancellation_details =  ''
                    self.cancellation_date = None
                if self.status == 'surrendered':
                    self.surrender_details = {}
                if self.status == 'suspended':
                    self.suspension_details = {}

                self.status = 'current'
                #self.suspension_details = {}
                self.save()
                send_approval_reinstate_email_notification(self, request)
                # Log approval action
                self.log_user_action(ApprovalUserAction.ACTION_REINSTATE_APPROVAL.format(self.id),request)
                # Log entry for proposal
                self.current_proposal.log_user_action(ProposalUserAction.ACTION_REINSTATE_APPROVAL.format(self.current_proposal.id),request)
            except:
                raise

    def approval_surrender(self,request,details):
        with transaction.atomic():
            try:
                if not request.user.mooringlicensing_organisations.filter(organisation_id = self.applicant_id):
                    if request.user not in self.allowed_assessors and not is_customer(request):
                        raise ValidationError('You do not have access to surrender this approval')
                if not self.can_reissue and self.can_action:
                    raise ValidationError('You cannot surrender approval if it is not current or suspended')
                self.surrender_details = {
                    'surrender_date' : details.get('surrender_date').strftime('%d/%m/%Y'),
                    'details': details.get('surrender_details'),
                }
                today = timezone.now().date()
                surrender_date = datetime.datetime.strptime(self.surrender_details['surrender_date'],'%d/%m/%Y')
                surrender_date = surrender_date.date()
                if surrender_date <= today:
                    if not self.status == 'surrendered':
                        self.status = 'surrendered'
                        self.set_to_surrender = False
                        self.save()
                        send_approval_surrender_email_notification(self)
                else:
                    self.set_to_surrender = True
                self.save()
                # Log approval action
                self.log_user_action(ApprovalUserAction.ACTION_SURRENDER_APPROVAL.format(self.id),request)
                # Log entry for proposal
                self.current_proposal.log_user_action(ProposalUserAction.ACTION_SURRENDER_APPROVAL.format(self.current_proposal.id),request)
            except:
                raise

    # required to clean db of approvals with no child objs
    @property
    def no_child_obj(self):
        no_child_obj = True
        if hasattr(self, 'waitinglistallocation'):
            no_child_obj = False
        elif hasattr(self, 'annualadmissionpermit'):
            no_child_obj = False
        elif hasattr(self, 'authoriseduserpermit'):
            no_child_obj = False
        elif hasattr(self, 'mooringlicence'):
            no_child_obj = False
        return no_child_obj

    @property
    def child_obj(self):
        if hasattr(self, 'waitinglistallocation'):
            return self.waitinglistallocation
        elif hasattr(self, 'annualadmissionpermit'):
            return self.annualadmissionpermit
        elif hasattr(self, 'authoriseduserpermit'):
            return self.authoriseduserpermit
        elif hasattr(self, 'mooringlicence'):
            return self.mooringlicence
        else:
            raise ObjectDoesNotExist("Approval must have an associated child object - WLA, AAP, AUP or ML")

    @classmethod
    def approval_types_dict(cls, include_codes=[]):
        type_list = []
        for approval_type in Approval.__subclasses__():
            if hasattr(approval_type, 'code'):
                if approval_type.code in include_codes:
                    type_list.append({
                        "code": approval_type.code,
                        "description": approval_type.description,
                    })

        return type_list


class WaitingListAllocation(Approval):
    approval = models.OneToOneField(Approval, parent_link=True)
    code = 'wla'
    prefix = 'WLA'
    description = 'Waiting List Allocation'

    class Meta:
        app_label = 'mooringlicensing'

    def save(self, *args, **kwargs):
        super(WaitingListAllocation, self).save(*args, **kwargs)
        self.approval.refresh_from_db()


class AnnualAdmissionPermit(Approval):
    approval = models.OneToOneField(Approval, parent_link=True)
    code = 'aap'
    prefix = 'AAP'
    description = 'Annual Admission Permit'

    class Meta:
        app_label = 'mooringlicensing'

    def save(self, *args, **kwargs):
        super(AnnualAdmissionPermit, self).save(*args, **kwargs)
        self.approval.refresh_from_db()


class AuthorisedUserPermit(Approval):
    approval = models.OneToOneField(Approval, parent_link=True)
    code = 'aup'
    prefix = 'AUP'
    description = 'Authorised User Permit'

    endorsed_by = models.ForeignKey(EmailUser, blank=True, null=True)

    class Meta:
        app_label = 'mooringlicensing'

    def save(self, *args, **kwargs):
        super(AuthorisedUserPermit, self).save(*args, **kwargs)
        self.approval.refresh_from_db()


class MooringLicence(Approval):
    approval = models.OneToOneField(Approval, parent_link=True)
    code = 'ml'
    prefix = 'ML'
    description = 'Mooring Licence'

    class Meta:
        app_label = 'mooringlicensing'

    def save(self, *args, **kwargs):
        super(MooringLicence, self).save(*args, **kwargs)
        self.approval.refresh_from_db()


class PreviewTempApproval(Approval):
    class Meta:
        app_label = 'mooringlicensing'
        #unique_together= ('lodgement_number', 'issue_date')


class ApprovalLogEntry(CommunicationsLogEntry):
    approval = models.ForeignKey(Approval, related_name='comms_logs')

    class Meta:
        app_label = 'mooringlicensing'

    def save(self, **kwargs):
        # save the application reference if the reference not provided
        if not self.reference:
            self.reference = self.approval.id
        super(ApprovalLogEntry, self).save(**kwargs)

class ApprovalLogDocument(Document):
    log_entry = models.ForeignKey('ApprovalLogEntry',related_name='documents', null=True,)
    _file = models.FileField(upload_to=update_approval_comms_log_filename, null=True, max_length=512)

    class Meta:
        app_label = 'mooringlicensing'

class ApprovalUserAction(UserAction):
    ACTION_CREATE_APPROVAL = "Create licence {}"
    ACTION_UPDATE_APPROVAL = "Create licence {}"
    ACTION_EXPIRE_APPROVAL = "Expire licence {}"
    ACTION_CANCEL_APPROVAL = "Cancel licence {}"
    ACTION_EXTEND_APPROVAL = "Extend licence {}"
    ACTION_SUSPEND_APPROVAL = "Suspend licence {}"
    ACTION_REINSTATE_APPROVAL = "Reinstate licence {}"
    ACTION_SURRENDER_APPROVAL = "surrender licence {}"
    ACTION_RENEW_APPROVAL = "Create renewal Application for licence {}"
    ACTION_AMEND_APPROVAL = "Create amendment Application for licence {}"


    class Meta:
        app_label = 'mooringlicensing'
        ordering = ('-when',)

    @classmethod
    def log_action(cls, approval, action, user):
        return cls.objects.create(
            approval=approval,
            who=user,
            what=str(action)
        )

    approval= models.ForeignKey(Approval, related_name='action_logs')


class DcvOrganisation(models.Model):
    name = models.CharField(max_length=128, null=True, blank=True)
    abn = models.CharField(max_length=50, null=True, blank=True, verbose_name='ABN', unique=True)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'mooringlicensing'


class DcvVessel(models.Model):
    rego_no = models.CharField(max_length=200, unique=True, blank=True, null=True)
    uvi_vessel_identifier = models.CharField(max_length=10, unique=True, blank=True, null=True)
    vessel_name = models.CharField(max_length=400, blank=True)
    dcv_organisation = models.ForeignKey(DcvOrganisation, blank=True, null=True)

    def __str__(self):
        return self.uvi_vessel_identifier

    class Meta:
        app_label = 'mooringlicensing'


class DcvAdmission(RevisionedMixin):
    LODGEMENT_NUMBER_PREFIX = 'DCV'

    submitter = models.ForeignKey(EmailUser, blank=True, null=True, related_name='dcv_admissions')
    lodgement_number = models.CharField(max_length=10, blank=True, default='')
    lodgement_datetime = models.DateTimeField(blank=True, null=True)  # This is the datetime when payment
    skipper = models.CharField(max_length=50, blank=True, null=True)
    contact_number = models.CharField(max_length=50, blank=True, null=True)
    dcv_vessel = models.ForeignKey(DcvVessel, blank=True, null=True, related_name='dcv_admissions')

    class Meta:
        app_label = 'mooringlicensing'

    def __str__(self):
        return self.lodgement_number

    @classmethod
    def get_next_id(cls):
        ids = map(int, [i.split(cls.LODGEMENT_NUMBER_PREFIX)[1] for i in cls.objects.all().values_list('lodgement_number', flat=True) if i])
        ids = list(ids)
        return max(ids) + 1 if len(ids) else 1

    def save(self, **kwargs):
        if self.lodgement_number in ['', None]:
            self.lodgement_number = self.LODGEMENT_NUMBER_PREFIX + '{0:06d}'.format(self.get_next_id())
        super(DcvAdmission, self).save(**kwargs)

    def generate_dcv_admission_doc(self):
        permit_document = create_dcv_admission_document(self)


class DcvAdmissionArrival(RevisionedMixin):
    dcv_admission = models.ForeignKey(DcvAdmission, null=True, blank=True, related_name='dcv_admission_arrivals')
    arrival_date = models.DateField(null=True, blank=True)
    private_visit = models.BooleanField(default=False)
    fee_season = models.ForeignKey('FeeSeason', null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)  # This is the season.start_date when payment
    end_date = models.DateField(null=True, blank=True)  # This is the season.end_date when payment
    fee_constructor = models.ForeignKey('FeeConstructor', on_delete=models.PROTECT, blank=True, null=True, related_name='dcv_admission_arrivals')

    class Meta:
        app_label = 'mooringlicensing'

    def __str__(self):
        return '{} ({})'.format(self.dcv_admission, self.arrival_date)


class AgeGroup(models.Model):
    AGE_GROUP_ADULT = 'adult'
    AGE_GROUP_CHILD = 'child'

    NAME_CHOICES = (
        (AGE_GROUP_ADULT, 'Adult'),
        (AGE_GROUP_CHILD, 'Child'),
    )
    code = models.CharField(max_length=40, choices=NAME_CHOICES, default=NAME_CHOICES[0][0])

    def __str__(self):
        for item in self.NAME_CHOICES:
            if self.code == item[0]:
                return item[1]
        return ''

    class Meta:
        app_label = 'mooringlicensing'


class AdmissionType(models.Model):
    ADMISSION_TYPE_LANDING = 'landing'
    ADMISSION_TYPE_EXTENDED_STAY = 'extended_stay'
    ADMISSION_TYPE_NOT_LANDING = 'not_landing'
    ADMISSION_TYPE_APPROVED_EVENTS = 'approved_events'

    TYPE_CHOICES = (
        (ADMISSION_TYPE_LANDING, 'Landing'),
        (ADMISSION_TYPE_EXTENDED_STAY, 'Extended stay'),
        (ADMISSION_TYPE_NOT_LANDING, 'Not landing'),
        (ADMISSION_TYPE_APPROVED_EVENTS, 'Approved events'),
    )
    code = models.CharField(max_length=40, choices=TYPE_CHOICES, default=TYPE_CHOICES[0][0])

    def __str__(self):
        for item in self.TYPE_CHOICES:
            if self.code == item[0]:
                return item[1]
        return ''

    class Meta:
        app_label = 'mooringlicensing'


class NumberOfPeople(RevisionedMixin):
    number = models.PositiveSmallIntegerField(null=True, blank=True, default=0)
    dcv_admission_arrival = models.ForeignKey(DcvAdmissionArrival, null=True, blank=True)
    age_group = models.ForeignKey(AgeGroup, null=True, blank=True)
    admission_type = models.ForeignKey(AdmissionType, null=True, blank=True)

    class Meta:
        app_label = 'mooringlicensing'

    def __str__(self):
        return '{} ({}, {}, {})'.format(self.number, self.dcv_admission_arrival, self.age_group, self.admission_type)


class DcvPermit(RevisionedMixin):
    DCV_PERMIT_STATUS_CURRENT = 'current'
    DCV_PERMIT_STATUS_EXPIRED = 'expired'
    STATUS_CHOICES = (
        (DCV_PERMIT_STATUS_CURRENT, 'Current'),
        (DCV_PERMIT_STATUS_EXPIRED, 'Expired'),
    )
    LODGEMENT_NUMBER_PREFIX = 'DCVP'

    submitter = models.ForeignKey(EmailUser, blank=True, null=True, related_name='dcv_permits')
    lodgement_number = models.CharField(max_length=10, blank=True, default='')
    lodgement_datetime = models.DateTimeField(blank=True, null=True)  # This is the datetime when payment
    fee_season = models.ForeignKey('FeeSeason', null=True, blank=True, related_name='dcv_permits')
    start_date = models.DateField(null=True, blank=True)  # This is the season.start_date when payment
    end_date = models.DateField(null=True, blank=True)  # This is the season.end_date when payment
    dcv_vessel = models.ForeignKey(DcvVessel, blank=True, null=True, related_name='dcv_permits')
    dcv_organisation = models.ForeignKey(DcvOrganisation, blank=True, null=True)

    @classmethod
    def get_next_id(cls):
        ids = map(int, [i.split(cls.LODGEMENT_NUMBER_PREFIX)[1] for i in cls.objects.all().values_list('lodgement_number', flat=True) if i])
        ids = list(ids)
        return max(ids) + 1 if len(ids) else 1

    @property
    def status(self, target_date=datetime.datetime.now(pytz.timezone(TIME_ZONE)).date()):
        if self.start_date:
            if self.start_date <= target_date <= self.end_date:
                return self.STATUS_CHOICES[0]
            else:
                return self.STATUS_CHOICES[1]
        else:
            return None

    def save(self, **kwargs):
        if self.lodgement_number in ['', None]:
            self.lodgement_number = self.LODGEMENT_NUMBER_PREFIX + '{0:06d}'.format(self.get_next_id())
        super(DcvPermit, self).save(**kwargs)

    def generate_dcv_permit_doc(self):
        # self.licence_document = create_approval_document(self, proposal, copied_to_permit, request_user)
        # self.save(version_comment='Created Approval PDF: {}'.format(self.licence_document.name))
        permit_document = create_dcv_permit_document(self)
        # self.save()

    class Meta:
        app_label = 'mooringlicensing'


def update_dcv_admission_doc_filename(instance, filename):
    return '{}/dcv_admissions/{}/admissions/{}'.format(settings.MEDIA_APP_DIR, instance.id, filename)


def update_dcv_permit_doc_filename(instance, filename):
    return '{}/dcv_permits/{}/permits/{}'.format(settings.MEDIA_APP_DIR, instance.id, filename)


class DcvAdmissionDocument(Document):
    dcv_admission = models.ForeignKey(DcvAdmission, related_name='admissions')
    _file = models.FileField(upload_to=update_dcv_admission_doc_filename, max_length=512)
    can_delete = models.BooleanField(default=False)  # after initial submit prevent document from being deleted

    def delete(self, using=None, keep_parents=False):
        if self.can_delete:
            return super(DcvAdmissionDocument, self).delete(using, keep_parents)
        logger.info('Cannot delete existing document object after Application has been submitted : {}'.format(self.name))

    class Meta:
        app_label = 'mooringlicensing'


class DcvPermitDocument(Document):
    dcv_permit = models.ForeignKey(DcvPermit, related_name='permits')
    _file = models.FileField(upload_to=update_dcv_permit_doc_filename, max_length=512)
    can_delete = models.BooleanField(default=False)  # after initial submit prevent document from being deleted

    def delete(self, using=None, keep_parents=False):
        if self.can_delete:
            return super(DcvPermitDocument, self).delete(using, keep_parents)
        logger.info('Cannot delete existing document object after Application has been submitted : {}'.format(self.name))

    class Meta:
        app_label = 'mooringlicensing'


@receiver(pre_delete, sender=Approval)
def delete_documents(sender, instance, *args, **kwargs):
    for document in instance.documents.all():
        try:
            document.delete()
        except:
            pass


#import reversion
#reversion.register(Approval, follow=['compliances', 'documents', 'comms_logs', 'action_logs'])
#reversion.register(ApprovalDocument, follow=['licence_document', 'cover_letter_document', 'renewal_document'])
#reversion.register(ApprovalLogEntry, follow=['documents'])
#reversion.register(ApprovalLogDocument)
#reversion.register(ApprovalUserAction)
#reversion.register(DistrictApproval)


