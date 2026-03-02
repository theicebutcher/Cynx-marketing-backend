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
