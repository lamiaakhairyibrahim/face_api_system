import json
import base64
import numpy as np
import cv2
import face_recognition
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.apps import apps
from django.db import connection

from .tasks import create_access_log_task 
from .ai_utils import recognize_face 

KNOWN_FACES_DATA = {
    'embeddings': [],
    'names': [],
    'profiles': []
}

class StreamConsumer(AsyncWebsocketConsumer):
    
    group_name = 'face_stream_group'

    async def connect(self):
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        print("WebSocket Connected and joined group: Ready for AI Stream.")
        
        await sync_to_async(self.load_known_faces)()


    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        print(f"WebSocket Disconnected with code: {close_code}")
        
    def load_known_faces(self):
        global KNOWN_FACES_DATA
        
        connection.close() 
        
        FaceProfile = apps.get_model('api', 'FaceProfile')
        all_profiles = FaceProfile.objects.filter(is_registered=True, face_embedding__isnull=False)
        
        KNOWN_FACES_DATA['embeddings'] = [p.face_embedding for p in all_profiles]
        KNOWN_FACES_DATA['names'] = [p.name for p in all_profiles]
        KNOWN_FACES_DATA['profiles'] = all_profiles
        print(f"Loaded {len(KNOWN_FACES_DATA['embeddings'])} known faces.")
        

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data)
            image_data_b64 = data.get('frame') 
            
            if not image_data_b64:
                return

            results = await sync_to_async(self.process_frame_and_recognize)(image_data_b64)
            
            await self.send(text_data=json.dumps({
                'status': 'processed',
                'detections': results
            }))
            
        except Exception as e:
            print(f"ERROR in Consumer Receive: {e}") 
            await self.send(text_data=json.dumps({'error': str(e), 'status': 'frame_error'}))


    def process_frame_and_recognize(self, image_data_b64):

        img_bytes = base64.b64decode(image_data_b64)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)
        print(f"DEBUG AI Check: Total faces detected in frame: {len(face_locations)}")

        results = []
        for face_encoding, (top, right, bottom, left) in zip(face_encodings, face_locations):
            
            match_index = recognize_face(
                unknown_encoding=face_encoding.tolist(), 
                known_embeddings=KNOWN_FACES_DATA['embeddings'],
                tolerance=0.62
            )
            print(f"DEBUG AI Check: Match Index found: {match_index}") 

            if match_index != -1:
                name = KNOWN_FACES_DATA['names'][match_index]
                is_recognized = True
                log_message = f"Recognition successful for {name}"
            else:
                name = "Stranger"
                is_recognized = False
                log_message = "New Stranger detected"

            create_access_log_task.delay(
                profile_name=name,
                log_message=log_message,
                is_recognized=is_recognized,
            )

            results.append({
                'name': name,
                'location': [top, right, bottom, left] 
            })

        return results

    async def reload_ai_library(self, event):
        await sync_to_async(self.load_known_faces)()

        await self.send(text_data=json.dumps({
            'type': 'status_update',
            'message': event['message'] 
        }))