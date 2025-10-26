# server/src/deps.py
import os
from typing import Optional
from fastapi import Header
DEMO_ID = os.getenv("DEMO_USER_ID", "user-demo-1")
async def current_user_id(x_user_id: Optional[str] = Header(default=None)):
    return x_user_id or DEMO_ID
