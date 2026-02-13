"""
CollectorStream API - Backend for iOS app
FastAPI server with JWT authentication, card management, and Ximilar integration
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn
import os

from auth import router as auth_router
from cards import router as cards_router
from images import router as images_router
from admin import router as admin_router
from recommendations import router as recommendations_router
from contact import router as contact_router
from database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown

app = FastAPI(
    title="CollectorStream API",
    description="Backend API for CollectorStream iOS app - Sports card collection management",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - restricted to production domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://collectorstream.com",
        "https://www.collectorstream.com",
        "https://api.collectorstream.com",
        "http://localhost:3000",  # For local development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/v1/auth", tags=["Authentication"])
app.include_router(cards_router, prefix="/v1/cards", tags=["Cards"])
app.include_router(images_router, prefix="/v1/images", tags=["Images"])
app.include_router(admin_router, prefix="/v1/admin", tags=["Admin"])
app.include_router(recommendations_router, prefix="/v1/cards", tags=["Recommendations"])
app.include_router(contact_router, prefix="/v1", tags=["Contact"])

# Serve uploaded images
uploads_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
if os.path.exists(uploads_dir):
    app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

@app.get("/")
async def root():
    return {
        "name": "CollectorStream API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
