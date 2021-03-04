from rest_framework import serializers
from django.db.models import Sum, Max
from mooringlicensing.components.main.models import (
        CommunicationsLogEntry, #Region, District, Tenure, 
        ApplicationType, #ActivityMatrix, AccessType, Park, Trail, Activity, ActivityCategory, Section, Zone, 
        #RequiredDocument, 
        Question, GlobalSettings
        )#, ParkPrice
#from mooringlicensing.components.proposals.models import  ProposalParkActivity
#from mooringlicensing.components.bookings.models import  ParkBooking
from ledger.accounts.models import EmailUser
from datetime import datetime, date
#from mooringlicensing.components.proposals.serializers import ProposalTypeSerializer

class CommunicationLogEntrySerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(queryset=EmailUser.objects.all(),required=False)
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


class ApplicationTypeSerializer(serializers.ModelSerializer):
    #regions = RegionSerializer(many=True)
    #activity_app_types = ActivitySerializer(many=True)
    #tenure_app_types = TenureSerializer(many=True)
    class Meta:
        model = ApplicationType
        #fields = ('id', 'name', 'activity_app_types', 'tenure_app_types')
        #fields = ('id', 'name', 'tenure_app_types')
        fields = '__all__'
        #extra_fields = ['pizzas']


class GlobalSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalSettings
        fields = ('key', 'value')



#class RequiredDocumentSerializer(serializers.ModelSerializer):
#    class Meta:
#        model = RequiredDocument
#        fields = ('id', 'park','activity', 'question')


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ('id', 'question_text', 'answer_one', 'answer_two', 'answer_three', 'answer_four','correct_answer', 'correct_answer_value')


class OracleSerializer(serializers.Serializer):
    date = serializers.DateField(input_formats=['%d/%m/%Y','%Y-%m-%d'])
    override = serializers.BooleanField(default=False)

