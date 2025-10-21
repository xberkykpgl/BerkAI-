from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Cookie
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import asyncio
import base64
from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContentWithMimeType
import httpx
from openai import AsyncOpenAI

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# API Keys
EMERGENT_LLM_KEY = os.environ['EMERGENT_LLM_KEY']
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']

# OpenAI client for TTS
openai_client = AsyncOpenAI(api_key=EMERGENT_LLM_KEY)

# ============= MODELS =============

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(alias="_id")
    email: str
    name: str
    picture: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserSession(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TherapySession(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_name: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None
    analysis_summary: Optional[Dict[str, Any]] = None
    status: str = "active"  # active, completed

class Message(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_id: str
    role: str  # user, assistant, system
    content: str
    video_analysis: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class VideoAnalysis(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_id: str
    frame_data: str  # base64
    analysis_result: Dict[str, Any]
    stress_level: Optional[float] = None
    emotion_detected: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ============= AUTH HELPERS =============

async def get_current_user(request: Request) -> Optional[User]:
    """Get current user from session token in cookie or Authorization header"""
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.replace("Bearer ", "")
    
    if not session_token:
        return None
    
    session = await db.user_sessions.find_one({
        "session_token": session_token,
        "expires_at": {"$gt": datetime.now(timezone.utc)}
    })
    
    if not session:
        return None
    
    user_doc = await db.users.find_one({"_id": session["user_id"]})
    if user_doc:
        return User(**user_doc)
    return None

# ============= AUTH ROUTES =============

@api_router.get("/auth/me")
async def get_me(request: Request):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

@api_router.post("/auth/session")
async def create_session_from_emergent(request: Request, response: Response):
    """Process session_id from Emergent Auth and create user session"""
    data = await request.json()
    session_id = data.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    
    # Get user data from Emergent Auth
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
        
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid session_id")
        
        user_data = resp.json()
    
    # Check if user exists
    existing_user = await db.users.find_one({"_id": user_data["email"]})
    
    if not existing_user:
        # Create new user
        user_doc = {
            "_id": user_data["email"],
            "email": user_data["email"],
            "name": user_data["name"],
            "picture": user_data.get("picture"),
            "created_at": datetime.now(timezone.utc)
        }
        await db.users.insert_one(user_doc)
    
    # Create session
    session_token = f"berkai_session_{uuid.uuid4()}"
    session_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_data["email"],
        "session_token": session_token,
        "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
        "created_at": datetime.now(timezone.utc)
    }
    await db.user_sessions.insert_one(session_doc)
    
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
    
    return {"success": True, "user": user_data}

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    user = await get_current_user(request)
    if user:
        session_token = request.cookies.get("session_token")
        if session_token:
            await db.user_sessions.delete_many({"session_token": session_token})
    
    response.delete_cookie("session_token", path="/")
    return {"success": True}

# ============= THERAPY SESSION ROUTES =============

@api_router.get("/sessions")
async def get_user_sessions(request: Request):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    sessions = await db.therapy_sessions.find(
        {"user_id": user.id},
        {"_id": 0}
    ).sort("started_at", -1).to_list(100)
    
    return sessions

@api_router.post("/sessions")
async def create_therapy_session(request: Request, session_name: str = "Nueva sesión"):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = TherapySession(
        user_id=user.id,
        session_name=session_name
    )
    
    doc = session.model_dump()
    await db.therapy_sessions.insert_one(doc)
    
    return session

@api_router.get("/sessions/{session_id}")
async def get_session(request: Request, session_id: str):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.therapy_sessions.find_one(
        {"id": session_id, "user_id": user.id},
        {"_id": 0}
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session

@api_router.patch("/sessions/{session_id}/complete")
async def complete_session(request: Request, session_id: str):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    data = await request.json()
    
    await db.therapy_sessions.update_one(
        {"id": session_id, "user_id": user.id},
        {
            "$set": {
                "status": "completed",
                "ended_at": datetime.now(timezone.utc),
                "analysis_summary": data.get("analysis_summary")
            }
        }
    )
    
    return {"success": True}

# ============= MESSAGE & CHAT ROUTES =============

@api_router.get("/sessions/{session_id}/messages")
async def get_session_messages(request: Request, session_id: str):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    messages = await db.messages.find(
        {"session_id": session_id, "user_id": user.id},
        {"_id": 0}
    ).sort("timestamp", 1).to_list(1000)
    
    return messages

@api_router.post("/sessions/{session_id}/chat")
async def chat_with_berkai(request: Request, session_id: str):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    data = await request.json()
    user_message_text = data.get("message", "")
    video_frame = data.get("video_frame")  # base64
    
    # Set timeout for entire operation
    timeout_seconds = 60  # Increased for video analysis
    
    # Save user message
    user_msg = Message(
        session_id=session_id,
        user_id=user.id,
        role="user",
        content=user_message_text
    )
    await db.messages.insert_one(user_msg.model_dump())
    
    # Get conversation history
    history = await db.messages.find(
        {"session_id": session_id, "user_id": user.id},
        {"_id": 0}
    ).sort("timestamp", 1).limit(20).to_list(20)
    
    # Video analysis if frame provided
    video_analysis_result = None
    if video_frame:
        video_analysis_result = await analyze_video_frame(video_frame, user.id, session_id)
    
    # Build context for GPT-5
    context_messages = []
    for msg in history[-10:]:
        context_messages.append(f"{msg['role']}: {msg['content']}")
    
    conversation_context = "\n".join(context_messages)
    
    system_prompt = f"""Sen BerkAI'sın, empatik ve profesyonel bir psikolojik destek asistanısın. 
    
Görevin:
1. Kullanıcının duygusal durumunu anlamak
2. Derinlemesine ve anlayışlı sorular sormak
3. Hem bir dost hem de profesyonel bir psikolog gibi davranmak
4. Kullanıcının sözlerini dikkatle dinlemek ve gerçek duygularını anlamaya çalışmak
5. Yargılamadan, destekleyici bir ortam oluşturmak

Kullanıcı profili: {user.name} ({user.email})

Önceki konuşma:
{conversation_context}
"""
    
    if video_analysis_result:
        system_prompt += f"\n\nVideo Analiz Sonuçları:\n{video_analysis_result.get('summary', '')}"
    
    # GPT-5 Chat
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"berkai_{session_id}",
        system_message=system_prompt
    ).with_model("openai", "gpt-5")
    
    ai_response = await chat.send_message(UserMessage(text=user_message_text))
    
    # Save AI response
    ai_msg = Message(
        session_id=session_id,
        user_id=user.id,
        role="assistant",
        content=ai_response,
        video_analysis=video_analysis_result
    )
    await db.messages.insert_one(ai_msg.model_dump())
    
    # Generate TTS audio
    audio_url = None
    try:
        # Generate speech using OpenAI TTS
        response = await openai_client.audio.speech.create(
            model="tts-1",
            voice="nova",  # Warm, friendly voice
            input=ai_response[:2000]  # Limit to 2000 chars for TTS
        )
        
        # Save audio file
        audio_filename = f"berkai_audio_{uuid.uuid4()}.mp3"
        audio_path = f"/tmp/{audio_filename}"
        
        # Write audio to file
        with open(audio_path, "wb") as f:
            async for chunk in response.iter_bytes(chunk_size=1024):
                f.write(chunk)
        
        audio_url = f"/api/audio/{audio_filename}"
    except Exception as e:
        logging.error(f"TTS generation error: {e}")
        # Continue without audio if TTS fails
    
    return {
        "message": ai_response,
        "video_analysis": video_analysis_result,
        "audio_url": audio_url
    }

# ============= VIDEO ANALYSIS =============

async def analyze_video_frame(frame_base64: str, user_id: str, session_id: str) -> Dict[str, Any]:
    """Analyze video frame using Gemini Vision"""
    try:
        # Save frame temporarily
        temp_path = f"/tmp/frame_{uuid.uuid4()}.jpg"
        
        # Decode base64 and save
        frame_data = base64.b64decode(frame_base64.split(',')[1] if ',' in frame_base64 else frame_base64)
        with open(temp_path, 'wb') as f:
            f.write(frame_data)
        
        # Gemini Vision Analysis
        chat = LlmChat(
            api_key=GEMINI_API_KEY,
            session_id=f"vision_{session_id}",
            system_message="Sen bir video analiz uzmanısın. Görüntülerdeki kişinin duygusal durumunu, stres seviyesini, göz hareketlerini ve vücut dilini analiz ediyorsun."
        ).with_model("gemini", "gemini-2.5-pro")
        
        video_file = FileContentWithMimeType(
            file_path=temp_path,
            mime_type="image/jpeg"
        )
        
        analysis_prompt = """Bu görüntüyü detaylıca analiz et ve şu bilgileri ver:

1. Yüz ifadesi ve duygu durumu
2. Göz hareketleri ve bakış yönü
3. Vücut dili ve el-kol hareketleri
4. Stres göstergeleri (0-10 arası skor)
5. Olası yalan veya rahatsızlık belirtileri
6. Genel psikolojik durum değerlendirmesi

JSON formatında yanıt ver:
{
  "emotion": "tespit edilen ana duygu",
  "stress_level": 0-10,
  "eye_movements": "açıklama",
  "body_language": "açıklama",
  "deception_indicators": ["göstergeler"],
  "psychological_state": "genel değerlendirme",
  "summary": "kısa özet"
}"""
        
        result = await chat.send_message(UserMessage(
            text=analysis_prompt,
            file_contents=[video_file]
        ))
        
        # Parse result
        import json
        try:
            analysis_data = json.loads(result)
        except:
            analysis_data = {
                "summary": result,
                "emotion": "belirsiz",
                "stress_level": 5
            }
        
        # Save analysis
        analysis = VideoAnalysis(
            session_id=session_id,
            user_id=user_id,
            frame_data=frame_base64[:100],  # Save only preview
            analysis_result=analysis_data,
            stress_level=analysis_data.get("stress_level"),
            emotion_detected=analysis_data.get("emotion")
        )
        await db.video_analyses.insert_one(analysis.model_dump())
        
        # Cleanup
        os.remove(temp_path)
        
        return analysis_data
        
    except Exception as e:
        logging.error(f"Video analysis error: {e}")
        return {
            "error": str(e),
            "summary": "Video analizi yapılamadı"
        }

@api_router.get("/sessions/{session_id}/analytics")
async def get_session_analytics(request: Request, session_id: str):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    analyses = await db.video_analyses.find(
        {"session_id": session_id, "user_id": user.id},
        {"_id": 0, "frame_data": 0}
    ).sort("timestamp", 1).to_list(100)
    
    # Calculate averages
    if analyses:
        avg_stress = sum([a.get("stress_level", 5) for a in analyses]) / len(analyses)
        emotions = [a.get("emotion_detected") for a in analyses if a.get("emotion_detected")]
    else:
        avg_stress = 0
        emotions = []
    
    return {
        "analyses": analyses,
        "summary": {
            "average_stress": round(avg_stress, 2),
            "total_frames": len(analyses),
            "detected_emotions": emotions
        }
    }

# ============= MAIN =============

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()