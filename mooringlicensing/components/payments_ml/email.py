import mimetypes

from ledger.payments.pdf import create_invoice_pdf_bytes

from mooringlicensing import settings
from mooringlicensing.components.emails.emails import TemplateEmailBase, _extract_email_headers


class DcvPermitNotification(TemplateEmailBase):
    subject = 'Dcv Permit notification.'
    html_template = 'mooringlicensing/emails/dcv_permit_notification.html'
    txt_template = 'mooringlicensing/emails/dcv_permit_notification.txt'


class DcvPermitFeeInvoiceEmail(TemplateEmailBase):
    subject = 'Dcv Permit fee invoice for your DcvPermit.'
    html_template = 'mooringlicensing/emails/dcv_permit_fee_invoice.html'
    txt_template = 'mooringlicensing/emails/dcv_permit_fee_invoice.txt'


class DcvAdmissionFeeInvoiceEmail(TemplateEmailBase):
    subject = 'Dcv Admission fee invoice for your DcvAdmission.'
    html_template = 'mooringlicensing/emails/dcv_admission_fee_invoice.html'
    txt_template = 'mooringlicensing/emails/dcv_admission_fee_invoice.txt'


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


def send_dcv_permit_notification(dcv_permit, invoice, to_email_addresses):
    email = DcvPermitNotification()

    context = {
        'dcv_permit': dcv_permit,
    }

    attachments = []
    # attach invoice
    contents = create_invoice_pdf_bytes('invoice.pdf', invoice,)
    attachments.append(('invoice#{}.pdf'.format(invoice.reference), contents, 'application/pdf'))
    # attach DcvPermit
    dcv_permit_doc = dcv_permit.permits.first()
    filename = str(dcv_permit_doc)
    # content = dcv_permit_doc.file.read()
    content = dcv_permit_doc._file.read()
    mime = mimetypes.guess_type(dcv_permit_doc.filename)[0]
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


def send_dcv_permit_fee_invoice(dcv_permit, invoice, to_email_addresses):
    email = DcvPermitFeeInvoiceEmail()

    context = {
        'dcv_permit': dcv_permit,
    }

    attachments = []
    # attach invoice
    contents = create_invoice_pdf_bytes('invoice.pdf', invoice,)
    attachments.append(('invoice#{}.pdf'.format(invoice.reference), contents, 'application/pdf'))
    # attach DcvPermit
    dcv_permit_doc = dcv_permit.permits.first()
    filename = str(dcv_permit_doc)
    # content = dcv_permit_doc.file.read()
    content = dcv_permit_doc._file.read()
    mime = mimetypes.guess_type(dcv_permit_doc.filename)[0]
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


def send_dcv_admission_fee_invoice(dcv_admission, invoice, to_email_addresses):
    email = DcvAdmissionFeeInvoiceEmail()

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
