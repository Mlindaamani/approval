# api/serializers.py
from rest_framework import serializers
from .models import Submission

class SubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ['id', 'status', 'metadata', 'parsed_data', 'comments', 'file']

class RejectSerializer(serializers.Serializer):
    comment = serializers.CharField(required=True, min_length=1)