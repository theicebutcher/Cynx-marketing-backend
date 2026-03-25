import os
import httpx
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel

from auth import validate_token

router = APIRouter()

@router.post("/anthropic")
async def proxy_anthropic(
    request: Request,
    authorization: Optional[str] = Header(None),
):
    """Proxy requests to Anthropic API."""
    await validate_token(authorization)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not set on server")

    body = await request.json()
    system = body.pop("system", None)

    # Use a long timeout — full HTML email generation can take 2-3 minutes
    async with httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=10.0)) as client:
        try:
            res = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    **body,
                    **({"system": system} if system else {})
                },
            )
            data = res.json()
            if res.status_code != 200:
                print(f"Anthropic error ({res.status_code}): {data}")
                raise HTTPException(status_code=res.status_code, detail=data.get("error", {}).get("message", "Anthropic Error"))
            return data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Anthropic proxy error: {str(e)}")

@router.post("/openai")
async def proxy_openai(
    request: Request,
    authorization: Optional[str] = Header(None),
):
    """Proxy requests to OpenAI API."""
    await validate_token(authorization)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set on server")

    body = await request.json()
    
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                json=body,
                timeout=60.0
            )
            return res.json()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"OpenAI proxy error: {str(e)}")

@router.post("/gemini")
async def proxy_gemini(
    request: Request,
    authorization: Optional[str] = Header(None),
):
    """Proxy requests to Gemini API."""
    await validate_token(authorization)
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not set on server")

    body = await request.json()
    model = body.pop("model", "gemini-2.0-flash")
    
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
                headers={"Content-Type": "application/json"},
                json=body,
                timeout=60.0
            )
            return res.json()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Gemini proxy error: {str(e)}")
