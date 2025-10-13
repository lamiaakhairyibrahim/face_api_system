from face_ai.celery import app
from celery import shared_task
from .ai_utils import get_face_embedding
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from datetime import timedelta

from django.utils import timezone

@app.task
def calculate_embedding_task(profile_id):
    """
    Celery task to asynchronously calculate the face embedding for a FaceProfile.

    Args:
        profile_id (uuid): The primary key (face_id) of the FaceProfile to process.
    """
    from .models import FaceProfile
    
    try:
        profile = FaceProfile.objects.get(face_id=profile_id) 
    except FaceProfile.DoesNotExist:
        print(f"Celery Error: Profile with ID {profile_id} not found.")
        return

    embedding_list = get_face_embedding(profile.face_image.name)
    
    if embedding_list:
        profile.face_embedding = embedding_list
        profile.is_registered = True
        profile.save(update_fields=['face_embedding', 'is_registered'])
        print(f"Celery Success: Embedding calculated and saved for {profile.name}.")

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "face_stream_group", 
            {
                "type": "reload_ai_library",
                "message": f"New profile {profile.name} saved. Reloading AI models.",
            }
        )
    else:
        print(f"Celery Warning: Face not detected in image for {profile.name}.")


@app.task
def create_access_log_task(profile_name, log_message, is_recognized, snapshot_base64=None):
    """
    Celery task to asynchronously create a new AccessLog entry.

    Args:
        profile_name (str): The name of the recognized person, or "Stranger".
        log_message (str): The detailed log description.
        is_recognized (bool): True if a profile was successfully matched.
        snapshot_base64 (str, optional): Base64 image data of the snapshot. (Currently unused).
    """
    from .models import AccessLog, FaceProfile
    
    profile = None
    if profile_name != "Stranger":
        try:
            profile = FaceProfile.objects.get(name=profile_name)
        except FaceProfile.DoesNotExist:
            profile = None

    AccessLog.objects.create(
        profile=profile,
        log_message=log_message,
        is_recognized=is_recognized,
    )
    print(f"Celery: Access Log created for {profile_name}.")

@shared_task 
def cleanup_old_logs():
    """
    Celery task to delete AccessLog entries older than 7 days.
    This task should be scheduled (e.g., using Celery Beat) to run daily.
    """
    from .models import AccessLog
    
    seven_days_ago = timezone.now() - timedelta(days=7)
    
    old_logs = AccessLog.objects.filter(timestamp__lt=seven_days_ago)
    
    deleted_count, _ = old_logs.delete()
    
    return f"Cleanup Success: Deleted {deleted_count} old logs (older than {seven_days_ago.strftime('%Y-%m-%d')})."