from fastapi import Header, HTTPException
from typing import Optional

def verify_api_key(
    authorization: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
):
    """Simple hardcoded test key - no database needed for local dev"""
    api_key = None

    # Check Authorization: Bearer xxx header
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            api_key = parts[1].strip()

    # Also accept X-API-Key header
    if not api_key and x_api_key:
        api_key = x_api_key.strip()

    # Accept "testkey" (what the GUI sends)
    if api_key == "testkey":
        # Fake user so the rest of the code works
        return type("FakeUser", (), {"id": 1, "api_key": api_key})()

    raise HTTPException(status_code=401, detail="Invalid API key")