import logging

from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.utils.encoding import smart_text
from django.core.urlresolvers import reverse
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from mooringlicensing.components.emails.emails import TemplateEmailBase
#from mooringlicensing.components.bookings.awaiting_payment_invoice_pdf import create_awaiting_payment_invoice_pdf_bytes
from datetime import datetime

logger = logging.getLogger(__name__)

SYSTEM_NAME = settings.SYSTEM_NAME_SHORT + ' Automated Message'


class ProposalDeclineSendNotificationEmail(TemplateEmailBase):
    subject = 'Your Application has been declined.'
    html_template = 'mooringlicensing/emails/proposals/send_decline_notification.html'
    txt_template = 'mooringlicensing/emails/proposals/send_decline_notification.txt'

class ProposalApprovalSendNotificationEmail(TemplateEmailBase):
    subject = '{} - Commercial Operations Licence Approved.'.format(settings.DEP_NAME)
    html_template = 'mooringlicensing/emails/proposals/send_approval_notification.html'
    txt_template = 'mooringlicensing/emails/proposals/send_approval_notification.txt'

class ProposalAwaitingPaymentApprovalSendNotificationEmail(TemplateEmailBase):
    subject = '{} - Commercial Filming Application - Pending Payment.'.format(settings.DEP_NAME)
    html_template = 'mooringlicensing/emails/proposals/send_awaiting_payment_approval_notification.html'
    txt_template = 'mooringlicensing/emails/proposals/send_awaiting_payment_approval_notification.txt'

class AmendmentRequestSendNotificationEmail(TemplateEmailBase):
    subject = '{} - Commercial Operations Incomplete application.'.format(settings.DEP_NAME)
    html_template = 'mooringlicensing/emails/proposals/send_amendment_notification.html'
    txt_template = 'mooringlicensing/emails/proposals/send_amendment_notification.txt'

class SubmitSendNotificationEmail(TemplateEmailBase):
    subject = 'A new Application has been submitted.'
    html_template = 'mooringlicensing/emails/proposals/send_submit_notification.html'
    txt_template = 'mooringlicensing/emails/proposals/send_submit_notification.txt'

class ExternalSubmitSendNotificationEmail(TemplateEmailBase):
    subject = '{} - Confirmation - Application submitted.'.format(settings.DEP_NAME)
    html_template = 'mooringlicensing/emails/proposals/send_external_submit_notification.html'
    txt_template = 'mooringlicensing/emails/proposals/send_external_submit_notification.txt'

class ApproverDeclineSendNotificationEmail(TemplateEmailBase):
    subject = 'An Application has been recommended for decline.'
    html_template = 'mooringlicensing/emails/proposals/send_approver_decline_notification.html'
    txt_template = 'mooringlicensing/emails/proposals/send_approver_decline_notification.txt'

class ApproverApproveSendNotificationEmail(TemplateEmailBase):
    subject = 'An Application has been recommended for approval.'
    html_template = 'mooringlicensing/emails/proposals/send_approver_approve_notification.html'
    txt_template = 'mooringlicensing/emails/proposals/send_approver_approve_notification.txt'

class ApproverSendBackNotificationEmail(TemplateEmailBase):
    subject = 'An Application has been sent back by approver.'
    html_template = 'mooringlicensing/emails/proposals/send_approver_sendback_notification.html'
    txt_template = 'mooringlicensing/emails/proposals/send_approver_sendback_notification.txt'


def send_amendment_email_notification(amendment_request, request, proposal):
    if proposal.is_filming_application:
        email = FilmingAmendmentRequestSendNotificationEmail()
    else:
        email = AmendmentRequestSendNotificationEmail()
    #reason = amendment_request.get_reason_display()
    reason = amendment_request.reason.reason
    url = request.build_absolute_uri(reverse('external-proposal-detail',kwargs={'proposal_pk': proposal.id}))

    if "-internal" in url:
        # remove '-internal'. This email is for external submitters
        url = ''.join(url.split('-internal'))

    context = {
        'proposal': proposal,
        'reason': reason,
        'amendment_request_text': amendment_request.text,
        'url': url
    }
    all_ccs = []
    if proposal.org_applicant and proposal.org_applicant.email:
        cc_list = proposal.org_applicant.email
        if cc_list:
            all_ccs = [cc_list]

    msg = email.send(proposal.submitter.email,cc=all_ccs, context=context)
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    _log_proposal_email(msg, proposal, sender=sender)
    if proposal.org_applicant:
        _log_org_email(msg, proposal.org_applicant, proposal.submitter, sender=sender)
    else:
        _log_user_email(msg, proposal.submitter, proposal.submitter, sender=sender)

