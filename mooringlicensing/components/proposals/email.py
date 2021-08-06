import logging
import mimetypes
from urllib.parse import urljoin
from os.path import join

from django.urls import reverse
from ledger.accounts.models import EmailUser

from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.utils.encoding import smart_text
from django.core.urlresolvers import reverse
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from mooringlicensing.components.approvals.email import CreateMooringLicenceApplicationEmail, \
    log_mla_created_proposal_email, _log_approval_email, _log_org_email, \
    _log_user_email
from mooringlicensing.components.emails.emails import TemplateEmailBase
from datetime import datetime, timezone

from mooringlicensing.components.main.models import NumberOfDaysType, NumberOfDaysSetting
from mooringlicensing.settings import CODE_DAYS_BEFORE_PERIOD_MLA, CODE_DAYS_FOR_SUBMIT_DOCUMENTS_MLA

logger = logging.getLogger(__name__)

SYSTEM_NAME = settings.SYSTEM_NAME_SHORT + ' Automated Message'


class ProposalDeclineSendNotificationEmail(TemplateEmailBase):
    subject = 'Your Application has been declined.'
    html_template = 'mooringlicensing/emails/proposals/send_decline_notification.html'
    txt_template = 'mooringlicensing/emails/proposals/send_decline_notification.txt'


# class ProposalApprovalSendNotificationEmail(TemplateEmailBase):
#     subject = '{} - Approved.'.format(settings.DEP_NAME)
#     html_template = 'mooringlicensing/emails/proposals/send_approval_notification.html'
#     txt_template = 'mooringlicensing/emails/proposals/send_approval_notification.txt'


class ProposalAwaitingPaymentApprovalSendNotificationEmail(TemplateEmailBase):
    subject = '{} - Commercial Filming Application - Pending Payment.'.format(settings.DEP_NAME)
    html_template = 'mooringlicensing/emails/proposals/send_awaiting_payment_approval_notification.html'
    txt_template = 'mooringlicensing/emails/proposals/send_awaiting_payment_approval_notification.txt'


# class AmendmentRequestSendNotificationEmail(TemplateEmailBase):
#     subject = '{} - Commercial Operations Incomplete application.'.format(settings.DEP_NAME)
#     html_template = 'mooringlicensing/emails/proposals/send_amendment_notification.html'
#     txt_template = 'mooringlicensing/emails/proposals/send_amendment_notification.txt'


class OtherDocumentsSumittedNotificationEmail(TemplateEmailBase):
    subject = 'Application: {} is ready for assessment.  Other documents have been submitted.'
    html_template = 'mooringlicensing/emails/proposals/send_documents_submitted_for_mla.html'
    txt_template = 'mooringlicensing/emails/proposals/send_documents_submitted_for_mla.txt'

    def __init__(self, proposal):
        self.subject = self.subject.format(proposal.lodgement_number)


# class DocumentsUploadForMooringLicenceApplicationEmail(TemplateEmailBase):
#     subject = 'A new Application has been submitted. (Documents required)'
#     html_template = 'mooringlicensing/emails/proposals/send_documents_upload_for_mla.html'
#     txt_template = 'mooringlicensing/emails/proposals/send_documents_upload_for_mla.txt'


class StickerPrintingBatchEmail(TemplateEmailBase):
    subject = 'Sticker Printing Batch'
    html_template = 'mooringlicensing/emails/proposals/send_endorsement_of_aua.html'
    txt_template = 'mooringlicensing/emails/proposals/send_endorsement_of_aua.txt'


# class ExpireMooringLicenceApplicationEmail(TemplateEmailBase):
#     subject = 'Mooring Licence Application {} has been expired'
#     html_template = 'mooringlicensing/emails/proposals/{}.html'
#     txt_template = 'mooringlicensing/emails/proposals/{}.txt'
#
#     def __init__(self, proposal, reason):
#         from mooringlicensing.components.proposals.models import MooringLicenceApplication
#
#         self.subject = self.subject.format(proposal.lodgement_number)
#         if reason == MooringLicenceApplication.REASON_FOR_EXPIRY_NOT_SUBMITTED:
#             self.html_template = self.html_template.format('send_expire_mooring_licence_application_not_submitted')
#             self.txt_template = self.html_template.format('send_expire_mooring_licence_application_not_submitted')
#         elif reason == MooringLicenceApplication.REASON_FOR_EXPIRY_NO_DOCUMENTS:
#             self.html_template = self.html_template.format('send_expire_mooring_licence_application_no_documents')
#             self.txt_template = self.html_template.format('send_expire_mooring_licence_application_no_documents')
#         else:
#             raise


# class InviteeReminderEmail(TemplateEmailBase):
#     subject = 'Reminder: Submission of Mooring Licence Application {}'
#     html_template = 'mooringlicensing/emails/proposals/send_reminder_submission_of_mla.html'
#     txt_template = 'mooringlicensing/emails/proposals/send_reminder_submission_of_mla.txt'
#
#     def __init__(self, proposal):
#         self.subject = self.subject.format(proposal.lodgement_number)


# class EndorserReminderEmail(TemplateEmailBase):
#     subject = 'Reminder: Endorsement of Authorised user application'
#     html_template = 'mooringlicensing/emails/proposals/send_reminder_endorsement_of_aua.html'
#     txt_template = 'mooringlicensing/emails/proposals/send_reminder_endorsement_of_aua.txt'


