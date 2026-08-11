from django.urls import path
from automation.views import (
    AutoApplyConfigurationView,
    AutoApplyEnableView,
    AutoApplyPauseView,
    AutoApplyRunListView,
    UserActionRequiredListView
)

urlpatterns = [
    path('auto-apply/config/', AutoApplyConfigurationView.as_view(), name='auto_apply_config'),
    path('auto-apply/enable/', AutoApplyEnableView.as_view(), name='auto_apply_enable'),
    path('auto-apply/pause/', AutoApplyPauseView.as_view(), name='auto_apply_pause'),
    path('auto-apply/runs/', AutoApplyRunListView.as_view(), name='auto_apply_runs'),
    path('auto-apply/action-required/', UserActionRequiredListView.as_view(), name='auto_apply_action_required'),
]
