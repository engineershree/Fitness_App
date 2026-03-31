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
import os

# Force all logs to stdout for Render compatibility
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Only stdout for Render
    ],
    force=True  # Override any existing logging configuration
)

# Set specific loggers to appropriate levels
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)  # SQL queries
logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)  # Connection pool
logging.getLogger('fastapi').setLevel(logging.INFO)  # FastAPI framework
logging.getLogger('uvicorn').setLevel(logging.INFO)  # Uvicorn server
logging.getLogger('uvicorn.access').setLevel(logging.INFO)  # Access logs

# Ensure root logger is properly configured
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

# Create console handler for Render
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Add handler to root logger if not already present
if not root_logger.handlers:
    root_logger.addHandler(console_handler)

logger = logging.getLogger(__name__)
logger.info("Fitness App starting up...")
logger.info(f"Logging level: {logger.level}")
logger.info(f"Root logger handlers: {len(root_logger.handlers)}")
logger.info(f"Environment: {os.environ.get('ENVIRONMENT', 'development')}")

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
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Mount static files for media directory
app.mount("/media", StaticFiles(directory="app/media"), name="media")

# Include API routes
app.include_router(api_router, prefix="/api")

@app.get("/")
def root():
    logger.info("Root endpoint accessed")
    print("[CONSOLE] Root endpoint called - testing logging")
    return {"message": "Fitness App API is running"}

@app.get("/test-logging")
def test_logging():
    """Test endpoint to verify logging is working on Render"""
    logger.info("=== LOGGING TEST STARTED ===")
    logger.debug("Debug message test")
    logger.info("Info message test")
    logger.warning("Warning message test")
    logger.error("Error message test")
    
    print("[CONSOLE] === CONSOLE LOGGING TEST ===")
    print("[CONSOLE] Debug test message")
    print("[CONSOLE] Info test message")
    print("[CONSOLE] Warning test message")
    print("[CONSOLE] Error test message")
    
    return {
        "message": "Logging test completed",
        "timestamp": str(logger.handlers),
        "logger_level": logger.level,
        "console_output": "Check Render logs for console output"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
