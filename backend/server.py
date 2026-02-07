from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import socketio
import os
import logging
import httpx
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from math import radians, sin, cos, sqrt, atan2

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Socket.IO setup
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

# Create the main app
app = FastAPI()

# Socket.IO ASGI app
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class Coordinates(BaseModel):
    lat: float
    lng: float

class User(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    profile_images: List[str] = []  # Up to 6 images in base64
    bio: Optional[str] = None
    verified: bool = False
    id_verification_image: Optional[str] = None
    blocked_users: List[str] = []
    created_at: datetime

class SessionDataResponse(BaseModel):
    id: str
    email: str
    name: str
    picture: Optional[str] = None
    session_token: str

class RouteCreate(BaseModel):
    start_coords: Coordinates
    end_coords: Coordinates
    start_address: str
    end_address: str
    departure_time: str  # Format: "HH:MM"
    days_of_week: List[str]  # ["monday", "tuesday", etc.]

class Route(BaseModel):
    route_id: str
    user_id: str
    start_coords: Coordinates
    end_coords: Coordinates
    start_address: str
    end_address: str
    departure_time: str
    days_of_week: List[str]
    active: bool = True
    created_at: datetime

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    profile_images: Optional[List[str]] = None

class ConnectionRequest(BaseModel):
    target_user_id: str

class ConnectionResponse(BaseModel):
    connection_id: str
    action: str  # "accept" or "reject"

class Connection(BaseModel):
    connection_id: str
    user1_id: str
    user2_id: str
    status: str  # "pending", "accepted", "rejected"
    created_at: datetime

class Message(BaseModel):
    message_id: str
    sender_id: str
    receiver_id: str
    content: str
    timestamp: datetime
    read: bool = False

class MessageCreate(BaseModel):
    receiver_id: str
    content: str

class ReportCreate(BaseModel):
    reported_user_id: str
    reason: str
    details: Optional[str] = None

class IDVerificationUpload(BaseModel):
    id_image: str  # base64

class MatchedUser(BaseModel):
    user_id: str
    name: str
    picture: Optional[str] = None
    bio: Optional[str] = None
    verified: bool
    route_match_score: float
    distance_to_start: float  # km
    distance_to_end: float  # km

# ==================== UTILITY FUNCTIONS ====================

def haversine_distance(coord1: Coordinates, coord2: Coordinates) -> float:
    """Calculate distance between two coordinates in km using Haversine formula"""
    R = 6371  # Earth's radius in km
    
    lat1, lon1 = radians(coord1.lat), radians(coord1.lng)
    lat2, lon2 = radians(coord2.lat), radians(coord2.lng)
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c

def time_difference_minutes(time1: str, time2: str) -> int:
    """Calculate difference between two times in minutes"""
    h1, m1 = map(int, time1.split(':'))
    h2, m2 = map(int, time2.split(':'))
    
    total1 = h1 * 60 + m1
    total2 = h2 * 60 + m2
    
    return abs(total1 - total2)

def calculate_match_score(user_route: Route, other_route: Route) -> Dict[str, float]:
    """Calculate compatibility score between two routes"""
    # Distance thresholds
    MAX_START_DISTANCE = 5  # km
    MAX_END_DISTANCE = 5  # km
    MAX_TIME_DIFF = 30  # minutes
    
    # Calculate distances
    start_distance = haversine_distance(user_route.start_coords, other_route.start_coords)
    end_distance = haversine_distance(user_route.end_coords, other_route.end_coords)
    
    # Calculate time difference
    time_diff = time_difference_minutes(user_route.departure_time, other_route.departure_time)
    
    # Check if routes are compatible
    if start_distance > MAX_START_DISTANCE or end_distance > MAX_END_DISTANCE or time_diff > MAX_TIME_DIFF:
        return None
    
    # Check if they share any common days
    common_days = set(user_route.days_of_week) & set(other_route.days_of_week)
    if not common_days:
        return None
    
    # Calculate score (0-100)
    start_score = max(0, 100 - (start_distance / MAX_START_DISTANCE * 100))
    end_score = max(0, 100 - (end_distance / MAX_END_DISTANCE * 100))
    time_score = max(0, 100 - (time_diff / MAX_TIME_DIFF * 100))
    day_score = (len(common_days) / len(user_route.days_of_week)) * 100
    
    total_score = (start_score * 0.3 + end_score * 0.3 + time_score * 0.25 + day_score * 0.15)
    
    return {
        "score": total_score,
        "start_distance": start_distance,
        "end_distance": end_distance,
        "time_diff": time_diff
    }

# ==================== AUTH HELPERS ====================

async def get_current_user(request: Request) -> Optional[User]:
    """Get current authenticated user from session token"""
    # Check cookie first
    session_token = request.cookies.get("session_token")
    
    # Fallback to Authorization header
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.replace("Bearer ", "")
    
    if not session_token:
        return None
    
    # Check session in database
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        return None
    
    # Check if session is expired
    expires_at = session["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    if expires_at < datetime.now(timezone.utc):
        await db.user_sessions.delete_one({"session_token": session_token})
        return None
    
    # Get user
    user_doc = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user_doc:
        return None
    
    return User(**user_doc)

def require_auth(user: Optional[User] = Depends(get_current_user)) -> User:
    """Dependency to require authentication"""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

# ==================== AUTH ENDPOINTS ====================

@api_router.post("/auth/exchange-session")
async def exchange_session(request: Request, response: Response):
    """Exchange session_id for session_token"""
    body = await request.json()
    session_id = body.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    
    # Call Emergent Auth API
    async with httpx.AsyncClient() as client:
        try:
            auth_response = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": session_id}
            )
            auth_response.raise_for_status()
            user_data = auth_response.json()
        except Exception as e:
            logger.error(f"Auth API error: {e}")
            raise HTTPException(status_code=400, detail="Invalid session_id")
    
    # Generate user_id if new user
    existing_user = await db.users.find_one({"email": user_data["email"]}, {"_id": 0})
    
    if existing_user:
        user_id = existing_user["user_id"]
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        
        # Create new user
        new_user = {
            "user_id": user_id,
            "email": user_data["email"],
            "name": user_data["name"],
            "picture": user_data.get("picture"),
            "profile_images": [],
            "bio": None,
            "verified": False,
            "id_verification_image": None,
            "blocked_users": [],
            "created_at": datetime.now(timezone.utc)
        }
        await db.users.insert_one(new_user)
    
    # Store session
    session_token = user_data["session_token"]
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc)
    })
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=7*24*60*60,
        path="/"
    )
    
    return {"session_token": session_token, "user_id": user_id}