class EndorsementOfAuthorisedUserApplicationEmail(TemplateEmailBase):
    subject = 'Endorsement of Authorised user application'
    html_template = 'mooringlicensing/emails/proposals/send_endorsement_of_aua.html'
    txt_template = 'mooringlicensing/emails/proposals/send_endorsement_of_aua.txt'


class PaymentRequiredEmail(TemplateEmailBase):
    subject = 'Payment required for approval of the application: {}'
    html_template = 'mooringlicensing/emails/proposals/payment_required_email.html'
    txt_template = 'mooringlicensing/emails/proposals/payment_required_email.txt'

    def __init__(self, proposal):
        self.subject = self.subject.format(proposal.lodgement_number)


#class SubmitSendNotificationEmail(TemplateEmailBase):
#    subject = 'A new Application has been submitted.'
#    # html_template = 'mooringlicensing/emails/proposals/send_submit_notification.html'
#    html_template = 'mooringlicensing/emails/base_email-rottnest.html'
#    txt_template = 'mooringlicensing/emails/proposals/send_submit_notification.txt'


class ExternalSubmitSendNotificationEmail(TemplateEmailBase):
    subject = '{} - Confirmation - Application submitted.'.format(settings.DEP_NAME)
    html_template = 'mooringlicensing/emails/proposals/send_external_submit_notification.html'
    txt_template = 'mooringlicensing/emails/proposals/send_external_submit_notification.txt'


# class ApproverDeclineSendNotificationEmail(TemplateEmailBase):
#     subject = 'An Application has been recommended for decline.'
#     html_template = 'mooringlicensing/emails/proposals/send_approver_decline_notification.html'
#     txt_template = 'mooringlicensing/emails/proposals/send_approver_decline_notification.txt'


# class ApproverApproveSendNotificationEmail(TemplateEmailBase):
#     subject = 'An Application has been recommended for approval.'
#     html_template = 'mooringlicensing/emails/proposals/send_approver_approve_notification.html'
#     txt_template = 'mooringlicensing/emails/proposals/send_approver_approve_notification.txt'


class ApproverSendBackNotificationEmail(TemplateEmailBase):
    subject = 'An Application has been sent back by approver.'
    html_template = 'mooringlicensing/emails/proposals/send_approver_sendback_notification.html'
    txt_template = 'mooringlicensing/emails/proposals/send_approver_sendback_notification.txt'


def log_proposal_email(msg, proposal, sender):
    try:
        sender_user = sender if isinstance(sender, EmailUser) else EmailUser.objects.get(email__icontains=sender)
    except:
        sender_user = EmailUser.objects.create(email=sender, password='')

    _log_proposal_email(msg, proposal, sender=sender_user)
    if proposal.org_applicant:
        _log_org_email(msg, proposal.org_applicant, proposal.submitter, sender=sender_user)
    else:
        _log_user_email(msg, proposal.submitter, proposal.submitter, sender=sender_user)


def send_other_documents_submitted_notification_email(request, proposal):
    email = OtherDocumentsSumittedNotificationEmail(proposal)

    context = {
        'proposal': proposal,
    }
    to_address = proposal.assessor_recipients
    cc = []
    bcc = []

    attachments = []
    for my_file in proposal.mooring_report_documents.all():
        if my_file._file is not None:
            file_name = my_file._file.name
            mime = mimetypes.guess_type(file_name)[0]
            if mime:
                attachment = (my_file.name, my_file._file.read(), mime)
                attachments.append(attachment)
    for my_file in proposal.written_proof_documents.all():
        if my_file._file is not None:
            file_name = my_file._file.name
            mime = mimetypes.guess_type(file_name)[0]
            if mime:
                attachment = (my_file.name, my_file._file.read(), mime)
                attachments.append(attachment)

    # Send email
    msg = email.send(to_address, context=context, attachments=attachments, cc=cc, bcc=bcc,)

    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    _log_proposal_email(msg, proposal, sender=sender)
    if proposal.org_applicant:
        _log_org_email(msg, proposal.org_applicant, proposal.submitter, sender=sender)
    else:
        _log_user_email(msg, proposal.submitter, proposal.submitter, sender=sender)

    return msg




def send_sticker_printing_batch_email(batches):
    if batches.count() == 0:
        return

    email = StickerPrintingBatchEmail()

    attachments = []
    for batch in batches:
        if batch._file is not None:
            file_name = batch._file.name
            mime = mimetypes.guess_type(file_name)[0]
            if mime:
                attachment = (batch.name, batch._file.read(), mime)
                attachments.append(attachment)

    context = {
        'batches': batches,
    }

    from mooringlicensing.components.proposals.models import StickerPrintingContact
    tos = StickerPrintingContact.objects.filter(type=StickerPrintingContact.TYPE_EMIAL_TO, enabled=True)
    ccs = StickerPrintingContact.objects.filter(type=StickerPrintingContact.TYPE_EMAIL_CC, enabled=True)
    bccs = StickerPrintingContact.objects.filter(type=StickerPrintingContact.TYPE_EMAIL_BCC, enabled=True)

    to_address = [contact.email for contact in tos]
    cc = [contact.email for contact in ccs]
    bcc = [contact.email for contact in bccs]

    # Send email
    # msg = email.send(to_address, context=context, attachments=attachments, cc=cc, bcc=bcc,)
    msg = email.send(to_address, context=context, attachments=attachments, cc=cc, bcc=bcc,)
    sender = settings.DEFAULT_FROM_EMAIL

    # _log_proposal_email(msg, proposal, sender=sender)
    # if proposal.org_applicant:
    #     _log_org_email(msg, proposal.org_applicant, proposal.submitter, sender=sender)
    # else:
    #     _log_user_email(msg, proposal.submitter, proposal.submitter, sender=sender)

    return msg


