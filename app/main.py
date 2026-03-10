from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.router import api_router
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import admin_router
from app.core.database import engine, Base
from app.models import *
import logging
import sys

# Configure logging for production debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Log to console for Render
        logging.FileHandler('fitness_app.log')  # Log to file
    ]
)

# Set specific loggers to appropriate levels
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)  # SQL queries
logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)  # Connection pool
logging.getLogger('fastapi').setLevel(logging.INFO)  # FastAPI framework
logging.getLogger('uvicorn').setLevel(logging.INFO)  # Uvicorn server

logger = logging.getLogger(__name__)
logger.info("Fitness App starting up...")

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Fitness App API")

# Configure CORS for admin frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React Admin Dev
        # Add your production admin domain here
        # "https://admin.yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Mount static files for media directory
app.mount("/media", StaticFiles(directory="app/media"), name="media")

# Include API routes
app.include_router(api_router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Fitness App API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
