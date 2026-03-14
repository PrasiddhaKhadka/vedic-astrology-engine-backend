from rest_framework import serializers


class BirthDataSerializer(serializers.Serializer):
    """Input serializer for birth data — used by all chart endpoints."""

    year   = serializers.IntegerField(min_value=1800, max_value=2100)
    month  = serializers.IntegerField(min_value=1, max_value=12)
    day    = serializers.IntegerField(min_value=1, max_value=31)
    hour   = serializers.IntegerField(min_value=0, max_value=23)
    minute = serializers.IntegerField(min_value=0, max_value=59)

    # Geographic coordinates of birth location
    latitude  = serializers.FloatField(min_value=-90.0,  max_value=90.0)
    longitude = serializers.FloatField(min_value=-180.0, max_value=180.0)

    # Optional: UTC offset in hours (e.g. +5.5 for IST, +5.75 for NPT)
    utc_offset = serializers.FloatField(default=0.0)

    # Optional: house system preference
    house_system = serializers.ChoiceField(
        choices=['whole_sign', 'placidus', 'equal', 'koch'],
        default='whole_sign'
    )

    def validate(self, data):
        """Cross-field validation."""
        import calendar
        max_day = calendar.monthrange(data['year'], data['month'])[1]
        if data['day'] > max_day:
            raise serializers.ValidationError(
                f"Day {data['day']} is invalid for month {data['month']}/{data['year']}"
            )
        return data