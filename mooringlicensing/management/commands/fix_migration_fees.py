#Script to fix an issue that occurred with migrated data
#Migrations were conducted with one set of fee constructors which were then replaced, after migration had been complete, with a new set of fee constructors
#Because of that, when an amendment is made of a given application the fee difference between the two different constructors is charged
#this script remedies that by effectively updating the fee records to use the new fees and report the amount paid as if they had been migrated with the newer, valid fee constructors
from django.core.management.base import BaseCommand
from mooringlicensing.components.payments_ml.models import FeeItemApplicationFee, FeeItem

class Command(BaseCommand):
    help = 'Update migration fee records to match correct fee constructors'

    def add_arguments(self, parser):
        parser.add_argument('--fix', action='store_true', default=False)

    def handle(self, *args, **options):
        acquired_fee_items = {}
        count = 0
        fix = options['fix']
        if fix:
            print("\nWill change fee items and amount paid where required\n")
        else:
            print("\nOnly reporting on fee items and amount paid changes required\n")
        fix_count = 0

        for i in FeeItemApplicationFee.objects.filter(application_fee__proposal__migrated=True):
            fee_item = i.fee_item
            if fee_item.id in acquired_fee_items:
                count += 1
                print("Proposal {} - id {} - payment record id {}".format(i.application_fee.proposal.lodgement_number,i.application_fee.proposal.id, i.id))
                print("\nchange fee item id from {} to {}".format(fee_item.id, acquired_fee_items[fee_item.id].id))
                amount_to_be_paid = acquired_fee_items[fee_item.id].get_absolute_amount(i.application_fee.proposal.vessel_length)
                print("change amount paid from {} to {}\n".format(i.amount_paid, amount_to_be_paid))
                if fix:
                    i.amount_paid = amount_to_be_paid
                    i.amount_to_be_paid = amount_to_be_paid
                    i.fee_item_id = acquired_fee_items[fee_item.id].id
                    i.save()
                    print("change applied for payment record with id {}".format(i.id))
                    fix_count += 1

            elif fee_item.fee_constructor and not fee_item.fee_constructor.enabled:
                count += 1
                print("Proposal {} - id {} - payment record id {}".format(i.application_fee.proposal.lodgement_number,i.application_fee.proposal.id, i.id))
                new_con_fee_item = FeeItem.objects.filter(
                    fee_period=fee_item.fee_period, 
                    vessel_size_category=fee_item.vessel_size_category,
                    proposal_type=fee_item.proposal_type,
                    fee_constructor__enabled=True,
                ).last()
                acquired_fee_items[fee_item.id] = new_con_fee_item
                print("\nchange fee item id from {} to {}".format(fee_item.id, acquired_fee_items[fee_item.id].id))
                amount_to_be_paid = acquired_fee_items[fee_item.id].get_absolute_amount(i.application_fee.proposal.vessel_length)
                print("change amount paid from {} to {}\n".format(i.amount_paid, amount_to_be_paid))
                if fix:
                    i.amount_paid = amount_to_be_paid
                    i.amount_to_be_paid = amount_to_be_paid
                    i.fee_item_id = acquired_fee_items[fee_item.id].id
                    i.save()
                    print("change applied for payment record with id {}".format(i.id))
                    fix_count += 1
        
        if fix:
            print("{} fee item application fee records adjusted".format(count))
        else:
            print("{} fee item application fee records require adjustment".format(count))