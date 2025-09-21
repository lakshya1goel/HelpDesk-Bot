from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from livekit import api
import uuid
from datetime import timedelta
from config import config

app = FastAPI(title="DeskHelp Support API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/token")
async def create_room_token():
    """Generate a LiveKit room token for anonymous users"""
    if not config.validate_livekit_config():
        missing_vars = config.get_missing_livekit_vars()
        raise HTTPException(
            status_code=500, 
            detail=f"LiveKit configuration missing: {', '.join(missing_vars)}"
        )
    
    session_id = str(uuid.uuid4())[:8]
    room_name = f"support-{session_id}"
    identity = f"customer-{session_id}"
    
    token = api.AccessToken(config.LIVEKIT_API_KEY, config.LIVEKIT_API_SECRET) \
        .with_identity(identity) \
        .with_name(f"Customer {session_id}") \
        .with_grants(api.VideoGrants(
            room_join=True,
            room=room_name,
        )) \
        .with_ttl(timedelta(hours=1))
    
    return {
        "token": token.to_jwt(),
        "url": config.LIVEKIT_URL,
        "room": room_name,
        "session_id": session_id
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}