@api_router.get("/auth/me")
async def get_me(current_user: User = Depends(require_auth)):
    """Get current user info"""
    return current_user

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response, current_user: User = Depends(require_auth)):
    """Logout current user"""
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    
    response.delete_cookie("session_token", path="/")
    return {"message": "Logged out successfully"}

# ==================== PROFILE ENDPOINTS ====================

@api_router.get("/profile/me")
async def get_my_profile(current_user: User = Depends(require_auth)):
    """Get my complete profile"""
    return current_user

@api_router.put("/profile/update")
async def update_profile(profile_data: ProfileUpdate, current_user: User = Depends(require_auth)):
    """Update user profile"""
    update_fields = {}
    
    if profile_data.name is not None:
        update_fields["name"] = profile_data.name
    if profile_data.bio is not None:
        update_fields["bio"] = profile_data.bio
    if profile_data.profile_images is not None:
        # Limit to 6 images
        update_fields["profile_images"] = profile_data.profile_images[:6]
    
    if update_fields:
        await db.users.update_one(
            {"user_id": current_user.user_id},
            {"$set": update_fields}
        )
    
    # Return updated user
    updated_user = await db.users.find_one({"user_id": current_user.user_id}, {"_id": 0})
    return User(**updated_user)

@api_router.post("/profile/verify-id")
async def verify_id(verification_data: IDVerificationUpload, current_user: User = Depends(require_auth)):
    """Upload ID verification image"""
    await db.users.update_one(
        {"user_id": current_user.user_id},
        {"$set": {"id_verification_image": verification_data.id_image, "verified": True}}
    )
    
    return {"message": "ID verification submitted successfully", "verified": True}

