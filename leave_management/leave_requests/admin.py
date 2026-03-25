from django.contrib import admin

from .models import LeaveRequest


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'status', 'requested_at', 'manager')
    list_filter = ('leave_type', 'status', 'manager')
    search_fields = ('employee__email', 'employee__first_name', 'employee__last_name', 'reason')
    readonly_fields = ('requested_at', 'decided_at')
    ordering = ('-requested_at',)

