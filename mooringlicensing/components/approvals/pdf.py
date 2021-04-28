from django.core.files.base import ContentFile

from mooringlicensing.doctopdf import create_dcv_permit_pdf_contents, create_dcv_admission_pdf_contents


def create_dcv_permit_document(dcv_permit):
    pdf_contents = create_dcv_permit_pdf_contents(dcv_permit)

    filename = 'dcv_permit-{}.pdf'.format(dcv_permit.lodgement_number)
    from mooringlicensing.components.approvals.models import DcvPermitDocument
    document = DcvPermitDocument.objects.create(dcv_permit=dcv_permit, name=filename)
    document._file.save(filename, ContentFile(pdf_contents), save=True)

    return document


def create_dcv_admission_document(dcv_admission):
    pdf_contents = create_dcv_admission_pdf_contents(dcv_admission)

    filename = 'dcv_admission-{}.pdf'.format(dcv_admission.lodgement_number)
    from mooringlicensing.components.approvals.models import DcvAdmissionDocument
    document = DcvAdmissionDocument.objects.create(dcv_admission=dcv_admission, name=filename)
    document._file.save(filename, ContentFile(pdf_contents), save=True)

    return document