def send_submit_email_notification(request, proposal):
    email = SubmitSendNotificationEmail()
    url = request.build_absolute_uri(reverse('internal-proposal-detail',kwargs={'proposal_pk': proposal.id}))
    if "-internal" not in url:
        # add it. This email is for internal staff (assessors)
        url = '-internal.{}'.format(settings.SITE_DOMAIN).join(url.split('.' + settings.SITE_DOMAIN))

    context = {
        'proposal': proposal,
        'url': url
    }

    msg = email.send(proposal.assessor_recipients, context=context)
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    _log_proposal_email(msg, proposal, sender=sender)
    if proposal.org_applicant:
        _log_org_email(msg, proposal.org_applicant, proposal.submitter, sender=sender)
    else:
        _log_user_email(msg, proposal.submitter, proposal.submitter, sender=sender)
    return msg

def send_external_submit_email_notification(request, proposal):
    email = ExternalSubmitSendNotificationEmail()
    url = request.build_absolute_uri(reverse('external-proposal-detail',kwargs={'proposal_pk': proposal.id}))

    if "-internal" in url:
        # remove '-internal'. This email is for external submitters
        url = ''.join(url.split('-internal'))

    context = {
        'proposal': proposal,
        'submitter': proposal.submitter.get_full_name(),
        'url': url
    }
    all_ccs = []
    if proposal.org_applicant and proposal.org_applicant.email:
        cc_list = proposal.org_applicant.email
        if cc_list:
            all_ccs = [cc_list]

    msg = email.send(proposal.submitter.email,cc=all_ccs, context=context)
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    _log_proposal_email(msg, proposal, sender=sender)
    if proposal.org_applicant:
        _log_org_email(msg, proposal.org_applicant, proposal.submitter, sender=sender)
    else:
        _log_user_email(msg, proposal.submitter, proposal.submitter, sender=sender)
    return msg

#send email when Proposal is 'proposed to decline' by assessor.
def send_approver_decline_email_notification(reason, request, proposal):
    email = ApproverDeclineSendNotificationEmail()
    url = request.build_absolute_uri(reverse('internal-proposal-detail',kwargs={'proposal_pk': proposal.id}))
    context = {
        'proposal': proposal,
        'reason': reason,
        'url': url
    }

    msg = email.send(proposal.approver_recipients, context=context)
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    _log_proposal_email(msg, proposal, sender=sender)
    if proposal.org_applicant:
        _log_org_email(msg, proposal.org_applicant, proposal.submitter, sender=sender)
    else:
        _log_user_email(msg, proposal.submitter, proposal.submitter, sender=sender)


def send_approver_approve_email_notification(request, proposal):
    email = ApproverApproveSendNotificationEmail()
    url = request.build_absolute_uri(reverse('internal-proposal-detail',kwargs={'proposal_pk': proposal.id}))
    context = {
        'start_date' : proposal.proposed_issuance_approval.get('start_date'),
        'expiry_date' : proposal.proposed_issuance_approval.get('expiry_date'),
        'details': proposal.proposed_issuance_approval.get('details'),
        'proposal': proposal,
        'url': url
    }

    msg = email.send(proposal.approver_recipients, context=context)
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    _log_proposal_email(msg, proposal, sender=sender)
    if proposal.org_applicant:
        _log_org_email(msg, proposal.org_applicant, proposal.submitter, sender=sender)
    else:
        _log_user_email(msg, proposal.submitter, proposal.submitter, sender=sender)


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
    _log_proposal_email(msg, proposal, sender=sender)
    if proposal.org_applicant:
        _log_org_email(msg, proposal.org_applicant, proposal.submitter, sender=sender)
    else:
        _log_user_email(msg, proposal.submitter, proposal.submitter, sender=sender)


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
    _log_proposal_email(msg, proposal, sender=sender)
    if proposal.org_applicant:
        _log_org_email(msg, proposal.org_applicant, proposal.submitter, sender=sender)
    else:
        _log_user_email(msg, proposal.submitter, proposal.submitter, sender=sender)


def send_proposal_approval_email_notification(proposal,request):
    if proposal.is_filming_licence:
        email = ProposalFilmingApprovalSendNotificationEmail()
    elif proposal.is_event_application:
        email= ProposalEventApprovalSendNotificationEmail()
    else:
        email = ProposalApprovalSendNotificationEmail()

    cc_list = proposal.proposed_issuance_approval['cc_email']
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
    if proposal.is_filming_licence:
        handbook_url= settings.COLS_FILMING_HANDBOOK_URL
    else:
        handbook_url= settings.COLS_HANDBOOK_URL
    context = {
        'proposal': proposal,
        'num_requirement_docs': len(attachments) - 1,
        'url': url,
        'handbook_url': handbook_url
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

def send_proposal_awaiting_payment_approval_email_notification(proposal, request):
    """ Send External Email with attached invoice and URL link to pay by credit card """
    email = ProposalAwaitingPaymentApprovalSendNotificationEmail()

    cc_list = proposal.proposed_issuance_approval['cc_email']
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

