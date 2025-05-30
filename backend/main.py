from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
import io
import os
from PIL import Image
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Malaria Detection API",
    version="1.0.3"
)

# Configuration - Absolute paths
BASE_DIR = Path(__file__).parent.resolve()
MODEL_PATH = BASE_DIR / "malaria_cnn_model.keras"
FRONTEND_DIR = BASE_DIR.parent / "frontend"

# Serve frontend files directly from the frontend directory
app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")

# Model loading
try:
    logger.info("Loading malaria detection model...")
    model = load_model(MODEL_PATH)
    logger.info("Model loaded successfully")
except Exception as e:
    logger.critical(f"Model loading failed: {str(e)}")
    raise RuntimeError(f"Model initialization failed: {str(e)}")

# Prediction threshold
PREDICTION_THRESHOLD = 0.65


def preprocess_image(img):
    """Prepare image for model prediction"""
    try:
        target_size = model.input_shape[1:3]
        img = img.resize(target_size, Image.Resampling.LANCZOS)
        img_array = image.img_to_array(img)
        img_array = img_array / 255.0
        return np.expand_dims(img_array, axis=0)
    except Exception as e:
        logger.error(f"Image preprocessing failed: {str(e)}")
        raise HTTPException(status_code=400, detail="Image processing error")


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the frontend HTML"""
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return FileResponse(index_path)


@app.get("/style.css")
async def serve_css():
    """Serve CSS file"""
    css_path = FRONTEND_DIR / "style.css"
    if not css_path.exists():
        raise HTTPException(status_code=404, detail="CSS not found")
    return FileResponse(css_path)


@app.get("/script.js")
async def serve_js():
    """Serve JavaScript file"""
    js_path = FRONTEND_DIR / "script.js"
    if not js_path.exists():
        raise HTTPException(status_code=404, detail="JS not found")
    return FileResponse(js_path)


@app.post("/predict/")
async def predict(file: UploadFile = File(...)):
    """Handle malaria detection prediction"""
    try:
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Only image files supported")

        contents = await file.read()
        img = Image.open(io.BytesIO(contents)).convert('RGB')
        img_array = preprocess_image(img)

        prediction = model.predict(img_array, verbose=0)[0]

        if model.output_shape == (None, 1):
            raw_score = float(prediction[0])
            result = "parasitized" if raw_score > PREDICTION_THRESHOLD else "uninfected"
            confidence = raw_score if result == "parasitized" else 1 - raw_score
        else:
            uninfected_conf = float(prediction[0])
            parasitized_conf = float(prediction[1])
            result = "parasitized" if parasitized_conf > PREDICTION_THRESHOLD else "uninfected"
            confidence = parasitized_conf if result == "parasitized" else uninfected_conf

        return JSONResponse({
            "status": "success",
            "prediction": result,
            "confidence": round(confidence * 100, 2)
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Prediction error")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )