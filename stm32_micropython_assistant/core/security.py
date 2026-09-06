"""
Simple API key check for the mobile endpoint.

Security note: since this key ships inside the compiled Android APK, it can
be extracted by anyone who decompiles the app. This is NOT a complete
security solution — it's a first line of defense against casual bots and
direct scripted abuse of the endpoint. For stronger protection later,
consider Firebase App Check or a per-install device token issued by the
server on first run.
"""

import os
from fastapi import Header, HTTPException, status

MOBILE_APP_API_KEY = os.getenv("MOBILE_APP_API_KEY", "")


async def verify_mobile_api_key(x_app_key: str = Header(default=None)):
    """
    FastAPI dependency. Raises 401 if the `X-App-Key` header doesn't match
    the configured secret. If MOBILE_APP_API_KEY is not set in .env (e.g.
    local development), the check is skipped so you don't get locked out —
    make sure to set a real value before deploying publicly.
    """
    if not MOBILE_APP_API_KEY:
        return

    if x_app_key != MOBILE_APP_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )
