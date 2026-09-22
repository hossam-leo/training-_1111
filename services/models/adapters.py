"""Optional model adapters. Heavy dependencies are optional and never silently fail."""
from dataclasses import dataclass
from typing import Any

@dataclass
class Detection:
    event_type: str
    payload: dict[str, Any]
    confidence: float | None
    usable: bool
    model_version: str

class BaseAdapter:
    name = 'base'
    version = 'unknown-1'
    def infer(self, frame: Any) -> Detection:
        return Detection('PRESENCE_UNKNOWN', {'reason':'adapter not configured'}, None, False, self.version)

class OpenCVHaarFaceAdapter(BaseAdapter):
    name = 'opencv-haar-face'
    version = 'opencv-haar-1'
    def __init__(self, cascade_path: str | None = None):
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError('Install opencv-python-headless to enable the CPU face adapter') from exc
        self.cv2 = cv2
        self.detector = cv2.CascadeClassifier(cascade_path or cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    def infer(self, frame: Any) -> Detection:
        gray = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2GRAY) if len(getattr(frame, 'shape', ())) == 3 else frame
        faces = self.detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        boxes = [{'x':int(x),'y':int(y),'w':int(w),'h':int(h)} for x,y,w,h in faces]
        event = 'FACE_ABSENT' if not boxes else ('MULTI_FACE' if len(boxes)>1 else 'FACE_PRESENT')
        brightness=float(gray.mean()) if getattr(gray,'size',0) else 0.0
        sharpness=float(self.cv2.Laplacian(gray,self.cv2.CV_64F).var()) if getattr(gray,'size',0) else 0.0
        quality={'brightness':round(brightness,3),'sharpness_laplacian_var':round(sharpness,3),'usable':bool(20<=brightness<=235 and sharpness>=10 and boxes)}
        return Detection(event, {'face_count':len(boxes),'boxes':boxes,'quality':quality,'input_schema':'BGR uint8 image HxWx3'}, 0.8 if boxes else 0.5, True, self.version)

class ONNXAdapter(BaseAdapter):
    name = 'onnx-runtime'
    version = 'onnx-configured-1'
    def __init__(self, model_path: str):
        try:
            import onnxruntime as ort
        except ImportError as exc:
            raise RuntimeError('Install onnxruntime or onnxruntime-gpu to enable this adapter') from exc
        self.session = ort.InferenceSession(model_path, providers=ort.get_available_providers())
    def infer(self, tensor: Any) -> Detection:
        inputs = {self.session.get_inputs()[0].name: tensor}
        outputs = self.session.run(None, inputs)
        return Detection('MODEL_OUTPUT', {'outputs': [o.tolist() if hasattr(o, 'tolist') else o for o in outputs]}, None, True, self.version)


def make_adapter(kind: str, **kwargs):
    if kind == 'opencv_haar_face': return OpenCVHaarFaceAdapter(**kwargs)
    if kind == 'onnx': return ONNXAdapter(**kwargs)
    return BaseAdapter()
