from django.conf import settings
from django.core.files.base import ContentFile
from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.utils.encoding import smart_str

from mooringlicensing.components.users.models import EmailUserLogEntry, private_storage
from ledger_api_client.managed_models import SystemUser, SystemUserAddress
from ledger_api_client.ledger_models import EmailUserRO


def create_system_user(email_user_id, email, first_name, last_name, dob, phone=None, mobile=None):
    return SystemUser.objects.create(
        ledger_id_id=email_user_id,
        email=email,
        legal_first_name=first_name,
        legal_last_name=last_name,
        legal_dob=dob,
        phone_number=phone,
        mobile_number=mobile,
    )

def get_or_create_system_user_address(system_user, system_address_dict, use_for_postal=False):
    """
        takes SystemUser object and SystemUserAddress dict, 
        checks if a corresponding SystemUserAddress records exists, 
        and create that SystemUserAddress record if it does not exist
    """
    qs = SystemUserAddress.objects.filter(system_user=system_user, **system_address_dict)
    if not qs.exists():
        SystemUserAddress.objects.create(system_user=system_user, **system_address_dict, use_for_postal=use_for_postal)
    elif use_for_postal and not qs.filter(use_for_postal=use_for_postal):
        for i in qs:
            i.use_for_postal=True
            i.change_by_user_id = i.system_user_id
            i.save()
        

def get_or_create_system_user(email_user_id, email, first_name, last_name, dob, phone=None, mobile=None, update=False):
    qs = SystemUser.objects.filter(ledger_id_id=email_user_id)
    if qs.exists():
        system_user = qs.first()
        if update:    
            system_user.change_by_user_id = system_user.id        
            system_user.email = email
            system_user.legal_first_name = first_name
            system_user.legal_last_name = last_name
            system_user.legal_dob = dob
            system_user.phone_number = phone
            system_user.mobile_number = mobile
            system_user.save()
        return system_user, False 
    else:
        if EmailUserRO.objects.filter(id=email_user_id, is_active=True).exists():
            try:
                system_user = SystemUser.objects.create(
                    ledger_id_id=email_user_id,
                    email=email,
                    legal_first_name=first_name,
                    legal_last_name=last_name,
                    legal_dob=dob,
                    phone_number=phone,
                    mobile_number=mobile,
                )
                return system_user, True
            except:
                #update the existing record with the correct ledger id
                existing = SystemUser.objects.get(email=email)
                existing.change_by_user_id = existing.id
                existing.ledger_id_id = email_user_id
                existing.save()
                return existing, False 
        else:
            raise Exception("Ledger Email User not Active")

def get_user_name(user):
    """
        return legal first name and legal last name over first name and last name if they exist
    """
    try:
        names = {"first_name":user.first_name,"last_name":user.last_name}
        if user.legal_first_name:
            names["first_name"] = user.legal_first_name
        if user.legal_last_name:
            names["last_name"] = user.legal_last_name
        names["full_name"] = names["first_name"] + " " + names["last_name"] 
    except:
        names = {"first_name":"unavailable","last_name":"unavailable","full_name":"unavailable"}

    return names

def _log_user_email(email_message, target_email_user, customer, sender=None, attachments=[]):
    if isinstance(email_message, (EmailMultiAlternatives, EmailMessage,)):
        text = email_message.body
        subject = email_message.subject
        fromm = smart_str(sender) if sender else smart_str(email_message.from_email)
        # the to email is normally a list
        if isinstance(email_message.to, list):
            to = ','.join(email_message.to)
        else:
            to = smart_str(email_message.to)
        # we log the cc and bcc in the same cc field of the log entry as a ',' comma separated string
        all_ccs = []
        if email_message.cc:
            all_ccs += list(email_message.cc)
        if email_message.bcc:
            all_ccs += list(email_message.bcc)
        all_ccs = ','.join(all_ccs)

    else:
        text = smart_str(email_message)
        subject = ''
        to = customer
        fromm = smart_str(sender) if sender else settings.SYSTEM_NAME_SHORT + ' Automated Message'
        all_ccs = ''

    customer = customer

    staff = sender

    kwargs = {
        'subject': subject,
        'text': text,
        'email_user_id': target_email_user if target_email_user else customer,
        'customer': customer,
        'staff': staff,
        'to': to,
        'fromm': fromm,
        'cc': all_ccs
    }

    email_entry = EmailUserLogEntry.objects.create(**kwargs)

    for attachment in attachments:
        path_to_file = '{}/emailuser/{}/communications/{}'.format(settings.MEDIA_APP_DIR, target_email_user, attachment[0])
        path = private_storage.save(path_to_file, ContentFile(attachment[1]))
        email_entry.documents.get_or_create(_file=path_to_file, name=attachment[0])

    return None
