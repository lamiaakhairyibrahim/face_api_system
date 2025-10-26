from django.shortcuts import render
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator
from django.utils import timezone

from rest_framework import viewsets

from .models import FaceLibrary, FaceProfile, AccessLog
from .serializers import FaceLibrarySerializer, FaceProfileSerializer, AccessLogSerializer

class FaceLibraryViewSet(viewsets.ModelViewSet):
    queryset = FaceLibrary.objects.all()
    serializer_class = FaceLibrarySerializer

class FaceProfileViewSet(viewsets.ModelViewSet):
    queryset = FaceProfile.objects.all()
    serializer_class = FaceProfileSerializer
    
class AccessLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AccessLog.objects.all().order_by('-timestamp')
    serializer_class = AccessLogSerializer

@method_decorator(login_required(login_url='/login/'), name='dispatch')
class LiveStreamView(View):
    def get(self, request):
        return render(request, 'api/index.html')

class AccessLogView(View):
    def get(self, request):
        
        today_start = timezone.localdate()
        today_logs_count = AccessLog.objects.filter(
            timestamp__gte=today_start
        ).count()
        
        log_list = AccessLog.objects.all().order_by('-timestamp')
        paginator = Paginator(log_list, 100) 
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context = {
            'logs': page_obj,
            'today_visitors_count': today_logs_count,
        }

        return render(request, 'api/logs.html', context)