def send_endorsement_of_authorised_user_application_email(request, proposal):
    email = EndorsementOfAuthorisedUserApplicationEmail()
    # url = request.build_absolute_uri(reverse('internal-proposal-detail', kwargs={'proposal_pk': proposal.id}))
    endorse_url = request.build_absolute_uri(reverse('endorse-url', kwargs={'uuid_str': proposal.child_obj.uuid}))
    decline_url = request.build_absolute_uri(reverse('decline-url', kwargs={'uuid_str': proposal.child_obj.uuid}))
    dashboard_url = request.build_absolute_uri(reverse('external'))

    # Configure recipients, contents, etc
    context = {
        'proposal': proposal,
        'endorse_url': endorse_url,
        'decline_url': decline_url,
        'dashboard_url': dashboard_url,
        'mooring': proposal.mooring,
    }
    to_address = proposal.site_licensee_email
    cc = []
    bcc = []

    # Send email
    msg = email.send(to_address, context=context, attachments=[], cc=cc, bcc=bcc,)
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    log_proposal_email(msg, proposal, sender)

    return msg


def send_emails_for_payment_required(request, proposal, attachments=[]):
    email = PaymentRequiredEmail(proposal)
    # url = request.build_absolute_uri(reverse('internal-proposal-detail', kwargs={'proposal_pk': proposal.id}))
    # if "-internal" not in url:
        # add it. This email is for internal staff (assessors)
        # url = '-internal.{}'.format(settings.SITE_DOMAIN).join(url.split('.' + settings.SITE_DOMAIN))

    # Configure recipients, contents, etc
    context = {
        'proposal': proposal,
        # 'url': url
    }
    to_address = proposal.submitter.email
    cc = proposal.child_obj.approver_recipients
    bcc = []

    # Send email
    msg = email.send(to_address, context=context, attachments=attachments, cc=cc, bcc=bcc,)
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    log_proposal_email(msg, proposal, sender)

    return msg




#def send_external_submit_email_notification(request, proposal):
#    # email = ExternalSubmitSendNotificationEmail()
#    email = TemplateEmailBase(
#        subject='{} - Confirmation - Application submitted.'.format(settings.DEP_NAME),
#        html_template='mooringlicensing/emails/proposals/send_external_submit_notification.html',
#        txt_template='mooringlicensing/emails/proposals/send_external_submit_notification.txt',
#    )
#    url = request.build_absolute_uri(reverse('external-proposal-detail',kwargs={'proposal_pk': proposal.id}))
#
#    if "-internal" in url:
#        # remove '-internal'. This email is for external submitters
#        url = ''.join(url.split('-internal'))
#
#    context = {
#        'proposal': proposal,
#        'submitter': proposal.submitter.get_full_name(),
#        'url': url
#    }
#    all_ccs = []
#    if proposal.org_applicant and proposal.org_applicant.email:
#        cc_list = proposal.org_applicant.email
#        if cc_list:
#            all_ccs = [cc_list]
#
#    msg = email.send(proposal.submitter.email, cc=all_ccs, context=context)
#    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
#    log_proposal_email(msg, proposal, sender)
#    return msg






def send_proposal_decline_email_notification(proposal,request,proposal_decline):
    email = ProposalDeclineSendNotificationEmail()

    context = {
        'proposal': proposal,

    }
    cc_list = proposal_decline.cc_email
    all_ccs = []
    if cc_list:
        all_ccs = cc_list.split(',')
    if proposal.org_applicant and proposal.org_applicant.email:
        all_ccs.append(proposal.org_applicant.email)

    msg = email.send(proposal.submitter.email, bcc= all_ccs, context=context)
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    log_proposal_email(msg, proposal, sender)
    return msg


def send_proposal_approver_sendback_email_notification(request, proposal):
    email = ApproverSendBackNotificationEmail()
    url = request.build_absolute_uri(reverse('internal-proposal-detail',kwargs={'proposal_pk': proposal.id}))

    if 'test-emails' in request.path_info:
        approver_comment = 'This is my test comment'
    else:
        approver_comment = proposal.approver_comment


    context = {
        'proposal': proposal,
        'url': url,
        'approver_comment': approver_comment
    }

    msg = email.send(proposal.assessor_recipients, context=context)
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    log_proposal_email(msg, proposal, sender)
    return msg



def send_proposal_awaiting_payment_approval_email_notification(proposal, request):
    """ Send External Email with attached invoice and URL link to pay by credit card """
    email = ProposalAwaitingPaymentApprovalSendNotificationEmail()

    cc_list = proposal.proposed_issuance_approval.get('cc_email')
    all_ccs = []
    if cc_list:
        all_ccs = cc_list.split(',')

    url = request.build_absolute_uri(reverse('external'))
    #payment_url = request.build_absolute_uri(reverse('existing_invoice_payment', kwargs={'invoice_ref':invoice.reference}))
    if "-internal" in url:
        # remove '-internal'. This email is for external submitters
        url = ''.join(url.split('-internal'))

    filename = 'confirmation.pdf'
    doc = None#create_awaiting_payment_invoice_pdf_bytes(filename, proposal)
    attachment = (filename, doc, 'application/pdf')

    context = {
        'proposal': proposal,
        'url': url,
    }

    msg = email.send(proposal.submitter.email, bcc=all_ccs, attachments=[attachment], context=context)
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    
    filename_appended = '{}_{}.{}'.format('confirmation', datetime.now().strftime('%d%b%Y'), 'pdf')
    log_proposal = _log_proposal_email(msg, proposal, sender=sender, file_bytes=doc, filename=filename_appended)

    if proposal.org_applicant:
        _log_org_email(msg, proposal.org_applicant, proposal.submitter, sender=sender)
    else:
        _log_user_email(msg, proposal.submitter, proposal.submitter, sender=sender)


