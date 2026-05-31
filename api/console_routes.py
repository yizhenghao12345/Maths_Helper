import os

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from typing import Optional

from console_auth import (
    verify_console_password,
    create_console_token,
    verify_console_token,
    logout_console_token,
    get_current_console_user,
)
import db
from ai_service import ai_service, PROVIDER_PRESETS, mask_api_key


router = APIRouter(prefix="/console", tags=["console"])


class LoginRequest(BaseModel):
    password: str


class AIConfigRequest(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None


class TestConnectionRequest(BaseModel):
    provider: str
    api_key: str
    base_url: str
    model: str


@router.post("/login")
async def login(request: LoginRequest):
    if not verify_console_password(request.password):
        raise HTTPException(status_code=401, detail="密码错误")
    token = create_console_token()
    return {"token": token}


@router.post("/logout")
async def logout(request: Request, user=Depends(get_current_console_user)):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    logout_console_token(token)
    return {"message": "已登出"}


@router.get("/health")
async def health(user=Depends(get_current_console_user)):
    db_path = db.DB_PATH
    db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
    session_count = db.get_stats()["total_sessions"]
    return {
        "status": "ok",
        "version": "0.0.4",
        "ai_enabled": ai_service.enabled,
        "ai_provider": ai_service.provider if ai_service.enabled else None,
        "ai_model": ai_service.model if ai_service.enabled else None,
        "ai_base_url": ai_service.base_url if ai_service.enabled else None,
        "db_size": db_size,
        "session_count": session_count,
    }


@router.get("/sessions")
async def list_sessions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: str = Query("all", pattern="^(active|completed|all)$"),
    user=Depends(get_current_console_user),
):
    if status == "active":
        conn = db._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM sessions WHERE is_completed = 0 ORDER BY last_active DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
            sessions = [db._row_to_session_dict(r) for r in rows]
            total = conn.execute("SELECT COUNT(*) FROM sessions WHERE is_completed = 0").fetchone()[0]
        finally:
            conn.close()
    elif status == "completed":
        conn = db._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM sessions WHERE is_completed = 1 ORDER BY last_active DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
            sessions = [db._row_to_session_dict(r) for r in rows]
            total = conn.execute("SELECT COUNT(*) FROM sessions WHERE is_completed = 1").fetchone()[0]
        finally:
            conn.close()
    else:
        sessions = db.list_sessions(limit=limit, offset=offset)
        conn = db._get_conn()
        try:
            total = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        finally:
            conn.close()
    return {"sessions": sessions, "total": total}


@router.get("/sessions/{session_id}")
async def get_session_detail(session_id: str, user=Depends(get_current_console_user)):
    session = db.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    history = db.get_question_history(session_id)
    return {"session": session, "question_history": history}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, user=Depends(get_current_console_user)):
    session = db.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    db.delete_session(session_id)
    return {"message": "会话已删除"}


@router.delete("/sessions")
async def cleanup_sessions(user=Depends(get_current_console_user)):
    count = db.cleanup_expired(1800)
    return {"message": f"清理了 {count} 个过期会话"}


@router.get("/stats")
async def get_stats(user=Depends(get_current_console_user)):
    return db.get_stats()


@router.get("/ai-logs")
async def get_ai_logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user=Depends(get_current_console_user),
):
    logs = db.get_ai_logs(limit=limit, offset=offset)
    return {"logs": logs}


@router.get("/providers")
async def get_providers(user=Depends(get_current_console_user)):
    return PROVIDER_PRESETS


@router.post("/test-connection")
async def test_connection(
    request: TestConnectionRequest, user=Depends(get_current_console_user)
):
    result = await ai_service.test_connection(
        provider=request.provider,
        api_key=request.api_key,
        base_url=request.base_url,
        model=request.model,
    )
    return result


@router.get("/ai-config")
async def get_ai_config(user=Depends(get_current_console_user)):
    return ai_service.get_full_config()


@router.patch("/ai-config")
async def update_ai_config(
    request: AIConfigRequest, user=Depends(get_current_console_user)
):
    if request.provider is not None:
        ai_service.provider = request.provider.lower()
        os.environ["AI_PROVIDER"] = request.provider
    if request.model is not None:
        ai_service.model = request.model
        os.environ["AI_MODEL"] = request.model
    if request.api_key is not None:
        ai_service.api_key = request.api_key
        os.environ["AI_API_KEY"] = request.api_key
        ai_service.enabled = bool(request.api_key)
    if request.base_url is not None:
        ai_service.base_url = request.base_url
        os.environ["AI_BASE_URL"] = request.base_url
    return {
        "provider": ai_service.provider,
        "model": ai_service.model,
        "enabled": ai_service.enabled,
        "base_url": ai_service.base_url,
        "api_key_masked": mask_api_key(ai_service.api_key),
    }
