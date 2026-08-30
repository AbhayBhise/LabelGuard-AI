import sys
from pathlib import Path

_here = Path(__file__).resolve().parent
# Local dev: backend root (where app/ lives) is 2 levels up.
sys.path.insert(0, str(_here.parents[1]))
# Docker: app is copied to /app/app and server to /app/server.py
if Path("/app").exists():
    sys.path.insert(0, "/app")

from fastapi import FastAPI, File, UploadFile
import numpy as np
import cv2

from app.services.ocr_engine import OCREngine

app = FastAPI(title="OCR Worker")
engine = OCREngine()


@app.get("/health")
def health():
    return {"status": "ok", "ocr_available": engine.available}


@app.post("/ocr")
async def ocr(image: UploadFile = File(...)):
    data = await image.read()
    arr = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    result = engine.extract(arr)
    return {
        "words": [
            {
                "text": w.text,
                "bbox": w.bbox.to_dict(),
                "confidence": w.confidence,
            }
            for w in result.words
        ]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
