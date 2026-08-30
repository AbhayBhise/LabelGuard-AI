import sys
from pathlib import Path

_here = Path(__file__).resolve().parent
sys.path.insert(0, str(_here.parents[1]))
if Path("/app").exists():
    sys.path.insert(0, "/app")

from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile
import numpy as np
import cv2

from app.services.font_detector import FontSizeDetector

app = FastAPI(title="Layout / Font Worker")
detector = FontSizeDetector()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/px-per-mm")
async def px_per_mm(image: UploadFile = File(...)):
    data = await image.read()
    arr = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    ratio = detector.compute_px_per_mm(arr)
    return {"px_per_mm": ratio}


@app.post("/font-heights")
async def font_heights(
    image: UploadFile = File(...),
    net_weight_grams: Optional[float] = Form(None),
):
    data = await image.read()
    arr = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    px_per_mm = detector.compute_px_per_mm(arr)
    min_height = detector.min_height_for(net_weight_grams or 0)
    return {
        "px_per_mm": px_per_mm,
        "min_height_mm": min_height,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
