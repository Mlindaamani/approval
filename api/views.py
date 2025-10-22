# api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Submission
from .serializers import SubmissionSerializer, RejectSerializer
from .permissions import IsDataProvider, IsInstitutionManager, IsSeniorMoEOfficial
from .tasks import parse_excel, notify_manager, notify_senior, notify_provider_rejection, notify_manager_rejection
import logging

logger = logging.getLogger(__name__)

class UploadView(APIView):
    permission_classes = [IsDataProvider]

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        if not file.name.lower().endswith('.xlsx'):
            return Response({'error': 'Invalid file format. Only .xlsx files are accepted.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            submission = Submission.objects.create(uploaded_by=request.user, file=file, status='parsing')
            parse_excel.delay(submission.id)
            return Response({'id': submission.id, 'status': 'parsing'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f'Error creating submission: {str(e)}')
            return Response({'error': 'Failed to create submission'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PreviewView(APIView):
    permission_classes = [IsDataProvider]

    def get(self, request, pk):
        submission = get_object_or_404(Submission, pk=pk, uploaded_by=request.user)
        if submission.status in ['parsing']:
            return Response({'status': submission.status, 'message': 'Parsing in progress'})
        elif submission.status == 'error':
            return Response({'status': submission.status, 'error': submission.comments}, status=status.HTTP_400_BAD_REQUEST)
        serializer = SubmissionSerializer(submission)
        return Response(serializer.data)

class SubmitView(APIView):
    permission_classes = [IsDataProvider]

    def post(self, request, pk):
        submission = get_object_or_404(Submission, pk=pk, uploaded_by=request.user, status='draft')
        submission.status = 'submitted'
        submission.save()
        notify_manager.delay(submission.id)
        return Response({'status': 'submitted'})

class PendingManagerView(APIView):
    permission_classes = [IsInstitutionManager]

    def get(self, request):
        submissions = Submission.objects.filter(status='submitted')
        serializer = SubmissionSerializer(submissions, many=True)
        return Response(serializer.data)

class ApproveManagerView(APIView):
    permission_classes = [IsInstitutionManager]

    def post(self, request, pk):
        submission = get_object_or_404(Submission, pk=pk, status='submitted')
        submission.status = 'manager_approved'
        submission.save()
        notify_senior.delay(submission.id)
        return Response({'status': 'manager_approved'})

class RejectManagerView(APIView):
    permission_classes = [IsInstitutionManager]

    def post(self, request, pk):
        submission = get_object_or_404(Submission, pk=pk, status='submitted')
        serializer = RejectSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        submission.status = 'manager_rejected'
        submission.comments = serializer.validated_data['comment']
        submission.save()
        notify_provider_rejection.delay(submission.id)
        return Response({'status': 'manager_rejected'})

class PendingSeniorView(APIView):
    permission_classes = [IsSeniorMoEOfficial]

    def get(self, request):
        submissions = Submission.objects.filter(status='manager_approved')
        serializer = SubmissionSerializer(submissions, many=True)
        return Response(serializer.data)

class ApproveSeniorView(APIView):
    permission_classes = [IsSeniorMoEOfficial]

    def post(self, request, pk):
        submission = get_object_or_404(Submission, pk=pk, status='manager_approved')
        submission.status = 'finalized'
        submission.save()
        return Response({'status': 'finalized'})

class RejectSeniorView(APIView):
    permission_classes = [IsSeniorMoEOfficial]

    def post(self, request, pk):
        submission = get_object_or_404(Submission, pk=pk, status='manager_approved')
        serializer = RejectSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        submission.status = 'senior_rejected'
        submission.comments = serializer.validated_data['comment']
        submission.save()
        notify_manager_rejection.delay(submission.id)
        return Response({'status': 'senior_rejected'})