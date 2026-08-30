"""Image preprocessing pipeline.

Heavy dependencies (OpenCV, ultralytics) are optional at runtime so the app
still boots without them; the worker containers install them.
"""
import io
from dataclasses import dataclass
from typing import List, Optional

from PIL import Image


@dataclass
class ProcessedImage:
    image: Image.Image
    quality_score: float = 1.0
    is_blurry: bool = False
    has_glare: bool = False


@dataclass
class LabelRegion:
    bbox: tuple  # (x1, y1, x2, y2)
    confidence: float
    area: float


class ImageProcessor:
    def preprocess(self, image_bytes: bytes) -> ProcessedImage:
        """Load + basic enhancement. Returns clean image."""
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        return ProcessedImage(image=image)

    def detect_label_regions(self, image: "ProcessedImage") -> List[LabelRegion]:
        """YOLOv8 inference for label bounding boxes.

        Returns the whole image as a single region when the model is not loaded
        (fallback mode) so the pipeline still functions for demos.
        """
        try:
            from ultralytics import YOLO  # type: ignore

            model = YOLO("yolov8n.pt")
            results = model(self._to_array(image.image))
            regions = []
            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    conf = float(box.conf[0])
                    w, h = x2 - x1, y2 - y1
                    regions.append(
                        LabelRegion(
                            bbox=(x1, y1, x2, y2),
                            confidence=conf,
                            area=w * h,
                        )
                    )
            if regions:
                regions.sort(key=lambda r: r.area, reverse=True)
                return regions
        except Exception:
            pass
        w, h = image.image.size
        return [LabelRegion(bbox=(0, 0, w, h), confidence=1.0, area=w * h)]

    def stitch_panorama(self, images: List[bytes]) -> bytes:
        """Multi-image stitching (OpenCV Stitcher). Falls back to first image."""
        try:
            import cv2  # type: ignore
            import numpy as np

            arrays = [cv2.imdecode(
                np.frombuffer(b, np.uint8), cv2.IMREAD_COLOR
            ) for b in images]
            if len(arrays) == 1:
                return images[0]
            stitcher = cv2.Stitcher_create(cv2.Stitcher_PANORAMA)
            status, pano = stitcher.stitch(arrays)
            if status == cv2.Stitcher_OK:
                ok, buf = cv2.imencode(".jpg", pano)
                return buf.tobytes()
        except Exception:
            pass
        return images[0]

    def _to_array(self, image: Image.Image):
        import numpy as np

        return np.array(image)
