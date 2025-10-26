from rest_framework import serializers

from .models import FaceLibrary, FaceProfile, AccessLog

class FaceLibrarySerializer(serializers.ModelSerializer):
    class Meta:
        model = FaceLibrary
        fields = '__all__'

class FaceProfileSerializer(serializers.ModelSerializer):
    face_id = serializers.UUIDField(read_only=True) 

    class Meta:
        model = FaceProfile
        fields = ('face_id', 'library', 'name', 'description', 'face_image', 'is_registered')
        read_only_fields = ('is_registered',) 

class AccessLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessLog
        fields = '__all__'