from rest_framework import serializers

from users.models import WaitlistEntry


class WaitlistEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = WaitlistEntry
        fields = ['id', 'email', 'role', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_email(self, value):
        if WaitlistEntry.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('This email is already on the waitlist.')
        return value
