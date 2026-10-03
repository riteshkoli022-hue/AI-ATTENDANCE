"""Local face verification adapter using OpenCV's free Haar detector.

This is an educational demo matcher, not a secure biometric identity system. It
stores a normalized 128x128 grayscale face crop and compares it using cosine
similarity. For real deployment use a vetted liveness-capable system and obtain
informed consent; client photos and GPS can be spoofed in a local demo.
"""
import base64
import re
import cv2
import numpy as np

DATA_URL = re.compile(r"^data:image/(?:jpeg|png|webp);base64,([A-Za-z0-9+/=]+)$")
CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

class FaceError(ValueError):
    pass

def _extract(data_url):
    match = DATA_URL.match(data_url or "")
    if not match:
        raise FaceError("Choose a valid camera image (JPEG or PNG).")
    try:
        raw = base64.b64decode(match.group(1), validate=True)
    except Exception as exc:
        raise FaceError("The camera image could not be read.") from exc
    if not raw or len(raw) > 1_500_000:
        raise FaceError("The camera image is empty or too large.")
    image = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise FaceError("The camera image could not be decoded.")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = CASCADE.detectMultiScale(gray, 1.15, 5, minSize=(70, 70))
    if len(faces) == 0:
        raise FaceError("No face detected. Move into good light and face the camera.")
    if len(faces) > 1:
        raise FaceError("More than one face detected. Make sure only you are in frame.")
    x, y, w, h = faces[0]
    crop = gray[y:y+h, x:x+w]
    crop = cv2.resize(crop, (128, 128), interpolation=cv2.INTER_AREA).astype(np.float32)
    crop = (crop - crop.mean()) / (crop.std() + 1e-6)
    return crop.flatten()

def encode_face(data_url):
    vector = _extract(data_url)
    # compact local representation; no raw camera image is retained
    return base64.b64encode(vector.astype(np.float32).tobytes()).decode("ascii")

def verify_face(profile, data_url, threshold=0.78):
    try:
        reference = np.frombuffer(base64.b64decode(profile, validate=True), dtype=np.float32)
        sample = _extract(data_url)
    except (ValueError, TypeError) as exc:
        if isinstance(exc, FaceError):
            raise
        raise FaceError("Face profile is invalid. Register your face again.") from exc
    if reference.shape != sample.shape:
        raise FaceError("Face profile is invalid. Register your face again.")
    similarity = float(np.dot(reference, sample) / ((np.linalg.norm(reference) * np.linalg.norm(sample)) + 1e-9))
    return similarity >= float(threshold), round(similarity, 3)
