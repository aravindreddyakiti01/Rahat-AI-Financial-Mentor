from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import APP_TITLE, APP_DESCRIPTION, APP_VERSION
from app.db.database import init_db
from app.db.repository import seed_factual_demo_data
from app.memory.hindsight import hindsight
from app.routers import auth, finance, goals, memory, agent, insights, demo

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    seed_factual_demo_data("demo_user")
    hindsight.seed_demo_memories("demo_user")
    yield
    # Shutdown

app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register modular routers
app.include_router(auth.router)
app.include_router(finance.router)
app.include_router(goals.router)
app.include_router(memory.router)
app.include_router(agent.router)
app.include_router(insights.router)
app.include_router(demo.router)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "product": "Rahat",
        "agent": "LangGraph Financial Mentor",
        "memory_layer": "Hindsight",
        "timestamp": datetime.now().isoformat()
    }
