from rest_framework import serializers

from accounts.models import User
from .models import LeaveRequest


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'role')


class LeaveRequestSerializer(serializers.ModelSerializer):
    employee = UserSerializer(read_only=True)
    manager = UserSerializer(read_only=True)

    class Meta:
        model = LeaveRequest
        fields = (
            'id',
            'employee',
            'manager',
            'leave_type',
            'start_date',
            'end_date',
            'duration_days',
            'reason',
            'status',
            'requested_at',
            'decided_at',
        )
        read_only_fields = ('status', 'requested_at', 'decided_at', 'duration_days')


class LeaveRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRequest
        fields = ('leave_type', 'start_date', 'end_date', 'reason')

    def validate(self, attrs):
        if attrs['end_date'] < attrs['start_date']:
            raise serializers.ValidationError('end_date must be on or after start_date')
        return attrs
