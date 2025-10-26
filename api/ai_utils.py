from django.conf import settings
import insightface
from insightface.app import FaceAnalysis
import numpy as np
import cv2
import os

app = FaceAnalysis(
    name='buffalo_l',
    providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
)
app.prepare(ctx_id=0, det_size=(640, 640))

print(f"✅ InsightFace initialized on: {app.det_model.providers}")


def get_face_embedding(image_path):
    try:
        full_image_path = os.path.join(settings.MEDIA_ROOT, image_path)
        image = cv2.imread(full_image_path)
        
        if image is None:
            print(f"ERROR: Cannot read image {image_path}")
            return None
        
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        faces = app.get(image_rgb)
        if len(faces) == 0:
            print(f"ERROR: No face found in {image_path}")
            return None
        all_embeddings = [face.embedding.tolist() for face in faces]
        print(f"INFO: Found {len(all_embeddings)} face(s) and extracted their embeddings.")
        return all_embeddings

    except Exception as e:
        print(f"AI Processing Error for {image_path}: {e}")
        return None


def recognize_face(unknown_embedding, known_embeddings, tolerance=0.5):
    if not known_embeddings or unknown_embedding is None:
        return -1

    try:
        unknown_emb = np.array(unknown_embedding)
        known_embs = np.array(known_embeddings)
        
        similarities = np.dot(known_embs, unknown_emb) / (
            np.linalg.norm(known_embs, axis=1) * np.linalg.norm(unknown_emb)
        )
        
        max_similarity_idx = np.argmax(similarities)
        max_similarity = similarities[max_similarity_idx]
        
        if max_similarity > tolerance:
            return int(max_similarity_idx)
        
        return -1

    except Exception as e:
        print(f"Recognition Error: {e}")
        return -1


def get_app():
    return app