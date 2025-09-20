from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from livekit import api
import os
import uuid
from datetime import timedelta

app = FastAPI(title="DeskHelp Support API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LiveKit configuration
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")  
LIVEKIT_URL = os.getenv("LIVEKIT_URL")

@app.post("/api/token")
async def create_room_token():
    """Generate a LiveKit room token for anonymous users"""
    if not all([LIVEKIT_API_KEY, LIVEKIT_API_SECRET, LIVEKIT_URL]):
        raise HTTPException(status_code=500, detail="LiveKit configuration missing")
    
    session_id = str(uuid.uuid4())[:8]
    room_name = f"support-{session_id}"
    identity = f"customer-{session_id}"
    
    token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET) \
        .with_identity(identity) \
        .with_name(f"Customer {session_id}") \
        .with_grants(api.VideoGrants(
            room_join=True,
            room=room_name,
        )) \
        .with_ttl(timedelta(hours=1))
    
    return {
        "token": token.to_jwt(),
        "url": LIVEKIT_URL,
        "room": room_name,
        "session_id": session_id
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}