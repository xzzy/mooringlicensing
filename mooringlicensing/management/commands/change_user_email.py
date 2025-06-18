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
    Proposal, ProposalApplicant, Owner, ProposalUserAction, ProposalLogEntry, MooringLogEntry, VesselLogEntry
)
from ledger_api_client.utils import get_or_create
from django.db import transaction
from mooringlicensing.components.users.utils import get_or_create_system_user_system_user

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

        new_email_ledger = EmailUserRO.objects.filter(email__iexact=new_email).last()
        #check if new email already exists on ledger (create new if it does not)
        if new_email_ledger:
            #if it already exists, check if system user record exists on ML - stop if it does (TBD what happens next)
            if SystemUser.objects.filter(email__iexact=new_email):
                print("Provided email already has an associated System User")
                return
        else:
            new_email_ledger = get_or_create(new_email)

        #get all pertaining records (anything that refers to ledger id or email, except for log emails)
        #Approval (submitter)
        #DcvAdmission (submitter, applicant)
        #DcvPermit (submitter, applicant)
        #ApprovalUserAction (who) 
        #StickerActionDetail (user)
        #ApprovalLogEntry (customer)
        
        #Compliance (submitter)
        #ComplianceUserAction (who)
        #ComplianceLogEntry (customer)

        #DcvAdmissionFee (created_by)
        #DcvPermitFee (created_by)
        #StickerActionFee (created_by)
        #ApplicationFee (created_by)

        #Proposal (submitter)
        #ProposalApplicant (email_user_id, email)
        #Owner (emailuser)
        #ProposalUserAction (who)
        #ProposalLogEntry (customer)
        #MooringLogEntry (customer)
        #VesselLogEntry (customer)

        change_ledger_id = {
            Approval: ["submitter"],
            DcvAdmission: ["submitter", "applicant"],
            DcvPermit: ["submitter", "applicant"],
            ApprovalUserAction: ["who"],
            StickerActionDetail: ["user"],
            ApprovalLogEntry: ["customer"],
            Compliance: ["submitter"],
            ComplianceUserAction: ["who"],
            ComplianceLogEntry: ["customer"],
            DcvAdmissionFee: ["created_by"],
            DcvPermitFee: ["created_by"],
            StickerActionFee: ["created_by"],
            ApplicationFee: ["created_by"],
            Proposal: ["submitter"],
            ProposalApplicant: ["email_user_id"],
            Owner: ["emailuser"],
            ProposalUserAction: ["who"],
            ProposalLogEntry: ["customer"],
            MooringLogEntry: ["customer"],
            VesselLogEntry: ["customer"],
        }
        change_email = {
            ProposalApplicant: ["email"]
        }
        log_change_models = {
            Approval: (ApprovalUserAction, "approval"), #(logging_model, logging_model_relation)
            Compliance: (ComplianceUserAction, "compliance"),
            Proposal: (ProposalUserAction, "proposal"),
            ProposalApplicant: (ProposalUserAction, "proposal", "proposal"), #(logging_model, logging_model_relation, changed_model_relation)
        }

        with transaction.atomic():

            system_user_system_user = get_or_create_system_user_system_user()

            #change all records to the new email and ledger id 
            #log all record changes to record's respective action logs where applicable (Applicant/Submitter/Holder Email Address change)
            current_email_system.email = new_email
            current_email_system.ledger_id_id = new_email_ledger.id
            current_email_system.change_by_user_id = system_user_system_user.id
            current_email_system.save()

            for k in change_email:
                for v in change_email[k]:
                    change = k.objects.filter(**{v:current_email_ledger.email})
                    if change.exists():
                        change.update(**{v:new_email_ledger.email})

            for k in change_ledger_id:
                changed = []
                for v in change_ledger_id[k]:
                    change = k.objects.filter(**{v:current_email_ledger.id})
                    if change.exists():
                        #change.update(**{v:new_email_ledger.id})
                        changed.append((k,v,change.values_list('id', flat=True)))
                if changed and k in log_change_models:
                    try:
                        logging_model = log_change_models[k][0]
                        logging_model_relation = log_change_models[k][1]
                        changed_model = k
                        changed_model_relation = None if len(log_change_models[k]) < 3 else log_change_models[k][3]
                    except Exception as e:
                        print("Error:",e)