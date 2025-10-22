from django.urls import path
from .views import (
    UploadView, PreviewView, SubmitView,
    PendingManagerView, ApproveManagerView, RejectManagerView,
    PendingSeniorView, ApproveSeniorView, RejectSeniorView,
)

urlpatterns = [
    path('upload/', UploadView.as_view(), name='upload'),
    path('preview/<int:pk>/', PreviewView.as_view(), name='preview'),
    path('submit/<int:pk>/', SubmitView.as_view(), name='submit'),
    path('manager/pending/', PendingManagerView.as_view(), name='manager_pending'),
    path('manager/approve/<int:pk>/', ApproveManagerView.as_view(), name='manager_approve'),
    path('manager/reject/<int:pk>/', RejectManagerView.as_view(), name='manager_reject'),
    path('senior/pending/', PendingSeniorView.as_view(), name='senior_pending'),
    path('senior/approve/<int:pk>/', ApproveSeniorView.as_view(), name='senior_approve'),
    path('senior/reject/<int:pk>/', RejectSeniorView.as_view(), name='senior_reject'),
]