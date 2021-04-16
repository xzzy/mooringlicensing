from django.core.files.base import ContentFile

from mooringlicensing.components.approvals.models import DcvPermitDocument


def create_dcv_permit_document(approval, proposal, copied_to_permit, user):
    pdf_contents = create_apiary_licence_pdf_contents(approval, proposal, copied_to_permit, user)

    if proposal.apiary_group_application_type:
        filename = 'approval-{}-{}.pdf'.format(approval.lodgement_number, proposal.lodgement_number)
    else:
        filename = 'approval-{}.pdf'.format(approval.lodgement_number)
    document = DcvPermitDocument.objects.create(approval=approval, name=filename)
    document._file.save(filename, ContentFile(pdf_contents), save=True)

    return document