def _log_proposal_email(email_message, proposal, sender=None, file_bytes=None, filename=None):
    from mooringlicensing.components.proposals.models import ProposalLogEntry
    if isinstance(email_message, (EmailMultiAlternatives, EmailMessage,)):
        # TODO this will log the plain text body, should we log the html instead
        text = email_message.body
        subject = email_message.subject
        fromm = smart_text(sender) if sender else smart_text(email_message.from_email)
        # the to email is normally a list
        if isinstance(email_message.to, list):
            to = ','.join(email_message.to)
        else:
            to = smart_text(email_message.to)
        # we log the cc and bcc in the same cc field of the log entry as a ',' comma separated string
        all_ccs = []
        if email_message.cc:
            all_ccs += list(email_message.cc)
        if email_message.bcc:
            all_ccs += list(email_message.bcc)
        all_ccs = ','.join(all_ccs)

    else:
        text = smart_text(email_message)
        subject = ''
        to = proposal.submitter.email
        fromm = smart_text(sender) if sender else SYSTEM_NAME
        all_ccs = ''

    customer = proposal.submitter

    staff = sender

    kwargs = {
        'subject': subject,
        'text': text,
        'proposal': proposal,
        'customer': customer,
        'staff': staff,
        'to': to,
        'fromm': fromm,
        'cc': all_ccs
    }

    email_entry = ProposalLogEntry.objects.create(**kwargs)

    if file_bytes and filename:
        # attach the file to the comms_log also
        path_to_file = '{}/proposals/{}/communications/{}'.format(settings.MEDIA_APP_DIR, proposal.id, filename)
        path = default_storage.save(path_to_file, ContentFile(file_bytes))
        email_entry.documents.get_or_create(_file=path_to_file, name=filename)

    return email_entry


def _log_org_email(email_message, organisation, customer ,sender=None):
    from mooringlicensing.components.organisations.models import OrganisationLogEntry
    if isinstance(email_message, (EmailMultiAlternatives, EmailMessage,)):
        # TODO this will log the plain text body, should we log the html instead
        text = email_message.body
        subject = email_message.subject
        fromm = smart_text(sender) if sender else smart_text(email_message.from_email)
        # the to email is normally a list
        if isinstance(email_message.to, list):
            to = ','.join(email_message.to)
        else:
            to = smart_text(email_message.to)
        # we log the cc and bcc in the same cc field of the log entry as a ',' comma separated string
        all_ccs = []
        if email_message.cc:
            all_ccs += list(email_message.cc)
        if email_message.bcc:
            all_ccs += list(email_message.bcc)
        all_ccs = ','.join(all_ccs)

    else:
        text = smart_text(email_message)
        subject = ''
        to = customer
        fromm = smart_text(sender) if sender else SYSTEM_NAME
        all_ccs = ''

    customer = customer

    staff = sender

    kwargs = {
        'subject': subject,
        'text': text,
        'organisation': organisation,
        'customer': customer,
        'staff': staff,
        'to': to,
        'fromm': fromm,
        'cc': all_ccs
    }

    email_entry = OrganisationLogEntry.objects.create(**kwargs)

    return email_entry

def _log_user_email(email_message, emailuser, customer ,sender=None):
    from ledger.accounts.models import EmailUserLogEntry
    if isinstance(email_message, (EmailMultiAlternatives, EmailMessage,)):
        # TODO this will log the plain text body, should we log the html instead
        text = email_message.body
        subject = email_message.subject
        fromm = smart_text(sender) if sender else smart_text(email_message.from_email)
        # the to email is normally a list
        if isinstance(email_message.to, list):
            to = ','.join(email_message.to)
        else:
            to = smart_text(email_message.to)
        # we log the cc and bcc in the same cc field of the log entry as a ',' comma separated string
        all_ccs = []
        if email_message.cc:
            all_ccs += list(email_message.cc)
        if email_message.bcc:
            all_ccs += list(email_message.bcc)
        all_ccs = ','.join(all_ccs)

    else:
        text = smart_text(email_message)
        subject = ''
        to = customer
        fromm = smart_text(sender) if sender else SYSTEM_NAME
        all_ccs = ''

    customer = customer

    staff = sender

    kwargs = {
        'subject': subject,
        'text': text,
        'emailuser': emailuser,
        'customer': customer,
        'staff': staff,
        'to': to,
        'fromm': fromm,
        'cc': all_ccs
    }

    email_entry = EmailUserLogEntry.objects.create(**kwargs)

    return email_entry


#####
### After refactoring ###
#####
def get_public_url(request=None):
    if request:
        web_url = request.META.get('HTTP_HOST', None)
    else:
        web_url = settings.SITE_URL if settings.SITE_URL else ''
    return web_url


