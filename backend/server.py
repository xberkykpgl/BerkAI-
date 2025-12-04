from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Cookie, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
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
from risk_assessment import analyze_message_risk, should_notify_doctor, generate_crisis_response

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

# OpenAI client for Whisper
openai_client = AsyncOpenAI(api_key=EMERGENT_LLM_KEY)

# ============= MODELS =============

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(alias="_id")
    email: str
    name: str
    picture: Optional[str] = None
    user_type: str = "patient"  # patient, doctor, psychiatrist
    user_id_number: str = ""  # Unique ID for linking
    license_number: Optional[str] = None  # For doctors/psychiatrists
    specialization: Optional[str] = None  # For doctors/psychiatrists
    assigned_patients: List[str] = []  # Patient IDs for doctors
    assigned_doctor_id: Optional[str] = None  # For patients
    therapy_approach: str = "general"  # CBT, DBT, ACT, general
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

class UserProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    main_issues: List[str] = []  # Ana sorunlar
    progress_notes: List[Dict[str, Any]] = []  # İlerleme notları
    important_events: List[Dict[str, Any]] = []  # Önemli olaylar
    triggers: List[str] = []  # Tetikleyiciler
    coping_strategies: List[str] = []  # Başa çıkma stratejileri
    session_summaries: List[Dict[str, Any]] = []  # Her seans özeti
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Admin(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(alias="_id")
    email: str
    name: str
    password_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AISettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    chat_model: str = "gpt-5"
    chat_provider: str = "openai"
    vision_model: str = "gemini-2.5-pro"
    tts_voice: str = "nova"
    tts_model: str = "tts-1"
    system_prompt: str
    max_message_length: int = 2000
    enable_video_analysis: bool = True
    enable_tts: bool = True
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RiskAssessment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_id: str
    message_id: str
    risk_level: int  # 0-10
    risk_category: str  # low, medium, high, critical
    risk_indicators: List[str]  # What triggered the risk
    suicide_risk: bool = False
    self_harm_risk: bool = False
    crisis_detected: bool = False
    doctor_notified: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TreatmentPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    doctor_id: str
    plan_title: str
    therapy_approach: str  # CBT, DBT, ACT, etc
    goals: List[str]
    interventions: List[str]
    homework: List[str]
    notes: str
    status: str = "active"  # active, completed, paused
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DoctorNote(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    doctor_id: str
    patient_id: str
    session_id: Optional[str] = None
    note_type: str  # clinical_note, observation, diagnosis
    content: str
    tags: List[str] = []
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ============= AUTH HELPERS =============

# Admin credentials from environment
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@berkai.com')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'BerkAI2025!')
AUTH_SERVICE_URL = os.environ.get('AUTH_SERVICE_URL', 'https://demobackend.emergentagent.com')

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

async def verify_admin(request: Request) -> bool:
    """Verify admin access"""
    admin_token = request.cookies.get("admin_token")
    
    if not admin_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            admin_token = auth_header.replace("Bearer ", "")
    
    if not admin_token:
        return False
    
    admin_session = await db.admin_sessions.find_one({
        "session_token": admin_token,
        "expires_at": {"$gt": datetime.now(timezone.utc)}
    })
    
    return admin_session is not None

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
    user_type = data.get("user_type", "patient")  # patient, doctor, psychiatrist
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    
    # Get user data from Emergent Auth
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{AUTH_SERVICE_URL}/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
        
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid session_id")
        
        user_data = resp.json()
    
    # Check if user exists
    existing_user = await db.users.find_one({"_id": user_data["email"]})
    
    if not existing_user:
        # Generate unique ID
        user_id_number = f"BRK{uuid.uuid4().hex[:8].upper()}"
        
        # Create new user
        user_doc = {
            "_id": user_data["email"],
            "email": user_data["email"],
            "name": user_data["name"],
            "picture": user_data.get("picture"),
            "user_type": user_type,
            "user_id_number": user_id_number,
            "assigned_patients": [],
            "therapy_approach": "general",
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
    
    return {"success": True, "user": user_data, "user_type": user_type}

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
    
    # Get all messages from this session
    session_messages = await db.messages.find(
        {"session_id": session_id, "user_id": user.id},
        {"_id": 0, "role": 1, "content": 1, "timestamp": 1}
    ).sort("timestamp", 1).to_list(1000)
    
    # Generate AI summary of this session
    session_summary = None
    if session_messages and len(session_messages) > 2:
        # Build conversation for AI analysis
        conversation_text = ""
        for msg in session_messages:
            role = "Kullanıcı" if msg['role'] == 'user' else "BerkAI"
            conversation_text += f"{role}: {msg['content']}\n"
        
        # Use AI to extract key insights
        summary_prompt = f"""Aşağıdaki terapi seansını analiz et ve ÖNEMLİ BİLGİLERİ ÇIKAR:

{conversation_text}

Lütfen şunları belirt:
1. Ana konular ve sorunlar
2. Kullanıcının paylaştığı önemli olaylar
3. Tetikleyiciler (stres, kaygı yaratan şeyler)
4. İlerleme işaretleri
5. Kullanışlı başa çıkma stratejileri

KISA VE ÖZ YAZ. Sadece ÖNEMLİ bilgileri çıkar."""

        try:
            chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=f"summary_{session_id}",
                system_message="Sen bir terapi seansı analiz uzmanısın. Seanslardan önemli bilgileri çıkarıp kısa özetler hazırlarsın."
            ).with_model("openai", "gpt-5")
            
            ai_summary = await chat.send_message(UserMessage(text=summary_prompt))
            session_summary = ai_summary
        except Exception as e:
            logging.error(f"Failed to generate session summary: {e}")
            session_summary = "Özet oluşturulamadı"
    
    # Update session as completed
    await db.therapy_sessions.update_one(
        {"id": session_id, "user_id": user.id},
        {
            "$set": {
                "status": "completed",
                "ended_at": datetime.now(timezone.utc),
                "analysis_summary": data.get("analysis_summary"),
                "ai_summary": session_summary
            }
        }
    )
    
    # Update or create user profile with session summary
    if session_summary:
        session_data = await db.therapy_sessions.find_one({"id": session_id})
        
        profile = await db.user_profiles.find_one({"user_id": user.id})
        
        if not profile:
            # Create new profile
            new_profile = UserProfile(
                user_id=user.id,
                session_summaries=[{
                    "session_id": session_id,
                    "date": datetime.now(timezone.utc).isoformat(),
                    "summary": session_summary
                }]
            )
            await db.user_profiles.insert_one(new_profile.model_dump())
        else:
            # Update existing profile
            await db.user_profiles.update_one(
                {"user_id": user.id},
                {
                    "$push": {
                        "session_summaries": {
                            "session_id": session_id,
                            "date": datetime.now(timezone.utc).isoformat(),
                            "summary": session_summary
                        }
                    },
                    "$set": {
                        "last_updated": datetime.now(timezone.utc)
                    }
                }
            )
    
    return {"success": True, "summary_generated": session_summary is not None}

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
    analyze_video = data.get("analyze_video", False)  # Optional video analysis
    
    # Save user message
    user_msg = Message(
        session_id=session_id,
        user_id=user.id,
        role="user",
        content=user_message_text
    )
    msg_doc = user_msg.model_dump()
    await db.messages.insert_one(msg_doc)
    message_id = msg_doc.get("id", user_msg.id)
    
    # ⚠️ RISK ASSESSMENT - Critical Feature
    risk_result = analyze_message_risk(user_message_text)
    
    # Save risk assessment to database
    risk_assessment = {
        "id": str(uuid.uuid4()),
        "user_id": user.id,
        "session_id": session_id,
        "message_id": message_id,
        "risk_level": risk_result["risk_level"],
        "risk_category": risk_result["risk_category"],
        "risk_indicators": risk_result["risk_indicators"],
        "suicide_risk": risk_result["suicide_risk"],
        "self_harm_risk": risk_result["self_harm_risk"],
        "crisis_detected": risk_result["crisis_detected"],
        "doctor_notified": False,
        "timestamp": datetime.now(timezone.utc)
    }
    await db.risk_assessments.insert_one(risk_assessment)
    
    # Notify doctor if high risk
    if should_notify_doctor(risk_result) and user.assigned_doctor_id:
        # Mark as notified
        await db.risk_assessments.update_one(
            {"id": risk_assessment["id"]},
            {"$set": {"doctor_notified": True}}
        )
        # In production: Send email/SMS to doctor
        logging.warning(f"🚨 HIGH RISK ALERT - User: {user.id}, Risk Level: {risk_result['risk_level']}")
    
    # If critical, return crisis response immediately
    if risk_result["risk_category"] == "critical":
        crisis_response = generate_crisis_response()
        
        # Save AI crisis response
        ai_msg = Message(
            session_id=session_id,
            user_id=user.id,
            role="assistant",
            content=crisis_response
        )
        await db.messages.insert_one(ai_msg.model_dump())
        
        return {
            "message": crisis_response,
            "risk_assessment": risk_result,
            "crisis_mode": True
        }
    
    # Get current session history (son 20 mesaj)
    current_session_messages = await db.messages.find(
        {"session_id": session_id, "user_id": user.id},
        {"_id": 0}
    ).sort("timestamp", 1).limit(20).to_list(20)
    
    # Load user profile with all session summaries (RAG system)
    user_profile = await db.user_profiles.find_one({"user_id": user.id})
    
    profile_context = ""
    if user_profile:
        # Build comprehensive profile context
        profile_context = "KULLANICI PROFİLİ VE GEÇMİŞ:\n"
        
        if user_profile.get("main_issues"):
            profile_context += f"\nAna Sorunlar: {', '.join(user_profile['main_issues'])}"
        
        if user_profile.get("triggers"):
            profile_context += f"\nTetikleyiciler: {', '.join(user_profile['triggers'])}"
        
        if user_profile.get("coping_strategies"):
            profile_context += f"\nBaşa Çıkma Stratejileri: {', '.join(user_profile['coping_strategies'])}"
        
        # Include session summaries (last 5 sessions)
        if user_profile.get("session_summaries"):
            profile_context += "\n\nÖnceki Seanslardan Önemli Notlar:"
            for summary_data in user_profile["session_summaries"][-5:]:
                profile_context += f"\n[{summary_data.get('date', 'Tarih yok')[:10]}]\n{summary_data.get('summary', '')}\n"
    
    # If no profile exists, create basic context from recent sessions
    if not profile_context:
        previous_sessions = await db.therapy_sessions.find(
            {"user_id": user.id, "id": {"$ne": session_id}, "ai_summary": {"$exists": True}},
            {"_id": 0, "started_at": 1, "ai_summary": 1}
        ).sort("started_at", -1).limit(3).to_list(3)
        
        if previous_sessions:
            profile_context = "Önceki Seanslardan Notlar:\n"
            for prev_session in previous_sessions:
                session_date = prev_session["started_at"].strftime("%d.%m.%Y")
                profile_context += f"\n[{session_date}]\n{prev_session.get('ai_summary', '')}\n"
    
    # Video analysis only if requested and frame provided
    video_analysis_result = None
    if analyze_video and video_frame:
        video_analysis_result = await analyze_video_frame(video_frame, user.id, session_id)
    
    # Build current conversation context
    context_messages = []
    for msg in current_session_messages[-10:]:  # Son 10 mesaj
        role = "Kullanıcı" if msg['role'] == 'user' else "BerkAI"
        context_messages.append(f"{role}: {msg['content']}")
    
    current_conversation = "\n".join(context_messages)
    
    # Enhanced system prompt with full user profile
    system_prompt = f"""Sen BerkAI'sın, empatik ve samimi bir psikolojik destek asistanısın.

Kullanıcı: {user.name}

{profile_context if profile_context else "İlk seans - önceki geçmiş yok"}

Bu Seanstaki Konuşma:
{current_conversation}

ÖNEMLİ İLETİŞİM KURALLARI:
1. **Tanışma Aşaması**: İlk mesajlarda kullanıcıyı tanımak için sorular sor. Samimi ve dostça ol.
2. **Sohbet Aşaması**: Her yanıtını MAKSIMUM 3-4 cümle ile sınırla. Kısa ve öz ol. Her seferde sadece birkaç soru sor, kullanıcıyı boğma.
3. **Öneri/Tavsiye Aşaması**: Bir öneri veya tavsiye veriyorsan, BURDA detaylı ve kapsamlı ol. Açıklayıcı ve yardımcı olabilirsin.

YAPMA:
- Uzun paragraflar yazma (öneri vermiyorsan)
- Soru yağmuruna tutma
- Aynı anda çok fazla şey sorma

YAP:
- Tek seferde az soru sor
- Kısa ve net yanıtlar ver
- Danışan rahat hissetsin
- Önceki seansları hatırla ve süreklilik sağla
- Samimi ama profesyonel ol"""
    
    if video_analysis_result:
        system_prompt += f"\n\nŞu anki duygusal durum: {video_analysis_result.get('emotion', 'belirsiz')}, Stres: {video_analysis_result.get('stress_level', 5)}/10"
    
    # GPT-5 Chat with user history context
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"berkai_{user.id}",  # User bazlı session ID - tüm seanslar aynı context
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
    
    return {
        "message": ai_response,
        "video_analysis": video_analysis_result,
        "risk_assessment": risk_result
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

# ============= AUDIO SERVING =============

@api_router.get("/audio/{filename}")
async def serve_audio(filename: str):
    """Serve generated audio files"""
    from fastapi.responses import FileResponse
    import os
    
    audio_path = f"/tmp/{filename}"
    
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(
        audio_path,
        media_type="audio/mpeg",
        filename=filename
    )

# ============= SPEECH TO TEXT =============

@api_router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Transcribe audio to text using Whisper"""
    try:
        # Save uploaded file temporarily
        temp_path = f"/tmp/audio_{uuid.uuid4()}.webm"
        
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Transcribe using Whisper
        with open(temp_path, "rb") as audio_file:
            transcript = await openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="tr"  # Turkish
            )
        
        # Cleanup
        os.remove(temp_path)
        
        return {"text": transcript.text}
        
    except Exception as e:
        logging.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail="Transcription failed")

# ============= DOCTOR ROUTES =============

@api_router.get("/doctor/patients")
async def get_doctor_patients(request: Request):
    """Get all patients assigned to doctor"""
    user = await get_current_user(request)
    if not user or user.user_type not in ["doctor", "psychiatrist"]:
        raise HTTPException(status_code=403, detail="Only doctors can access")
    
    # Get assigned patients
    patients = await db.users.find(
        {"_id": {"$in": user.assigned_patients}}
    ).to_list(100)
    
    # Get session counts and risk levels for each patient
    for patient in patients:
        patient_id = patient["_id"]
        patient["id"] = patient_id  # Add id field for consistency
        
        session_count = await db.therapy_sessions.count_documents({"user_id": patient_id})
        patient["session_count"] = session_count
        
        # Get latest risk assessment
        latest_risk = await db.risk_assessments.find_one(
            {"user_id": patient_id},
            sort=[("timestamp", -1)]
        )
        patient["latest_risk"] = latest_risk["risk_category"] if latest_risk else "low"
        
        # Remove _id to avoid serialization issues
        patient.pop("_id", None)
    
    return patients

@api_router.post("/doctor/add-patient")
async def add_patient_to_doctor(request: Request):
    """Add patient to doctor using patient ID"""
    user = await get_current_user(request)
    if not user or user.user_type not in ["doctor", "psychiatrist"]:
        raise HTTPException(status_code=403, detail="Only doctors can access")
    
    data = await request.json()
    patient_id_number = data.get("patient_id_number")
    
    # Find patient by ID number
    patient = await db.users.find_one({"user_id_number": patient_id_number})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    if patient.get("user_type") != "patient":
        raise HTTPException(status_code=400, detail="User is not a patient")
    
    # Add patient to doctor's list
    if patient["_id"] not in user.assigned_patients:
        await db.users.update_one(
            {"_id": user.id},
            {"$push": {"assigned_patients": patient["_id"]}}
        )
    
    # Set doctor for patient
    await db.users.update_one(
        {"_id": patient["_id"]},
        {"$set": {"assigned_doctor_id": user.id}}
    )
    
    return {"success": True, "patient": patient}

@api_router.get("/doctor/patient/{patient_id}/risk-alerts")
async def get_patient_risk_alerts(request: Request, patient_id: str):
    """Get risk assessments for a patient"""
    user = await get_current_user(request)
    if not user or user.user_type not in ["doctor", "psychiatrist"]:
        raise HTTPException(status_code=403, detail="Only doctors can access")
    
    # Verify patient is assigned to doctor
    assigned_patient_ids = [str(pid) for pid in user.assigned_patients]
    if patient_id not in assigned_patient_ids:
        raise HTTPException(status_code=403, detail="Patient not assigned to you")
    
    # Get risk assessments
    risks = await db.risk_assessments.find(
        {"user_id": patient_id},
        {"_id": 0}
    ).sort("timestamp", -1).limit(50).to_list(50)
    
    return risks

@api_router.post("/doctor/patient/{patient_id}/note")
async def add_doctor_note(request: Request, patient_id: str):
    """Add clinical note for patient"""
    user = await get_current_user(request)
    if not user or user.user_type not in ["doctor", "psychiatrist"]:
        raise HTTPException(status_code=403, detail="Only doctors can access")
    
    # Convert assigned_patients to strings for comparison
    assigned_patient_ids = [str(pid) for pid in user.assigned_patients]
    if patient_id not in assigned_patient_ids:
        raise HTTPException(status_code=403, detail="Patient not assigned to you")
    
    data = await request.json()
    
    note = {
        "id": str(uuid.uuid4()),
        "doctor_id": user.id,
        "patient_id": patient_id,
        "session_id": data.get("session_id"),
        "note_type": data.get("note_type", "clinical_note"),
        "content": data.get("content"),
        "tags": data.get("tags", []),
        "timestamp": datetime.now(timezone.utc)
    }
    
    await db.doctor_notes.insert_one(note)
    
    # Return serializable version (exclude MongoDB _id)
    note_response = {
        "id": note["id"],
        "doctor_id": note["doctor_id"],
        "patient_id": note["patient_id"],
        "session_id": note["session_id"],
        "note_type": note["note_type"],
        "content": note["content"],
        "tags": note["tags"],
        "timestamp": note["timestamp"].isoformat()
    }
    return {"success": True, "note": note_response}

@api_router.get("/doctor/patient/{patient_id}/notes")
async def get_patient_notes(request: Request, patient_id: str):
    """Get all notes for a patient"""
    user = await get_current_user(request)
    if not user or user.user_type not in ["doctor", "psychiatrist"]:
        raise HTTPException(status_code=403, detail="Only doctors can access")
    
    assigned_patient_ids = [str(pid) for pid in user.assigned_patients]
    if patient_id not in assigned_patient_ids:
        raise HTTPException(status_code=403, detail="Patient not assigned to you")
    
    notes = await db.doctor_notes.find(
        {"patient_id": patient_id},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(100)
    
    return notes

# ============= ADMIN ROUTES =============

@api_router.post("/admin/login")
async def admin_login(request: Request, response: Response):
    """Admin login endpoint"""
    data = await request.json()
    email = data.get("email")
    password = data.get("password")
    
    if email != ADMIN_EMAIL or password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create admin session
    admin_token = f"admin_session_{uuid.uuid4()}"
    admin_session_doc = {
        "session_token": admin_token,
        "email": email,
        "expires_at": datetime.now(timezone.utc) + timedelta(days=1),
        "created_at": datetime.now(timezone.utc)
    }
    await db.admin_sessions.insert_one(admin_session_doc)
    
    # Set cookie
    response.set_cookie(
        key="admin_token",
        value=admin_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=24*60*60,
        path="/"
    )
    
    return {"success": True, "email": email}

@api_router.post("/admin/logout")
async def admin_logout(request: Request, response: Response):
    """Admin logout"""
    admin_token = request.cookies.get("admin_token")
    if admin_token:
        await db.admin_sessions.delete_many({"session_token": admin_token})
    response.delete_cookie("admin_token", path="/")
    return {"success": True}

@api_router.get("/admin/verify")
async def verify_admin_access(request: Request):
    """Verify admin session"""
    is_admin = await verify_admin(request)
    if not is_admin:
        raise HTTPException(status_code=401, detail="Not authorized")
    return {"success": True}

@api_router.get("/admin/stats")
async def get_admin_stats(request: Request):
    """Get platform statistics"""
    is_admin = await verify_admin(request)
    if not is_admin:
        raise HTTPException(status_code=401, detail="Not authorized")
    
    # Count documents
    total_users = await db.users.count_documents({})
    total_sessions = await db.therapy_sessions.count_documents({})
    total_messages = await db.messages.count_documents({})
    active_sessions = await db.therapy_sessions.count_documents({"status": "active"})
    total_analyses = await db.video_analyses.count_documents({})
    
    # Recent activity
    recent_sessions = await db.therapy_sessions.find({}).sort("started_at", -1).limit(10).to_list(10)
    recent_users = await db.users.find({}).sort("created_at", -1).limit(10).to_list(10)
    
    # Average stress level
    all_analyses = await db.video_analyses.find({"stress_level": {"$exists": True}}).to_list(1000)
    avg_stress = sum([a.get("stress_level", 0) for a in all_analyses]) / len(all_analyses) if all_analyses else 0
    
    # Emotion distribution
    emotions = [a.get("emotion_detected") for a in all_analyses if a.get("emotion_detected")]
    from collections import Counter
    emotion_counts = dict(Counter(emotions))
    
    return {
        "totals": {
            "users": total_users,
            "sessions": total_sessions,
            "messages": total_messages,
            "active_sessions": active_sessions,
            "video_analyses": total_analyses
        },
        "analytics": {
            "average_stress": round(avg_stress, 2),
            "emotion_distribution": emotion_counts
        },
        "recent_activity": {
            "sessions": [{"id": s.get("id"), "user_id": s.get("user_id"), "started_at": s.get("started_at"), "status": s.get("status")} for s in recent_sessions],
            "users": [{"email": u.get("email"), "name": u.get("name"), "created_at": u.get("created_at")} for u in recent_users]
        }
    }

@api_router.get("/admin/users")
async def get_all_users(request: Request):
    """Get all users"""
    is_admin = await verify_admin(request)
    if not is_admin:
        raise HTTPException(status_code=401, detail="Not authorized")
    
    users = await db.users.find({}, {"_id": 1, "email": 1, "name": 1, "picture": 1, "created_at": 1}).to_list(1000)
    
    # Get session counts for each user
    for user in users:
        session_count = await db.therapy_sessions.count_documents({"user_id": user["_id"]})
        message_count = await db.messages.count_documents({"user_id": user["_id"]})
        user["session_count"] = session_count
        user["message_count"] = message_count
        user["id"] = user.pop("_id")
    
    return users

@api_router.get("/admin/users/{user_id}")
async def get_user_detail(request: Request, user_id: str):
    """Get user details"""
    is_admin = await verify_admin(request)
    if not is_admin:
        raise HTTPException(status_code=401, detail="Not authorized")
    
    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    sessions = await db.therapy_sessions.find({"user_id": user_id}).sort("started_at", -1).to_list(100)
    messages = await db.messages.find({"user_id": user_id}, {"_id": 0}).sort("timestamp", -1).to_list(500)  # Increased to 500
    
    user["id"] = user.pop("_id")
    
    return {
        "user": user,
        "sessions": sessions,
        "recent_messages": messages
    }

@api_router.get("/admin/sessions")
async def get_all_sessions(request: Request, limit: int = 50):
    """Get all therapy sessions"""
    is_admin = await verify_admin(request)
    if not is_admin:
        raise HTTPException(status_code=401, detail="Not authorized")
    
    sessions = await db.therapy_sessions.find({}).sort("started_at", -1).limit(limit).to_list(limit)
    
    return sessions

@api_router.get("/admin/sessions/{session_id}/messages")
async def get_session_messages_admin(request: Request, session_id: str):
    """Get session messages (admin)"""
    is_admin = await verify_admin(request)
    if not is_admin:
        raise HTTPException(status_code=401, detail="Not authorized")
    
    messages = await db.messages.find({"session_id": session_id}, {"_id": 0}).sort("timestamp", 1).to_list(1000)
    
    return messages

@api_router.get("/admin/settings")
async def get_ai_settings(request: Request):
    """Get AI settings"""
    is_admin = await verify_admin(request)
    if not is_admin:
        raise HTTPException(status_code=401, detail="Not authorized")
    
    settings = await db.ai_settings.find_one({})
    
    if not settings:
        # Default settings
        default_settings = {
            "id": str(uuid.uuid4()),
            "chat_model": "gpt-5",
            "chat_provider": "openai",
            "vision_model": "gemini-2.5-pro",
            "tts_voice": "nova",
            "tts_model": "tts-1",
            "system_prompt": "Sen BerkAI'sın, empatik ve profesyonel bir psikolojik destek asistanısın.",
            "max_message_length": 2000,
            "enable_video_analysis": True,
            "enable_tts": True,
            "updated_at": datetime.now(timezone.utc)
        }
        await db.ai_settings.insert_one(default_settings)
        return default_settings
    
    return settings

@api_router.put("/admin/settings")
async def update_ai_settings(request: Request):
    """Update AI settings"""
    is_admin = await verify_admin(request)
    if not is_admin:
        raise HTTPException(status_code=401, detail="Not authorized")
    
    data = await request.json()
    data["updated_at"] = datetime.now(timezone.utc)
    
    await db.ai_settings.update_one(
        {},
        {"$set": data},
        upsert=True
    )
    
    return {"success": True}

@api_router.get("/admin/all-messages")
async def get_all_messages(request: Request, limit: int = 100, skip: int = 0, user_id: str = None):
    """Get all messages with filtering"""
    is_admin = await verify_admin(request)
    if not is_admin:
        raise HTTPException(status_code=401, detail="Not authorized")
    
    query = {}
    if user_id:
        query["user_id"] = user_id
    
    messages = await db.messages.find(query, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
    total_count = await db.messages.count_documents(query)
    
    # Enrich with user info
    for msg in messages:
        user = await db.users.find_one({"_id": msg.get("user_id")}, {"name": 1, "email": 1})
        if user:
            msg["user_name"] = user.get("name", "Unknown")
            msg["user_email"] = user.get("email", "Unknown")
    
    return {
        "messages": messages,
        "total": total_count,
        "skip": skip,
        "limit": limit
    }

@api_router.get("/admin/profiles")
async def get_all_profiles(request: Request):
    """Get all user profiles (RAG system)"""
    is_admin = await verify_admin(request)
    if not is_admin:
        raise HTTPException(status_code=401, detail="Not authorized")
    
    profiles = await db.user_profiles.find({}, {"_id": 0}).to_list(1000)
    
    # Enrich with user info
    for profile in profiles:
        user = await db.users.find_one({"_id": profile.get("user_id")}, {"name": 1, "email": 1})
        if user:
            profile["user_name"] = user.get("name", "Unknown")
            profile["user_email"] = user.get("email", "Unknown")
    
    return profiles

@api_router.get("/admin/search")
async def search_messages(request: Request, query: str, limit: int = 50):
    """Search messages by content"""
    is_admin = await verify_admin(request)
    if not is_admin:
        raise HTTPException(status_code=401, detail="Not authorized")
    
    # Search in message content
    messages = await db.messages.find(
        {"content": {"$regex": query, "$options": "i"}},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    # Enrich with user and session info
    for msg in messages:
        user = await db.users.find_one({"_id": msg.get("user_id")}, {"name": 1, "email": 1})
        session = await db.therapy_sessions.find_one({"id": msg.get("session_id")}, {"session_name": 1, "started_at": 1})
        
        if user:
            msg["user_name"] = user.get("name", "Unknown")
            msg["user_email"] = user.get("email", "Unknown")
        if session:
            msg["session_name"] = session.get("session_name", "Unknown")
            msg["session_date"] = session.get("started_at")
    
    return {"results": messages, "count": len(messages), "query": query}

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