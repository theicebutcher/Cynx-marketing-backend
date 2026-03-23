import os

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from routers import email, images, ai

app = FastAPI(title="Cynx Engage API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://*.vercel.app",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:5174",
        "https://cynx-engage.vercel.app",
        "https://cynx-email.vercel.app",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=3600,
)

app.include_router(email.router, prefix="/api/email", tags=["email"])
app.include_router(images.router, prefix="/api/images", tags=["images"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])


@app.get("/")
def root():
    return {"status": "ok", "service": "Cynx Engage API"}


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "Cynx Engage API",
        "env_check": {
            "SUPABASE_URL": "set" if os.getenv("SUPABASE_URL") else "missing",
            "CLOUDINARY": "set" if os.getenv("CLOUDINARY_CLOUD_NAME") else "missing",
            "SMTP": "set" if os.getenv("SMTP_HOST") else "missing",
            "GEMINI": "set" if os.getenv("GEMINI_API_KEY") else "missing",
        }
    }

@app.get("/api/health")
def health():
    return {"status": "ok", "env_check": {
        "SUPABASE_URL": "set" if os.getenv("SUPABASE_URL") else "missing",
        "CLOUDINARY": "set" if os.getenv("CLOUDINARY_CLOUD_NAME") else "missing",
        "SMTP": "set" if os.getenv("SMTP_HOST") else "missing",
    }}