def send_confirmation_email_upon_submit(request, proposal, payment_made, attachments=[]):
    # 1
    email = TemplateEmailBase(
        subject='Successful submission of application',
        html_template='mooringlicensing/emails/send_confirmation_email_upon_submit.html',
        txt_template='mooringlicensing/emails/send_confirmation_email_upon_submit.txt',
    )

    url = request.build_absolute_uri(reverse('external-proposal-detail', kwargs={'proposal_pk': proposal.id}))
    if "-internal" not in url:
        # add it. This email is for internal staff (assessors)
        url = '-internal.{}'.format(settings.SITE_DOMAIN).join(url.split('.' + settings.SITE_DOMAIN))

    # Configure recipients, contents, etc
    context = {
        'public_url': get_public_url(request),
        'proposal': proposal,
        'payment_made': payment_made,
        'url': url,
    }
    to_address = proposal.submitter.email
    cc = []
    bcc = []

    # Send email
    # in send() method, self.html_template is rendered by context and attached as alternative
    # In other words, self.html_template should be full html-email
    msg = email.send(to_address, context=context, attachments=attachments, cc=cc, bcc=bcc,)
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    log_proposal_email(msg, proposal, sender)

    return msg


def send_notification_email_upon_submit_to_assessor(request, proposal, attachments=[]):
    # 2
    email = TemplateEmailBase(
        subject='A new application has been submitted',
        html_template='mooringlicensing/emails/send_notification_email_upon_submit_to_assessor.html',
        txt_template='mooringlicensing/emails/send_notification_email_upon_submit_to_assessor.txt',
    )

    url = request.build_absolute_uri(reverse('internal-proposal-detail', kwargs={'proposal_pk': proposal.id}))

    context = {
        'public_url': get_public_url(request),
        'proposal': proposal,
        'url': url,
    }
    to_address = proposal.assessor_recipients
    cc = []
    bcc = []

    # Send email
    # in send() method, self.html_template is rendered by context and attached as alternative
    # In other words, self.html_template should be full html-email
    msg = email.send(to_address, context=context, attachments=attachments, cc=cc, bcc=bcc,)
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    log_proposal_email(msg, proposal, sender)

    return msg


def send_approver_approve_email_notification(request, proposal):
    # 3
    email = TemplateEmailBase(
        subject='An application is ready for approval or decline',
        html_template='mooringlicensing/emails/send_approver_approve_notification.html',
        txt_template='mooringlicensing/emails/send_approver_approve_notification.txt',
    )

    url = request.build_absolute_uri(reverse('internal-proposal-detail', kwargs={'proposal_pk': proposal.id}))

    context = {
        'public_url': get_public_url(request),
        'start_date' : proposal.proposed_issuance_approval.get('start_date'),
        'expiry_date' : proposal.proposed_issuance_approval.get('expiry_date'),
        'details': proposal.proposed_issuance_approval.get('details'),
        'proposal': proposal,
        'url': url
    }

    msg = email.send(proposal.approver_recipients, context=context)
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    log_proposal_email(msg, proposal, sender)
    return msg


def send_approver_decline_email_notification(reason, request, proposal):
    # 3
    # email = ApproverDeclineSendNotificationEmail()
    email = TemplateEmailBase(
        subject='An application is ready for approval or decline',
        html_template='mooringlicensing/emails/send_approver_decline_notification.html',
        txt_template='mooringlicensing/emails/send_approver_decline_notification.txt',
    )
    url = request.build_absolute_uri(reverse('internal-proposal-detail', kwargs={'proposal_pk': proposal.id}))
    context = {
        'public_url': get_public_url(request),
        'proposal': proposal,
        'reason': reason,
        'url': url
    }

    msg = email.send(proposal.approver_recipients, context=context)
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    log_proposal_email(msg, proposal, sender)
    return msg


# TODO: #4

def send_amendment_email_notification(amendment_request, request, proposal):
    # 5
    email = TemplateEmailBase(
        subject='An amendment to your application is required',
        html_template='mooringlicensing/emails/send_amendment_notification.html',
        txt_template='mooringlicensing/emails/send_amendment_notification.txt',
    )

    reason = amendment_request.reason.reason
    url = request.build_absolute_uri(reverse('external-proposal-detail', kwargs={'proposal_pk': proposal.id}))

    if "-internal" in url:
        # remove '-internal'. This email is for external submitters
        url = ''.join(url.split('-internal'))

    context = {
        'public_url': get_public_url(request),
        'recipient': proposal.submitter,
        'proposal': proposal,
        'reason': reason,
        'amendment_request_text': amendment_request.text,
        'url': url
    }

    to = proposal.submitter.email
    all_ccs = []
    if proposal.org_applicant and proposal.org_applicant.email:
        cc_list = proposal.org_applicant.email
        if cc_list:
            all_ccs = [cc_list]

    msg = email.send(to, cc=all_ccs, context=context)
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    _log_proposal_email(msg, proposal, sender=sender)
    if proposal.org_applicant:
        _log_org_email(msg, proposal.org_applicant, proposal.submitter, sender=sender)
    else:
        _log_user_email(msg, proposal.submitter, proposal.submitter, sender=sender)


