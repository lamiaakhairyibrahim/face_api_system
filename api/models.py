from django.db import models
from django.contrib.postgres.fields import ArrayField 
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _ 
from django.db import transaction
import uuid

from .tasks import calculate_embedding_task

class FaceLibrary(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("اسم المكتبة"))
    description = models.TextField(blank=True, verbose_name=_("وصف المكتبة"))
    creation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class FaceProfile(models.Model):
    face_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    library = models.ForeignKey(FaceLibrary, on_delete=models.CASCADE, related_name='faces', verbose_name=_("المكتبة المرتبطة"))
    
    name = models.CharField(max_length=150, verbose_name=_("اسم الشخص"))
    description = models.TextField(blank=True, verbose_name=_("وصف إضافي"))
    face_image = models.ImageField(upload_to='faces_images/', verbose_name=_("صورة الوجه"))
    face_embedding = ArrayField(models.FloatField(), size=128, blank=True, null=True, verbose_name=_("التمثيل الرقمي (Embedding)"))
    is_registered = models.BooleanField(default=False, verbose_name=_("هل تم استخراج الـ Embedding؟"))

    def __str__(self):
        return f"{self.name} ({self.library.name})"


class AccessLog(models.Model):
    profile = models.ForeignKey(FaceProfile, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("الشخص المعرف عليه"))
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ ووقت الحدث"))
    is_recognized = models.BooleanField(default=False, verbose_name=_("هل تم التعرف عليه؟"))
    snapshot_image = models.ImageField(upload_to='log_snapshots/', blank=True, null=True, verbose_name=_("صورة اللقطة"))
    log_message = models.CharField(max_length=255, verbose_name=_("رسالة السجل"))

    def __str__(self):
        return f"Log at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

@receiver(post_save, sender=FaceProfile)
def process_face_on_save(sender, instance, created, **kwargs):
    if created:
        transaction.on_commit(
            lambda: calculate_embedding_task.delay(profile_id=instance.pk)
        )
        print(f"ASYNC Signal: Task submitted for {instance.name} with PK={instance.pk} (On Commit).")

