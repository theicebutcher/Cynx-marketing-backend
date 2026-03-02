import os
import httpx
from fastapi import HTTPException


async def validate_token(authorization: str | None) -> dict:
    """Validate a Supabase JWT by calling the Supabase auth API."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")

    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY", "")

    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{supabase_url}/auth/v1/user",
            headers={
                "Authorization": authorization,
                "apikey": supabase_anon_key,
            },
        )
        if res.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return res.json()
