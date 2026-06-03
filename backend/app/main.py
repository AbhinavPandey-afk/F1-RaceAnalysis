from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.telemetry import router as telemetry_router
from app.routes.ai_analysis import router as ai_router
from app.routes.strategy import router as strategy_router
from app.routes.drivers import router as drivers_router

app = FastAPI()

# ==========================================
# CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# ROUTERS
# ==========================================

app.include_router(telemetry_router)
app.include_router(ai_router)
app.include_router(strategy_router)
app.include_router(drivers_router)

# ==========================================
# ROOT
# ==========================================

@app.get("/")
def home():
    return {
        "message": "RaceMind AI Backend Running"
    }