def send_create_mooring_licence_application_email_notification(request, approval):
    # 6
    email = TemplateEmailBase(
        subject='Invitation to apply for a mooring licence',
        html_template='mooringlicensing/emails/create_mooring_licence_application_notification.html',
        txt_template='mooringlicensing/emails/create_mooring_licence_application_notification.txt',
    )

    proposal = approval.current_proposal
    ria_generated_proposal = approval.ria_generated_proposal.all()[0] if approval.ria_generated_proposal.all() else None
    #url=settings.SITE_URL if settings.SITE_URL else ''
    #url += reverse('external')

    url = request.build_absolute_uri(reverse('external-proposal-detail', kwargs={'proposal_pk': proposal.id}))
    if "-internal" in url:
        # remove '-internal'. This email is for external submitters
        url = ''.join(url.split('-internal'))

    today = timezone.localtime(timezone.now()).date()
    days_type = NumberOfDaysType.objects.get(code=CODE_DAYS_BEFORE_PERIOD_MLA)
    days_setting_application_period = NumberOfDaysSetting.get_setting_by_date(days_type, today)
    days_type = NumberOfDaysType.objects.get(code=CODE_DAYS_FOR_SUBMIT_DOCUMENTS_MLA)
    days_setting_documents_period = NumberOfDaysSetting.get_setting_by_date(days_type, today)

    context = {
        'public_url': get_public_url(request),
        'approval': approval,
        'proposal': proposal,
        'recipient': proposal.submitter,
        'application_period': days_setting_application_period.number_of_days,
        'documents_period': days_setting_documents_period.number_of_days,
        'mla_proposal': ria_generated_proposal,
        'url': url,
        'message_details': request.data.get('message_details'),
    }
    sender = settings.DEFAULT_FROM_EMAIL
    try:
        sender_user = EmailUser.objects.get(email__icontains=sender)
    except:
        EmailUser.objects.create(email=sender, password='')
        sender_user = EmailUser.objects.get(email__icontains=sender)

    attachments = []
    if approval.waiting_list_offer_documents.all():
        for doc in approval.waiting_list_offer_documents.all():
            #file_name = doc._file.name
            file_name = doc.name
            attachment = (file_name, doc._file.file.read())
            attachments.append(attachment)

    bcc = request.data.get('cc_email')
    bcc_list = bcc.split(',')
    msg = email.send(proposal.submitter.email, bcc=bcc_list, attachments=attachments, context=context)
    #msg = email.send(proposal.submitter.email, attachments=attachments, context=context)
    sender = settings.DEFAULT_FROM_EMAIL
    #_log_approval_email(msg, approval, sender=sender_user)
    log_mla_created_proposal_email(msg, ria_generated_proposal, sender=sender_user)
    #_log_user_email(msg, approval.submitter, proposal.submitter, sender=sender_user)
    _log_user_email(msg, ria_generated_proposal.submitter, ria_generated_proposal.submitter, sender=sender_user)


def send_documents_upload_for_mooring_licence_application_email(request, proposal):
    # 7
    email = TemplateEmailBase(
        subject='Upload of additional documents for mooring licence application',
        html_template='mooringlicensing/emails/send_documents_upload_for_mla.html',
        txt_template='mooringlicensing/emails/send_documents_upload_for_mla.txt',
    )
    document_upload_url = proposal.get_document_upload_url(request)

    today = timezone.localtime(timezone.now()).date()
    days_type = NumberOfDaysType.objects.get(code=CODE_DAYS_FOR_SUBMIT_DOCUMENTS_MLA)
    days_setting = NumberOfDaysSetting.get_setting_by_date(days_type, today)

    url = request.build_absolute_uri(reverse('external-proposal-detail', kwargs={'proposal_pk': proposal.id}))

    # Configure recipients, contents, etc
    context = {
        'public_url': get_public_url(request),
        'proposal': proposal,
        'documents_upload_url': document_upload_url,
        'url': url,
        'number_of_days': days_setting.number_of_days,
    }
    to_address = proposal.submitter.email
    cc = []
    bcc = []

    # Send email
    msg = email.send(to_address, context=context, attachments=[], cc=cc, bcc=bcc,)

    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    _log_proposal_email(msg, proposal, sender=sender)
    if proposal.org_applicant:
        _log_org_email(msg, proposal.org_applicant, proposal.submitter, sender=sender)
    else:
        _log_user_email(msg, proposal.submitter, proposal.submitter, sender=sender)

    return msg


#  8
#  9
# 10


def send_invitee_reminder_email(proposal, due_date, number_of_days, request=None):
    # 11
    email = TemplateEmailBase(
        subject='Reminder to apply for a mooring licence',
        html_template='mooringlicensing/emails/send_reminder_submission_of_mla.html',
        txt_template='mooringlicensing/emails/send_reminder_submission_of_mla.txt',
    )
    # url = settings.SITE_URL if settings.SITE_URL else ''
    # proposal_url = join(url, 'external', 'proposal', str(proposal.id))
    url = request.build_absolute_uri(reverse('external-proposal-detail', kwargs={'proposal_pk': proposal.id}))

    context = {
        'public_url': get_public_url(request),
        'proposal': proposal,
        'recipient': proposal.submitter,
        'url': url,
        'due_date': due_date,
        'number_of_days': number_of_days,
    }
    to_address = proposal.submitter.email
    cc = []
    bcc = []

    # Send email
    msg = email.send(to_address, context=context, attachments=[], cc=cc, bcc=bcc,)
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    log_proposal_email(msg, proposal, sender)
    return msg


