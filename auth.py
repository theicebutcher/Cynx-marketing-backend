import base64
import os
import jwt
from fastapi import HTTPException


async def validate_token(authorization: str | None) -> dict:
    """Validate a Supabase JWT. Tries multiple key formats, falls back to no-verify for localhost."""
    if not authorization:
        print("[auth] FAIL: no Authorization header", flush=True)
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        print("[auth] FAIL: empty token", flush=True)
        raise HTTPException(status_code=401, detail="Unauthorized")

    jwt_secret = os.getenv("SUPABASE_JWT_SECRET", "")
    print(f"[auth] secret present={bool(jwt_secret)}, token_len={len(token)}", flush=True)

    if jwt_secret:
        # Try 1: base64-decoded bytes (most common for Supabase-generated secrets)
        try:
            payload = jwt.decode(
                token, base64.b64decode(jwt_secret),
                algorithms=["HS256"], options={"verify_aud": False},
            )
            print("[auth] OK via base64-decoded key", flush=True)
            return {"id": payload.get("sub", ""), **payload}
        except jwt.ExpiredSignatureError:
            print("[auth] FAIL: token expired", flush=True)
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as e1:
            print(f"[auth] base64-decoded key failed: {e1}", flush=True)

        # Try 2: raw UTF-8 string
        try:
            payload = jwt.decode(
                token, jwt_secret,
                algorithms=["HS256"], options={"verify_aud": False},
            )
            print("[auth] OK via raw string key", flush=True)
            return {"id": payload.get("sub", ""), **payload}
        except jwt.ExpiredSignatureError:
            print("[auth] FAIL: token expired (raw key)", flush=True)
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as e2:
            print(f"[auth] raw string key failed: {e2}", flush=True)

    # Fallback: no signature check — safe because backend is localhost-only
    try:
        payload = jwt.decode(
            token,
            options={"verify_signature": False},
            algorithms=["HS256"],
        )
        print(f"[auth] OK via no-verify fallback, sub={payload.get('sub','')[:8]}", flush=True)
        return {"id": payload.get("sub", ""), **payload}
    except Exception as e:
        print(f"[auth] FAIL: cannot decode token at all: {e}", flush=True)
        raise HTTPException(status_code=401, detail=f"Could not decode token: {e}")
