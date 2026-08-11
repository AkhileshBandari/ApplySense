from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from automation.models import AutoApplyConfiguration, AutoApplyRun, UserActionRequired
from automation.serializers import (
    AutoApplyConfigurationSerializer, 
    AutoApplyRunSerializer, 
    UserActionRequiredSerializer
)

class AutoApplyConfigurationView(generics.RetrieveUpdateAPIView):
    serializer_class = AutoApplyConfigurationSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        obj, created = AutoApplyConfiguration.objects.get_or_create(user=self.request.user)
        return obj

class AutoApplyEnableView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        config, created = AutoApplyConfiguration.objects.get_or_create(user=request.user)
        config.auto_apply_enabled = True
        config.save()
        return Response({"status": "Auto Apply Enabled"}, status=status.HTTP_200_OK)

class AutoApplyPauseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        config, created = AutoApplyConfiguration.objects.get_or_create(user=request.user)
        config.auto_apply_enabled = False
        config.save()
        return Response({"status": "Auto Apply Paused"}, status=status.HTTP_200_OK)

class AutoApplyRunListView(generics.ListAPIView):
    serializer_class = AutoApplyRunSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AutoApplyRun.objects.filter(user=self.request.user).order_by('-created_at')

class UserActionRequiredListView(generics.ListAPIView):
    serializer_class = UserActionRequiredSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserActionRequired.objects.filter(user=self.request.user, resolved_at__isnull=True)
