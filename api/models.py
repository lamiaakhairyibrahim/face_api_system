from django.db import models
import uuid
from django.contrib.postgres.fields import ArrayField 
from .tasks import calculate_embedding_task
from django.db.models.signals import post_save
from django.dispatch import receiver

class FaceLibrary(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="اسم المكتبة")
    description = models.TextField(blank=True, verbose_name="وصف المكتبة")
    creation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class FaceProfile(models.Model):
    face_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    library = models.ForeignKey(FaceLibrary, on_delete=models.CASCADE, related_name='faces', verbose_name="المكتبة المرتبطة")
    
    name = models.CharField(max_length=150, verbose_name="اسم الشخص")
    description = models.TextField(blank=True, verbose_name="وصف إضافي")
    face_image = models.ImageField(upload_to='faces_images/', verbose_name="صورة الوجه")
    face_embedding = ArrayField(models.FloatField(), size=128, blank=True, null=True, verbose_name="التمثيل الرقمي (Embedding)")
    is_registered = models.BooleanField(default=False, verbose_name="هل تم استخراج الـ Embedding؟")

    def __str__(self):
        return f"{self.name} ({self.library.name})"


class AccessLog(models.Model):
    profile = models.ForeignKey(FaceProfile, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="الشخص المعرف عليه")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ ووقت الحدث")
    is_recognized = models.BooleanField(default=False, verbose_name="هل تم التعرف عليه؟")
    snapshot_image = models.ImageField(upload_to='log_snapshots/', blank=True, null=True, verbose_name="صورة اللقطة")
    log_message = models.CharField(max_length=255, verbose_name="رسالة السجل")

    def __str__(self):
        return f"Log at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

@receiver(post_save, sender=FaceProfile)
def process_face_on_save(sender, instance, created, **kwargs):
    if created:
        calculate_embedding_task.delay(profile_id=instance.pk) 
        print(f"ASYNC Signal: Task submitted for {instance.name} with PK={instance.pk}.")

