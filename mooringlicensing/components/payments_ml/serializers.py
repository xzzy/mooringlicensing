from rest_framework import serializers

from mooringlicensing.components.approvals.models import DcvPermit


class DcvPermitSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    lodgement_number = serializers.ReadOnlyField()

    class Meta:
        model = DcvPermit
        fields = (
            'id',
            'lodgement_number',
        )
