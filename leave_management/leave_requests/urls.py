from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import LeaveRequestViewSet, dashboard, register

router = DefaultRouter()
router.register(r'leave-requests', LeaveRequestViewSet, basename='leave-request')

urlpatterns = [
    path('api/', include(router.urls)),
    path('dashboard/', dashboard, name='leave_dashboard'),
    path('register/', register, name='register'),
]
