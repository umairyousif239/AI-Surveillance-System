from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

# IMPORTANT: We now import the process managers from vision
from backend.api.vision import router as vision_router, start_vision, stop_vision
from backend.api.alerts import router as alerts_router
from backend.api.sensors import router as sensors_router
from backend.api.login import router as auth_router, get_password_hash

from backend.modules.auth_store import init_auth_db, create_user_in_db
from backend.modules.alert_loop import alert_loop

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auth Database Startup
    init_auth_db()
    hashed_pw = get_password_hash("fyp2026")
    create_user_in_db("admin", hashed_pw)
    print("Auth Database initialized")
    
    # 1. Start the isolated YOLO Multiprocessing Engine
    start_vision()
    print("✅ Vision AI Multiprocessing Engine started")

    # 2. Start the Alert Fusion loop
    task = asyncio.create_task(alert_loop())
    print("✅ Alert evaluation loop started")

    yield  # FastAPI Server handles web traffic here

    # Shutdown Sequence (Zombie Process Prevention)
    task.cancel()
    stop_vision()
    print("🛑 Shutting down backend safely")

app = FastAPI(
    title="AI Surveillance Backend",
    description="Edge Inference and Streaming",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost",       
        "capacitor://localhost"   
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(vision_router)
app.include_router(sensors_router)
app.include_router(alerts_router)

@app.get("/")
def root():
    return {
        "status": "running",
        "services": ["vision", "sensors", "alerts"],
        "architecture": "multiprocessing"
    }