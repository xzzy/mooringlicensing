from rest_framework import serializers

from mooringlicensing.components.approvals.models import (
    DcvPermit, DcvVessel, DcvAdmission, 
    DcvAdmissionArrival, NumberOfPeople, AgeGroup
)
from mooringlicensing.components.payments_ml.models import FeeSeason, FeeConstructor


class DcvAdmissionSerializer(serializers.ModelSerializer):
    dcv_vessel_id = serializers.IntegerField(required=True)

    class Meta:
        model = DcvAdmission
        fields = (
            'id',
            'lodgement_number',
            'submitter', 
            'applicant',
            'skipper',
            'contact_number',
            'dcv_vessel_id',
            'date_created',
            'status',
        )
        read_only_fields = (
            'id',
            'lodgement_number',
            'date_created',
        )

    def validate(self, data):
        field_errors = {}
        non_field_errors = []

        if not self.partial:
            if not data['skipper']:
                field_errors['skipper'] = ['Please enter the skipper name.',]
            if not data['contact_number']:
                field_errors['contact_number'] = ['Please enter the contact number.',]

            # Raise errors
            if field_errors:
                raise serializers.ValidationError(field_errors)
            if non_field_errors:
                raise serializers.ValidationError(non_field_errors)

        return data


class DcvAdmissionArrivalSerializer(serializers.ModelSerializer):
    arrival_date = serializers.DateField(input_formats=(['%d/%m/%Y']))
    departure_date = serializers.DateField(input_formats=(['%d/%m/%Y']))

    def validate(self, data):
        field_errors = {}
        non_field_errors = []

        if not self.partial:
            if not data.get('arrival_date', None):
                field_errors['year'] = ['Please enter an arrival date.',]
            if not data.get('departure_date', None):
                field_errors['year'] = ['Please enter an departure date.',]

            # Raise errors
            if field_errors:
                raise serializers.ValidationError(field_errors)
            if non_field_errors:
                raise serializers.ValidationError(non_field_errors)
            
        return data

    class Meta:
        model = DcvAdmissionArrival
        fields = (
            'id',
            'arrival_date',
            'departure_date',
            'dcv_admission',
            'private_visit',
        )
        read_only_fields = (
            'id',
        )


class NumberOfPeopleSerializer(serializers.ModelSerializer):

    def validate(self, data):
        return data

    class Meta:
        model = NumberOfPeople
        fields = (
            'id',
            'number',
            'dcv_admission_arrival',
            'age_group',
            'admission_type',
        )
        read_only_fields = (
            'id',
        )


class FeeSeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeSeason
        fields = (
            'id',
            'name'
        )


class DcvPermitSimpleSerializer(serializers.ModelSerializer):
    fee_season = FeeSeasonSerializer()
    dcv_organisation_name = serializers.SerializerMethodField()

    class Meta:
        model = DcvPermit
        fields = (
            'lodgement_number',
            'fee_season',
            'dcv_organisation_name',
        )

    def get_dcv_organisation_name(self, obj):
        try:
            if obj.dcv_organisation:
                return obj.dcv_organisation.name
            else:
                return obj.applicant_obj.get_full_name() + ' (P)'
        except:
            return ''


class DcvPermitSerializer(serializers.ModelSerializer):
    dcv_vessel_id = serializers.IntegerField(required=True)
    dcv_organisation_id = serializers.IntegerField(required=True)
    fee_season_id = serializers.IntegerField(required=True)

    def validate(self, data):
        field_errors = {}
        non_field_errors = []

        if not self.partial:
            if not data['fee_season_id']:
                field_errors['Season'] = ['Please select a season.',]

            #exclude cancelled permits from this list
            dcv_permit_qs = DcvPermit.objects.exclude(status=DcvPermit.DCV_PERMIT_STATUS_CANCELLED).filter(
                dcv_vessel_id=data.get('dcv_vessel_id', 0),
                fee_season_id=data.get('fee_season_id', 0),
            )
            if dcv_permit_qs:
                dcv_vessel = DcvVessel.objects.get(id=data.get('dcv_vessel_id'))
                fee_season = FeeSeason.objects.get(id=data.get('fee_season_id'))
                non_field_errors.append(f'DcvPermit for the vessel: {dcv_vessel} for the season: {fee_season.name} has been already issued.')

            # Raise errors
            if field_errors:
                raise serializers.ValidationError(field_errors)
            if non_field_errors:
                raise serializers.ValidationError(non_field_errors)

        return data

    def get_permits(self, obj):
        permit_urls = []
        for doc in obj.dcv_permit_documents.all():
            permit_urls.append(doc._file.url)

    class Meta:
        model = DcvPermit
        fields = (
            'id',
            'lodgement_number',
            'submitter',
            'applicant',
            'lodgement_datetime',
            'dcv_vessel_id',
            'dcv_organisation_id',
            'fee_season_id',
            'start_date',
            'end_date',
            'postal_address_line1',
            'postal_address_line2',
            'postal_address_line3',
            'postal_address_suburb',
            'postal_address_postcode',
            'postal_address_state',
            'postal_address_country',
        )
        read_only_fields = (
            'id',
            'lodgement_number',
            'start_date',
            'end_date',
        )


class FeeConstructorSerializer(serializers.ModelSerializer):
    start_date = serializers.ReadOnlyField()
    end_date = serializers.ReadOnlyField()
    fee_season = FeeSeasonSerializer()
    fee_items = serializers.SerializerMethodField()

    class Meta:
        model = FeeConstructor
        fields = (
            'id',
            'start_date',
            'end_date',
            'fee_season',
            'incur_gst',
            'fee_items',
        )

    def get_fee_items(self, fee_constructor):
        fee_configurations = {}

        for age_group in AgeGroup.NAME_CHOICES:
            fee_configurations[age_group[0]] = {}
        for fee_item in fee_constructor.feeitem_set.all():
            if fee_item.admission_type:
                fee_configurations[fee_item.age_group.code].update({fee_item.admission_type.code: fee_item.amount})

        return fee_configurations

