from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from backend.app.core.security import actor_from_token
from backend.app.db.database import rows
from backend.app.services.audit_service import record
from backend.app.services.codex_service import start_codex
from backend.app.services.hermes_service import send_hermes_chat
from backend.app.services.runtime_service import runtime_status

router = APIRouter(prefix='/api')

class RuntimeCodexIn(BaseModel):
    task: str
    workspace: str
    branch: str | None = None
    test_command: str | None = None
    auto_commit: bool = False
    background: bool = True

class RuntimeHermesChatIn(BaseModel):
    message: str
    thread_id: str | None = None

def actor(req: Request):
    return actor_from_token(req.headers.get('x-admin-token') or req.headers.get('authorization'))

@router.get('/systems/status')
async def systems_status_runtime():
    status = await runtime_status()
    recent_failed = rows("SELECT * FROM audit_log WHERE status IN ('failed','error') ORDER BY id DESC LIMIT 5")
    active = rows("SELECT * FROM agent_processes WHERE status='running' ORDER BY started_at DESC")
    for system in status['systems']:
        prefix = str(system.get('name','')).split('-')[0]
        system['active_sessions'] = len([p for p in active if prefix in p.get('kind','')])
    status['active_processes'] = active
    status['recent_failed_actions'] = recent_failed
    return status

@router.post('/codex/run')
async def codex_run_runtime(body: RuntimeCodexIn, request: Request):
    try:
        return start_codex(**body.model_dump(), actor=actor(request))
    except Exception as e:
        record('codex.run.start','failed',actor=actor(request),target_agent='codex-worker',workspace=body.workspace,command_type='codex',error=e)
        raise HTTPException(400, str(e))

@router.post('/hermes/chat')
def hermes_chat_runtime(body: RuntimeHermesChatIn, request: Request):
    try:
        return send_hermes_chat(body.message, body.thread_id, actor(request))
    except Exception as e:
        raise HTTPException(502, str(e))
