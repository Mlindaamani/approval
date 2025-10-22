from django.db import models

from django.contrib.auth.models import User

class Submission(models.Model):
    STATUS_CHOICES = [
        ('parsing', 'Parsing'),
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('manager_approved', 'Approved by Manager'),
        ('manager_rejected', 'Rejected by Manager'),
        ('finalized', 'Finalized'),
        ('senior_rejected', 'Rejected by Senior'),
        ('error', 'Error'),
    ]

    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    file = models.FileField(upload_to='excels/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='parsing')
    metadata = models.JSONField(null=True, blank=True)
    parsed_data = models.JSONField(null=True, blank=True)
    comments = models.TextField(blank=True)

    def __str__(self):
        return f"Submission {self.id} by {self.uploaded_by.username}"