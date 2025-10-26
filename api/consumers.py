from django.apps import apps
from django.db import connection
import json
import base64
import numpy as np
import cv2
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

from .tasks import create_access_log_task 
from .ai_utils import recognize_face, get_app

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
        print(f"✅ Loaded {len(KNOWN_FACES_DATA['embeddings'])} known faces.")

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data)
            image_data_b64 = data.get('frame') 
            if not image_data_b64:
                return
            
            processed_frame_b64, detections = await sync_to_async(self.process_frame_and_recognize)(image_data_b64)
            
            await self.send(text_data=json.dumps({
                'status': 'processed',
                'frame': processed_frame_b64,
                'detections': detections
            }))
        except Exception as e:
            print(f"❌ ERROR in Consumer Receive: {e}")
            await self.send(text_data=json.dumps({'error': str(e), 'status': 'frame_error'}))


    def process_frame_and_recognize(self, image_data_b64):

        img_bytes = base64.b64decode(image_data_b64)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        app = get_app()
        
        faces = app.get(frame_rgb)
        
        results = []
        
        for face in faces:
            bbox = face.bbox.astype(int)
            left, top, right, bottom = bbox[0], bbox[1], bbox[2], bbox[3]
            
            face_embedding = face.embedding.tolist()
            
            match_index = recognize_face(
                unknown_embedding=face_embedding, 
                known_embeddings=KNOWN_FACES_DATA['embeddings'],
                tolerance=0.5
            )
            
            if match_index != -1:
                name = KNOWN_FACES_DATA['names'][match_index]
                is_recognized = True
                color = (16, 185, 129)
            else:
                name = "Stranger"
                is_recognized = False
                color = (239, 68, 68)
            
            log_message = f"Recognition successful for {name}" if is_recognized else "New Stranger detected"
            
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            cv2.putText(
                frame, 
                name, 
                (left + 6, bottom - 6), 
                cv2.FONT_HERSHEY_DUPLEX, 
                0.8, 
                (255, 255, 255), 
                1
            )
            
            create_access_log_task.delay(
                profile_name=name,
                log_message=log_message,
                is_recognized=is_recognized,
            )
            
            results.append({'name': name, 'is_recognized': is_recognized})
        
        _, buffer = cv2.imencode('.jpeg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        processed_frame_b64 = base64.b64encode(buffer).decode('utf-8')
        
        return processed_frame_b64, results

    async def reload_ai_library(self, event):
        await sync_to_async(self.load_known_faces)()

        await self.send(text_data=json.dumps({
            'type': 'status_update',
            'message': event['message'] 
        }))