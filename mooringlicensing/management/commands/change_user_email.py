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
    Proposal, ProposalApplicant, Owner, ProposalUserAction, ProposalLogEntry, MooringLogEntry, VesselLogEntry, VesselOwnership
)
from ledger_api_client.utils import get_or_create, change_user_invoice_ownership
from django.db import transaction
from mooringlicensing.components.users.utils import get_or_create_system_user_system_user

class Command(BaseCommand):
    help = 'Change user email address and all associated mooring licensing records'

    def add_arguments(self, parser):
        parser.add_argument('--current_email', type=str)
        parser.add_argument('--new_email', type=str)

    def check_proposals_and_approvals(self,to_be_changed,existing):
        #TODO go through each proposal/approval type and ensure no conflict between to_be_changed and existing
        #check for application limit rules (e.g. one wla per user), vessel rules (can only be one application at a time, can not be on an AAP and an MLA, etc)

        proposals_to_be_changed = list(filter(lambda i: i[0]==Proposal),to_be_changed)
        proposals_existing = list(filter(lambda i: i[0]==Proposal),existing)

        approvals_to_be_changed = list(filter(lambda i: i[0]==Approval),to_be_changed)
        approvals_existing = list(filter(lambda i: i[0]==Approval),existing)

        # WAITING LIST APPLICATION RULES
        # Vessel cannot be part of another Waiting List application in status other than issued, declined or discarded
        # Vessel cannot be part of a current or suspended Waiting List Allocation
        # Vessel cannot be part of a Mooring Licence application in status other than issued, declined or discarded
        # Vessel cannot be part of a current or suspended Mooring Licence allocation (as nominated vessel or as one of other vessels on the licence)
        # A person cannot start a Waiting List Application if there is another Waiting List application for that person in status other than issued, declined, discarded
        # A person cannot start a Waiting List Application if there is another Waiting List Allocation for that person in status other than cancelled, expired, surrendered
        # A person cannot start a Waiting List Application if there is a Mooring Licence application in status other than issued, declined or discarded
        # A person cannot start a Waiting List Application if there is a Mooring Licence in status Current or Suspended

        # (Inferred) WAITING LIST ALLOCATION RULES
        # A person cannot have a Current or Suspended Waiting List Allocation if there is another New Waiting List application for that person in status other than issued, declined, discarded
        # A person cannot have a Current or Suspended Waiting List Allocation if there is a Mooring Licence application in status other than issued, declined or discarded
        # A person can have only one Current or Suspended Waiting List Allocation in status other than cancelled, expired, surrendered
        # A person cannot have a Current or Suspended Waiting List Allocation if there is a Mooring Licence in status Current or Suspended

        # ANNUAL ADMISSION APPLICATION RULES
        # Vessel cannot be part of another Annual Admission application in status other than issued, declined or discarded
        # Vessel cannot be part of a current or suspended Annual Admission Permit
        # Vessel cannot be part of an Authorised User application in status other than issued, declined or discarded
        # Vessel cannot be part of a current or suspended Authorised User Permit
        # Vessel cannot be part of a Mooring Licence application in status other than issued, declined or discarded
        # Vessel cannot be part of a current or suspended Mooring Licence (as nominated vessel or as one of other vessels on the licence)

        # (Inferred) ANNUAL ADMISSION PERMIT RULES
        # Vessel cannot be part of a New Annual Admission application in status other than issued, declined or discarded
        # Vessel cannot be part of a another current or suspended Annual Admission Permit

        # Vessel cannot be part of an Authorised User application in status other than issued, declined or discarded
        # Vessel cannot be part of a current or suspended Authorised User Permit
        # Vessel cannot be part of a Mooring Licence application in status other than issued, declined or discarded
        # Vessel cannot be part of a current or suspended Mooring Licence (as nominated vessel or as one of other vessels on the licence)

        return False, "Record merging not yet supported", []

    def check_ownerships(self,to_be_changed,existing):
        owners_to_be_changed = list(filter(lambda i: i[0]==Owner),to_be_changed)
        owners_existing = list(filter(lambda i: i[0]==Owner),existing)

        if owners_to_be_changed and owners_existing:
            to_be_changed_rego_nos = []
            for i in owners_to_be_changed[1]:
                to_be_changed_rego_nos += list(i.vessels.filter(vesselownership__end_date=None).values_list('rego_no',flat=True))

            existing_rego_nos = []
            for i in owners_existing[1]:
                existing_rego_nos += list(i.vessels.filter(vesselownership__end_date=None).values_list('rego_no',flat=True))

            intersecting_rego_nos = list(set(existing_rego_nos).intersection(set(to_be_changed_rego_nos)))
            if intersecting_rego_nos:
                return False, "Both accounts own vessels with rego_nos {intersecting_rego_nos}. Please discontinue vessel ownerships under one user to allow for records to merge."
        else:
            return True, "No conflicting Owner records"

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
        if not new_email_ledger:
            new_email_resp = get_or_create(new_email)["data"]["email"]
            new_email_ledger = EmailUserRO.objects.filter(email__iexact=new_email_resp).last()

        system_user_exists = False
        #if it already exists, check if system user record exists on ML - stop if it does
        if SystemUser.objects.filter(email__iexact=new_email):
            print("Provided email already has an associated System User")
            system_user_exists = True

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

        potential_blockers = [Approval,Proposal,Owner]

        special_handling = {Owner:False} #if a model require special handling under certain conditions, set Key bool to True

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
            #change all records to the new email and ledger id 
            #log all record changes to record's respective action logs where applicable (Applicant/Submitter/Holder Email Address change)
            if not system_user_exists:
                SystemUser.objects.create(
                    email = new_email,
                    ledger_id_id = new_email_ledger.id,
                    first_name = current_email_system.first_name,
                    last_name = current_email_system.last_name,
                    is_staff = current_email_system.is_staff,
                    is_active = current_email_system.is_active,
                    title = current_email_system.title,
                    legal_dob = current_email_system.legal_dob,
                    phone_number = current_email_system.phone_number,
                    mobile_number = current_email_system.mobile_number,
                    fax_number = current_email_system.fax_number,
                )
            else:
                existing_system_user = SystemUser.objects.filter(email__iexact=new_email).first()
                #if somehow a system user already exists but their ledger id does not match that of the provided email, update it (with a warning)
                if existing_system_user.ledger_id_id != new_email_ledger.id: 
                    if existing_system_user.ledger_id_id != None:
                        
                        answer = input(f"""
    ####################################################################################################################################################################################################################            
    WARNING: Existing system user account has a different ledger id ({existing_system_user.ledger_id_id}) to that of the provided new email address {new_email} ledger id {new_email_ledger.id}

    Proceeding will change the the ledger id of the system user record for {new_email} from {existing_system_user.ledger_id_id} to {new_email_ledger.id}. 

    Do not proceed if there are other records referencing ledger id {existing_system_user.ledger_id_id} that need to remain associated with the new email - they should be adjusted prior to conducting an email change.
    #################################################################################################################################################################################################################### 
    Are you sure you want to continue? (y/n): """)
                        if answer.lower() != 'y':
                            return
                    else:
                        print(f"System user with email {new_email} does not have a ledger id set, updating to use ledger id {new_email_ledger.id}")
                    system_user_system_user = get_or_create_system_user_system_user()
                    existing_system_user.ledger_id_id = new_email_ledger.id
                    existing_system_user.change_by_user_id = system_user_system_user.id
                    existing_system_user.save()

                #first, get every record from the current email that will move to the new email (only models in change_ledger_id need to be checked)
                to_be_changed = []
                for k in change_ledger_id: 
                    if k in potential_blockers:
                        for v in change_ledger_id[k]:
                            change = k.objects.filter(**{v:current_email_ledger.id})
                            if change.exists():
                                to_be_changed.append((k,list(change)))

                existing = []
                for k in change_ledger_id:
                    if k in potential_blockers:
                        for v in change_ledger_id[k]:
                            exists = k.objects.filter(**{v:new_email_ledger.id})
                            if exists.exists():
                                existing.append((k,list(exists)))

                print(to_be_changed)
                print(existing)

                if to_be_changed and existing:
                    #check validity - if a record cannot be moved STOP
                    #proposals and approvals will need to be checked together to ensure they can exist on the same user
                    valid1, reason, merging_records = self.check_proposals_and_approvals(to_be_changed, existing)
                    print(reason)
                    #owners will require special handling - users may only have one owner record each so the vessel ownerships will need to be moved instead
                    #if a current vessel_ownership on the current owner shares a rego_no with the new owner's current vessel_ownerships, count as invalid and STOP
                    valid2, reason = self.check_ownerships(to_be_changed, existing)
                    print(reason)

                    if valid1 and valid2:
                        #deliver a warning - once merged the change CANNOT be reversed, so make that clear to the user
                        answer = input(f"""
###############################################################################################################################################################                                    
WARNING: you are about to merge {merging_records} and related records (such as logs and relation tables) in to a user with existing records!                
This process cannot be reversed using the change_user_email management command, the records will be bound to the same user once this process has completed. 

Will move and merge records from {current_email} in to {new_email}. Potential payment adjustments will need to be reviewed and conducted manually.
###############################################################################################################################################################  
Are you sure you want to continue? (y/n): """)
                        if answer.lower() != 'y':
                            return
                    else:
                        return 
                else:
                    if not to_be_changed:
                        print("Current user has no potentially conflicting records - change can proceed")
                    if not existing:
                        print("New (existing) user has no potentially conflicting records - change can proceed")

            for k in change_email:
                changed = []
                for v in change_email[k]:
                    change = k.objects.filter(**{v:current_email_ledger.email})
                    if change.exists():
                        count = change.count()
                        changed.append((v,list(change)))
                        change.update(**{v:new_email_ledger.email})
                        print("changed {} {} {}(s)".format(count,k._meta.model_name,v))
                        
                if changed and k in log_change_models:
                    try:
                        logging_model = log_change_models[k][0]
                        logging_model_relation = log_change_models[k][1]
                        changed_model = k
                        changed_model_relation = None if len(log_change_models[k]) < 3 else log_change_models[k][2]
                        for i in changed:
                            for c in i[1]:
                                if changed_model_relation:
                                    action = "Changed {} field due to user email change from {} to {} change for {} {} {}".format(i[0], current_email, new_email,changed_model._meta.model_name,logging_model_relation,getattr(c,changed_model_relation))
                                    print(logging_model.log_action(getattr(c,changed_model_relation),action))
                                else:
                                    action = "Changed {} field due to user email change from {} to {} change for {} {}".format(i[0], current_email, new_email,changed_model._meta.model_name,c)
                                    print(logging_model.log_action(c,action))

                    except Exception as e:
                        print("Error:",e)

            for k in change_ledger_id:
                if k in special_handling and special_handling[k]:
                    continue
                changed = []
                for v in change_ledger_id[k]:
                    change = k.objects.filter(**{v:current_email_ledger.id})
                    if change.exists():
                        count = change.count()
                        changed.append((v,list(change)))
                        change.update(**{v:new_email_ledger.id})
                        print("changed {} {} {}(s)".format(count,k._meta.model_name,v))
                        
                if changed and k in log_change_models:
                    try:
                        logging_model = log_change_models[k][0]
                        logging_model_relation = log_change_models[k][1]
                        changed_model = k
                        changed_model_relation = None if len(log_change_models[k]) < 3 else log_change_models[k][2]
                        for i in changed:
                            for c in i[1]:
                                if changed_model_relation:
                                    action = "Changed {} field due to user email from {} to {} change for {} {} {}".format(i[0], current_email, new_email, changed_model._meta.model_name,logging_model_relation,getattr(c,changed_model_relation))
                                    print(logging_model.log_action(getattr(c,changed_model_relation),action))
                                else:
                                    action = "Changed {} field due to user email from {} to {} change for {} {}".format(i[0], current_email, new_email, changed_model._meta.model_name,c)
                                    print(logging_model.log_action(c,action))

                    except Exception as e:
                        print("Error:",e)
        
            #special handling for certain models happens here
            if special_handling[Owner]:
                #Users may only have one owner record, so we have to change to change VesselOwnership records instead
                try:
                    current_owner = Owner.objects.get(emailuser=new_email_ledger.id)
                    new_owner = Owner.objects.get(emailuser=new_email_ledger.id)
                    VesselOwnership.objects.filter(owner=current_owner).update(owner=new_owner)
                except Exception as e:
                    print(e)

            #transfer invoice ownership on ledger - raise an error if this fails
            res = change_user_invoice_ownership(current_email, new_email)
            if not 'message' in res or res['message'] != 'success':
                raise ValueError("Invoice ownership change failed")
            print("change_user_invoice_ownership response:", res['message'])
            