@api_router.get("/profile/{user_id}")
async def get_user_profile(user_id: str, current_user: User = Depends(require_auth)):
    """Get another user's profile"""
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "id_verification_image": 0, "blocked_users": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

# ==================== ROUTE ENDPOINTS ====================

@api_router.post("/routes/create")
async def create_route(route_data: RouteCreate, current_user: User = Depends(require_auth)):
    """Create a new route"""
    route_id = f"route_{uuid.uuid4().hex[:12]}"
    
    route = {
        "route_id": route_id,
        "user_id": current_user.user_id,
        "start_coords": route_data.start_coords.dict(),
        "end_coords": route_data.end_coords.dict(),
        "start_address": route_data.start_address,
        "end_address": route_data.end_address,
        "departure_time": route_data.departure_time,
        "days_of_week": route_data.days_of_week,
        "active": True,
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.routes.insert_one(route)
    
    return Route(**route)

@api_router.get("/routes/my-routes")
async def get_my_routes(current_user: User = Depends(require_auth)):
    """Get all my routes"""
    routes = await db.routes.find({"user_id": current_user.user_id}, {"_id": 0}).to_list(100)
    return [Route(**route) for route in routes]

@api_router.put("/routes/{route_id}")
async def update_route(route_id: str, route_data: RouteCreate, current_user: User = Depends(require_auth)):
    """Update a route"""
    route = await db.routes.find_one({"route_id": route_id, "user_id": current_user.user_id}, {"_id": 0})
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    update_data = route_data.dict()
    update_data["start_coords"] = update_data["start_coords"]
    update_data["end_coords"] = update_data["end_coords"]
    
    await db.routes.update_one(
        {"route_id": route_id},
        {"$set": update_data}
    )
    
    updated_route = await db.routes.find_one({"route_id": route_id}, {"_id": 0})
    return Route(**updated_route)

@api_router.delete("/routes/{route_id}")
async def delete_route(route_id: str, current_user: User = Depends(require_auth)):
    """Delete a route"""
    result = await db.routes.delete_one({"route_id": route_id, "user_id": current_user.user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Route not found")
    
    return {"message": "Route deleted successfully"}

# ==================== DISCOVERY ENDPOINTS ====================

@api_router.get("/discovery/matches")
async def get_matches(current_user: User = Depends(require_auth)):
    """Get matched users based on routes"""
    # Get user's active routes
    user_routes = await db.routes.find({"user_id": current_user.user_id, "active": True}, {"_id": 0}).to_list(100)
    
    if not user_routes:
        return []
    
    # Get all other active routes
    all_routes = await db.routes.find(
        {"user_id": {"$ne": current_user.user_id}, "active": True},
        {"_id": 0}
    ).to_list(1000)
    
    # Collect matching user IDs first
    potential_matches = []
    seen_users = set()
    
    for user_route_dict in user_routes:
        user_route = Route(**user_route_dict)
        
        for other_route_dict in all_routes:
            other_route = Route(**other_route_dict)
            
            # Skip if already seen
            if other_route.user_id in seen_users or other_route.user_id in current_user.blocked_users:
                continue
            
            # Calculate match score
            match_result = calculate_match_score(user_route, other_route)
            
            if match_result and match_result["score"] > 30:  # Minimum 30% match
                potential_matches.append({
                    "user_id": other_route.user_id,
                    "match_result": match_result
                })
                seen_users.add(other_route.user_id)
    
    # Batch fetch all matched users in a single query
    if not potential_matches:
        return []
    
    user_ids = [m["user_id"] for m in potential_matches]
    users = await db.users.find(
        {"user_id": {"$in": user_ids}},
        {"_id": 0, "user_id": 1, "name": 1, "picture": 1, "bio": 1, "verified": 1, "blocked_users": 1}
    ).to_list(None)
    
    # Create user lookup dictionary
    users_dict = {u["user_id"]: u for u in users}
    
    # Build final matches list
    matches = []
    for match in potential_matches:
        user_id = match["user_id"]
        match_result = match["match_result"]
        
        if user_id in users_dict:
            other_user = users_dict[user_id]
            if current_user.user_id not in other_user.get("blocked_users", []):
                matches.append({
                    "user_id": other_user["user_id"],
                    "name": other_user["name"],
                    "picture": other_user.get("picture"),
                    "bio": other_user.get("bio"),
                    "verified": other_user.get("verified", False),
                    "route_match_score": round(match_result["score"], 1),
                    "distance_to_start": round(match_result["start_distance"], 2),
                    "distance_to_end": round(match_result["end_distance"], 2)
                })
    
    # Sort by score (highest first)
    matches.sort(key=lambda x: x["route_match_score"], reverse=True)
    
    return matches[:50]  # Return top 50 matches

# ==================== CONNECTION ENDPOINTS ====================

@api_router.post("/connections/request")
async def create_connection_request(conn_request: ConnectionRequest, current_user: User = Depends(require_auth)):
    """Send connection request to another user"""
    # Check if connection already exists
    existing = await db.connections.find_one({
        "$or": [
            {"user1_id": current_user.user_id, "user2_id": conn_request.target_user_id},
            {"user1_id": conn_request.target_user_id, "user2_id": current_user.user_id}
        ]
    }, {"_id": 0})
    
    if existing:
        raise HTTPException(status_code=400, detail="Connection already exists")
    
    connection_id = f"conn_{uuid.uuid4().hex[:12]}"
    
    connection = {
        "connection_id": connection_id,
        "user1_id": current_user.user_id,
        "user2_id": conn_request.target_user_id,
        "status": "pending",
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.connections.insert_one(connection)
    
    return Connection(**connection)

@api_router.post("/connections/respond")
async def respond_to_connection(conn_response: ConnectionResponse, current_user: User = Depends(require_auth)):
    """Accept or reject connection request"""
    connection = await db.connections.find_one(
        {"connection_id": conn_response.connection_id, "user2_id": current_user.user_id},
        {"_id": 0}
    )
    
    if not connection:
        raise HTTPException(status_code=404, detail="Connection request not found")
    
    await db.connections.update_one(
        {"connection_id": conn_response.connection_id},
        {"$set": {"status": conn_response.action}}
    )
    
    updated_connection = await db.connections.find_one({"connection_id": conn_response.connection_id}, {"_id": 0})
    return Connection(**updated_connection)

@api_router.get("/connections/list")
async def get_connections(status: Optional[str] = None, current_user: User = Depends(require_auth)):
    """Get all connections (pending, accepted, rejected)"""
    query = {
        "$or": [
            {"user1_id": current_user.user_id},
            {"user2_id": current_user.user_id}
        ]
    }
    
    if status:
        query["status"] = status
    
    connections = await db.connections.find(query, {"_id": 0}).to_list(1000)
    
    # Enrich with user info
    result = []
    for conn in connections:
        other_user_id = conn["user2_id"] if conn["user1_id"] == current_user.user_id else conn["user1_id"]
        other_user = await db.users.find_one(
            {"user_id": other_user_id},
            {"_id": 0, "user_id": 1, "name": 1, "picture": 1, "verified": 1}
        )
        
        if other_user:
            result.append({
                **conn,
                "other_user": other_user
            })
    
    return result

# ==================== MESSAGE ENDPOINTS ====================

@api_router.get("/messages/conversation/{other_user_id}")
async def get_conversation(other_user_id: str, current_user: User = Depends(require_auth)):
    """Get conversation with another user"""
    messages = await db.messages.find(
        {
            "$or": [
                {"sender_id": current_user.user_id, "receiver_id": other_user_id},
                {"sender_id": other_user_id, "receiver_id": current_user.user_id}
            ]
        },
        {"_id": 0}
    ).sort("timestamp", 1).to_list(1000)
    
    return [Message(**msg) for msg in messages]

@api_router.post("/messages/send")
async def send_message(message_data: MessageCreate, current_user: User = Depends(require_auth)):
    """Send a message"""
    message_id = f"msg_{uuid.uuid4().hex[:12]}"
    
    message = {
        "message_id": message_id,
        "sender_id": current_user.user_id,
        "receiver_id": message_data.receiver_id,
        "content": message_data.content,
        "timestamp": datetime.now(timezone.utc),
        "read": False
    }
    
    await db.messages.insert_one(message)
    
    # Emit socket event
    await sio.emit('new_message', Message(**message).dict(), room=message_data.receiver_id)
    
    return Message(**message)

@api_router.post("/messages/mark-read/{other_user_id}")
async def mark_messages_read(other_user_id: str, current_user: User = Depends(require_auth)):
    """Mark all messages from a user as read"""
    await db.messages.update_many(
        {"sender_id": other_user_id, "receiver_id": current_user.user_id, "read": False},
        {"$set": {"read": True}}
    )
    
    return {"message": "Messages marked as read"}

# ==================== SAFETY ENDPOINTS ====================

@api_router.post("/reports/create")
async def create_report(report_data: ReportCreate, current_user: User = Depends(require_auth)):
    """Report a user"""
    report_id = f"report_{uuid.uuid4().hex[:12]}"
    
    report = {
        "report_id": report_id,
        "reporter_id": current_user.user_id,
        "reported_user_id": report_data.reported_user_id,
        "reason": report_data.reason,
        "details": report_data.details,
        "timestamp": datetime.now(timezone.utc)
    }
    
    await db.reports.insert_one(report)
    
    return {"message": "Report submitted successfully", "report_id": report_id}

@api_router.post("/reports/block/{user_id}")
async def block_user(user_id: str, current_user: User = Depends(require_auth)):
    """Block a user"""
    await db.users.update_one(
        {"user_id": current_user.user_id},
        {"$addToSet": {"blocked_users": user_id}}
    )
    
    return {"message": "User blocked successfully"}

@api_router.post("/reports/unblock/{user_id}")
async def unblock_user(user_id: str, current_user: User = Depends(require_auth)):
    """Unblock a user"""
    await db.users.update_one(
        {"user_id": current_user.user_id},
        {"$pull": {"blocked_users": user_id}}
    )
    
    return {"message": "User unblocked successfully"}

# ==================== SOCKET.IO EVENTS ====================

@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")

@sio.event
async def join_room(sid, data):
    """Join a room (user's own user_id room)"""
    user_id = data.get("user_id")
    if user_id:
        await sio.enter_room(sid, user_id)
        logger.info(f"User {user_id} joined room")

@sio.event
async def send_message(sid, data):
    """Send a real-time message"""
    message_id = f"msg_{uuid.uuid4().hex[:12]}"
    
    message = {
        "message_id": message_id,
        "sender_id": data["sender_id"],
        "receiver_id": data["receiver_id"],
        "content": data["content"],
        "timestamp": datetime.now(timezone.utc),
        "read": False
    }
    
    # Save to database
    await db.messages.insert_one(message)
    
    # Emit to receiver
    message["timestamp"] = message["timestamp"].isoformat()
    await sio.emit('receive_message', message, room=data["receiver_id"])
    
    # Confirm to sender
    await sio.emit('message_sent', message, room=sid)

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
