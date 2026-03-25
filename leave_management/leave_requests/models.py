from django.db import models
from django.utils import timezone

from accounts.models import User


class LeaveRequest(models.Model):
    TYPE_ANNUAL = 'ANNUAL'
    TYPE_SICK = 'SICK'
    TYPE_UNPAID = 'UNPAID'

    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_CANCELLED = 'CANCELLED'

    LEAVE_TYPE_CHOICES = [
        (TYPE_ANNUAL, 'Annual'),
        (TYPE_SICK, 'Sick'),
        (TYPE_UNPAID, 'Unpaid'),
    ]

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    employee = models.ForeignKey(User, related_name='leave_requests', on_delete=models.CASCADE)
    manager = models.ForeignKey(User, related_name='managed_leave_requests', null=True, blank=True, on_delete=models.SET_NULL)
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES, default=TYPE_ANNUAL)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    requested_at = models.DateTimeField(default=timezone.now)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-requested_at']

    def __str__(self):
        return f"{self.employee.email} {self.leave_type} {self.start_date}..{self.end_date} [{self.status}]"

    @property
    def duration_days(self):
        return (self.end_date - self.start_date).days + 1

    def approve(self, manager):
        self.status = self.STATUS_APPROVED
        self.manager = manager
        self.decided_at = timezone.now()
        self.save(update_fields=['status', 'manager', 'decided_at'])

    def reject(self, manager):
        self.status = self.STATUS_REJECTED
        self.manager = manager
        self.decided_at = timezone.now()
        self.save(update_fields=['status', 'manager', 'decided_at'])

    def cancel(self):
        self.status = self.STATUS_CANCELLED
        self.decided_at = timezone.now()
        self.save(update_fields=['status', 'decided_at'])
