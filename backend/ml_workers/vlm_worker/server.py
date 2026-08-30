import sys
from pathlib import Path

_here = Path(__file__).resolve().parent
sys.path.insert(0, str(_here.parents[1]))
if Path("/app").exists():
    sys.path.insert(0, "/app")

from fastapi import FastAPI, File, UploadFile

from app.services.vlm_engine import VLMEngine

app = FastAPI(title="VLM Worker")
engine = VLMEngine()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/extract")
async def extract(image: UploadFile = File(...)):
    data = await image.read()
    fields = await engine.extract_fields(data)
    return fields


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
