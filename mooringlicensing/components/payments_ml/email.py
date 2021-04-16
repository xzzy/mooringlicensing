from ledger.payments.pdf import create_invoice_pdf_bytes

from mooringlicensing import settings
from mooringlicensing.components.emails.emails import TemplateEmailBase, _extract_email_headers


class DcvPermitFeeInvoiceEmail(TemplateEmailBase):
    subject = 'Dcv Permit fee invoice for your DcvPermit.'
    html_template = 'mooringlicensing/emails/dcv_permit_fee_invoice.html'
    txt_template = 'mooringlicensing/emails/dcv_permit_fee_invoice.txt'


def send_dcv_permit_fee_invoice(dcv_permit, invoice, to_email_addresses):
    email = DcvPermitFeeInvoiceEmail()

    context = {
        'dcv_permit': dcv_permit,
    }

    attachments = []
    contents = create_invoice_pdf_bytes('invoice.pdf', invoice,)
    attachments.append(('invoice#{}.pdf'.format(invoice.reference), contents, 'application/pdf'))

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
