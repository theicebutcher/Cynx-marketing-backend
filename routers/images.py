import os
import uuid
import base64
from typing import Optional

import cloudinary
import cloudinary.uploader
from google import genai
from google.genai import types
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from supabase import create_client

from auth import validate_token

router = APIRouter()

# ── Cloudinary ────────────────────────────────────────────────
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)

# ── Gemini (matching reference app) ──────────────────────────
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
GEMINI_MODEL = "gemini-3-pro-image-preview"

# ── Supabase (for saving generated image records) ─────────────
_sb = create_client(
    os.getenv("SUPABASE_URL", ""),
    os.getenv("SUPABASE_ANON_KEY", ""),
)


def _save_to_supabase(image_url: str, prompt: str, user_id: Optional[str]):
    """Save generated image record to Supabase generated_images table (matches reference app)."""
    try:
        _sb.table("generated_images").insert({
            "image_url": image_url,
            "prompt": prompt,
            "template_type": "campaign_hero",
            "original_filename": image_url.split("/")[-1],
            "user_id": user_id,
        }).execute()
    except Exception as e:
        # Non-fatal — log but don't break the response
        print(f"[images] Supabase save warning: {e}")


# ── Models ────────────────────────────────────────────────────

class UploadImageRequest(BaseModel):
    image: str          # base64-encoded (no data URI prefix)
    mimeType: str = "image/jpeg"
    folder: str = "cynx/campaigns"
    public_id: Optional[str] = None


class GenerateImageRequest(BaseModel):
    prompt: str
    folder: str = "cynx/campaigns"


# ── Routes ────────────────────────────────────────────────────

@router.post("/upload")
async def upload_image(
    req: UploadImageRequest,
    authorization: Optional[str] = Header(None),
):
    await validate_token(authorization)
    try:
        data_uri = f"data:{req.mimeType};base64,{req.image}"
        opts = {"folder": req.folder, "resource_type": "image"}
        if req.public_id:
            opts["public_id"] = req.public_id
        result = cloudinary.uploader.upload(data_uri, **opts)
        return {"url": result["secure_url"], "public_id": result["public_id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
async def generate_image(
    req: GenerateImageRequest,
    authorization: Optional[str] = Header(None),
):
    """Generate a campaign hero image with Gemini, upload to Cloudinary, save to Supabase."""
    user = await validate_token(authorization)
    user_id = user.get("id") if isinstance(user, dict) else None

    # ── 1. Generate with Gemini ───────────────────────────────
    try:
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[req.prompt],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"]
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gemini error: {e}")

    # Find the image part in the response
    img_part = None
    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data:
            img_part = part
            break

    if not img_part:
        raise HTTPException(status_code=502, detail="Gemini returned no image")

    mime_type = img_part.inline_data.mime_type   # e.g. "image/png"
    img_bytes = img_part.inline_data.data         # raw bytes

    # ── 2. Upload to Cloudinary ───────────────────────────────
    try:
        ext = "png" if "png" in mime_type else "jpg"
        public_id = f"cynx_campaign_{uuid.uuid4().hex[:8]}"
        b64 = base64.b64encode(img_bytes).decode()
        data_uri = f"data:{mime_type};base64,{b64}"
        result = cloudinary.uploader.upload(
            data_uri,
            folder=req.folder,
            resource_type="image",
            public_id=public_id,
        )
        image_url = result["secure_url"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cloudinary upload failed: {e}")

    # ── 3. Save record to Supabase ────────────────────────────
    _save_to_supabase(image_url, req.prompt, user_id)

    return {"url": image_url, "public_id": result["public_id"]}
