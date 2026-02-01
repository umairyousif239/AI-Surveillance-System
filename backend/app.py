from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio

from backend.api.vision import router as vision_router
from backend.api.alerts import router as alerts_router
from backend.api.sensors import router as sensors_router
from backend.modules.alert_loop import alert_loop

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    task = asyncio.create_task(alert_loop())
    print("✅ Alert evaluation loop started")

    yield  # App runs here

    # Shutdown (optional cleanup)
    task.cancel()
    print("🛑 Shutting down backend")

app = FastAPI(
    title="AI Surveillance Backend",
    description="Edge Inference and Streaming",
    version="0.1.0",
    lifespan=lifespan
)

# Usage of vision API
app.include_router(vision_router)

# Usage of Sensor ingestion (ESP32 → backend) API
app.include_router(sensors_router)

# Usage of Alert evaluation & retrieval API
app.include_router(alerts_router)

# Health Check
@app.get("/")
def root():
    return {
        "status": "running",
        "services": ["vision", "sensors", "alerts"],
        "alerts_mode": "background"
    }