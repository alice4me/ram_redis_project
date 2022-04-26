from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from ram_redis_app.config import DATETIME_FORMAT, LOAD_CHOICES


class SingleLoadSerializer(serializers.Serializer):
    load_type = serializers.ChoiceField(
       choices=LOAD_CHOICES,
       error_messages={'invalid_choice': 'Incorrect input data. Please, select from {}'.format(LOAD_CHOICES)}
    )


class DateTimeSerializer(serializers.Serializer):
    date_from = serializers.DateTimeField(format=DATETIME_FORMAT, input_formats=[DATETIME_FORMAT], required=False)
    date_to = serializers.DateTimeField(format=DATETIME_FORMAT, input_formats=[DATETIME_FORMAT], required=False)

    def validate(self, validated_data):
        date_from = validated_data.get('date_from')
        date_to = validated_data.get('date_to')
        if all([date_from, date_to]) and date_to < date_from:
            raise ValidationError('Date_to lower than date_from')
        return validated_data
