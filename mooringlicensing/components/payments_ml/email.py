import mimetypes

from ledger.payments.pdf import create_invoice_pdf_bytes
from django.contrib.auth.models import Group

from mooringlicensing import settings
from mooringlicensing.components.emails.emails import TemplateEmailBase, _extract_email_headers
from mooringlicensing.components.emails.utils import get_user_as_email_user


class ApplicationSubmitConfirmationEmail(TemplateEmailBase):
    subject = 'Your application has been successfully submitted.'
    html_template = 'mooringlicensing/emails/application_submit_confirmation_email.html'
    txt_template = 'mooringlicensing/emails/application_submit_confirmation_email.txt'


def send_application_submit_confirmation_email(proposal, to_email_addresses):
    email = ApplicationSubmitConfirmationEmail()

    context = {
        'proposal': proposal,
    }

    attachments = []
    to_address = to_email_addresses
    cc = []
    bcc = []

    msg = email.send(
        to_address,
        context=context,
        attachments=attachments,
        cc=cc,
        bcc=bcc,
    )

    # sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    sender = settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)
    return email_data


def send_dcv_permit_mail(dcv_permit, invoice, request):
    email = TemplateEmailBase(
        subject='Dcv Permit.',
        html_template='mooringlicensing/emails/dcv_permit_mail.html',
        txt_template='mooringlicensing/emails/dcv_permit_mail.txt',
    )

    context = {
        'dcv_permit': dcv_permit,
        'recipient': dcv_permit.submitter,
    }

    attachments = []

    # attach invoice
    contents = create_invoice_pdf_bytes('invoice.pdf', invoice,)
    attachments.append(('invoice#{}.pdf'.format(invoice.reference), contents, 'application/pdf'))

    # attach DcvPermit
    dcv_permit_doc = dcv_permit.permits.first()
    filename = str(dcv_permit_doc)
    content = dcv_permit_doc._file.read()
    mime = mimetypes.guess_type(dcv_permit_doc.filename)[0]
    attachments.append((filename, content, mime))

    to = dcv_permit.submitter.email
    cc = []
    bcc = []

    # Update bcc if
    dcv_group = Group.objects.get(name=settings.GROUP_DCV_PERMIT_ADMIN)
    users = dcv_group.user_set.all()
    if users:
        bcc = [user.email for user in users]

    msg = email.send(
        to,
        context=context,
        attachments=attachments,
        cc=cc,
        bcc=bcc,
    )

    sender = get_user_as_email_user(msg.from_email)
    email_data = _extract_email_headers(msg, sender=sender)
    return email_data


# Remove once merged
#def send_dcv_permit_notification(dcv_permit, invoice, to_email_addresses):
#    email = TemplateEmailBase(
#        subject='Dcv Permit notification.',
#        html_template='mooringlicensing/emails/dcv_permit_notification.html',
#        txt_template='mooringlicensing/emails/dcv_permit_notification.txt',
#    )
#
#    context = {
#        'dcv_permit': dcv_permit,
#    }
#
#    attachments = []
#    # attach invoice
#    contents = create_invoice_pdf_bytes('invoice.pdf', invoice,)
#    attachments.append(('invoice#{}.pdf'.format(invoice.reference), contents, 'application/pdf'))
#    # attach DcvPermit
#    dcv_permit_doc = dcv_permit.permits.first()
#    filename = str(dcv_permit_doc)
#    # content = dcv_permit_doc.file.read()
#    content = dcv_permit_doc._file.read()
#    mime = mimetypes.guess_type(dcv_permit_doc.filename)[0]
#    attachments.append((filename, content, mime))
#
#    to_address = to_email_addresses
#    cc = []
#    bcc = []
#
#    msg = email.send(
#        to_address,
#        context=context,
#        attachments=attachments,
#        cc=cc,
#        bcc=bcc,
#    )
#
#    # sender = request.user if request else settings.DEFAULT_FROM_EMAIL
#    sender = settings.DEFAULT_FROM_EMAIL
#    email_data = _extract_email_headers(msg, sender=sender)
#    return email_data
#
#
## Remove once merged
#def send_dcv_permit_fee_invoice(dcv_permit, invoice, to_email_addresses):
#    email = TemplateEmailBase(
#        subject='Dcv Permit fee invoice for your DcvPermit.',
#        html_template='mooringlicensing/emails/dcv_permit_fee_invoice.html',
#        txt_template='mooringlicensing/emails/dcv_permit_fee_invoice.txt',
#    )
#
#    context = {
#        'dcv_permit': dcv_permit,
#    }
#
#    attachments = []
#    # attach invoice
#    contents = create_invoice_pdf_bytes('invoice.pdf', invoice,)
#    attachments.append(('invoice#{}.pdf'.format(invoice.reference), contents, 'application/pdf'))
#    # attach DcvPermit
#    dcv_permit_doc = dcv_permit.permits.first()
#    filename = str(dcv_permit_doc)
#    # content = dcv_permit_doc.file.read()
#    content = dcv_permit_doc._file.read()
#    mime = mimetypes.guess_type(dcv_permit_doc.filename)[0]
#    attachments.append((filename, content, mime))
#
#    to_address = to_email_addresses
#    cc = []
#    bcc = []
#
#    msg = email.send(
#        to_address,
#        context=context,
#        attachments=attachments,
#        cc=cc,
#        bcc=bcc,
#    )
#
#    # sender = request.user if request else settings.DEFAULT_FROM_EMAIL
#    sender = settings.DEFAULT_FROM_EMAIL
#    email_data = _extract_email_headers(msg, sender=sender)
#    return email_data


def send_dcv_admission_fee_invoice(dcv_admission, invoice, to_email_addresses):
    email = TemplateEmailBase(
        subject='Dcv Admission fee invoice for your DcvAdmission.',
        html_template='mooringlicensing/emails/dcv_admission_fee_invoice.html',
        txt_template='mooringlicensing/emails/dcv_admission_fee_invoice.txt',
    )

    context = {
        'dcv_admission': dcv_admission,
    }

    attachments = []
    # attach invoice
    contents = create_invoice_pdf_bytes('invoice.pdf', invoice,)
    attachments.append(('invoice#{}.pdf'.format(invoice.reference), contents, 'application/pdf'))
    # attach DcvPermit
    dcv_admission_doc = dcv_admission.admissions.first()
    filename = str(dcv_admission_doc)
    # content = dcv_permit_doc.file.read()
    content = dcv_admission_doc._file.read()
    mime = mimetypes.guess_type(dcv_admission_doc.filename)[0]
    attachments.append((filename, content, mime))

    to_address = to_email_addresses
    cc = []
    bcc = []

    msg = email.send(
        to_address,
        context=context,
        attachments=attachments,
        cc=cc,
        bcc=bcc,
    )

    # sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    sender = settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)
    return email_data