def send_expire_mooring_licence_application_email(proposal, reason, due_date,):
    from mooringlicensing.components.proposals.models import MooringLicenceApplication
    # 12
    # 13
    # Expire mooring licence application if additional documents are not submitted within a configurable number of days
    # from the initial submit of the mooring licence application and email to inform the applicant
    if reason == MooringLicenceApplication.REASON_FOR_EXPIRY_NO_DOCUMENTS:
        html_template='mooringlicensing/emails/send_expire_mooring_licence_application_no_documents.html',
        txt_template='mooringlicensing/emails/send_expire_mooring_licence_application_no_documents.txt',
    elif reason == MooringLicenceApplication.REASON_FOR_EXPIRY_NOT_SUBMITTED:
        html_template='mooringlicensing/emails/send_expire_mooring_licence_application_not_submitted.html',
        txt_template='mooringlicensing/emails/send_expire_mooring_licence_application_not_submitted.txt',
    else:
        # Should not reach here
        return

    email = TemplateEmailBase(
        subject='Your application for a mooring licence',
        html_template=html_template,
        txt_template=txt_template,
    )
    url = settings.SITE_URL if settings.SITE_URL else ''
    dashboard_url = url + reverse('external')

    # Configure recipients, contents, etc
    context = {
        'proposal': proposal,
        'recipient': proposal.submitter,
        'dashboard_url': dashboard_url,
    }
    to_address = proposal.submitter.email
    cc = []
    bcc = []

    # Send email
    msg = email.send(to_address, context=context, attachments=[], cc=cc, bcc=bcc,)
    sender = settings.DEFAULT_FROM_EMAIL
    log_proposal_email(msg, proposal, sender)
    return msg


def send_expire_mla_notification_to_assessor(proposal, reason, due_date):
    # 14
    email = TemplateEmailBase(
        subject='Mooring licence application not submitted on time',
        html_template='mooringlicensing/emails/send_expire_mla_notification_to_assessor.html',
        txt_template='mooringlicensing/emails/send_expire_mla_notification_to_assessor.txt',
    )

    mooring_name = proposal.mooring.name if proposal.mooring else ''

    context = {
        'public_url': get_public_url(),
        'proposal': proposal,
        'applicant': proposal.submitter,
        'due_date': due_date,
        'mooring_name': mooring_name,
    }

    to_address = proposal.assessor_recipients
    cc = []
    bcc = []

    # Send email
    msg = email.send(to_address, context=context, attachments=[], cc=cc, bcc=bcc,)
    sender = settings.DEFAULT_FROM_EMAIL
    log_proposal_email(msg, proposal, sender)
    return msg


def send_endorser_reminder_email(proposal, due_date, request=None):
    # 15
    email = TemplateEmailBase(
        subject='Your endorsement of an Authorised User Permit application is due',
        html_template='mooringlicensing/emails/proposals/send_reminder_endorsement_of_aua.html',
        txt_template='mooringlicensing/emails/proposals/send_reminder_endorsement_of_aua.txt',
    )

    url = settings.SITE_URL if settings.SITE_URL else ''
    endorse_url = url + reverse('endorse-url', kwargs={'uuid_str': proposal.child_obj.uuid})
    decline_url = url + reverse('decline-url', kwargs={'uuid_str': proposal.child_obj.uuid})
    proposal_url = url + reverse('external-proposal-detail', kwargs={'proposal_pk': proposal.id})

    try:
        endorser = EmailUser.objects.get(email=proposal.site_licensee_email)
    except:
        # Should not reach here
        return

    mooring_name = proposal.mooring.name if proposal.mooring else ''

    # Configure recipients, contents, etc
    context = {
        'public_url': get_public_url(request),
        'proposal': proposal,
        'endorser': endorser,
        'applicant': proposal.submitter,
        'endorse_url': endorse_url,
        'decline_url': decline_url,
        'proposal_url': proposal_url,
        'mooring_name': mooring_name,
        'due_date': due_date,
    }
    to_address = proposal.site_licensee_email
    cc = []
    bcc = []

    # Send email
    msg = email.send(to_address, context=context, attachments=[], cc=cc, bcc=bcc,)
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    log_proposal_email(msg, proposal, sender)
    return msg


def send_approval_renewal_email_notification(approval):
    # 16
    email = TemplateEmailBase(
        subject='Renewal notice for your {} {}'.format(approval.description, approval.lodgement_number),
        html_template='mooringlicensing/emails/approval_renewal_notification.html',
        txt_template='mooringlicensing/emails/approval_renewal_notification.txt',
    )
    proposal = approval.current_proposal
    url = settings.SITE_URL if settings.SITE_URL else ''
    dashboard_url = url + reverse('external')

    context = {
        'public_url': get_public_url(),
        'approval': approval,
        'proposal': approval.current_proposal,
        'url': dashboard_url,
        'expiry_date': approval.expiry_date,
    }
    sender = settings.DEFAULT_FROM_EMAIL

    try:
        sender_user = EmailUser.objects.get(email__icontains=sender)
    except:
        EmailUser.objects.create(email=sender, password='')
        sender_user = EmailUser.objects.get(email__icontains=sender)

    #attach renewal notice
    if approval.renewal_document and approval.renewal_document._file is not None:
        renewal_document= approval.renewal_document._file
        file_name = approval.renewal_document.name
        attachment = (file_name, renewal_document.file.read(), 'application/pdf')
        attachment = [attachment]
    else:
        attachment = []
    all_ccs = []
    if proposal.org_applicant and proposal.org_applicant.email:
        cc_list = proposal.org_applicant.email
        if cc_list:
            all_ccs = [cc_list]

    msg = email.send(proposal.submitter.email,cc=all_ccs, attachments=attachment, context=context)
    sender = settings.DEFAULT_FROM_EMAIL
    _log_approval_email(msg, approval, sender=sender_user)
    #_log_org_email(msg, approval.applicant, proposal.submitter, sender=sender_user)
    if approval.org_applicant:
        _log_org_email(msg, approval.org_applicant, proposal.submitter, sender=sender_user)
    else:
        _log_user_email(msg, approval.submitter, proposal.submitter, sender=sender_user)


