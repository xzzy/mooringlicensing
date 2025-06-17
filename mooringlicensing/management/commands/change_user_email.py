from django.core.management.base import BaseCommand
from ledger_api_client.ledger_models import EmailUserRO
from ledger_api_client.managed_models import SystemUser

from mooringlicensing.components.approvals.models import (
    Approval, DcvAdmission, DcvPermit, ApprovalUserAction, StickerActionDetail, ApprovalLogEntry
)
from mooringlicensing.components.compliances.models import (
    Compliance, ComplianceUserAction, ComplianceLogEntry
)
from mooringlicensing.components.payments_ml.models import (
    DcvAdmissionFee, DcvPermitFee, StickerActionFee, ApplicationFee
)
from mooringlicensing.components.proposals.models import (
    Proposal, ProposalApplicant, Owner, ProposalRequest, ProposalDeclinedDetails, ProposalUserAction, ProposalLogEntry, MooringLogEntry, VesselLogEntry
)

class Command(BaseCommand):
    help = 'Change user email address and all associated mooring licensing records'

    def add_arguments(self, parser):
        parser.add_argument('--current_email', type=str)
        parser.add_argument('--new_email', type=str)

    def handle(self, *args, **options):

        if not(options["current_email"] and options["new_email"]):
            print("please specify both the current email and the new email with the --current_email and --new_email options respectively")
            return

        #get original email
        current_email = options["current_email"]

        #get new email
        new_email = options["new_email"]

        #check if original email exists both on ledger and locally
        current_email_ledger = EmailUserRO.objects.filter(email__iexact=current_email).last()
        current_email_system = SystemUser.objects.filter(email__iexact=current_email).last()

        if not current_email_system:
            print("System User record does not exist for specified current email")
            return
        if not current_email_ledger:
            print("Ledger User record does not exist for specified current email")
            return

        change_ledger_id = {}
        change_email = {}
        #get all pertaining records (anything that refers to ledger id or email, except for log emails)
        #Approval (submitter)
        change_ledger_id["approval_submitter"] = Approval.objects.filter(submitter=current_email_ledger.id)
        #DcvAdmission (submitter, applicant)
        change_ledger_id["dcv_admission_submitter"] = DcvAdmission.objects.filter(submitter=current_email_ledger.id)
        change_ledger_id["dcv_admission_applicant"] = DcvAdmission.objects.filter(applicant=current_email_ledger.id)
        #DcvPermit (submitter, applicant)
        change_ledger_id["dcv_permit_submitter"] = DcvPermit.objects.filter(submitter=current_email_ledger.id)
        change_ledger_id["dcv_permit_applicant"] = DcvPermit.objects.filter(applicant=current_email_ledger.id)
        #ApprovalUserAction (who) 
        change_ledger_id["approver_user_action_who"] = ApprovalUserAction.objects.filter(who=current_email_ledger.id)
        #StickerActionDetail (user)
        change_ledger_id["sticker_action_detail_user"] = StickerActionDetail.objects.filter(user=current_email_ledger.id)
        #ApprovalLogEntry (customer)
        change_ledger_id["approval_log_entry_customer"] = ApprovalLogEntry.objects.filter(customer=current_email_ledger.id)
        
        #Compliance (assigned_to, submitter)
        change_ledger_id["compliance_assigned_to"] = Compliance.objects.filter(assigned_to=current_email_ledger.id)
        change_ledger_id["compliance_submitter"] = Compliance.objects.filter(submitter=current_email_ledger.id)
        #ComplianceUserAction (who)
        change_ledger_id["compliance_user_action_who"] = ComplianceUserAction.objects.filter(who=current_email_ledger.id)
        #ComplianceLogEntry (customer)
        change_ledger_id["compliance_log_entry_customer"] = ComplianceLogEntry.objects.filter(customer=current_email_ledger.id)

        #DcvAdmissionFee (created_by)
        change_ledger_id["dcv_admission_fee_created_by"] = DcvAdmissionFee.objects.filter(created_by=current_email_ledger.id)
        #DcvPermitFee (created_by)
        change_ledger_id["dcv_permit_fee_created_by"] = DcvPermitFee.objects.filter(created_by=current_email_ledger.id)
        #StickerActionFee (created_by)
        change_ledger_id["sticker_action_fee_created_by"] = StickerActionFee.objects.filter(created_by=current_email_ledger.id)
        #ApplicationFee (created_by)
        change_ledger_id["application_fee_created_by"] = ApplicationFee.objects.filter(created_by=current_email_ledger.id)

        #Proposal (submitter)
        change_ledger_id["proposal_submitter"] = Proposal.objects.filter(submitter=current_email_ledger.id)
        #ProposalApplicant (email_user_id, email)
        change_ledger_id["proposal_applicant_email_user_id"] = ProposalApplicant.objects.filter(email_user_id=current_email_ledger.id)
        change_email["proposal_applicant_email"] = ProposalApplicant.objects.filter(email=current_email)
        #Owner (emailuser)
        change_ledger_id["owner_emailuser"] = Owner.objects.filter(emailuser=current_email_ledger.id)
        #ProposalUserAction (who)
        change_ledger_id["proposal_user_action_who"] = ProposalUserAction.objects.filter(who=current_email_ledger.id)
        #ProposalLogEntry (customer)
        change_ledger_id["proposal_log_entry_customer"] = ProposalLogEntry.objects.filter(customer=current_email_ledger.id)
        #MooringLogEntry (customer)
        change_ledger_id["mooring_log_entry_customer"] = MooringLogEntry.objects.filter(customer=current_email_ledger.id)
        #VesselLogEntry (customer)
        change_ledger_id["vessel_log_entry_customer"] = VesselLogEntry.objects.filter(customer=current_email_ledger.id)

        #check if new email already exists on ledger (create new if it does not)

        #if it already exists, check if system user records exists on ML - stop if it does (TBD what happens next)

        #change all records to the new email and ledger id 
        
        #log all record changes to record's respective action logs where applicable (Applicant/Submitter/Holder Email Address change)