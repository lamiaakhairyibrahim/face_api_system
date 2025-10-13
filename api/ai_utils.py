import face_recognition
import numpy as np
from django.conf import settings
import os


def get_face_embedding(image_path):
    try:
        full_image_path = os.path.join(settings.MEDIA_ROOT, image_path)
        image = face_recognition.load_image_file(full_image_path)
        face_locations = face_recognition.face_locations(image)

        if not face_locations or len(face_locations) > 1:
            print(f"ERROR: No face or multiple faces found in {image_path}")
            return None

        face_encodings = face_recognition.face_encodings(image, face_locations)
        
        return face_encodings[0].tolist()

    except Exception as e:
        print(f"AI Processing Error for {image_path}: {e}")
        return None

def recognize_face(unknown_encoding, known_embeddings, tolerance=0.62):
    if not known_embeddings:
        return -1

    known_encodings_array = np.array(known_embeddings)
    
    matches = face_recognition.compare_faces(
        known_face_encodings=known_encodings_array,
        face_encoding_to_check=np.array(unknown_encoding),
        tolerance=tolerance
    )
    
    try:
        first_match_index = matches.index(True)
        return first_match_index
    except ValueError:
        return -1