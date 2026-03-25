from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.shortcuts import redirect
from django.contrib import messages
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import User
from .models import LeaveRequest
from .serializers import LeaveRequestCreateSerializer, LeaveRequestSerializer


class IsEmployeeOrManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.role in (User.ROLE_MANAGER, User.ROLE_HR):
            return True
        return obj.employee_id == request.user.id


class LeaveRequestViewSet(viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.select_related('employee', 'manager').all()
    permission_classes = [permissions.IsAuthenticated, IsEmployeeOrManager]

    def get_serializer_class(self):
        if self.action == 'create':
            return LeaveRequestCreateSerializer
        return LeaveRequestSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in (User.ROLE_MANAGER, User.ROLE_HR):
            return self.queryset
        return self.queryset.filter(employee=user)

    def perform_create(self, serializer):
        serializer.save(employee=self.request.user, status=LeaveRequest.STATUS_PENDING)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve_request(self, request, pk=None):
        leave = get_object_or_404(LeaveRequest, pk=pk)
        if request.user.role not in (User.ROLE_MANAGER, User.ROLE_HR):
            return Response({'detail': 'Only manager or HR can approve'}, status=status.HTTP_403_FORBIDDEN)
        if leave.status != LeaveRequest.STATUS_PENDING:
            return Response({'detail': 'Only pending requests can be approved'}, status=status.HTTP_400_BAD_REQUEST)
        leave.approve(request.user)
        return Response({'status': 'approved'})

    @action(detail=True, methods=['post'], url_path='reject')
    def reject_request(self, request, pk=None):
        leave = get_object_or_404(LeaveRequest, pk=pk)
        if request.user.role not in (User.ROLE_MANAGER, User.ROLE_HR):
            return Response({'detail': 'Only manager or HR can reject'}, status=status.HTTP_403_FORBIDDEN)
        if leave.status != LeaveRequest.STATUS_PENDING:
            return Response({'detail': 'Only pending requests can be rejected'}, status=status.HTTP_400_BAD_REQUEST)
        leave.reject(request.user)
        return Response({'status': 'rejected'})


@login_required
def dashboard(request):
    user = request.user
    if user.role in (User.ROLE_MANAGER, User.ROLE_HR):
        pending = LeaveRequest.objects.filter(status=LeaveRequest.STATUS_PENDING)
    else:
        pending = LeaveRequest.objects.filter(employee=user, status=LeaveRequest.STATUS_PENDING)

    recent = LeaveRequest.objects.filter(employee=user).order_by('-requested_at')[:10] if user.role == User.ROLE_EMPLOYEE else LeaveRequest.objects.all().order_by('-requested_at')[:10]

    stats = {
        'total': LeaveRequest.objects.count(),
        'pending': LeaveRequest.objects.filter(status=LeaveRequest.STATUS_PENDING).count(),
        'approved': LeaveRequest.objects.filter(status=LeaveRequest.STATUS_APPROVED).count(),
        'rejected': LeaveRequest.objects.filter(status=LeaveRequest.STATUS_REJECTED).count(),
        'my_pending': LeaveRequest.objects.filter(employee=user, status=LeaveRequest.STATUS_PENDING).count(),
    }

    # Handle leave request creation for employees
    if request.method == 'POST' and user.role == User.ROLE_EMPLOYEE:
        from datetime import datetime
        leave_type = request.POST.get('leave_type')
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        reason = request.POST.get('reason', '')

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

            if end_date < start_date:
                messages.error(request, 'End date must be after start date.')
            else:
                LeaveRequest.objects.create(
                    employee=user,
                    leave_type=leave_type,
                    start_date=start_date,
                    end_date=end_date,
                    reason=reason,
                    status=LeaveRequest.STATUS_PENDING
                )
                messages.success(request, 'Leave request submitted successfully!')
                return redirect('leave_dashboard')
        except ValueError:
            messages.error(request, 'Invalid date format.')

    # Handle approve/reject actions for managers/HR
    if request.method == 'POST' and (user.role == User.ROLE_MANAGER or user.role == User.ROLE_HR):
        action = request.POST.get('action')
        leave_id = request.POST.get('leave_id')

        if action and leave_id:
            try:
                leave = LeaveRequest.objects.get(id=leave_id)
                if leave.status != LeaveRequest.STATUS_PENDING:
                    messages.error(request, 'Only pending requests can be processed.')
                elif action == 'approve':
                    leave.approve(user)
                    messages.success(request, f'Leave request #{leave.id} approved.')
                elif action == 'reject':
                    leave.reject(user)
                    messages.success(request, f'Leave request #{leave.id} rejected.')
                else:
                    messages.error(request, 'Invalid action.')
            except LeaveRequest.DoesNotExist:
                messages.error(request, 'Leave request not found.')
            except Exception as e:
                messages.error(request, f'Error processing request: {str(e)}')

            return redirect('leave_dashboard')

    return render(request, 'leave_requests/dashboard.html', {'pending': pending, 'recent': recent, 'stats': stats})


def register(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        role = request.POST.get('role')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'registration/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'registration/register.html')

        user = User.objects.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            password=password1
        )

        login(request, user)
        messages.success(request, 'Registration successful!')
        return redirect('leave_dashboard')

    return render(request, 'registration/register.html')
