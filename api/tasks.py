# api/tasks.py
from celery import shared_task
import pandas as pd
from django.core.mail import send_mail
from django.conf import settings
from .models import Submission
from django.contrib.auth.models import Group
import logging

logger = logging.getLogger(__name__)

@shared_task
def parse_excel(sub_id):
    try:
        sub = Submission.objects.get(id=sub_id)
        if not sub.file.name.lower().endswith('.xlsx'):
            sub.status = 'error'
            sub.comments = 'Invalid file format. Only .xlsx files are accepted.'
            sub.save()
            return

        df = pd.read_excel(sub.file.path, engine='openpyxl')

        required_headers = ['timestamp', 'value', 'title', 'unit', 'start_date', 'end_date', 'type', 'sector']
        missing_headers = [col for col in required_headers if col not in df.columns]
        if missing_headers:
            sub.status = 'error'
            sub.comments = f'Missing required headers: {", ".join(missing_headers)}'
            sub.save()
            return

        # Check metadata consistency
        metadata_columns = ['title', 'unit', 'start_date', 'end_date', 'type', 'sector']
        metadata = {}
        for col in metadata_columns:
            unique_values = df[col].dropna().unique()
            if len(unique_values) != 1:
                sub.status = 'error'
                sub.comments = f'Inconsistent values in {col}. All rows must have the same value.'
                sub.save()
                return
            metadata[col] = unique_values[0] if len(unique_values) > 0 else None

        # Parse data with validation
        parsed_data = []
        for index, row in df.iterrows():
            try:
                timestamp = row['timestamp']
                if pd.isna(timestamp):
                    continue
                if not isinstance(timestamp, pd.Timestamp):
                    timestamp = pd.to_datetime(timestamp)
                timestamp_iso = timestamp.isoformat()

                value = row['value']
                if pd.isna(value):
                    continue
                value = float(value)

                parsed_data.append({
                    'timestamp': timestamp_iso,
                    'value': value,
                })
            except ValueError as e:
                sub.status = 'error'
                sub.comments = f'Invalid data in row {index + 2}: {str(e)}'
                sub.save()
                return

        if not parsed_data:
            sub.status = 'error'
            sub.comments = 'No valid data rows found in the Excel file.'
            sub.save()
            return

        sub.metadata = metadata
        sub.parsed_data = parsed_data
        sub.status = 'draft'
        sub.save()
    except Exception as e:
        logger.error(f'Error parsing submission {sub_id}: {str(e)}')
        try:
            sub = Submission.objects.get(id=sub_id)
            sub.status = 'error'
            sub.comments = f'Unexpected error: {str(e)}'
            sub.save()
        except:
            pass

@shared_task
def notify_manager(sub_id):
    try:
        sub = Submission.objects.get(id=sub_id)
        managers_group = Group.objects.get(name='InstitutionManager')
        managers = managers_group.user_set.all()
        for manager in managers:
            if manager.email:
                send_mail(
                    'New Data Submission Pending Review',
                    f'A new submission (ID: {sub.id}) has been submitted for your review.',
                    settings.DEFAULT_FROM_EMAIL,
                    [manager.email],
                )
    except Exception as e:
        logger.error(f'Error notifying managers for submission {sub_id}: {str(e)}')

@shared_task
def notify_senior(sub_id):
    try:
        sub = Submission.objects.get(id=sub_id)
        seniors_group = Group.objects.get(name='SeniorMoEOfficial')
        seniors = seniors_group.user_set.all()
        for senior in seniors:
            if senior.email:
                send_mail(
                    'Data Submission Pending Senior Approval',
                    f'A submission (ID: {sub.id}) has been approved by the manager and is pending your approval.',
                    settings.DEFAULT_FROM_EMAIL,
                    [senior.email],
                )
    except Exception as e:
        logger.error(f'Error notifying seniors for submission {sub_id}: {str(e)}')

@shared_task
def notify_provider_rejection(sub_id):
    try:
        sub = Submission.objects.get(id=sub_id)
        if sub.uploaded_by.email:
            send_mail(
                'Data Submission Rejected by Manager',
                f'Your submission (ID: {sub.id}) has been rejected. Comments: {sub.comments}',
                settings.DEFAULT_FROM_EMAIL,
                [sub.uploaded_by.email],
            )
    except Exception as e:
        logger.error(f'Error notifying provider for rejection {sub_id}: {str(e)}')

@shared_task
def notify_manager_rejection(sub_id):
    try:
        sub = Submission.objects.get(id=sub_id)
        managers_group = Group.objects.get(name='InstitutionManager')
        managers = managers_group.user_set.all()
        for manager in managers:
            if manager.email:
                send_mail(
                    'Data Submission Rejected by Senior',
                    f'Submission (ID: {sub.id}) has been rejected by senior. Comments: {sub.comments}',
                    settings.DEFAULT_FROM_EMAIL,
                    [manager.email],
                )
    except Exception as e:
        logger.error(f'Error notifying managers for senior rejection {sub_id}: {str(e)}')

@shared_task
def send_reminders():
    try:
        # Pending for managers
        pending_submitted = Submission.objects.filter(status='submitted')
        if pending_submitted.exists():
            managers_group = Group.objects.get(name='InstitutionManager')
            for manager in managers_group.user_set.all():
                if manager.email:
                    send_mail(
                        'Reminder: Pending Submissions',
                        f'You have {pending_submitted.count()} pending data submissions awaiting your review.',
                        settings.DEFAULT_FROM_EMAIL,
                        [manager.email],
                    )

        # Pending for seniors
        pending_manager_approved = Submission.objects.filter(status='manager_approved')
        if pending_manager_approved.exists():
            seniors_group = Group.objects.get(name='SeniorMoEOfficial')
            for senior in seniors_group.user_set.all():
                if senior.email:
                    send_mail(
                        'Reminder: Pending Senior Approvals',
                        f'You have {pending_manager_approved.count()} pending data submissions awaiting your approval.',
                        settings.DEFAULT_FROM_EMAIL,
                        [senior.email],
                    )
    except Exception as e:
        logger.error(f'Error sending reminders: {str(e)}')