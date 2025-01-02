from rest_framework import serializers
from mooringlicensing import settings
from mooringlicensing.components.main.models import CommunicationsLogEntry
from ledger_api_client.ledger_models import EmailUserRO, Invoice
from mooringlicensing.ledger_api_utils import get_invoice_payment_status


class CommunicationLogEntrySerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(queryset=EmailUserRO.objects.all(),required=False)
    documents = serializers.SerializerMethodField()
    class Meta:
        model = CommunicationsLogEntry
        fields = (
            'id',
            'customer',
            'to',
            'fromm',
            'cc',
            'type',
            'reference',
            'subject'
            'text',
            'created',
            'staff',
            'proposal'
            'documents'
        )

    def get_documents(self,obj):
        return [[d.name,d._file.url] for d in obj.documents.all()]

#TODO no longer in user - consider removing
class InvoiceSerializer(serializers.ModelSerializer):
    payment_status = serializers.SerializerMethodField()
    invoice_url = serializers.SerializerMethodField()
    ledger_payment_url = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = (
            'id',
            'amount',
            'reference',
            'payment_status',
            'settlement_date',
            'invoice_url',
            'ledger_payment_url',
        )

    def get_payment_status(self, invoice):
        invoice_payment_status = get_invoice_payment_status(invoice.id).lower()

        if invoice_payment_status == 'unpaid':
            return 'Unpaid'
        elif invoice_payment_status == 'partially_paid':
            return 'Partially Paid'
        elif invoice_payment_status == 'paid':
            return 'Paid'
        else:
            return 'Over Paid'

    def get_invoice_url(self, invoice):
        return f'/ledger-toolkit-api/invoice-pdf/{invoice.reference}/'

    def get_ledger_payment_url(self, invoice):
        return f'{settings.LEDGER_UI_URL}/ledger/payments/oracle/payments?invoice_no={invoice.reference}'