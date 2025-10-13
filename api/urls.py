from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FaceLibraryViewSet,
    FaceProfileViewSet,
    AccessLogViewSet,
    LiveStreamView,
    AccessLogView,
    )

router = DefaultRouter()
router.register(r'libraries', FaceLibraryViewSet)
router.register(r'profiles', FaceProfileViewSet)
router.register(r'logs', AccessLogViewSet)

urlpatterns = [
    path('', LiveStreamView.as_view(), name='live_stream'),
    path('logsv/', AccessLogView.as_view(), name='access_logs'),
    path('api/', include(router.urls)),

]