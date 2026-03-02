import os

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from routers import email, images

app = FastAPI(title="Cynx Engage API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(email.router, prefix="/api/email", tags=["email"])
app.include_router(images.router, prefix="/api/images", tags=["images"])


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
