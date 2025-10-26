from django.contrib import admin

from .models import FaceLibrary, FaceProfile, AccessLog

@admin.register(FaceProfile)
class FaceProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'library', 'is_registered', 'face_id')
    list_filter = ('library', 'is_registered')
    search_fields = ('name', 'face_id')
    readonly_fields = ('face_id', 'is_registered', 'face_embedding')

@admin.register(FaceLibrary)
class FaceLibraryAdmin(admin.ModelAdmin):
    list_display = ('name', 'creation_date')

@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'profile_name', 'is_recognized', 'log_message')
    list_filter = ('is_recognized', 'timestamp')
    search_fields = ('profile__name', 'log_message')

    def profile_name(self, obj):
        return obj.profile.name if obj.profile else "Stranger"
    profile_name.short_description = 'الشخص'