def send_application_processed_email(proposal, decision, with_payment, request):
    # 17
    from mooringlicensing.components.proposals.models import WaitingListApplication, AnnualAdmissionApplication, AuthorisedUserApplication, MooringLicenceApplication

    if proposal.application_type.code == WaitingListApplication.code:
        send_wla_processed_email(proposal, decision, with_payment, request)
    else:
        html_template = 'mooringlicensing/emails/send_wla_processed.html',
        txt_template = 'mooringlicensing/emails/send_wla_processed.txt',
        if decision == 'approved':
            subject='Your waiting list allocation application {} has been approved'.format(proposal.lodgement_number)
        elif decision == 'declined':
            subject='Your waiting list allocation application {} has been declined'.format(proposal.lodgement_number)

        email = TemplateEmailBase(
            subject=subject,
            html_template=html_template,
            txt_template=txt_template,
        )

        cc_list = proposal.proposed_issuance_approval.get('cc_email')
        all_ccs = []
        if cc_list:
            all_ccs = cc_list.split(',')

        attachments = []
        licence_document= proposal.approval.licence_document._file
        if licence_document is not None:
            file_name = proposal.approval.licence_document.name
            attachment = (file_name, licence_document.file.read(), 'application/pdf')
            attachments.append(attachment)

            # add requirement documents
            for requirement in proposal.requirements.exclude(is_deleted=True):
                for doc in requirement.requirement_documents.all():
                    file_name = doc._file.name
                    #attachment = (file_name, doc._file.file.read(), 'image/*')
                    attachment = (file_name, doc._file.file.read())
                    attachments.append(attachment)

        url = request.build_absolute_uri(reverse('external'))
        if "-internal" in url:
            # remove '-internal'. This email is for external submitters
            url = ''.join(url.split('-internal'))
        # if proposal.is_filming_licence:
        #     handbook_url= settings.COLS_FILMING_HANDBOOK_URL
        # else:
        #     handbook_url= settings.COLS_HANDBOOK_URL
        context = {
            'public_url': get_public_url(request),
            'proposal': proposal,
            'num_requirement_docs': len(attachments) - 1,
            'url': url,
            # 'handbook_url': handbook_url
        }

        msg = email.send(proposal.submitter.email, bcc= all_ccs, attachments=attachments, context=context)
        sender = request.user if request else settings.DEFAULT_FROM_EMAIL

        email_entry =_log_proposal_email(msg, proposal, sender=sender)
        path_to_file = '{}/proposals/{}/approvals/{}'.format(settings.MEDIA_APP_DIR, proposal.id, file_name)
        email_entry.documents.get_or_create(_file=path_to_file, name=file_name)

        if proposal.org_applicant:
            _log_org_email(msg, proposal.org_applicant, proposal.submitter, sender=sender)
        else:
            _log_user_email(msg, proposal.submitter, proposal.submitter, sender=sender)


def send_wla_processed_email(proposal, decision, with_payment, request):
    if decision == 'approved':
        subject = 'Your waiting list allocation application {} has been approved'.format(proposal.lodgement_number)
        details = proposal.proposed_issuance_approval.get('details'),

    elif decision == 'declined':
        subject = 'Your waiting list allocation application {} has been declined'.format(proposal.lodgement_number)
        details = proposal.proposaldeclineddetails.reason

    html_template = 'mooringlicensing/emails/send_wla_processed_email.html',
    txt_template = 'mooringlicensing/emails/send_wla_processed_email.txt',

    context = {
        'public_url': get_public_url(request),
        'proposal': proposal,
        'decision': decision,
        'details': details,
    }

    email = TemplateEmailBase(
        subject=subject,
        html_template=html_template,
        txt_template=txt_template,
    )

    to_address = proposal.submitter.email
    cc = []
    bcc = []

    # Send email
    msg = email.send(to_address, context=context, attachments=[], cc=cc, bcc=bcc,)

    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    log_proposal_email(msg, proposal, sender)
    return msg


def send_aaa_processed_email(proposal, decision, with_payment, request):
    if decision == 'approved':
        subject = 'Your annual admission application {} has been approved'.format(proposal.lodgement_number)
    elif decision == 'declined':
        subject = 'Your annual admission application {} has been declined'.format(proposal.lodgement_number)
    html_template = 'mooringlicensing/emails/send_aaa_processed_email.html',
    txt_template = 'mooringlicensing/emails/send_aaa_processed_email.txt',


def send_aua_processed_email(proposal, decision, with_payment, request):
    if decision == 'approved':
        subject = 'Your authorised user application {} has been approved'.format(proposal.lodgement_number)
    elif decision == 'declined':
        subject = 'Your authorised user application {} has been declined'.format(proposal.lodgement_number)
    html_template = 'mooringlicensing/emails/send_aua_processed_email.html',
    txt_template = 'mooringlicensing/emails/send_aua_processed_email.txt',


def send_mla_processed_email(proposal, decision, with_payment, request):
    if decision == 'approved':
        subject = 'Your mooring licence application {} has been approved'.format(proposal.lodgement_number)
    elif decision == 'declined':
        subject = 'Your mooring licence application {} has been declined'.format(proposal.lodgement_number)
    html_template = 'mooringlicensing/emails/send_mla_processed_email.html',
    txt_template = 'mooringlicensing/emails/send_mla_processed_email.txt',


